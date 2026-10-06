"""Evaluate explicitly labeled synthetic cases; not the brief's proposed 200-posting dataset."""

import json
from pathlib import Path

from sklearn.metrics import classification_report, confusion_matrix

from job_agents.eligibility import evaluate
from job_agents.models import Applicant, Job

ROOT = Path(__file__).resolve().parent.parent
applicant = json.loads((ROOT / "examples/applicant.json").read_text())
jobs = json.loads((ROOT / "examples/jobs.json").read_text())
cases = json.loads((ROOT / "examples/eligibility_cases.json").read_text())
expected, actual, results = [], [], []
for case in cases:
    profile = Applicant.model_validate({**applicant, **case.get("applicant_patch", {})})
    job = Job.model_validate({**jobs[case["job_index"]], **case.get("job_patch", {})})
    result = evaluate(profile, job)
    expected.append(case["expected"])
    actual.append(result.status)
    results.append({"id": case["id"], "expected": case["expected"], "actual": result.status})
labels = ["eligible", "ineligible", "needs_information"]
report = {
    "dataset": "synthetic POC scenarios",
    "n": len(cases),
    "cases": results,
    "classification": classification_report(
        expected, actual, labels=labels, output_dict=True, zero_division=0
    ),
    "confusion_matrix": confusion_matrix(expected, actual, labels=labels).tolist(),
    "label_order": labels,
}
print(json.dumps(report, indent=2))
if expected != actual:
    raise SystemExit(1)
