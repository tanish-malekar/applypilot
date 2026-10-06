import os

import pytest

from job_agents.workflow import Workflow
from tests.conftest import FakeBrowser


@pytest.mark.postgres
def test_postgres_restores_accounts_artifacts_and_interrupted_workflows(
    tmp_path, request_data, monkeypatch
):
    database_url = os.environ.get("PG_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set PG_TEST_DATABASE_URL to an isolated PostgreSQL test database.")
    monkeypatch.setenv("DATABASE_URL", database_url)
    request_data.applicant.work_authorized = None
    first = Workflow(tmp_path / "first", browser=FakeBrowser())
    run = first.start(request_data)
    assert run["status"] == "needs_information"
    first.store.claim(run["run_id"], "account-one")
    first.store.save_profile("account-one", {"name": "Persistent Test Profile"})
    first.store.save_artifact(run["run_id"], b"test-evidence-bytes")
    first.close()

    second = Workflow(tmp_path / "second", browser=FakeBrowser())
    assert second.store.owns(run["run_id"], "account-one")
    assert not second.store.owns(run["run_id"], "account-two")
    assert second.store.get_profile("account-one")["name"] == "Persistent Test Profile"
    assert second.store.get_artifact(run["run_id"]) == b"test-evidence-bytes"
    prepared = second.resume(run["run_id"], {"work_authorized": True})
    assert prepared["status"] == "awaiting_review"
    second.close()

    third = Workflow(tmp_path / "third", browser=FakeBrowser())
    assert third.store.recall(request_data.applicant.id)["work_authorized"] is True
    submitted = third.resume(run["run_id"], {"approved": True})
    assert submitted["status"] == "submitted"
    with pytest.raises(ValueError, match="not waiting"):
        third.resume(run["run_id"], {"approved": True})
    third.close()
