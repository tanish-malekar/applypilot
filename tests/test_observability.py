import json

from job_agents.observability import Observer
from job_agents.storage import Store


class Collector:
    def __init__(self):
        self.calls = []

    def create_run(self, **data):
        self.calls.append(data)

    def update_run(self, identifier, **data):
        self.calls.append(data)


def test_payload_redaction_and_durable_budget(tmp_path):
    store = Store(tmp_path)
    collector = Collector()
    observer = Observer(store, collector, limit=2)
    state = {"applicant": {"email": "private@example.com"}, "key": "SECRET-CREDENTIAL"}
    operation = observer.wrap("content", lambda state: {"status": "failed", "content": state})
    for _ in range(4):
        assert operation(state)["status"] == "failed"
    assert len(collector.calls) == 4
    assert "private@example.com" not in json.dumps(collector.calls, default=str)
    assert "SECRET-CREDENTIAL" not in json.dumps(collector.calls, default=str)
    assert collector.calls[-1]["extra"]["metadata"]["outcome"] == "failed"
    restarted = Observer(Store(tmp_path), collector, limit=2)
    restarted.wrap("content", lambda s: {})(state)
    assert len(collector.calls) == 4


def test_telemetry_failure_never_breaks_workflow(tmp_path):
    class Broken:
        def create_run(self, **data):
            raise RuntimeError("Private provider failure")

    observer = Observer(Store(tmp_path), Broken(), limit=1)
    assert observer.wrap("content", lambda s: {"ok": True})({}) == {"ok": True}
    assert observer.failed_exports == 1


def test_tracing_requires_opt_in_key_and_durable_storage(tmp_path, monkeypatch):
    monkeypatch.setenv("APPLYPILOT_TRACING", "1")
    monkeypatch.setenv("APPLYPILOT_LANGSMITH_API_KEY", "not-a-live-key")
    assert Observer.from_environment(Store(tmp_path)).client is None


def test_automatic_tracing_is_suppressed_even_if_globally_enabled(tmp_path):
    from langsmith import tracing_context
    from langsmith.run_helpers import get_tracing_context

    observer = Observer(Store(tmp_path))
    operation = observer.wrap(
        "content", lambda state: {"enabled": get_tracing_context()["enabled"]}
    )
    with tracing_context(enabled=True):
        assert operation({})["enabled"] is False
