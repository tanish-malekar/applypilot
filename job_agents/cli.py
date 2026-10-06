import argparse
import json
from pathlib import Path

import httpx

from job_agents.eligibility import evaluate
from job_agents.models import Applicant, Job


def main():
    parser = argparse.ArgumentParser(description="Run the local job application POC")
    parser.add_argument("command", choices=["demo", "eligibility"])
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--applicant", type=Path, default=Path("examples/applicant.json"))
    parser.add_argument("--jobs", type=Path, default=Path("examples/jobs.json"))
    parser.add_argument("--approve-sandbox", action="store_true")
    args = parser.parse_args()
    applicant = Applicant.model_validate_json(args.applicant.read_text())
    jobs = [Job.model_validate(j) for j in json.loads(args.jobs.read_text())]
    if args.command == "eligibility":
        print(
            json.dumps(
                [{"job_id": j.id, **evaluate(applicant, j).model_dump(mode="json")} for j in jobs],
                indent=2,
            )
        )
        return
    with httpx.Client(base_url=args.base_url, timeout=90) as client:
        response = client.post(
            "/api/runs",
            json={
                "applicant": applicant.model_dump(mode="json"),
                "job": jobs[0].model_dump(mode="json"),
            },
        )
        response.raise_for_status()
        run = response.json()
        if args.approve_sandbox and run["status"] == "awaiting_review":
            response = client.post(f"/api/runs/{run['run_id']}/resume", json={"approved": True})
            response.raise_for_status()
            run = response.json()
        print(json.dumps(run, indent=2))


if __name__ == "__main__":
    main()
