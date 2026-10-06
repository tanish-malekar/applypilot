# ApplyPilot deployment

Live platform: https://job-application-agents.onrender.com

The existing Render service is srv-db2mi9qj9qps73eo5m7g, connected to tanish-malekar/applypilot on main. Its original service URL remains stable after the repository rename. The platform UI and repository are branded ApplyPilot. Use this existing service for updates; creating another Blueprint is unnecessary. The hosted workflow has been verified using Groq and a sandbox approval/submission.

The website serves real Greenhouse jobs and the ApplyPilot workflow from the same FastAPI service. The Dockerfile builds the React/Vite frontend in a Node.js stage and serves its bundled assets through FastAPI in the Python runtime. Deploy the Dockerfile through Render using the **Free** instance plan. `render.yaml` contains the configuration and enables deployment from actual commits on `main`.

1. Sign in to [Render](https://dashboard.render.com).
2. Connect only the `tanish-malekar/applypilot` repository to Render, or deploy its Blueprint. The source repo can remain private.
3. Choose Docker, Free, port from the platform environment, and `/health` as the health check. The startup script aligns browser loopback navigation with that port.
4. Deploy. Visit the returned HTTPS URL. Test a fixture through review and receipt, then search the live Greenhouse feed.
5. For actual hosted AI, use a **Groq Free-plan** account, set the secret `GROQ_API_KEY`, set `CONTENT_MODE=groq`, and keep `GROQ_MODEL=openai/gpt-oss-20b`. [Groq's limits](https://console.groq.com/docs/rate-limits) list this model on the free plan. Do not enable a paid plan or attach billing for ApplyPilot. API failures are visible; the app does not silently pretend it called a model.

Without a model key the platform is still functional, using deterministic grounded facts. Local Ollama is also supported; it runs an installed open model on the developer's computer, not on a free Render instance.

## Limits that affect the demo

[Render Free documentation](https://render.com/docs/free) states that services sleep after 15 idle minutes, can take roughly a minute to wake, and lose local files/SQLite state on restart, redeploy, or sleep. Cloud application history and checkpoint memory therefore last only for the current instance lifetime. Local use persists across process restarts. There is no paid disk or database in this deployment.

Free services share 750 instance hours monthly and have bandwidth/build quotas. Keep the workspace on a free plan with no payment method so quota exhaustion suspends services instead of creating overage charges. This is suitable for a low-traffic personal installation. Anonymous visitor cookies scope histories and applicant memory; it is not a production identity/account system. Use fictional data for public demonstrations.

Hugging Face Docker was considered, but its current [Spaces documentation](https://huggingface.co/docs/hub/spaces-overview) says compute Spaces require a paid plan. No paid service has been provisioned.
