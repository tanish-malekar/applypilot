"""A contextual-bandit DOM policy; submit controls are outside its action space."""
import hashlib
import json
import re
from pathlib import Path

FEATURE_VERSION = "dom-candidate-v1"
ALIASES = {
    "name": ["full name", "your name", "candidate name"],
    "email": ["email", "email address", "contact email"],
    "location": ["location", "city", "home city"],
    "work_authorized": ["authorized to work", "work authorization", "employment eligibility"],
    "needs_sponsorship": ["need sponsorship", "visa sponsorship", "sponsorship required"],
    "cover_letter": ["application statement", "cover letter", "motivation"],
    "application_answers": ["application questions", "additional answers", "screening answers"],
    "resume": ["resume document", "resume", "cv upload"],
}


def words(text):
    return set(re.findall(r"[a-z0-9]+", text.lower().replace("_", " ")))


def compatible(field, candidate):
    typ, tag = candidate["type"], candidate["tag"]
    if field == "resume": return typ == "file"
    if field in {"work_authorized", "needs_sponsorship"}: return tag == "select"
    return tag in {"input", "textarea"} and typ in {"text", "email", "tel", "search", "textarea"}


def features(field, candidate, used):
    label = candidate["label"].lower().strip()
    aliases = ALIASES[field]
    intent = words(" ".join(aliases))
    visible = words(label + " " + candidate["name"] + " " + candidate["id"])
    return [max(len(words(alias) & visible) / max(1, len(words(alias) | visible)) for alias in aliases),
            float(label in aliases), float(candidate["name"] == field), float(candidate["id"] == field),
            float(compatible(field, candidate)), float(candidate["required"]),
            float(candidate["slot"] in used), len(intent & visible) / max(1, len(intent))]


def scan(page):
    return page.locator("input,textarea,select").evaluate_all("""elements => elements.filter(el =>
      !el.disabled && !el.readOnly && el.type !== 'hidden' && el.type !== 'password' &&
      el.getClientRects().length).map((el, slot) => {
        el.setAttribute('data-applypilot-slot', String(slot));
        return {slot, tag: el.tagName.toLowerCase(), type: el.type || el.tagName.toLowerCase(),
          id: el.id, name: el.name || '', required: el.required,
          label: el.getAttribute('aria-label') || [...(el.labels || [])].map(x => x.textContent).join(' ') || el.placeholder || ''};
      })""")


def network():
    from torch import nn
    return nn.Sequential(nn.Linear(8, 32), nn.Tanh(), nn.Linear(32, 1))


class DOMPolicy:
    def __init__(self, path):
        import torch
        self.torch = torch
        path = Path(path)
        manifest = json.loads(path.with_suffix(".json").read_text())
        if manifest["feature_version"] != FEATURE_VERSION or manifest["algorithm"] != "REINFORCE contextual bandit":
            raise ValueError("Incompatible DOM policy artifact")
        if hashlib.sha256(path.read_bytes()).hexdigest() != manifest["weights_sha256"]:
            raise ValueError("DOM weights do not match their training manifest")
        self.model = network()
        self.model.load_state_dict(torch.load(path, map_location="cpu", weights_only=True))
        self.model.eval()

    def select(self, field, candidates, used):
        allowed = [c for c in candidates if compatible(field, c) and c["slot"] not in used]
        if not allowed: raise ValueError(f"No supported DOM action for {field}")
        with self.torch.inference_mode():
            scores = self.model(self.torch.tensor([features(field, c, used) for c in allowed], dtype=self.torch.float32)).flatten()
        return allowed[int(scores.argmax())]

    def fill(self, page, fields, resume):
        candidates, used, trace = scan(page), set(), []
        for field, value in [*fields.items(), ("resume", resume)]:
            chosen = self.select(field, candidates, used)
            locator = page.locator(f'[data-applypilot-slot="{chosen["slot"]}"]')
            if field == "resume": locator.set_input_files(value)
            elif chosen["tag"] == "select": locator.select_option(value)
            else: locator.fill(value)
            used.add(chosen["slot"])
            trace.append({"field": field, "slot": chosen["slot"], "label": chosen["label"], "policy": FEATURE_VERSION})
        return trace
