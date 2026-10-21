"""Train an evidence-bound LoRA resume adapter from reviewed prompt/completion pairs."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from job_agents.models import ResumeRewrite
from job_agents.tailor import PROMPT_VERSION, prompt, validate_rewrites


def load(path):
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if not rows or len({r["id"] for r in rows}) != len(rows): raise ValueError("Unique nonempty row IDs required")
    for row in rows:
        validate_rewrites([ResumeRewrite.model_validate(b) for b in row["bullets"]], row["facts"])
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--validation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-model", default="Qwen/Qwen2.5-Coder-7B-Instruct")
    parser.add_argument("--revision", default="c03e6d358207e414f1eca0bb1891e29f1db0e242")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-f0-9]{40}", args.revision): raise ValueError("Pin an immutable revision")
    train, validation = load(args.train), load(args.validation)
    # A person's facts and every augmentation of them belong to one split.
    def identities(rows):
        return {r["profile_id"] for r in rows}, {json.dumps(r["facts"], sort_keys=True) for r in rows}
    if any(a & b for a, b in zip(identities(train), identities(validation))):
        raise ValueError("Profile leakage between train and validation")
    import torch
    from datasets import Dataset
    from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed
    from peft import LoraConfig
    from trl import SFTConfig, SFTTrainer
    if not torch.cuda.is_available(): raise RuntimeError("This SFT recipe requires a CUDA GPU")
    set_seed(42)
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, revision=args.revision, trust_remote_code=False)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    def prepare(rows):
        output = []
        for row in rows:
            messages = prompt(row["job"], row["facts"])
            completion = [{"role": "assistant", "content": json.dumps({"bullets": row["bullets"]})}]
            if len(tokenizer.apply_chat_template(messages + completion)) > 4096:
                raise ValueError("Refusing to truncate source evidence or completion")
            output.append({"prompt": messages, "completion": completion})
        return Dataset.from_list(output)
    training_data, validation_data = prepare(train), prepare(validation)
    args.output.mkdir(parents=True, exist_ok=False)
    bf16 = torch.cuda.is_bf16_supported()
    model = AutoModelForCausalLM.from_pretrained(args.base_model, revision=args.revision,
        trust_remote_code=False, torch_dtype=torch.bfloat16 if bf16 else torch.float16)
    model.config.use_cache = False
    model.enable_input_require_grads()
    config = SFTConfig(output_dir=str(args.output), num_train_epochs=3,
        per_device_train_batch_size=1, per_device_eval_batch_size=1, gradient_accumulation_steps=8,
        learning_rate=2e-4, max_length=4096, completion_only_loss=True, packing=False,
        bf16=bf16, fp16=not bf16, gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False}, eval_strategy="epoch", save_strategy="epoch",
        load_best_model_at_end=True, metric_for_best_model="eval_loss", greater_is_better=False,
        save_total_limit=2, report_to=[], seed=42, eos_token=tokenizer.eos_token)
    trainer = SFTTrainer(model=model, args=config, train_dataset=training_data,
        eval_dataset=validation_data, processing_class=tokenizer,
        peft_config=LoraConfig(r=16, lora_alpha=32, lora_dropout=.05, task_type="CAUSAL_LM",
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]))
    result = trainer.train()
    adapter = args.output / "adapter"
    trainer.save_model(str(adapter)); tokenizer.save_pretrained(adapter)
    manifest = {"prompt_version": PROMPT_VERSION, "base_model": args.base_model, "revision": args.revision,
        "train_rows": len(train), "validation_rows": len(validation), "metrics": result.metrics,
        "data_sha256": {str(path.name): hashlib.sha256(path.read_bytes()).hexdigest() for path in [args.train, args.validation]},
        "selection": "validation completion loss"}
    (adapter / "training_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__": main()
