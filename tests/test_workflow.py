import pytest

from job_agents.models import RunRequest
from job_agents.workflow import Workflow
from tests.conftest import FakeBrowser


def test_review_is_required_and_rejection_does_not_submit(tmp_path, request_data):
    browser = FakeBrowser()
    flow = Workflow(tmp_path, browser=browser)
    run = flow.start(request_data)
    assert run["status"] == "awaiting_review"
    assert browser.submissions == 0
    run = flow.resume(run["run_id"], {"approved": False})
    assert run["status"] == "rejected"
    assert browser.submissions == 0
    flow.close()


def test_restart_preserves_pending_review(tmp_path, request_data):
    flow = Workflow(tmp_path, browser=FakeBrowser())
    run = flow.start(request_data)
    flow.close()
    browser = FakeBrowser()
    restarted = Workflow(tmp_path, browser=browser)
    run = restarted.resume(run["run_id"], {"approved": True})
    assert run["status"] == "submitted"
    assert browser.submissions == 1
    assert sum(e["agent"] == "content" for e in run["trace"]) == 1
    with pytest.raises(ValueError, match="not waiting"):
        restarted.resume(run["run_id"], {"approved": True})
    restarted.close()


def test_missing_fact_is_reused_and_scoped(tmp_path, request_data):
    browser = FakeBrowser()
    flow = Workflow(tmp_path, browser=browser)
    request_data.applicant.work_authorized = None
    first = flow.start(request_data)
    assert first["status"] == "needs_information"
    assert browser.preparations == 0
    first = flow.resume(first["run_id"], {"work_authorized": True})
    assert first["status"] == "awaiting_review"
    second = flow.start(request_data)
    assert second["status"] == "awaiting_review"
    assert second["applicant"]["work_authorized"] is True
    request_data.applicant.id = "different-applicant"
    assert flow.start(request_data)["status"] == "needs_information"
    flow.close()


def test_failures_stop_before_review(tmp_path, request_data):
    browser = FakeBrowser(mismatch=True)
    flow = Workflow(tmp_path, browser=browser)
    run = flow.start(request_data)
    assert run["status"] == "verification_failed"
    assert not run["pending"]
    assert browser.submissions == 0
    flow.close()


def test_navigation_failure_is_visible(tmp_path, request_data):
    flow = Workflow(tmp_path, browser=FakeBrowser(crash=True))
    run = flow.start(request_data)
    assert run["status"] == "failed"
    assert "navigation failed" in run["trace"][-2]["message"]
    flow.close()


@pytest.mark.parametrize("index,expected", [(1, "ineligible"), (2, "blocked")])
def test_ineligible_and_unknown_jobs_do_not_execute(tmp_path, applicant, jobs, index, expected):
    browser = FakeBrowser()
    flow = Workflow(tmp_path, browser=browser)
    run = flow.start(RunRequest(applicant=applicant, job=jobs[index]))
    assert run["status"] == expected
    assert browser.preparations == 0
    flow.close()


def test_invalid_resume_preserves_interrupt(tmp_path, request_data):
    flow = Workflow(tmp_path, browser=FakeBrowser())
    request_data.applicant.work_authorized = None
    run = flow.start(request_data)
    with pytest.raises(ValueError):
        flow.resume(run["run_id"], {"work_authorized": True, "degree": "phd"})
    assert flow.snapshot(run["run_id"])["status"] == "needs_information"
    assert flow.resume(run["run_id"], {"work_authorized": True})["status"] == "awaiting_review"
    flow.close()
