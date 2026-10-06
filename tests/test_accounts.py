import base64
import json
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

from job_agents.api import create_app
from job_agents.auth import Accounts
from tests.conftest import FakeBrowser


@pytest.fixture
def accounts(monkeypatch):
    identities = {"alice-session": str(uuid4()), "bob-session": str(uuid4())}
    original = httpx.AsyncClient

    def upstream(request):
        if request.url.path == "/auth/v1/settings":
            return httpx.Response(200, json={"external": {"google": True}})
        token = request.headers.get("authorization", "").removeprefix("Bearer ")
        if token not in identities:
            return httpx.Response(401, json={"message": "Invalid token"})
        return httpx.Response(
            200,
            json={
                "id": identities[token],
                "email": token.split("-")[0] + "@example.com",
                "email_confirmed_at": "2026-10-06T00:00:00Z",
                "user_metadata": {},
            },
        )

    monkeypatch.setenv("SUPABASE_URL", "https://accounts.example.com")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "sb_publishable_test")
    monkeypatch.setattr(
        "job_agents.auth.httpx.AsyncClient",
        lambda **kwargs: original(transport=httpx.MockTransport(upstream), **kwargs),
    )
    monkeypatch.setattr("job_agents.workflow.SandboxBrowser", lambda *args: FakeBrowser())
    return identities


def test_managed_accounts_verify_tokens_and_isolate_history(tmp_path, request_data, accounts):
    with TestClient(create_app(tmp_path)) as client:
        assert client.get("/").status_code in (200, 503)  # frontend build is independent
        config = client.get("/api/auth/config").json()
        assert config["google_enabled"] and not config["demo_mode"]
        assert client.get("/api/runs").status_code == 401
        assert client.get("/api/profile").status_code == 401
        assert (
            client.get("/api/runs", headers={"Authorization": "Bearer forged"}).status_code == 401
        )
        alice = {"Authorization": "Bearer alice-session"}
        bob = {"Authorization": "Bearer bob-session"}
        new_profile = client.get("/api/profile", headers=alice).json()
        assert new_profile["email"] == "alice@example.com"
        assert new_profile["degree"] is None and new_profile["skills"] == []
        saved = client.post(
            "/api/profile", headers=alice, json=request_data.applicant.model_dump(mode="json")
        )
        assert saved.status_code == 200
        response = client.post(
            "/api/runs", headers=alice, json=request_data.model_dump(mode="json")
        )
        assert response.status_code == 200
        run = response.json()
        assert run["applicant"]["id"] == "user:" + accounts["alice-session"] + ":default"
        client.cookies.clear()
        assert len(client.get("/api/runs", headers=alice).json()) == 1
        assert client.get("/api/runs", headers=bob).json() == []
        assert client.get(f"/api/runs/{run['run_id']}", headers=bob).status_code == 404
        assert client.get(f"/api/runs/{run['run_id']}/screenshot", headers=bob).status_code == 404
        assert (
            client.post(
                f"/api/runs/{run['run_id']}/resume", headers=bob, json={"approved": True}
            ).status_code
            == 404
        )
        assert client.get("/api/profile", headers=bob).json()["email"] == "bob@example.com"
    with TestClient(create_app(tmp_path)) as restarted:
        assert len(restarted.get("/api/runs", headers=alice).json()) == 1
        assert restarted.get("/api/profile", headers=alice).json()["name"] == saved.json()["name"]
        assert (
            restarted.post(
                f"/api/runs/{run['run_id']}/resume", headers=alice, json={"approved": True}
            ).json()["status"]
            == "submitted"
        )


def test_private_keys_are_never_exposed_as_public_config(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://accounts.example.com")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "sb_secret_must_not_be_exposed")
    with pytest.raises(ValueError, match="public"):
        Accounts()
    payload = base64.urlsafe_b64encode(json.dumps({"role": "service_role"}).encode()).decode()
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "header." + payload + ".signature")
    with pytest.raises(ValueError, match="public"):
        Accounts()


def test_required_auth_without_provider_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTH_REQUIRED", "1")
    with TestClient(create_app(tmp_path)) as client:
        assert not client.get("/api/auth/config").json()["demo_mode"]
        assert client.get("/api/runs").status_code == 503


def test_hosted_accounts_require_durable_database(monkeypatch, accounts):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        with TestClient(create_app()):
            pass
