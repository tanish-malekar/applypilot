from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Applicant(Model):
    id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1)
    email: str = Field(pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    degree: Literal["high_school", "bachelors", "masters", "phd"] | None = None
    graduation_date: date | None = None
    experience_years: float | None = Field(default=None, ge=0)
    location: str | None = None
    work_authorized: bool | None = None
    needs_sponsorship: bool | None = None
    has_clearance: bool | None = None
    skills: list[str] = Field(default_factory=list)
    accomplishments: list[str] = Field(default_factory=list)


class ProfileAnswers(Model):
    degree: Literal["high_school", "bachelors", "masters", "phd"] | None = None
    graduation_date: date | None = None
    experience_years: float | None = Field(default=None, ge=0)
    location: str | None = None
    work_authorized: bool | None = None
    needs_sponsorship: bool | None = None
    has_clearance: bool | None = None


class Job(Model):
    id: str = Field(min_length=1)
    title: str
    company: str
    description: str
    skills: list[str] = Field(default_factory=list)
    source: str = "fixture"
    source_url: str | None = None
    source_location: str | None = None
    extraction_notes: list[str] = Field(default_factory=list)
    min_degree: Literal["high_school", "bachelors", "masters", "phd"] | None = None
    graduation_start: date | None = None
    graduation_end: date | None = None
    min_experience_years: float | None = Field(default=None, ge=0)
    allowed_locations: list[str] = Field(default_factory=list)
    requires_work_authorization: bool = True
    offers_sponsorship: bool | None = None
    requires_clearance: bool = False


class RunRequest(Model):
    applicant: Applicant
    job: Job


class ReviewDecision(Model):
    approved: bool


class ConstraintResult(Model):
    name: str
    status: Literal["pass", "fail", "unknown", "not_applicable"]
    evidence: str
    missing_profile_field: str | None = None


class Eligibility(Model):
    status: Literal["eligible", "ineligible", "needs_information"]
    checks: list[ConstraintResult]


class ContentSelection(Model):
    fact_ids: list[str] = Field(min_length=1, max_length=12)


class PreparedContent(Model):
    text: str
    fact_ids: list[str]
    facts: dict[str, str]
    mode: Literal["deterministic", "ollama", "groq"]
