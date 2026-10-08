# Privacy-safe LangSmith tracing

Optional LangSmith integration records one independent span per workflow node. The content-node duration includes its model call. It does not export model prompts, completions, token counts, applicant identity, application text, job text, browser screenshots, cookies, credentials, or exception messages. The in-app trace remains the detailed account-scoped workflow audit.

Automatic SDK/LangChain tracing is explicitly disabled around workflow execution. Manual exports use empty inputs/outputs, random trace IDs, fixed node names, allowlisted outcomes, numerical duration, and timestamps. SDK runtime collection is disabled. Tests use an in-memory collector and verify that private fixture values never reach the export payload.

## Activation

Use an existing LangSmith Developer/free account without enabling billing or paid features. Enter its API key directly in the existing Render service's secret settings:

```text
APPLYPILOT_TRACING=1
APPLYPILOT_LANGSMITH_API_KEY=<private key entered in Render>
APPLYPILOT_TRACE_LIMIT=100
```

An external `DATABASE_URL` must already be configured. Without durable storage, exports remain disabled so redeployments cannot reset the quota. Do not turn on `LANGSMITH_TRACING` or `LANGCHAIN_TRACING_V2`; raw automatic tracing is not the supported integration.

The database atomically reserves up to 100 trace records **in total**, shared across workers and restarts. A lower limit is allowed. The cap never automatically resets; this intentionally favors cost control over continuous collection. Failed export attempts still consume a slot. Raising the environment limit cannot exceed 100. Do not delete the quota row to evade the cap. A trace may remain unfinished if its update request fails; the application still continues. `Observer.failed_exports` records local export failures without provider error text.

Spans appear under `applypilot-sanitized`. After adding the key, run a fictional application and inspect the actual LangSmith workspace: confirm node names, timing and outcome metadata, and empty inputs/outputs before describing tracing as active. No live trace has been verified yet.

The underlying APIs are documented in the official [Client reference](https://reference.langchain.com/python/langsmith/client/Client) and [tracing context reference](https://reference.langchain.com/python/langsmith/run_helpers/tracing_context).
