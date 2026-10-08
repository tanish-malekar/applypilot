"""Eight labeled synthetic workflows against real Chromium and local application sandboxes."""

import argparse
import json
from copy import deepcopy
from pathlib import Path

import httpx

from job_agents.browser import expected_fields, validate_base_url
from job_agents.content import verify_bundle
from job_agents.models import Applicant, Job, PreparedContent

parser = argparse.ArgumentParser()
parser.add_argument("--base-url", default="http://127.0.0.1:8000")
parser.add_argument("--output", type=Path)
args = parser.parse_args()
validate_base_url(args.base_url)
results = []
with httpx.Client(base_url=args.base_url, timeout=90) as client:
    demo = client.get("/api/demo").json()
    cases = [
        ("standard-approved", 0, "submitted"),
        ("alternate-approved", 0, "submitted"),
        ("missing-authorization", 0, "submitted"),
        ("human-question", 0, "submitted"),
        ("human-rejected", 0, "rejected"),
        ("ineligible", 1, "ineligible"),
        ("unknown-policy", 2, "blocked"),
        ("invalid-answer", 0, "needs_information"),
    ]
    for name, index, expected in cases:
        profile, job = deepcopy(demo["applicant"]), deepcopy(demo["jobs"][index])
        # Unique applicant namespaces make memory interventions independent cases.
        profile["id"] = "evaluation-" + name
        if name == "alternate-approved":
            job["form_layout"] = "alternate"
        if name == "missing-authorization":
            profile["work_authorized"] = None
        if name in {"human-question", "invalid-answer"}:
            job["questions"] = [{"id": "start", "prompt": "When can you start?"}]
        response = client.post("/api/runs", json={"applicant": profile, "job": job})
        response.raise_for_status()
        run = response.json()
        interventions = 0
        if name == "missing-authorization":
            interventions += 1
            response = client.post(
                f"/api/runs/{run['run_id']}/resume", json={"work_authorized": True}
            )
            response.raise_for_status()
            run = response.json()
        elif name == "human-question":
            interventions += 1
            response = client.post(
                f"/api/runs/{run['run_id']}/resume", json={"answers": {"start": "June 2027"}}
            )
            response.raise_for_status()
            run = response.json()
        elif name == "invalid-answer":
            response = client.post(
                f"/api/runs/{run['run_id']}/resume", json={"answers": {"start": ""}}
            )
            assert response.status_code == 422
        errors, matches, total = [], 0, 0
        if "browser" in run:
            applicant = Applicant.model_validate(run["applicant"])
            content = PreparedContent.model_validate(run["content"])
            errors = verify_bundle(applicant, Job.model_validate(run["job"]), content)
            fields = expected_fields(applicant, content)
            total = len(fields)
            matches = sum(run["browser"]["fields"].get(k) == v for k, v in fields.items())
            assert run["browser"]["upload"] == ["resume.txt"]
            response = client.get(f"/api/runs/{run['run_id']}/screenshot")
            assert response.status_code == 200 and response.content.startswith(b"\x89PNG")
        if run["status"] == "awaiting_review":
            interventions += 1
            response = client.post(
                f"/api/runs/{run['run_id']}/resume", json={"approved": name != "human-rejected"}
            )
            response.raise_for_status()
            run = response.json()
        results.append(
            {
                "case": name,
                "expected": expected,
                "actual": run["status"],
                "passed": run["status"] == expected and not errors and matches == total,
                "field_matches": matches,
                "field_count": total,
                "grounding_errors": errors,
                "human_interventions": interventions,
            }
        )
report = {
    "dataset": "8 labeled synthetic sandbox workflows; no employer applications",
    "model_mode": "server-configured; results are not model quality benchmarks",
    "cases": results,
    "passed": sum(r["passed"] for r in results),
    "total": len(results),
    "submitted": sum(r["actual"] == "submitted" for r in results),
    "field_matches": sum(r["field_matches"] for r in results),
    "field_count": sum(r["field_count"] for r in results),
    "human_interventions": sum(r["human_interventions"] for r in results),
}
text = json.dumps(report, indent=2) + "\n"
print(text)
if args.output:
    args.output.write_text(text)
if report["passed"] != report["total"]:
    raise SystemExit(1)
