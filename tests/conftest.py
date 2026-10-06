import json
from pathlib import Path

import pytest

from job_agents.browser import expected_fields
from job_agents.models import Applicant, Job, RunRequest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def applicant():
    return Applicant.model_validate_json((ROOT / "examples/applicant.json").read_text())


@pytest.fixture
def jobs():
    return [Job.model_validate(j) for j in json.loads((ROOT / "examples/jobs.json").read_text())]


@pytest.fixture
def request_data(applicant, jobs):
    return RunRequest(applicant=applicant, job=jobs[0])


class FakeBrowser:
    def __init__(self, mismatch=False, crash=False):
        self.mismatch = mismatch
        self.crash = crash
        self.submissions = 0
        self.preparations = 0

    def prepare(self, run_id, applicant, content):
        self.preparations += 1
        if self.crash:
            raise RuntimeError("Browser navigation failed")
        fields = expected_fields(applicant, content)
        if self.mismatch:
            fields["email"] = "wrong@example.com"
        return {"fields": fields, "upload": ["resume.txt"], "errors": []}

    def submit(self, run_id, applicant, content):
        self.submissions += 1
        return {**self.prepare(run_id, applicant, content), "receipt": f"sandbox-{run_id}"}
