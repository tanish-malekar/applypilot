# Three-day implementation plan

Dates are America/New_York. Make substantive commits on the day the work happens; never backdate, fabricate activity, or make empty commits. The user also requested a deployed, functional, free website and clarified that a basic POC with one job source is sufficient. Keep scope small.

## Day 1 — October 6, 2026

Create the GitHub repository first and share its URL. Build a working POC with a live Greenhouse public job feed, applicant editing, eligibility constraints, grounded application content, Chromium execution against a local ATS form, verification, approval/rejection, checkpoints, session-isolated tracking, and meaningful tests. Prepare Render Free deployment; deploy as soon as the user completes Render sign-in. Use Groq Free plan if a key is supplied, otherwise keep the no-key deterministic mode clearly labeled.

## Day 2 — October 7, 2026, 10:00 AM

Complete the user-confirmed application-content scope: separate generated text resume, cover letter, and answers to explicit application questions. Use verified profile facts and cite their evidence; do not invent applicant experience, skills, achievements, or answers. Keep unsupported answers unresolved for human input. Show the three outputs in the existing workspace, require human review, and use them in the built-in form autofill/upload workflow. Add meaningful content-grounding, missing-answer, and prompt-injection evals alongside the existing guardrails. Preserve the current LangGraph/LangChain/FastAPI/Playwright stack and one-source scope.

Improve the existing **single Greenhouse source**, rather than adding more providers. Priorities: provenance and conservative requirement extraction; test sponsorship ambiguity and graduation/experience language; applicant memory retrieval beyond exact field reuse; browser handling for an alternate local form layout; a small labeled ingestion/memory evaluation set. Preserve the React/Vite frontend and responsive dashboard under frontend/. Build it with npm ci and npm run build before API/UI tests; do not restore the old static HTML interface. Test, record evidence in PROGRESS.md, commit and push. If deployment remains pending and credentials are available, complete it and verify live functionality. Keep hosting/model choices free; do not upgrade plans. Maintain the deployed service through its GitHub integration.

## Day 3 — October 8, 2026, 10:00 AM

Integrate optional LangSmith tracing for workflow/model execution, timing, and failure visibility. Use the Developer free allowance with a hard usage limit; do not enable billing or paid features. Request the user's LangSmith API key through secret settings when activation is required, and verify an actual trace in the user's workspace before claiming live tracing. Keep applicant text, personal fields, and credentials out of telemetry through explicit input/output redaction; use fictional fixtures for hosted verification. Missing tracing credentials must not prevent the application workflow from functioning, and pending activation must be reported accurately.

Evaluate the integrated POC on the local form variants and labeled synthetic job cases. Report completion rate, field correctness, interventions, failures, and grounding checks with dataset size and limitations. Add failure taxonomy, demonstration instructions, and final README polish. Fix observed failures, verify the live site when available, test, commit and push. Disable the two-day build automation when milestones are complete.

## Operational constraints

Read README.md and PROGRESS.md before changing anything. Preserve user edits. No real job submissions are authorized by the research brief. No secrets, provided PDF, student IDs, applicant personal data, screenshots containing private information, virtual environments, or runtime databases belong in Git. Never claim the synthetic cases are the proposed 200 manually labeled job postings. Hosted Free storage can reset and the service can sleep; document this plainly. Follow up on unavailable credentials rather than claiming deployment or provider integration is verified.

## Account and home-page requirements added October 6

Preserve the public landing page, signup/login/password-recovery screens, Supabase Google OAuth handoff, account ownership enforcement, persisted profiles, private screenshot evidence, and PostgreSQL checkpoint support. Finish provider activation and create a confirmed test account when the user supplies the project configuration and completes the required provider setup. Do not claim public signup, Google login, or email delivery is live until checked against the real project. Never revert authenticated user ownership to visitor cookies in an account-enabled deployment. Do not remove `DATABASE_URL` or downgrade real-user data to ephemeral SQLite. Read docs/ACCOUNTS_SETUP.md. Preserve these account features during the Day 2/3 content and tracing work; tracing must not leak actual users' personal data. Run all browser tests with `pytest -m browser`; CI includes a PostgreSQL restart/resume test.
