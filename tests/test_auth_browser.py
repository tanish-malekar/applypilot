"""Exercise the managed-auth UI against an isolated provider fixture, not real credentials."""

import base64
import json
import os
import time
from urllib.parse import parse_qs, urlparse

import pytest
from playwright.sync_api import expect, sync_playwright


def install_provider(page):
    user = {
        "id": "0c808d2f-c139-4a1c-b1a0-c247596a0e63",
        "email": "taylor@example.com",
        "aud": "authenticated",
        "role": "authenticated",
        "email_confirmed_at": "2026-10-06T00:00:00Z",
        "user_metadata": {"full_name": "Taylor Sample"},
        "app_metadata": {"provider": "email"},
        "identities": [],
    }

    def encode(item):
        return base64.urlsafe_b64encode(json.dumps(item).encode()).decode().rstrip("=")

    token = (
        encode({"alg": "HS256", "typ": "JWT"})
        + "."
        + encode(
            {
                "sub": user["id"],
                "aud": "authenticated",
                "exp": int(time.time()) + 3600,
                "iss": "https://auth.test.invalid/auth/v1",
                "role": "authenticated",
            }
        )
        + ".fixture-signature"
    )
    session = {
        "access_token": token,
        "refresh_token": "fixture-refresh-token",
        "expires_in": 3600,
        "token_type": "bearer",
        "user": user,
    }
    calls = []
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
    }

    def provider(route):
        request = route.request
        calls.append((request.url, request.post_data_json if request.post_data else None))
        if request.method == "OPTIONS":
            route.fulfill(status=200, headers=headers)
        elif "/authorize?" in request.url:
            route.fulfill(
                status=200, content_type="text/html", body="<h1>OAuth handoff fixture</h1>"
            )
        elif "/signup" in request.url:
            route.fulfill(json={"user": user, "session": None}, headers=headers)
        elif "/logout" in request.url:
            route.fulfill(status=204, headers=headers)
        elif "/user" in request.url:
            route.fulfill(json=user, headers=headers)
        else:
            route.fulfill(json=session, headers=headers)

    page.route("https://auth.test.invalid/auth/v1/**", provider)
    page.route(
        "**/api/auth/config",
        lambda route: route.fulfill(
            json={
                "enabled": True,
                "demo_mode": False,
                "url": "https://auth.test.invalid",
                "publishable_key": "sb_publishable_fixture",
                "google_enabled": True,
            }
        ),
    )
    profile = {
        "id": "default",
        "name": user["user_metadata"]["full_name"],
        "email": user["email"],
        "degree": None,
        "graduation_date": None,
        "experience_years": None,
        "location": None,
        "work_authorized": None,
        "needs_sponsorship": None,
        "has_clearance": None,
        "skills": [],
        "accomplishments": [],
    }

    def account_data(route):
        assert route.request.headers.get("authorization") == "Bearer " + token
        route.fulfill(json=profile if route.request.url.endswith("/api/profile") else [])

    page.route("**/api/profile", account_data)
    page.route("**/api/runs", account_data)
    return calls


@pytest.mark.browser
def test_public_demo_needs_no_login_details_or_api():
    if os.environ.get("RUN_BROWSER_TESTS") != "1":
        pytest.skip("Build the frontend and start the local API.")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        api_calls = []

        def unavailable(route):
            api_calls.append(route.request.url)
            route.abort()

        page.route("**/api/**", unavailable)
        page.goto("http://127.0.0.1:8000/demo")
        expect(
            page.get_by_role("heading", name="Your first application. Already prepared.")
        ).to_be_visible()
        expect(page.get_by_role("button", name="Approve demo application")).to_be_visible()
        expect(page.locator("input, textarea, select")).to_have_count(0)
        page.get_by_role("tab", name="1. Sample profile").click()
        expect(page.get_by_role("heading", name="Alex Morgan", exact=True)).to_be_visible()
        page.get_by_role("tab", name="2. Filled form").click()
        form = page.get_by_alt_text(
            "Recorded sandbox form filled for fictional applicant Alex Morgan"
        )
        expect(form).to_be_visible()
        assert form.evaluate("img => img.complete && img.naturalWidth > 0")
        page.get_by_role("tab", name="3. Review & approve").click()
        page.get_by_role("button", name="Approve demo application").click()
        expect(page.get_by_text("Demo complete — recorded sandbox outcome")).to_be_visible()
        page.get_by_role("button", name="Restart demo").click()
        page.get_by_role("button", name="Reject", exact=True).click()
        expect(page.get_by_role("status")).to_contain_text("Nothing was sent")
        page.reload()
        expect(page.get_by_role("button", name="Approve demo application")).to_be_visible()
        assert not api_calls
        page.set_viewport_size({"width": 390, "height": 844})
        expect(
            page.get_by_role("heading", name="Your first application. Already prepared.")
        ).to_be_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        browser.close()


