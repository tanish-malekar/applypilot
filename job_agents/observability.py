"""Opt-in metadata-only LangSmith spans. No application payload is sent."""

from datetime import datetime, timezone
from functools import wraps
from time import perf_counter
from uuid import uuid4

from langsmith import Client, tracing_context


class Observer:
    def __init__(self, store, client=None, limit=100):
        self.store = store
        self.client = client
        self.limit = max(0, min(int(limit), 100))
        self.failed_exports = 0

    @classmethod
    def from_environment(cls, store):
        import os

        # Durable global quota survives deployment and is shared across workers.
        key = os.environ.get("APPLYPILOT_LANGSMITH_API_KEY")
        enabled = os.environ.get("APPLYPILOT_TRACING") == "1" and store.database_url and key
        client = None
        if enabled:
            client = Client(
                api_key=key,
                api_url="https://api.smith.langchain.com",
                auto_batch_tracing=False,
                hide_inputs=True,
                hide_outputs=True,
                omit_traced_runtime_info=True,
                timeout_ms=2000,
            )
        return cls(store, client, os.environ.get("APPLYPILOT_TRACE_LIMIT", "100"))

    def wrap(self, name, function):
        @wraps(function)
        def wrapped(state):
            started = datetime.now(timezone.utc)
            tick = perf_counter()
            outcome = "completed"
            try:
                # Disable SDK automatic tracing even if globally enabled by mistake.
                with tracing_context(enabled=False):
                    result = function(state)
                if result.get("status") in {
                    "failed",
                    "verification_failed",
                    "blocked",
                    "ineligible",
                }:
                    outcome = result["status"]
                return result
            except BaseException:
                # Interrupts are control flow, never export their applicant-bearing payload.
                outcome = "interrupted_or_error"
                raise
            finally:
                self.export(name, started, perf_counter() - tick, outcome)

        return wrapped

    def export(self, name, started, elapsed, outcome):
        if self.client is None:
            return
        try:
            if not self.store.reserve_trace(self.limit):
                return
            identifier = uuid4()
            # Only constant node names, allowlisted outcomes and numerical timings.
            self.client.create_run(
                id=identifier,
                name=f"ApplyPilot.{name}",
                run_type="chain",
                inputs={},
                project_name="applypilot-sanitized",
                start_time=started,
                extra={"metadata": {"component": name}},
            )
            self.client.update_run(
                identifier,
                end_time=datetime.now(timezone.utc),
                outputs={},
                extra={
                    "metadata": {
                        "component": name,
                        "outcome": outcome,
                        "duration_ms": round(elapsed * 1000, 2),
                    }
                },
            )
        except Exception:
            # Telemetry cannot fail an application or leak a provider exception.
            self.failed_exports += 1
