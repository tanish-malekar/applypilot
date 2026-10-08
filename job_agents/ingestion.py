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
            r"(?:we (?:do |will )?sponsor|"
            r"(?<!no )(?<!not )(?:visa )?sponsorship (?:is )?available)",
            description,
            re.I,
        )
    )
    conditional = bool(
        re.search(
            r"sponsor.{0,60}(?:case.by.case|may|might)|(?:may|might).{0,40}sponsor",
            description,
            re.I,
        )
    )
    if yes_sponsor:
        positive_clauses = re.split(r"[.;\n]", description)
        yes_sponsor = any(
            re.search(r"we (?:do |will )?sponsor|sponsorship (?:is )?available", clause, re.I)
            and not re.search(r"\b(?:no|not|cannot|unable|without)\b", clause, re.I)
            for clause in positive_clauses
        )
    conditional = conditional or bool(
        re.search(r"sponsor.{0,60}(?:only|subject to|depending)", description, re.I)
    )
    # Conflicting or conditional evidence cannot resolve a policy.
    sponsorship = (
        None
        if conditional
        else False
        if no_sponsor and not yes_sponsor
        else (True if yes_sponsor and not no_sponsor else None)
    )
    clauses = re.split(r"[.;\n]", description)
    evidence = {}
    degree = None
    years = []
    for clause in clauses:
        if re.search(r"preferred|nice to have|equivalent|or experience|up to", clause, re.I):
            continue
        requirement = re.search(r"required|must|minimum|at least|require", clause, re.I)
        if not requirement:
            continue
        if re.search(r"bachelor['’]?s degree", clause, re.I):
            degree = "bachelors"
            evidence.setdefault("min_degree", []).append(clause.strip())
        match = re.search(
            r"(\d+)\+? years? (?:of )?(?:professional |relevant )?experience", clause, re.I
        )
        if match:
            years.append(float(match.group(1)))
            evidence.setdefault("min_experience_years", []).append(clause.strip())
    policy_clauses = [c.strip() for c in clauses if re.search(r"sponsor", c, re.I)]
    if policy_clauses:
        evidence["offers_sponsorship"] = policy_clauses
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
        min_experience_years=max(years) if years else None,
        offers_sponsorship=sponsorship,
        requires_work_authorization=False,
        source="greenhouse",
        source_url=source_url,
        source_location=raw.get("location", {}).get("name", "Unspecified"),
        requirement_evidence=evidence,
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
