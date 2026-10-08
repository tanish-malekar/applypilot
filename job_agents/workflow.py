import operator
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, TypedDict
from uuid import uuid4

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from langsmith import tracing_context

from job_agents.browser import SandboxBrowser, expected_fields
from job_agents.content import generate, question_key, verify_bundle, verify_content
from job_agents.eligibility import evaluate
from job_agents.models import (
    Applicant,
    Eligibility,
    Job,
    PreparedContent,
    ProfileAnswers,
    QuestionResponses,
    ReviewDecision,
    RunRequest,
)
from job_agents.observability import Observer
from job_agents.storage import Store


class State(TypedDict, total=False):
    run_id: str
    applicant: dict
    job: dict
    status: str
    eligibility: dict
    content: dict
    browser: dict
    verification: dict
    decision: dict
    receipt: str
    trace: Annotated[list[dict], operator.add]


def event(agent: str, message: str):
    return [{"agent": agent, "message": message, "at": datetime.now(timezone.utc).isoformat()}]


class Workflow:
    def __init__(
        self,
        directory: Path,
        base_url="http://127.0.0.1:8000",
        content_mode="deterministic",
        browser=None,
    ):
        database_url = os.environ.get("DATABASE_URL")
        self.store = Store(directory, database_url)
        self.observer = Observer.from_environment(self.store)
        self.browser = browser or SandboxBrowser(base_url, directory)
        self.content_mode = content_mode
        self.postgres_context = None
        if database_url:
            from langgraph.checkpoint.postgres import PostgresSaver

            self.postgres_context = PostgresSaver.from_conn_string(database_url)
            saver = self.postgres_context.__enter__()
            saver.conn.execute("SET search_path TO applypilot")
            saver.setup()
            self.connection = None
        else:
            self.connection = sqlite3.connect(
                directory / "checkpoints.sqlite", check_same_thread=False
            )
            saver = SqliteSaver(self.connection)
        self.lock = threading.RLock()
        self.graph = self.build().compile(checkpointer=saver)

    def close(self):
        if self.postgres_context:
            self.postgres_context.__exit__(None, None, None)
        elif self.connection:
            self.connection.close()

    def build(self):
        graph = StateGraph(State)
        for name in [
            "discovery",
            "memory",
            "eligibility",
            "missing_information",
            "content",
            "question_information",
            "application",
            "verification",
            "review",
            "auto_apply",
            "finish",
        ]:
            graph.add_node(name, self.observer.wrap(name, getattr(self, name)))
        graph.add_edge(START, "discovery")
        graph.add_edge("discovery", "memory")
        graph.add_edge("memory", "eligibility")
        graph.add_conditional_edges("eligibility", self.route_eligibility)
        graph.add_edge("missing_information", "eligibility")
        graph.add_conditional_edges(
            "content",
            lambda s: (
                "finish"
                if s["status"] == "failed"
                else (
                    "question_information"
                    if any(a["answer"] is None for a in s["content"].get("answers", []))
                    else "application"
                )
            ),
        )
        graph.add_edge("question_information", "content")
        graph.add_conditional_edges(
            "application", lambda s: "finish" if s["status"] == "failed" else "verification"
        )
        graph.add_conditional_edges(
            "verification", lambda s: "review" if s["verification"]["passed"] else "finish"
        )
        graph.add_conditional_edges(
            "review", lambda s: "auto_apply" if s["decision"]["approved"] else "finish"
        )
        graph.add_edge("auto_apply", "finish")
        graph.add_edge("finish", END)
        return graph

    def discovery(self, state):
        job = Job.model_validate(state["job"])
        return {
            "job": job.model_dump(mode="json"),
            "status": "running",
            "trace": event("discovery", f"Normalized job {job.id} from {job.source}."),
        }

    def memory(self, state):
        profile = dict(state["applicant"])
        cached = self.store.recall(profile["id"])
        reused = []
        for field, value in cached.items():
            if field in ProfileAnswers.model_fields and profile.get(field) is None:
                profile[field] = value
                reused.append(field)
        saved_answers = cached.get("application_answers", {})
        profile["application_answers"] = {**saved_answers, **profile.get("application_answers", {})}
        applicant = Applicant.model_validate(profile)
        return {
            "applicant": applicant.model_dump(mode="json"),
            "trace": event("memory", f"Reused human-provided fields: {reused}."),
        }

    def eligibility(self, state):
        result = evaluate(
            Applicant.model_validate(state["applicant"]), Job.model_validate(state["job"])
        )
        return {
            "eligibility": result.model_dump(mode="json"),
            "trace": event("eligibility", result.status),
        }

    def route_eligibility(self, state):
        result = Eligibility.model_validate(state["eligibility"])
        if result.status == "eligible":
            return "content"
        if result.status == "ineligible":
            return "finish"
        # Unknown employer policy must be resolved from a source, not invented applicant facts.
        if any(c.status == "unknown" and c.missing_profile_field is None for c in result.checks):
            return "finish"
        return "missing_information"

    def missing_information(self, state):
        fields = sorted(
            {
                c["missing_profile_field"]
                for c in state["eligibility"]["checks"]
                if c["missing_profile_field"]
            }
        )
        answers = interrupt(
            {
                "kind": "missing_information",
                "fields": fields,
                "message": "Provide missing applicant facts to continue.",
            }
        )
        parsed = ProfileAnswers.model_validate(answers).model_dump(mode="json", exclude_none=True)
        if set(parsed) != set(fields):
            raise ValueError(f"Provide exactly the requested missing fields: {fields}")
        profile = {**state["applicant"], **parsed}
        validated = Applicant.model_validate(profile)
        self.store.remember(validated.id, parsed)
        return {
            "applicant": validated.model_dump(mode="json"),
            "trace": event("memory", f"Stored human-provided facts: {fields}."),
        }

    def content(self, state):
        try:
            content = generate(
                Applicant.model_validate(state["applicant"]),
                Job.model_validate(state["job"]),
                self.content_mode,
            )
            return {
                "content": content.model_dump(mode="json"),
                "trace": event("content", f"Selected {len(content.fact_ids)} grounded facts."),
            }
        except Exception as exc:
            return {"status": "failed", "trace": event("content", f"{type(exc).__name__}: {exc}")}

    def question_information(self, state):
        questions = [a for a in state["content"]["answers"] if a["answer"] is None]
        response = interrupt(
            {
                "kind": "question_information",
                "questions": questions,
                "message": "Provide verified answers; agents will not guess.",
            }
        )
        parsed = QuestionResponses.model_validate(response).answers
        if set(parsed) != {q["id"] for q in questions} or any(
            not value.strip() or len(value) > 4000 for value in parsed.values()
        ):
            raise ValueError(
                "Provide one non-empty answer per requested question (maximum 4000 characters)."
            )
        applicant = Applicant.model_validate(state["applicant"])
        applicant.application_answers.update(
            {
                question_key(Job.model_validate(state["job"]), q["prompt"]): parsed[q["id"]].strip()
                for q in questions
            }
        )
        self.store.remember(applicant.id, {"application_answers": applicant.application_answers})
        return {
            "applicant": applicant.model_dump(mode="json"),
            "trace": event("memory", "Stored human-provided application answers."),
        }

    def application(self, state):
        try:
            result = self.browser.prepare(
                state["run_id"],
                Applicant.model_validate(state["applicant"]),
                PreparedContent.model_validate(state["content"]),
            )
            return {"browser": result, "trace": event("application", "Filled local sandbox form.")}
        except Exception as exc:
            return {
                "status": "failed",
                "trace": event("application", f"{type(exc).__name__}: {exc}"),
            }

    def verification(self, state):
        applicant = Applicant.model_validate(state["applicant"])
        content = PreparedContent.model_validate(state["content"])
        errors = (
            verify_bundle(applicant, Job.model_validate(state["job"]), content)
            if content.resume
            else verify_content(applicant, content)
        )
        expected = expected_fields(applicant, content)
        observed = state["browser"].get("fields", {})
        errors += [
            f"Field mismatch: {key}"
            for key, value in expected.items()
            if observed.get(key) != value
        ]
        errors += state["browser"].get("errors", [])
        if state["browser"].get("upload") != ["resume.txt"]:
            errors.append("Resume upload was not verified.")
        return {
            "verification": {"passed": not errors, "errors": errors},
            "status": "awaiting_review" if not errors else "verification_failed",
            "trace": event("verification", "Passed." if not errors else "; ".join(errors)),
        }

    def review(self, state):
        response = interrupt(
            {
                "kind": "review",
                "message": "Review the local sandbox application.",
                "content": state["content"]["text"],
                "fields": state["browser"]["fields"],
            }
        )
        decision = ReviewDecision.model_validate(response)
        return {
            "decision": decision.model_dump(),
            "status": "approved" if decision.approved else "rejected",
            "trace": event("review", "Approved." if decision.approved else "Rejected."),
        }

    def auto_apply(self, state):
        try:
            if not state["verification"]["passed"] or not state["decision"]["approved"]:
                raise ValueError("Submission prerequisites were not met.")
            result = self.browser.submit(
                state["run_id"],
                Applicant.model_validate(state["applicant"]),
                PreparedContent.model_validate(state["content"]),
            )
            if not result.get("receipt"):
                raise ValueError("Sandbox submission did not return a receipt.")
            return {
                "status": "submitted",
                "receipt": result["receipt"],
                "browser": result,
                "trace": event("auto_apply", "Submitted verified local application."),
            }
        except Exception as exc:
            return {
                "status": "failed",
                "trace": event("auto_apply", f"{type(exc).__name__}: {exc}"),
            }

    def finish(self, state):
        status = state["status"]
        if status == "running":
            status = "ineligible" if state["eligibility"]["status"] == "ineligible" else "blocked"
        return {"status": status, "trace": event("tracking", f"Recorded outcome: {status}.")}

    def config(self, run_id):
        return {"configurable": {"thread_id": run_id}, "recursion_limit": 50}

    def snapshot(self, run_id):
        snapshot = self.graph.get_state(self.config(run_id))
        if not snapshot.values:
            raise KeyError(run_id)
        result = dict(snapshot.values)
        pending = [i.value for task in snapshot.tasks for i in task.interrupts]
        result["pending"] = pending
        if pending:
            result["status"] = (
                "needs_information"
                if pending[0]["kind"] in {"missing_information", "question_information"}
                else "awaiting_review"
            )
        screenshot = result.get("browser", {}).get("screenshot")
        if screenshot and Path(screenshot).is_file():
            self.store.save_artifact(run_id, Path(screenshot).read_bytes())
        self.store.save_run(run_id, result)
        return result

    def start(self, request: RunRequest):
        run_id = str(uuid4())
        with self.lock, tracing_context(enabled=False):
            self.graph.invoke(
                {
                    "run_id": run_id,
                    "applicant": request.applicant.model_dump(mode="json"),
                    "job": request.job.model_dump(mode="json"),
                    "trace": [],
                },
                self.config(run_id),
            )
            return self.snapshot(run_id)

    def resume(self, run_id: str, answer: dict):
        with self.lock, tracing_context(enabled=False):
            current = self.snapshot(run_id)
            if not current["pending"]:
                raise ValueError("Run is not waiting for input.")
            pending = current["pending"][0]
            if pending["kind"] == "review":
                ReviewDecision.model_validate(answer)
            elif pending["kind"] == "question_information":
                values = QuestionResponses.model_validate(answer).answers
                if set(values) != {q["id"] for q in pending["questions"]} or any(
                    not v.strip() or len(v) > 4000 for v in values.values()
                ):
                    raise ValueError("Provide exactly the requested question answers.")
            else:
                parsed = ProfileAnswers.model_validate(answer).model_dump(exclude_none=True)
                if set(parsed) != set(pending["fields"]):
                    raise ValueError(f"Provide exactly these fields: {pending['fields']}")
            self.graph.invoke(Command(resume=answer), self.config(run_id))
            return self.snapshot(run_id)