@pytest.mark.browser
def test_public_pages_survive_account_service_outage():
    if os.environ.get("RUN_BROWSER_TESTS") != "1":
        pytest.skip("Build the frontend and start the local API.")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        pending = []
        page.route("**/api/auth/config", lambda route: pending.append(route))
        page.goto("http://127.0.0.1:8000", wait_until="domcontentloaded")
        expect(page.get_by_role("button", name="Get started", exact=True)).to_be_visible()
        assert pending
        pending.pop().fulfill(status=503, json={"detail": "Provider unavailable"})
        expect(page.get_by_role("button", name="Get started", exact=True)).to_be_visible()
        page.get_by_role("button", name="Get started", exact=True).click()
        expect(page.get_by_role("button", name="Try again", exact=True)).to_be_visible()
        assert page.url.endswith("/signup")
        expect(page.get_by_role("heading", name="Dashboard", exact=True)).to_have_count(0)
        page.goto("http://127.0.0.1:8000", wait_until="domcontentloaded")
        page.get_by_role("button", name="Try the demo", exact=True).click()
        expect(page.get_by_role("button", name="Approve demo application")).to_be_visible()
        assert page.url.endswith("/demo")
        page.goto("http://127.0.0.1:8000/privacy", wait_until="domcontentloaded")
        expect(page.locator("main")).to_be_visible()
        expect(page.get_by_role("button", name="Try again", exact=True)).to_have_count(0)
        browser.close()


@pytest.mark.browser
def test_signup_confirmation_login_reload_and_logout():
    if os.environ.get("RUN_BROWSER_TESTS") != "1":
        pytest.skip("Build the frontend and start the local API.")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        calls = install_provider(page)
        page.goto("http://127.0.0.1:8000")
        expect(
            page.get_by_alt_text(
                "ApplyPilot dashboard showing pastel job cards, profile navigation, "
                "and an application status table"
            )
        ).to_be_visible()
        page.get_by_role("button", name="Get started", exact=True).click()
        page.get_by_label("Full name", exact=True).fill("Taylor Sample")
        page.get_by_label("Email address", exact=True).fill("taylor@example.com")
        page.get_by_label("Password", exact=True).fill("fixture-only-password")
        page.get_by_label("Confirm password", exact=True).fill("different-password")
        page.get_by_role("button", name="Create account", exact=True).click()
        expect(page.get_by_text("The passwords do not match.")).to_be_visible()
        page.get_by_label("Confirm password", exact=True).fill("fixture-only-password")
        page.get_by_role("button", name="Create account", exact=True).click()
        expect(
            page.get_by_text("Check your email to confirm your account, then return to log in.")
        ).to_be_visible()
        signup = next(payload for url, payload in calls if "/signup" in url and payload)
        assert signup["data"]["full_name"] == "Taylor Sample"
        page.get_by_role("button", name="Log in", exact=True).click()
        page.get_by_label("Email address", exact=True).fill("taylor@example.com")
        page.get_by_label("Password", exact=True).fill("fixture-only-password")
        page.get_by_role("button", name="Log in", exact=True).click()
        expect(page.get_by_role("heading", name="Dashboard", exact=True)).to_be_visible()
        page.reload()
        expect(page.get_by_role("heading", name="Dashboard", exact=True)).to_be_visible()
        page.get_by_role("button", name="Log out", exact=True).click()
        expect(page.get_by_role("button", name="Get started", exact=True)).to_be_visible()
        page.goto("http://127.0.0.1:8000/app")
        expect(page.get_by_role("heading", name="Welcome back.", exact=True)).to_be_visible()
        assert page.url.endswith("/login")
        page.goto("http://127.0.0.1:8000/practice")
        expect(page.get_by_role("heading", name="Welcome back.", exact=True)).to_be_visible()
        assert page.url.endswith("/login")
        browser.close()


@pytest.mark.browser
def test_google_signin_uses_pkce_and_a_fixed_callback():
    if os.environ.get("RUN_BROWSER_TESTS") != "1":
        pytest.skip("Build the frontend and start the local API.")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        install_provider(page)
        page.goto("http://127.0.0.1:8000/login")
        page.get_by_role("button", name="Continue with Google", exact=True).click()
        expect(page.get_by_role("heading", name="OAuth handoff fixture")).to_be_visible()
        parameters = parse_qs(urlparse(page.url).query)
        assert parameters["provider"] == ["google"]
        assert parameters["redirect_to"] == ["http://127.0.0.1:8000/auth/callback"]
        assert parameters["code_challenge_method"] == ["s256"]
        assert parameters["code_challenge"]
        browser.close()
