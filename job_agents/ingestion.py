"""One read-only job source: Greenhouse's public Job Board API."""

import html
import re
from html.parser import HTMLParser
from urllib.parse import urlparse

import httpx

from job_agents.models import Job


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def plain_text(value: str) -> str:
    parser = TextParser()
    parser.feed(html.unescape(value))
    return " ".join(" ".join(parser.parts).split())


def normalize(board: str, raw: dict) -> Job:
    description = plain_text(raw.get("content", ""))
    # Only explicit phrases are interpreted. Unknown policy remains unknown.
    no_sponsor = bool(
        re.search(
            r"(?:unable to|do not|cannot|will not) (?:offer |provide )?sponsor|"
            r"no (?:visa )?sponsorship|without (?:visa )?sponsorship",
            description,
            re.I,
        )
    )
    yes_sponsor = bool(
        re.search(
            r"(?:we (?:do |will )?sponsor|(?:visa )?sponsorship (?:is )?available)",
            description,
            re.I,
        )
    )
    # Conflicting evidence cannot resolve a policy.
    sponsorship = (
        False
        if no_sponsor and not yes_sponsor
        else (True if yes_sponsor and not no_sponsor else None)
    )
    experience = re.search(
        r"(\d+)\+? years (?:of )?(?:professional |relevant )?experience", description, re.I
    )
    degree = "bachelors" if re.search(r"bachelor'?s degree", description, re.I) else None
    skills = [
        skill
        for skill in [
            "Python",
            "LangGraph",
            "LangChain",
            "FastAPI",
            "Playwright",
            "PyTorch",
            "TensorFlow",
            "SQL",
            "Docker",
        ]
        if re.search(r"\b" + re.escape(skill) + r"\b", description, re.I)
    ]
    source_url = raw.get("absolute_url", "")
    parsed = urlparse(source_url)
    if parsed.scheme != "https" or not parsed.hostname:
        source_url = None
    return Job(
        id=f"greenhouse-{board}-{raw['id']}",
        title=raw["title"],
        company=board,
        description=description,
        skills=skills,
        min_degree=degree,
        min_experience_years=float(experience.group(1)) if experience else None,
        offers_sponsorship=sponsorship,
        requires_work_authorization=False,
        source="greenhouse",
        source_url=source_url,
        source_location=raw.get("location", {}).get("name", "Unspecified"),
        extraction_notes=[
            "Conservative regex extraction; review the original posting.",
            "Location, graduation, clearance, and authorization requirements are not inferred.",
        ],
    )


def fetch_jobs(board="arvaintelligence", query="", client=None):
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", board):
        raise ValueError("Invalid Greenhouse board token.")
    owns_client = client is None
    client = client or httpx.Client(timeout=20, follow_redirects=False)
    try:
        response = client.get(
            f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs", params={"content": "true"}
        )
        response.raise_for_status()
        jobs = [normalize(board, raw) for raw in response.json()["jobs"]]
        if query:
            terms = query.casefold().split()
            jobs = [
                j
                for j in jobs
                if all(term in f"{j.title} {j.description}".casefold() for term in terms)
            ]
        return [j.model_dump(mode="json") for j in jobs[:50]]
    finally:
        if owns_client:
            client.close()
