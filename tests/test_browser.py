import os

import httpx
import pytest


@pytest.mark.browser
def test_real_chromium_prepare_and_submit():
    if os.environ.get("RUN_BROWSER_TESTS") != "1":
        pytest.skip("Set RUN_BROWSER_TESTS=1 and start the local API on port 8000.")
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=90) as client:
        demo = client.get("/api/demo").json()
        response = client.post(
            "/api/runs", json={"applicant": demo["applicant"], "job": demo["jobs"][0]}
        )
        response.raise_for_status()
        run = response.json()
        assert run["status"] == "awaiting_review", run
        assert run["browser"]["upload"] == ["resume.txt"]
        assert client.get(f"/api/runs/{run['run_id']}/screenshot").status_code == 200
        response = client.post(f"/api/runs/{run['run_id']}/resume", json={"approved": True})
        response.raise_for_status()
        submitted = response.json()
        assert submitted["status"] == "submitted", submitted
        assert submitted["receipt"] == f"sandbox-{run['run_id']}"
        assert (
            client.post(f"/api/runs/{run['run_id']}/resume", json={"approved": True}).status_code
            == 422
        )
