"""Online REINFORCE over local Playwright form environments, never employer sites."""
import argparse
import hashlib
import html
import json
import random
import time
from pathlib import Path
from job_agents.dom_policy import ALIASES, FEATURE_VERSION, compatible, features, network, scan


def main():
    import torch
    from playwright.sync_api import sync_playwright
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=4000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.episodes < 1: raise ValueError("Episodes must be positive")
    args.output.mkdir(parents=True, exist_ok=False)
    rng = random.Random(args.seed); torch.manual_seed(args.seed)
    model = network(); optimizer = torch.optim.Adam(model.parameters(), lr=.003)
    baseline, ledger = 0., []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            # No page may reach an external service, including during training.
            page.route("**/*", lambda route: route.abort())
            for episode in range(args.episodes):
                fields = list(ALIASES); rng.shuffle(fields)
                target = rng.choice(fields)
                controls = []
                for index, field in enumerate(fields):
                    label = rng.choice(ALIASES[field])
                    identity = field if rng.random() < .25 else f"field-{rng.randrange(10**9)}"
                    if field in {"work_authorized", "needs_sponsorship"}:
                        control = f'<select id="{identity}"><option value="">Choose</option><option value="yes">Yes</option><option value="no">No</option></select>'
                    elif field in {"cover_letter", "application_answers"}:
                        control = f'<textarea id="{identity}"></textarea>'
                    else:
                        typ = "file" if field == "resume" else "email" if field == "email" else "text"
                        control = f'<input id="{identity}" type="{typ}">'
                    controls.append(f'<label for="{identity}">{html.escape(label)}</label>{control}')
                page.set_content('<form>' + ''.join(controls) + '<button type="submit">Submit</button></form>')
                candidates = [c for c in scan(page) if compatible(target, c)]
                x = torch.tensor([features(target, c, set()) for c in candidates], dtype=torch.float32)
                distribution = torch.distributions.Categorical(logits=model(x).flatten())
                action = distribution.sample(); chosen = candidates[int(action)]
                locator = page.locator(f'[data-applypilot-slot="{chosen["slot"]}"]')
                start = time.perf_counter()
                value = 'candidate@example.test' if target == 'email' else 'sample answer'
                if target == 'resume':
                    locator.set_input_files({"name": "resume.txt", "mimeType": "text/plain", "buffer": b"Fictional resume"})
                    readback = locator.evaluate("el => el.files[0].name") == "resume.txt"
                elif chosen['tag'] == 'select':
                    locator.select_option('yes'); readback = locator.input_value() == 'yes'
                else:
                    locator.fill(value); readback = locator.input_value() == value
                correct = chosen['slot'] == fields.index(target) and readback
                latency = time.perf_counter() - start
                reward = (1. if correct else -2.) - .01 * min(latency, 5.)
                advantage = reward - baseline
                loss = -distribution.log_prob(action) * advantage - .01 * distribution.entropy()
                optimizer.zero_grad(); loss.backward(); optimizer.step()
                baseline = .95 * baseline + .05 * reward
                ledger.append({"episode": episode, "correct": correct, "reward": reward, "action_seconds": latency})
        finally: browser.close()
    torch.save(model.state_dict(), args.output / 'policy.pt')
    manifest = {"weights_sha256": hashlib.sha256((args.output / "policy.pt").read_bytes()).hexdigest(),
        "feature_version": FEATURE_VERSION, "algorithm": "REINFORCE contextual bandit",
        "episodes": args.episodes, "seed": args.seed, "reward": "+1 correct field/readback; -2 wrong field; minus .01 per capped action second",
        "environment": "synthetic local forms; eight field intents; no submit action"}
    (args.output / 'policy.json').write_text(json.dumps(manifest, indent=2) + "\n")
    (args.output / 'training.jsonl').write_text(''.join(json.dumps(row) + "\n" for row in ledger))


if __name__ == '__main__': main()
