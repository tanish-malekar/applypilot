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

## October 6, 2026 — React frontend and visual redesign

Migrated the dashboard to React 19 with Vite and Lucide icons. Added a responsive sidebar/top navigation, a new visual identity, live/sample job-source tabs, selectable job cards, applicant profile dialog, application studio, grounding evidence, browser screenshots, approval/rejection controls, activity timeline, and application history. Counters use actual feed/run data. Retained the existing FastAPI workflow endpoints and sandbox submission boundaries.

The Dockerfile builds the frontend in a Node.js stage and serves its bundled assets through the Python service. Generated bundles and node_modules remain ignored. Updated GitHub Actions to build the frontend and run both Chromium integration tests. Locally verified the production build, 16 unit/API/workflow tests, the original browser submission test, and a React test covering profile edits, missing-fact recovery, browser evidence, human approval, and reopening a submitted run after refresh. Desktop and mobile views were visually checked; the mobile page has no horizontal overflow. npm audit reported no dependency vulnerabilities.

Deployment verified on the public Render service: React JavaScript and CSS bundles returned successfully, the UI completed a Groq-backed application through review and a sandbox receipt, and live Greenhouse search displayed 2 opportunities. All 18 tests and the frontend build passed in GitHub Actions ([run](https://github.com/tanish-malekar/applypilot/actions/runs/37540662053)). The README includes an actual screenshot of the deployed React workspace.

## October 6, 2026 — Reference-inspired dashboard

Rebuilt the React interface around the supplied dashboard reference: light sidebar and top search, forest-green controls, a spacious illustrated hero, pastel opportunity cards, and a full-width application table. Each card starts its own preparation workflow; review and browser evidence open in a focused native dialog. Added working title/company search, status filters, a review-next action, and a contextual help panel. Document readiness, status, timestamps, and counters use actual workflow data. Font assets are bundled locally with their open-source licenses.

Verified the production build, Ruff, all 18 tests, and the 16-scenario synthetic evaluation. Expanded the React browser test to cover title/company filtering, application status filters, and mobile overflow alongside profile editing, missing facts, evidence, approval, and persisted history. Visually inspected desktop and mobile layouts; fixed an overflowing table accessibility label at the narrow breakpoint.

Published commit `4d48fcc` on Render Free and verified the public interface: a Groq-backed application reached human review and a submitted sandbox receipt, an ineligible sample role stopped before preparation, and Greenhouse search returned two live jobs. The full-page README screenshot shows the deployed dashboard with actual outcomes from these checks. GitHub Actions passed the production frontend build and all 18 tests ([run](https://github.com/tanish-malekar/applypilot/actions/runs/37542066465)).

## October 6, 2026 — Public home page and managed account integration

Added a public feature home page using the actual dashboard screenshot, account screens for signup, login, Google OAuth, confirmation, and password recovery, a data information page, and desktop/mobile logout controls. Supabase sessions use PKCE; the API verifies tokens with the provider before using stable account IDs for profile and run ownership. New accounts do not inherit the sample applicant's qualifications. Profile edits persist through the API, and protected browser evidence is loaded with the account token.

Added external PostgreSQL storage in a private schema for profiles, facts, runs, receipts, screenshots, and LangGraph checkpoints, with SQLite retained for the credential-free sample workspace. Hosted account activation fails closed without complete provider configuration and durable storage. Added tests for invalid tokens, cross-account access, account history/profile restoration, signup confirmation, login/logout/refresh, and the Google PKCE handoff against a provider fixture. Added a PostgreSQL interrupted-workflow restart/resume test and a free ephemeral PostgreSQL service in GitHub Actions. Local checks: production frontend build and Ruff passed; 24 tests passed. GitHub Actions passed all 25 tests, including the real PostgreSQL restart/resume test and all four browser tests ([run](https://github.com/tanish-malekar/applypilot/actions/runs/37546428023)). The public home page is deployed and was visually checked on desktop and mobile; its dashboard preview uses an actual workspace screenshot. Login/signup routes show the explicit setup-pending state until the provider is connected.

Provider activation is pending the user's Supabase project and Google/email provider configuration. The browser reached Supabase's sign-in page; no provider account or paid resource was created. Test account provisioning is prepared through the dashboard instructions or an optional one-time Admin API helper, but no live test credentials have been created or claimed yet.

## October 8, 2026 — Content milestone catch-up and integrated evaluation

The October 7 run was interrupted after read-only inspection; no implementation or commit was made that day. Remaining content work was implemented on October 8, with actual commit dates preserved.

Implemented separate grounded text resume and cover-letter documents, downloads in the React application studio, explicit question answers with fact evidence, and a human-answer interrupt for unsupported questions. Answers persist by applicant and company with case/whitespace-normalized question keys; a restart/resume/isolation test verifies reuse without crossing account or employer boundaries. Added conservative requirement-clause evidence and tests for preferred/equivalent degrees, required experience, graduation ambiguity, and conditional/negated sponsorship. Added an alternate local form with different IDs/layout, cover-letter/question autofill, and uploaded resume-content verification. Preserved authentication, PostgreSQL checkpoints, the public home page, and the free single-service deployment.

Added optional metadata-only LangSmith spans, automatic-tracing suppression, empty input/output exports, fixed outcome metadata, and an atomic persistent lifetime cap of 100 records. Exports require both explicit opt-in and external PostgreSQL; no LangSmith key was supplied, so live tracing remains unactivated. Added redaction, quota persistence and export-outage tests; no paid resources or billing were enabled.

Local integrated evaluation: 8/8 expected outcomes, four approved eligible workflows reaching sandbox receipts, 35/35 prepared fields matching across five applications, zero grounding errors in those five, seven human interventions. Results are synthetic regression evidence, not measured real-world performance. Browser testing exposed a profile draft initialization race; corrected it and added untouched-degree preservation checks. See EVALUATION.md and OBSERVABILITY.md for failure analysis and setup limits. Provider account activation and a confirmed live test account are still pending Supabase/Google/email configuration.

Validation before deployment: Ruff and the production frontend build passed. Unit/API/guardrail tests: 41 passed locally; the PostgreSQL-only test is reserved for CI. The full five-test Chromium suite passed, including auth-provider fixtures, alternate forms, question input and the responsive React workflow. The 16-case synthetic eligibility set still passes. Live provider activation has not been claimed.

Published implementation commit `b10d635` to origin/main on October 8. Render Free reports that commit live (deploy duration 1m42s). GitHub Actions passed all 47 tests: 42 non-browser tests including PostgreSQL restoration, and five Chromium tests; its integrated evaluator also passed all eight cases ([run](https://github.com/tanish-malekar/applypilot/actions/runs/37823163033)). A further local React regression verifies the unsupported-question input screen through answer submission, approval and history. Live Greenhouse search returned three AI-matching jobs with requirement provenance. The deployed Groq workflow prepared distinct resume/cover-letter/question outputs, verified fields and browser evidence, and paused for human review.

Live approval verification completed: the Groq-backed application returned a submitted sandbox receipt after human approval. The React studio displayed separate documents, a grounded explicit question answer and verified browser evidence. Managed-account config still reports disabled; no public signup, Google login, test password or live LangSmith trace is represented as active. Both independent implementation milestones are now shipped; provider activation remains a user-configuration follow-up.

## October 8, 2026 — Managed-account deployment activation

Configured the user's public Supabase settings and required account authentication in the existing Render Free service. Saved the deployed site URL and exact callback/recovery redirects in Supabase. Initial startup failed because the database URI still contained its password placeholder; the user corrected the secret directly in Render. The corrected deployment completed application startup, and the live `/api/auth/config` now reports `enabled: true`, `demo_mode: false`, and `google_enabled: false`. An unauthenticated `/api/profile` request returns HTTP 401, and the live React login page presents email/password login with Google explicitly unavailable.

A confirmed fictional test-user form is prepared in Supabase for the user to enter its password. Test-user creation and successful account login have not yet been verified. Public confirmation/reset email delivery and Google OAuth still require provider setup; these are not represented as working. No private credentials were added to the repository.

## October 25, 2026 — Restore the live platform

Diagnosed the timeout on the public site: the existing Supabase Free project was paused, its public hostname did not resolve, and Render startup failed with PostgreSQL `tenant/user ... not found`. Resumed the existing project without changing credentials, database ownership, account requirements, or plan. Supabase confirmed restoration complete. The first deployment of the repair failed while restoration was still in progress; redeploying after restoration succeeded.

Published `58ecbd5`: public home/privacy pages render independently of account initialization, account routes remain gated, and timeout errors use actionable wording. Added a browser regression for a stalled/failed account-config request, including no anonymous workspace fallback. The production frontend build, Ruff, and all six local browser tests passed. GitHub Actions passed the full build, PostgreSQL/API tests, evaluations, and browser suite ([run](https://github.com/tanish-malekar/applypilot/actions/runs/40220900583)). Render reports the repair live and serves its new frontend bundle. Live checks: `/health` returns 200, Supabase settings returns 200, managed accounts remain enabled with demo mode disabled, and an unauthenticated profile request returns 401. The existing browser session refreshed successfully into the authenticated dashboard, including persisted application history from October 10. Google remains disabled; public email delivery and live LangSmith activation were not changed or newly verified.

## October 25, 2026 — One-click public demo

Added a prominent **Try the demo** home-page action and public `/demo` walkthrough that opens immediately to a prepared application. Visitors can inspect a prefilled fictional profile, real recorded Playwright form screenshot, eligibility checks, separate documents, answers, evidence, and activity; approve/reject controls replay the recorded outcome and restart resets the walkthrough. Captured the bundled artifacts from an actual local deterministic sandbox run through approval and receipt. The interface explicitly identifies recorded results and does not imply new model generation or submission. Demo interactions use browser-local state, need no login or personal input, make no API calls on direct entry, and do not modify account histories.

Account workflows retain their existing authentication and ownership protections. The former live visitor-scoped sample workspace remains available at `/practice` only when managed accounts are disabled. Updated documentation and moved its full workflow browser test to that route. Added public-demo tests for API outage, profile/form review, screenshot loading, approve/reject/reset/reload, mobile overflow, and home-page entry while account configuration is unavailable. Verified the production frontend build, Ruff, and all seven local browser tests. Deployment verification follows the implementation push.

Published `a0b3ed8`; Render reports the commit live. GitHub Actions passed the full checks including seven browser tests, real PostgreSQL restoration and integrated evaluation ([run](https://github.com/tanish-malekar/applypilot/actions/runs/40221897962)). Verified the deployed `/demo` opens directly to its recorded application, approval changes to the clearly labelled recorded outcome, restart clears the decision, and the filled-form screenshot displays. The hosted unauthenticated profile endpoint still returns 401.

## October 25, 2026 — Animated autofill and submission demo

Added the default **Watch the agent** demo view: animated typing into the sample fields, cursor indicators, resume upload, cover-letter/question entry, field verification, sample human approval, a visible Submit click, and the recorded sandbox receipt. The browser pane scrolls to each active field and stays in view. Added pause/play, replay, speed controls, progress/activity indicators, mobile layout, and reduced-motion opt-in playback. The animation uses the existing fictional recording and is explicitly labelled a replay; it does not control a new browser session, call a model, or submit a new application. The actual screenshot and interactive review remain available in adjacent tabs.

Production frontend build and Ruff passed; all eight local browser tests passed. New deterministic-clock coverage verifies partial typing, pause/resume, upload completion, approval preceding the Submit animation, receipt, restart, reduced-motion behavior and mobile overflow. Updated the image check to await decoding before asserting image dimensions. Deployment verification follows the implementation push.
