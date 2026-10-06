# Stack selection from employer postings

Reviewed October 6, 2026. This is a small, purposive sample of six employer-hosted applied AI and agent engineering postings, not a market-wide popularity ranking. Initial searches included framework names and therefore overrepresent them. One additional framework-neutral Applied AI search was used as a cross-check. Retired listings and candidate resumes were excluded. Names count once per posting, even if repeated; alternative/preferred tools also count. This supports choosing a relevant stack, not claiming statistical market share.

| Employer / role | Explicit technologies relevant to ApplyPilot | Source |
|---|---|---|
| Frontier / AI Engineer | LangGraph, LangChain, FastAPI, Pydantic, Playwright, scikit-learn; model training tools also listed | [Employer posting](https://www.myfrontier.ai/careers/vacancies/ai-engineer/) |
| Focused / Senior Agent Engineer | LangChain, LangGraph, LangSmith, Python, FastAPI | [Employer posting](https://job-boards.greenhouse.io/focused/jobs/8002448003) |
| Arva Intelligence / AI Software Engineer | LangGraph, LangChain, Python, Django, PostgreSQL | [Employer posting](https://job-boards.greenhouse.io/arvaintelligence/jobs/5379891008) |
| Encora / Senior AI Engineer | LangChain, LangGraph, LlamaIndex, Semantic Kernel, Python, evaluation | [Employer posting](https://job-boards.greenhouse.io/encora10/jobs/5228413007) |
| SimplifyNext / AI Engineer | LangChain, LangGraph, Ollama, vLLM, Docker, Python, training frameworks | [Employer posting](https://job-boards.greenhouse.io/simplifynext/jobs/5019281007) |
| OpenAI / Applied AI Engineer, API Platform, Digital Natives | Python/JS/TS, agent architecture, context engineering, evaluation; no agent framework named | [Employer posting](https://openai.com/careers/applied-ai-engineer-api-platform-digital-natives-san-francisco/) |

LangChain and LangGraph each appear in 5/6 sampled postings. FastAPI appears in 2/6. Playwright, Pydantic, scikit-learn, and Ollama each appear in 1/6. These counts are descriptive of this biased sample only. Python, evaluation, tool use, and production reliability recur across the sources.

## Implemented choices

- **LangGraph:** real shared-state graph, conditional routing, SQLite checkpoints, dynamic missing-information and review interrupts.
- **LangChain:** structured-output model adapters; Groq Free-plan hosted model or local Ollama. The no-key baseline deliberately uses deterministic facts and is labeled accordingly.
- **FastAPI + Pydantic:** typed API, explicit applicant/job schemas, input validation.
- **Playwright:** actual Chromium observation, field filling, document upload, screenshots, re-verification, and sandbox submission.
- **scikit-learn:** classification metrics for explicitly labeled synthetic scenarios.
- **SQLite:** minimal local persistence. Render Free storage is ephemeral; it is not a durable cloud memory service.

PyTorch, a vector database, additional agent frameworks, and a heavy frontend are unnecessary for the initial scope. Semantic retrieval and observability are follow-up milestones, and are not presented as already implemented.

## Primary technical references

[LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts), [persistence](https://docs.langchain.com/oss/python/langgraph/persistence), [LangChain Groq](https://docs.langchain.com/oss/python/integrations/chat/groq), [LangChain Ollama](https://docs.langchain.com/oss/python/integrations/chat/ollama), [Playwright actions](https://playwright.dev/python/docs/input), [Greenhouse Job Board API](https://docs.greenhouse.io/job-board.html).
