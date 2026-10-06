import httpx
import pytest

from job_agents.ingestion import fetch_jobs, normalize


def raw(content):
    return {
        "id": 123,
        "title": "AI Engineer",
        "content": content,
        "location": {"name": "Remote"},
        "absolute_url": "https://job-boards.greenhouse.io/demo/jobs/123",
    }


def test_normalization_preserves_unknown_policy():
    job = normalize("demo", raw("<p>Python agents &amp; APIs.</p>"))
    assert job.offers_sponsorship is None
    assert job.source == "greenhouse"
    assert job.description == "Python agents & APIs."
    assert job.skills == ["Python"]


def test_conflicting_sponsorship_remains_unknown():
    job = normalize("demo", raw("No sponsorship. Visa sponsorship is available."))
    assert job.offers_sponsorship is None


def test_public_feed_and_search():
    def handler(request):
        assert request.url.host == "boards-api.greenhouse.io"
        assert request.url.params["content"] == "true"
        return httpx.Response(200, json={"jobs": [raw("Python LangGraph")]})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        jobs = fetch_jobs("demo", "LangGraph", client)
        assert len(jobs) == 1
        assert fetch_jobs("demo", "Cobol", client) == []


def test_board_url_injection_is_rejected():
    with pytest.raises(ValueError):
        fetch_jobs("../../example.com")
