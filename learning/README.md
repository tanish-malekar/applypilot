# Learned Resume Tailor and Form Navigator

The LangGraph workflow connects a Resume Tailor, a Playwright Form Navigator, and
an independent Verifier before its existing human review interrupt. Learned paths
are opt-in; deterministic/Groq/Ollama modes remain available for the hosted demo.

## SFT resume rewriting

```sh
pip install -e '.[learning]'
python learning/train_resume.py --train learning/examples/train.jsonl --validation learning/examples/validation.jsonl --output learning/artifacts/resume
# Then configure the server process:
export CONTENT_MODE=sft
export RESUME_SFT_ADAPTER=learning/artifacts/resume/adapter
```

The supplied 48/12 synthetic pairs demonstrate the schema using fictional people;
production adaptation should use consented, reviewed examples with broader
coverage. Each row contains an ID, profile ID, job, verified facts, and edited
bullets with source fact IDs. All variants of a profile belong to one split.
The trainer rejects profile/fact overlap, pins the base revision, masks prompt
loss, and selects a rank-16 LoRA adapter by validation completion loss. It saves
adapter weights and a manifest containing data hashes and model/prompt identity.

SFT mode loads that adapter locally through PyTorch/Transformers/PEFT and writes
resume bullets; it does not silently substitute an untuned model. Source IDs,
quantity preservation, and proper-noun checks run at generation and verification.
They are conservative structural checks, not proof of semantic entailment.
Review rewritten claims before approving. Original facts, cover letters, and
question answers remain separately available. The verifier checks browser values
and the uploaded resume before submission.

## RL DOM policy

```sh
python -m playwright install chromium
python learning/train_dom.py --output learning/artifacts/dom --episodes 4000
export DOM_POLICY_PATH=learning/artifacts/dom/policy.pt
```

REINFORCE optimizes an eight-feature MLP in a contextual-bandit environment.
A state is a requested field and visible DOM candidates; actions select a
compatible editable control. Rewards use the actual target field plus Playwright
readback, penalize wrong targets, and include bounded action cost. Layout order,
labels, and IDs vary across local generated forms. Training records per-episode
reward and latency. The policy is greedy at inference and cannot click submit,
open links, or change the existing browser's loopback network boundary. The
independent verifier still reads canonical sandbox fields, so a mistaken policy
mapping cannot pass on the strength of its own action trace. Policy weights and
feature/algorithm metadata are loaded together; missing artifacts fail explicitly.

This is one-step RL for field selection, not a general website navigation model.
Evaluate new ATS schemas and held-out label/layout families before expanding its
action space. Employer websites are outside this repository's execution adapter.

## 150-posting paired evaluation

Record one JSON line for each distinct posting with `posting_id`, and `manual`,
`baseline`, `learned` objects containing `seconds`, `correct_fields`, `total_fields`.
Use the same applicant, required fields, and posting for all modes. Keep postings
and employer/layout families out of training. Include eligibility handling,
resume editing, review, and corrections in elapsed time; independently review
field correctness before correction. Use consented observations or controlled
replicas and retain dataset provenance beside the private ledger.

```sh
python scripts/report_application_benchmark.py learning/private/sessions.jsonl --output learning/artifacts/benchmark.json
```

The reporter requires 150 unique paired postings, rejects invalid denominators,
and calculates time reduction versus manual entry, field accuracy, absolute
percentage-point gain, and relative lift versus baseline autofill. Synthetic
training episodes and the recorded dashboard demo are separate from this ledger.

Model training and inference require a suitably provisioned GPU/model host;
install the learning extra separately from the Render free-tier demo image.
Training data and model weights remain ignored locally. No hub upload is automatic.

References: [TRL SFTTrainer](https://huggingface.co/docs/trl/sft_trainer),
[PyTorch distributions](https://docs.pytorch.org/docs/stable/distributions.html),
[Playwright locators](https://playwright.dev/python/docs/locators).
