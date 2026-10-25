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

[Render Free documentation](https://render.com/docs/free) states that services sleep after 15 idle minutes, can take roughly a minute to wake, and lose local files/SQLite state on restart, redeploy, or sleep. Without an external database, sample-workspace history and checkpoint memory last only for the current instance lifetime. Managed account deployments require an external PostgreSQL database; a Supabase Free project provides account storage and checkpoints without a paid Render disk. Local SQLite use persists across process restarts.

Free services share 750 instance hours monthly and have bandwidth/build quotas. Keep the workspace on a free plan with no payment method so quota exhaustion suspends services instead of creating overage charges. This is suitable for a low-traffic personal installation. When managed accounts are not configured, anonymous visitor cookies scope the sample workspace; use fictional data in that mode. Configuring Supabase requires durable PostgreSQL storage, verifies account tokens on protected requests, and disables anonymous workflow access. Follow [account setup](ACCOUNTS_SETUP.md) before inviting real users; Google provider configuration and public signup email delivery must be verified.

Hugging Face Docker was considered, but its current [Spaces documentation](https://huggingface.co/docs/hub/spaces-overview) says compute Spaces require a paid plan. No paid service has been provisioned.

## Account-enabled deployment

### Recover a paused database

If Render cannot start and its PostgreSQL logs report `tenant/user ... not found`, check the existing Supabase project's dashboard before changing credentials. A paused project can also stop resolving at its public API hostname. Use **Resume project** on the existing Free project, wait for it to become healthy, then restart or redeploy the existing Render service. Preserve `DATABASE_URL` and all account configuration; do not substitute anonymous access or a new empty database. Verify `/health`, `/api/auth/config`, the login page, and an authenticated workspace after recovery.

The React home and privacy pages render without waiting for account initialization. Account routes still require successful configuration and session loading; an unavailable account service does not enable the sample workspace. A database outage can still prevent the Python service from starting, so database recovery is required for the full site.

Configure `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `DATABASE_URL`, and `AUTH_REQUIRED=1` together in the existing Render service. The first two are public browser configuration; the PostgreSQL URI stays private. Use Supabase's session pooler on port 5432 with TLS. The application initializes its private database schema and LangGraph checkpoint tables automatically. Sign-in requires only the public Supabase key; do not give the frontend a secret/service-role key. No paid service has been provisioned.

The public home page is served at `/`, the no-login recorded walkthrough at `/demo`, account screens at `/signup` and `/login`, and the authenticated dashboard at `/app`. The demo uses bundled fictional data and an actual recorded form screenshot; it does not need account configuration, create model calls, or change account history. Google/email callbacks use `/auth/callback`; reset links use `/auth/recovery`. Google availability is discovered from provider settings. Without managed accounts, the live visitor-scoped sample workflow is available at `/practice`; account-enabled installations keep that live anonymous workflow disabled.
