from fastapi.testclient import TestClient

from job_agents.api import create_app
from tests.conftest import FakeBrowser


def test_visitor_history_and_resume_are_isolated(tmp_path, request_data, monkeypatch):
    monkeypatch.setattr("job_agents.workflow.SandboxBrowser", lambda *args: FakeBrowser())
    app = create_app(tmp_path)
    with TestClient(app) as owner:
        run = owner.post("/api/runs", json=request_data.model_dump(mode="json")).json()
        assert run["status"] == "awaiting_review"
        saved_cookie = owner.cookies.get("visitor")
        owner.cookies.clear()
        assert owner.get("/api/runs").json() == []
        assert owner.get(f"/api/runs/{run['run_id']}").status_code == 404
        assert (
            owner.post(f"/api/runs/{run['run_id']}/resume", json={"approved": True}).status_code
            == 404
        )
        owner.cookies.clear()
        owner.cookies.set("visitor", saved_cookie)
        assert len(owner.get("/api/runs").json()) == 1
