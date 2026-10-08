# Evaluation and failure analysis

The checked-in [integrated results](integrated-evaluation-results.json) describe eight labeled synthetic workflows executed with real Chromium against local application forms. They are a small regression set, not an accuracy benchmark on employers or a 200-posting dataset. The recorded local run used deterministic content; hosted Groq verification is recorded separately in PROGRESS.md.

| Check | Observed result |
| --- | --- |
| Expected workflow outcomes | 8/8 |
| Eligible, approved workflows reaching a sandbox receipt | 4/4 |
| Prepared form values matching the approved payload | 35/35 across five prepared applications |
| Grounding violations in prepared content | 0 across those five applications |
| Human interventions | 7: five approval/rejection decisions and two missing-information answers |
| Intentional stops | One rejection, one ineligible profile, one unknown employer policy, one invalid answer kept paused |

Run the production frontend build and start the API, then execute:

```bash
python scripts/evaluate.py
python scripts/evaluate_integrated.py --output docs/integrated-evaluation-results.json
RUN_BROWSER_TESTS=1 pytest -q -m browser
```

The eligibility evaluator checks 16 labeled synthetic cases. Unit tests additionally cover preferred versus required degrees/experience, conditional and conflicting sponsorship, exact requirement evidence, fact/document tampering, untrusted job instructions, missing answers, persisted answer reuse, account isolation, and telemetry redaction/quota enforcement. The browser suite covers both form layouts, resume upload, cover-letter autofill, question answers, approval, rejection boundaries, account UI fixtures, and the responsive React workspace. CI runs a real PostgreSQL workflow restart/resume test.

## Failure taxonomy

| Condition | Behavior and recovery |
| --- | --- |
| Missing applicant fact | Pause before form execution; accept exactly the requested facts |
| Unsupported question | Pause for a human answer; remember it only for this applicant and matching company/question |
| Ambiguous employer policy | Block preparation; inspect the original source rather than invent a policy |
| Untrusted instructions in job text | Treat as data; the model can select only verified fact IDs |
| Invalid or repeated model fact IDs | Mark content generation failed; no application execution |
| Document/answer tampering | Independent verification fails; no approval or submission |
| Browser navigation/upload/field failure | Visible failed or verification-failed outcome; do not report success |
| Human rejection | Record rejected; no submission |
| Repeated approval of completed run | Reject request; preserve the original receipt |
| Model/provider outage | Visible failure; no silent claim that an LLM succeeded |
| Trace export outage or quota exhausted | Continue workflow; omit further telemetry |
| Account provider not configured | Keep login disabled and the fictional sample workspace available |

Testing found a profile-dialog initialization race during fast edits. Its draft now initializes before painting, and the browser regression checks that untouched degree information survives editing.

## Practical limits

The alternate form changes IDs and layout while preserving accessible labels. This does not establish reliability on arbitrary employer ATS forms. Live Greenhouse ingestion uses conservative phrase extraction with evidence; graduation/location requirements remain unparsed and require source review. Live listings do not invent application questions when the feed has not supplied them. Synthetic roles supply explicit questions for end-to-end exercises.

Content is assembled using fixed prose and verified facts. Groq/Ollama choose facts rather than freely writing applicant claims. Human answers are user assertions, not independently verified employment records. Answer memory normalizes case/whitespace and includes the employer in its key; it does not infer semantic equivalence across differently worded questions.

No latency reduction, real-world eligibility accuracy, employer submission rate, or resume impact metric has been measured. Supabase/Google/email activation and live LangSmith verification remain dependent on maintainer configuration.
