from job_agents.models import Applicant, ConstraintResult, Eligibility, Job

DEGREES = {"high_school": 0, "bachelors": 1, "masters": 2, "phd": 3}


def evaluate(applicant: Applicant, job: Job) -> Eligibility:
    checks: list[ConstraintResult] = []

    def add(name, condition, evidence, missing=None):
        status = "unknown" if condition is None else "pass" if condition else "fail"
        checks.append(
            ConstraintResult(
                name=name, status=status, evidence=evidence, missing_profile_field=missing
            )
        )

    def unused(name):
        checks.append(
            ConstraintResult(
                name=name,
                status="not_applicable",
                evidence="No explicit constraint in normalized job.",
            )
        )

    if job.min_degree is None:
        unused("degree")
    else:
        add(
            "degree",
            None
            if applicant.degree is None
            else DEGREES[applicant.degree] >= DEGREES[job.min_degree],
            f"Minimum: {job.min_degree}; applicant: {applicant.degree}",
            "degree" if applicant.degree is None else None,
        )
    if job.graduation_start is None and job.graduation_end is None:
        unused("graduation")
    else:
        d = applicant.graduation_date
        match = (
            None
            if d is None
            else (
                (job.graduation_start is None or d >= job.graduation_start)
                and (job.graduation_end is None or d <= job.graduation_end)
            )
        )
        add(
            "graduation",
            match,
            f"Window: {job.graduation_start}..{job.graduation_end}; applicant: {d}",
            "graduation_date" if d is None else None,
        )
    if job.min_experience_years is None:
        unused("experience")
    else:
        add(
            "experience",
            None
            if applicant.experience_years is None
            else applicant.experience_years >= job.min_experience_years,
            f"Minimum years: {job.min_experience_years}; applicant: {applicant.experience_years}",
            "experience_years" if applicant.experience_years is None else None,
        )
    if not job.allowed_locations:
        unused("location")
    else:
        add(
            "location",
            None
            if applicant.location is None
            else applicant.location.casefold() in {x.casefold() for x in job.allowed_locations},
            f"Allowed: {job.allowed_locations}; applicant: {applicant.location}",
            "location" if applicant.location is None else None,
        )
    if not job.requires_work_authorization:
        unused("work_authorization")
    else:
        add(
            "work_authorization",
            applicant.work_authorized,
            f"Work authorization required; applicant: {applicant.work_authorized}",
            "work_authorized" if applicant.work_authorized is None else None,
        )
    if applicant.needs_sponsorship is False:
        unused("sponsorship")
    elif applicant.needs_sponsorship is None:
        add(
            "sponsorship",
            None,
            "Applicant sponsorship requirement is unknown.",
            "needs_sponsorship",
        )
    else:
        add(
            "sponsorship",
            job.offers_sponsorship,
            f"Applicant needs sponsorship; job offers sponsorship: {job.offers_sponsorship}",
        )
    if not job.requires_clearance:
        unused("clearance")
    else:
        add(
            "clearance",
            applicant.has_clearance,
            f"Clearance required; applicant: {applicant.has_clearance}",
            "has_clearance" if applicant.has_clearance is None else None,
        )
    statuses = {c.status for c in checks}
    status = (
        "ineligible"
        if "fail" in statuses
        else ("needs_information" if "unknown" in statuses else "eligible")
    )
    return Eligibility(status=status, checks=checks)
