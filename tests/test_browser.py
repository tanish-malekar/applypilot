import os

import httpx
import pytest
from playwright.sync_api import expect, sync_playwright


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


@pytest.mark.browser
def test_react_profile_missing_fact_approval_and_history():
    if os.environ.get("RUN_BROWSER_TESTS") != "1":
        pytest.skip("Build the frontend and start the local API on port 8000.")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        with httpx.Client(base_url="http://127.0.0.1:8000") as source:
            demo = source.get("/api/demo").json()
        demo["jobs"][0]["questions"].append({"id": "start", "prompt": "When can you start?"})
        page.route("**/api/demo", lambda route: route.fulfill(json=demo))
        page.goto("http://127.0.0.1:8000/demo")
        page.get_by_label("Search by title or company").fill("Secure")
        expect(
            page.get_by_role("button", name="Prepare application for ML Engineer, Secure Systems")
        ).to_be_visible()
        expect(
            page.get_by_role("button", name="Prepare application for Applied ML Engineer Intern")
        ).to_have_count(0)
        page.get_by_role("button", name="Clear search").click()
        page.get_by_role("button", name="My profile", exact=True).click()
        page.get_by_label("Full name", exact=True).fill("Taylor Sample")
        page.get_by_label("Email", exact=True).fill("taylor@example.com")
        page.get_by_text("Explore the workflow", exact=True).click()
        page.get_by_label("Try a missing work-authorization fact").check()
        expect(page.get_by_role("combobox", name="Degree", exact=True)).to_have_value("masters")
        page.get_by_role("button", name="Save profile", exact=True).click()
        page.get_by_role(
            "button", name="Prepare application for Applied ML Engineer Intern", exact=True
        ).click()
        expect(page.get_by_text("A little help from you", exact=True)).to_be_visible(timeout=90000)
        page.get_by_label("work authorized", exact=True).select_option("true")
        page.get_by_role("button", name="Save facts & continue", exact=True).click()
        question = page.get_by_label("When can you start?", exact=True)
        expect(question).to_be_visible(timeout=90000)
        question.fill("June 2027")
        page.get_by_role("button", name="Save answers & continue", exact=True).click()
        approve = page.get_by_role("button", name="Approve sandbox submission", exact=True)
        expect(approve).to_be_visible(timeout=90000)
        expect(page.locator(".document-text").first).to_contain_text("Taylor Sample")
        page.get_by_text("Browser evidence", exact=True).click()
        expect(
            page.get_by_alt_text("Application form filled and verified by the browser agent")
        ).to_be_visible()
        approve.click()
        expect(page.get_by_text("Application submitted to the sandbox", exact=True)).to_be_visible(
            timeout=90000
        )
        page.reload()
        page.get_by_role("button", name="Applications 1", exact=True).click()
        page.get_by_role("button", name="Submitted", exact=True).click()
        expect(page.locator(".applications .history-item")).to_have_count(1)
        page.get_by_role("button", name="Blocked", exact=True).click()
        expect(page.locator(".applications .history-item")).to_have_count(0)
        expect(page.get_by_text("No applications match this view.")).to_be_visible()
        page.get_by_role("button", name="All", exact=True).click()
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate(
            "document.documentElement.scrollWidth <= document.documentElement.clientWidth"
        )
        page.locator(".applications .history-item").click()
        expect(page.get_by_text("Application submitted to the sandbox", exact=True)).to_be_visible(
            timeout=90000
        )
        expect(
            page.get_by_role("button", name="Approve sandbox submission", exact=True)
        ).to_have_count(0)
        browser.close()


@pytest.mark.browser
def test_alternate_form_with_questions_and_human_answer():
    if os.environ.get("RUN_BROWSER_TESTS") != "1":
        pytest.skip("Start the local API on port 8000.")
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=90) as client:
        demo = client.get("/api/demo").json()
        job = {
            **demo["jobs"][0],
            "form_layout": "alternate",
            "questions": [
                {"id": "skills", "prompt": "Relevant skills?", "fact_id": "skills"},
                {"id": "start", "prompt": "When can you start?"},
            ],
        }
        run = client.post("/api/runs", json={"applicant": demo["applicant"], "job": job}).json()
        assert run["status"] == "needs_information", run
        assert "browser" not in run
        response = client.post(
            f"/api/runs/{run['run_id']}/resume", json={"answers": {"start": "June 2027"}}
        )
        response.raise_for_status()
        run = response.json()
        assert run["status"] == "awaiting_review", run
        assert "June 2027" in run["browser"]["fields"]["application_answers"]
        assert run["content"]["cover_letter"]["text"] == run["browser"]["fields"]["cover_letter"]
        submitted = client.post(f"/api/runs/{run['run_id']}/resume", json={"approved": True}).json()
        assert submitted["status"] == "submitted", submitted
