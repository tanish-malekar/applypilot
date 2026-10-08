from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from job_agents.models import Applicant, PreparedContent

LABELS = {
    "name": "Full name",
    "email": "Email address",
    "location": "Location",
    "work_authorized": "Authorized to work",
    "needs_sponsorship": "Need sponsorship",
    "cover_letter": "Application statement",
    "application_answers": "Application questions",
}


def expected_fields(applicant: Applicant, content: PreparedContent) -> dict[str, str]:
    return {
        "name": applicant.name,
        "email": applicant.email,
        "location": applicant.location or "",
        "work_authorized": ""
        if applicant.work_authorized is None
        else "yes"
        if applicant.work_authorized
        else "no",
        "needs_sponsorship": ""
        if applicant.needs_sponsorship is None
        else "yes"
        if applicant.needs_sponsorship
        else "no",
        "cover_letter": content.cover_letter.text if content.cover_letter else content.text,
        "application_answers": "\n\n".join(f"{a.prompt}\n{a.answer}" for a in content.answers),
    }


def validate_base_url(base_url: str):
    parsed = urlparse(base_url)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
        or parsed.username
        or parsed.password
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Browser execution requires a loopback HTTP sandbox origin.")
    return parsed


class SandboxBrowser:
    def __init__(self, base_url: str, directory: Path):
        self.base_url = base_url.rstrip("/")
        self.origin = validate_base_url(base_url)
        self.directory = directory

    def _execute(self, run_id, applicant, content, submit=False):
        fields = expected_fields(applicant, content)
        output = self.directory / "artifacts" / run_id
        output.mkdir(parents=True, exist_ok=True)
        resume = output / "resume.txt"
        resume.write_text(
            content.resume.text
            if content.resume
            else (f"{applicant.name}\n{applicant.email}\n\n" + "\n".join(content.facts.values())),
            encoding="utf-8",
        )
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                context = browser.new_context(viewport={"width": 1280, "height": 900})

                def guard(route):
                    target = urlparse(route.request.url)
                    if (target.scheme, target.hostname, target.port) != (
                        self.origin.scheme,
                        self.origin.hostname,
                        self.origin.port,
                    ):
                        route.abort()
                    else:
                        route.continue_()

                context.route("**/*", guard)
                page = context.new_page()
                page.goto(f"{self.base_url}/sandbox/{run_id}", wait_until="networkidle")
                observed = []
                for key, value in fields.items():
                    locator = page.get_by_label(LABELS[key], exact=True)
                    observed.append({"field": key, "label": LABELS[key], "count": locator.count()})
                    if key in {"work_authorized", "needs_sponsorship"}:
                        locator.select_option(value)
                    else:
                        locator.fill(value)
                page.get_by_label("Resume document", exact=True).set_input_files(resume)
                actual = {
                    key: page.get_by_label(label, exact=True).input_value()
                    for key, label in LABELS.items()
                }
                upload = page.get_by_label("Resume document", exact=True).evaluate(
                    "el => Array.from(el.files).map(f => f.name)"
                )
                errors = [f"Field mismatch: {k}" for k in fields if fields[k] != actual[k]]
                uploaded_text = page.get_by_label("Resume document", exact=True).evaluate(
                    "async el => await el.files[0].text()"
                )
                if uploaded_text != resume.read_text(encoding="utf-8"):
                    errors.append("Resume contents differ from the generated document.")
                if upload != [resume.name]:
                    errors.append("Resume upload mismatch.")
                screenshot = output / ("submitted.png" if submit else "prepared.png")
                receipt = None
                if submit:
                    if errors:
                        raise ValueError("Browser re-verification failed: " + "; ".join(errors))
                    page.get_by_role(
                        "button", name="Submit sandbox application", exact=True
                    ).click()
                    page.get_by_test_id("receipt").wait_for(state="visible")
                    receipt = page.get_by_test_id("receipt").inner_text()
                page.screenshot(path=str(screenshot), full_page=True)
                return {
                    "fields": actual,
                    "upload": upload,
                    "errors": errors,
                    "observed_fields": observed,
                    "screenshot": str(screenshot),
                    "receipt": receipt,
                }
            finally:
                browser.close()

    def prepare(self, run_id: str, applicant: Applicant, content: PreparedContent):
        return self._execute(run_id, applicant, content)

    def submit(self, run_id: str, applicant: Applicant, content: PreparedContent):
        # A fresh browser restores the persisted payload and re-verifies it before clicking.
        return self._execute(run_id, applicant, content, submit=True)
