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


@pytest.mark.parametrize(
    "description,degree,years",
    [
        ("Bachelor's degree preferred. 5 years of experience preferred.", None, None),
        ("Bachelor's degree or equivalent experience required.", None, None),
        ("Minimum 3 years of relevant experience. Bachelor's degree required.", "bachelors", 3),
        ("At least 1 year of experience required. Graduation in 2027 preferred.", None, 1),
    ],
)
def test_requirements_are_explicit_and_sourced(description, degree, years):
    job = normalize("demo", raw(description))
    assert job.min_degree == degree
    assert job.min_experience_years == years
    assert job.graduation_start is None
    for clauses in job.requirement_evidence.values():
        assert all(clause in description for clause in clauses)


def test_conditional_sponsorship_is_not_a_commitment():
    job = normalize("demo", raw("We may sponsor on a case-by-case basis."))
    assert job.offers_sponsorship is None


@pytest.mark.parametrize(
    "text",
    [
        "No visa sponsorship available.",
        "Visa sponsorship is not available.",
        "Sponsorship available only for certain locations.",
    ],
)
def test_sponsorship_negation_and_conditions_never_become_yes(text):
    assert normalize("demo", raw(text)).offers_sponsorship is not True
