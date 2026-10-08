import html
import json
import os
import re
import secrets
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from job_agents.auth import Accounts
from job_agents.browser import expected_fields
from job_agents.ingestion import fetch_jobs
from job_agents.models import Applicant, PreparedContent, RunRequest
from job_agents.workflow import Workflow

WEB = Path(__file__).parent / "web"
APP_WEB = WEB / "app"
EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def create_app(directory: Path | None = None, base_url: str | None = None):
    local_override = directory is not None
    directory = directory or Path(os.environ.get("JOB_AGENTS_DATA_DIR", "runtime"))
    base_url = base_url or os.environ.get("JOB_AGENTS_BASE_URL", "http://127.0.0.1:8000")

    @asynccontextmanager
    async def lifespan(app):
        if accounts.required and not accounts.enabled and not local_override:
            raise RuntimeError("Configure SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY together.")
        if accounts.required and not os.environ.get("DATABASE_URL") and not local_override:
            raise RuntimeError("DATABASE_URL is required for durable account storage.")
        app.state.workflow = Workflow(
            directory, base_url, content_mode=os.environ.get("CONTENT_MODE", "deterministic")
        )
        yield
        app.state.workflow.close()

    app = FastAPI(title="ApplyPilot", version="0.1.0", lifespan=lifespan)
    app.mount("/assets", StaticFiles(directory=APP_WEB / "assets", check_dir=False), name="assets")

    accounts = Accounts()
    admission = threading.BoundedSemaphore(2)

    @app.middleware("http")
    async def visitor_session(request: Request, call_next):
        session = request.cookies.get("visitor", "")
        if not re.fullmatch(r"[a-zA-Z0-9_-]{32}", session):
            session = secrets.token_urlsafe(24)
        request.state.visitor = session
        request.state.account = None
        protected = request.url.path.startswith(("/api/runs", "/api/profile", "/api/me"))
        authorization = request.headers.get("authorization", "")
        if protected and (accounts.required or authorization):
            try:
                user = await accounts.verify(authorization)
                request.state.account = user
                request.state.visitor = "user:" + user["id"]
            except HTTPException as exc:
                return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
        response = await call_next(request)
        response.set_cookie(
            "visitor",
            session,
            httponly=True,
            samesite="lax",
            secure=request.url.scheme == "https",
            max_age=86400 * 30,
        )
        return response

    def require_owner(request, run_id):
        if not request.app.state.workflow.store.owns(str(run_id), request.state.visitor):
            raise HTTPException(404, "Run not found")

    @app.get("/privacy", response_class=HTMLResponse)
    @app.get("/auth/recovery", response_class=HTMLResponse)
    @app.get("/auth/callback", response_class=HTMLResponse)
    @app.get("/reset-password", response_class=HTMLResponse)
    @app.get("/signup", response_class=HTMLResponse)
    @app.get("/login", response_class=HTMLResponse)
    @app.get("/app", response_class=HTMLResponse)
    @app.get("/demo", response_class=HTMLResponse)
    @app.get("/", response_class=HTMLResponse)
    def home():
        if not (APP_WEB / "index.html").is_file():
            raise HTTPException(
                503, "Build the React frontend: npm ci and npm run build in frontend/."
            )
        return FileResponse(APP_WEB / "index.html", headers={"Cache-Control": "no-cache"})

    @app.get("/health")
    def health():
        return {"status": "ok", "mode": "local_sandbox"}

    @app.get("/api/auth/config")
    async def auth_config():
        return await accounts.public_config()

    @app.get("/api/me")
    def me(request: Request):
        return {"user": request.state.account}

    @app.get("/api/profile")
    def profile(request: Request):
        saved = request.app.state.workflow.store.get_profile(request.state.visitor)
        if saved:
            return saved
        if request.state.account:
            user = request.state.account
            return Applicant(
                id="default", name=user["name"] or user["email"].split("@")[0], email=user["email"]
            ).model_dump(mode="json")
        return json.loads((EXAMPLES / "applicant.json").read_text())

    @app.post("/api/profile")
    def save_profile(body: Applicant, request: Request):
        body.id = "default"
        data = body.model_dump(mode="json")
        request.app.state.workflow.store.save_profile(request.state.visitor, data)
        return data

    @app.get("/api/demo")
    def demo():
        return {
            "applicant": json.loads((EXAMPLES / "applicant.json").read_text()),
            "jobs": json.loads((EXAMPLES / "jobs.json").read_text()),
        }

    @app.get("/api/jobs")
    def discover(board: str = "arvaintelligence", query: str = ""):
        try:
            return {"source": "greenhouse", "board": board, "jobs": fetch_jobs(board, query)}
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        except (httpx.HTTPError, KeyError) as exc:
            raise HTTPException(502, "Greenhouse feed is unavailable; try again later.") from exc

    @app.post("/api/runs")
    def start(body: RunRequest, request: Request):
        if not admission.acquire(blocking=False):
            raise HTTPException(429, "Application workers are busy. Try again shortly.")
        try:
            body.applicant.id = (
                request.state.visitor
                + ":"
                + ("default" if request.state.account else body.applicant.id[:60])
            )
            run = request.app.state.workflow.start(body)
            request.app.state.workflow.store.claim(run["run_id"], request.state.visitor)
            return run
        finally:
            admission.release()

    @app.get("/api/runs")
    def runs(request: Request):
        return request.app.state.workflow.store.list_runs(request.state.visitor)

    @app.get("/api/runs/{run_id}")
    def get_run(run_id: UUID, request: Request):
        require_owner(request, run_id)
        workflow = request.app.state.workflow
        with workflow.lock:
            try:
                return workflow.snapshot(str(run_id))
            except KeyError:
                raise HTTPException(404, "Run not found") from None

    @app.post("/api/runs/{run_id}/resume")
    def resume(run_id: UUID, body: dict, request: Request):
        require_owner(request, run_id)
        if not admission.acquire(blocking=False):
            raise HTTPException(429, "Application workers are busy. Try again shortly.")
        try:
            return request.app.state.workflow.resume(str(run_id), body)
        except KeyError:
            raise HTTPException(404, "Run not found") from None
        except (ValueError, ValidationError) as exc:
            raise HTTPException(422, str(exc)) from exc
        finally:
            admission.release()

    @app.get("/api/runs/{run_id}/screenshot")
    def screenshot(run_id: UUID, request: Request):
        require_owner(request, run_id)
        run = request.app.state.workflow.store.get_run(str(run_id))
        if not run or not run.get("browser", {}).get("screenshot"):
            raise HTTPException(404, "Screenshot not available")
        png = request.app.state.workflow.store.get_artifact(str(run_id))
        if png:
            return Response(
                png, media_type="image/png", headers={"Cache-Control": "private, no-store"}
            )
        path = Path(run["browser"]["screenshot"])
        if not path.is_file():
            raise HTTPException(404, "Screenshot not available")
        return FileResponse(
            path, media_type="image/png", headers={"Cache-Control": "private, no-store"}
        )

    @app.get("/sandbox/{run_id}", response_class=HTMLResponse)
    def sandbox(run_id: UUID, request: Request):
        state = request.app.state.workflow.graph.get_state(
            request.app.state.workflow.config(str(run_id))
        ).values
        if not state:
            raise HTTPException(404, "Run not found")
        page = (
            (WEB / "sandbox.html")
            .read_text()
            .replace("__RUN_ID__", str(run_id))
            .replace("__COMPANY__", html.escape(state["job"]["company"]))
            .replace("__TITLE__", html.escape(state["job"]["title"]))
        )

        if state["job"].get("form_layout") == "alternate":
            # Same accessible labels, different IDs and a two-column layout.
            for key in [
                "name",
                "email",
                "location",
                "work_authorized",
                "needs_sponsorship",
                "cover_letter",
                "application_answers",
                "resume",
            ]:
                page = page.replace(f'for="{key}"', f'for="alternate-{key}"').replace(
                    f'id="{key}"', f'id="alternate-{key}"'
                )
            page = page.replace(
                '<form id="application">',
                '<form id="application" style="display:grid;'
                'grid-template-columns:1fr 2fr;gap:10px">',
            )
        return page

    @app.post("/sandbox/{run_id}/submit")
    async def submit(run_id: UUID, request: Request):
        workflow = request.app.state.workflow
        state = workflow.graph.get_state(workflow.config(str(run_id))).values
        if (
            not state
            or state.get("eligibility", {}).get("status") != "eligible"
            or not state.get("verification", {}).get("passed")
            or not state.get("decision", {}).get("approved")
        ):
            raise HTTPException(409, "Workflow has not approved this sandbox application")
        payload = await request.json()
        required = expected_fields(
            Applicant.model_validate(state["applicant"]),
            PreparedContent.model_validate(state["content"]),
        )
        if payload.get("fields") != required or payload.get("resume_name") != "resume.txt":
            raise HTTPException(422, "Submitted fields differ from the approved application")
        receipt = workflow.store.submit(str(run_id), payload)
        return {"receipt_id": receipt["receipt_id"]}

    return app


app = create_app()
