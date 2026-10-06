# Build progress

## October 6, 2026 — Day 1

Repository created first: https://github.com/tanish-malekar/applypilot (private).

Implemented the single-source Greenhouse feed, editable applicant profile, LangGraph specialized roles, eligibility constraints, applicant-scoped fact memory, SQLite checkpoints, missing-info/review interrupts, deterministic fact-grounded content, optional LangChain Groq/Ollama adapters, actual Chromium form filling and text-resume upload, screenshot evidence, verification, rejection/submission outcomes, session-isolated histories, and idempotent sandbox receipts.

Validation completed locally:

- Ruff: passed.
- GitHub Actions on Linux/Python 3.12: passed, including the Chromium integration test ([run](https://github.com/tanish-malekar/applypilot/actions/runs/37534285357)).
- Unit/API/workflow tests: 16 passed.
- Chromium integration test: passed; verified form fields, upload, screenshot, review, submission receipt, and refusal to resume an already-completed run.
- Synthetic eligibility evaluation: 16/16 labeled scenarios matched; metrics in `day1-eligibility-results.json`. This is a smoke set, not evidence of real-world accuracy.
- Live Greenhouse request: returned 2 keyword-matching jobs from the Arva Intelligence board.
- Website manually checked: complete sandbox submission displayed a receipt; live job discovery displayed the returned jobs; local preview is open in Codex.

Deployed on Render Free at https://job-application-agents.onrender.com. Fixed container startup package resolution and verified the public health endpoint, 2 live Greenhouse keyword matches, Groq-backed selection of 6 verified facts, Chromium field filling and resume upload, screenshot retrieval, independent verification, human approval, and a sandbox submission receipt. No paid plan has been provisioned. Local Ollama has not been verified. Renamed the repository and platform to ApplyPilot; updated the public README and interface around supported workflows.

A heartbeat is scheduled for October 7 and 8 at 10:00 AM America/New_York. It makes substantive changes, tests, commits, and pushes on the real day of work. It follows BUILD_PLAN.md and includes maintaining the deployed website. Local execution requires the computer and app to be available.
