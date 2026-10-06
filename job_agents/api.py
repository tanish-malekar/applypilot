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
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import ValidationError

from job_agents.browser import expected_fields
from job_agents.ingestion import fetch_jobs
from job_agents.models import Applicant, PreparedContent, RunRequest
from job_agents.workflow import Workflow

WEB = Path(__file__).parent / "web"
EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def create_app(directory: Path | None = None, base_url: str | None = None):
    directory = directory or Path(os.environ.get("JOB_AGENTS_DATA_DIR", "runtime"))
    base_url = base_url or os.environ.get("JOB_AGENTS_BASE_URL", "http://127.0.0.1:8000")

    @asynccontextmanager
    async def lifespan(app):
        app.state.workflow = Workflow(
            directory, base_url, content_mode=os.environ.get("CONTENT_MODE", "deterministic")
        )
        yield
        app.state.workflow.close()

    app = FastAPI(title="Job Application Agents", version="0.1.0", lifespan=lifespan)

    admission = threading.BoundedSemaphore(2)

    @app.middleware("http")
    async def visitor_session(request: Request, call_next):
        session = request.cookies.get("visitor", "")
        if not re.fullmatch(r"[a-zA-Z0-9_-]{32}", session):
            session = secrets.token_urlsafe(24)
        request.state.visitor = session
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

    @app.get("/", response_class=HTMLResponse)
    def home():
        return (WEB / "index.html").read_text()

    @app.get("/health")
    def health():
        return {"status": "ok", "mode": "local_sandbox"}

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
            raise HTTPException(429, "Demo is busy. Try again shortly.")
        try:
            body.applicant.id = request.state.visitor + ":" + body.applicant.id[:60]
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
            raise HTTPException(429, "Demo is busy. Try again shortly.")
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
        return FileResponse(run["browser"]["screenshot"], media_type="image/png")

    @app.get("/sandbox/{run_id}", response_class=HTMLResponse)
    def sandbox(run_id: UUID, request: Request):
        state = request.app.state.workflow.graph.get_state(
            request.app.state.workflow.config(str(run_id))
        ).values
        if not state:
            raise HTTPException(404, "Run not found")
        return (
            (WEB / "sandbox.html")
            .read_text()
            .replace("__RUN_ID__", str(run_id))
            .replace("__COMPANY__", html.escape(state["job"]["company"]))
            .replace("__TITLE__", html.escape(state["job"]["title"]))
        )

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
