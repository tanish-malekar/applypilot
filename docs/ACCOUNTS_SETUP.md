# Enable managed accounts

ApplyPilot's public home page, signup/login screens, Google OAuth handoff, password recovery, account-scoped profiles, and persistent PostgreSQL workflows are implemented. Real account activation requires a project owned by the platform maintainer. No private provider credentials belong in GitHub or the frontend.

## Free Supabase project

1. Sign in at https://supabase.com/dashboard and create an **ApplyPilot** project on the Free plan. Do not enable billing or upgrade the plan. Choose a strong database password and keep it private.
2. From the project's API settings, copy the project URL and **publishable** key (or legacy **anon** key). These are public application configuration. Never substitute a secret/service-role key.
3. From **Connect**, choose the PostgreSQL **session pooler** connection string, port **5432**. Insert your database password into the connection URI using URL encoding for reserved characters. Add `sslmode=require`. The session pooler supports IPv4 hosting; avoid the transaction pooler for these persistent workflow connections.
4. In the existing Render service's environment settings, configure all of these together:

   ```text
   SUPABASE_URL=https://YOUR_PROJECT.supabase.co
   SUPABASE_PUBLISHABLE_KEY=YOUR_PUBLIC_KEY
   DATABASE_URL=YOUR_PRIVATE_SESSION_POOLER_URI
   AUTH_REQUIRED=1
   ```

   Preserve the existing Groq configuration. The database connection URI is a secret; enter it directly in Render. ApplyPilot refuses to expose secret/service-role keys as public config and refuses to launch hosted accounts without durable database storage.

5. The backend creates a private `applypilot` PostgreSQL schema, account-owned profiles and histories, screenshot evidence, and LangGraph checkpoint tables on startup. The schema is not part of the public Data API, and public schema privileges are revoked. Do not add this schema to Supabase's exposed schemas.

## Authentication URLs

Under Supabase Authentication URL Configuration:

- Site URL: `https://job-application-agents.onrender.com`
- Allowed redirects: `https://job-application-agents.onrender.com/auth/callback` and `https://job-application-agents.onrender.com/auth/recovery`
- Optional local development redirects: `http://127.0.0.1:8000/auth/callback` and `http://127.0.0.1:8000/auth/recovery`

Use explicit redirect URLs. Email/password signup uses email confirmation. Enable a mail service before inviting the public: Supabase's default sender is restricted and is not suitable for arbitrary real-user signup or password recovery. Configure an SMTP provider with a free tier that you control, and verify delivery of confirmation and reset messages. Google sign-in does not require confirmation emails because Google verifies the user's identity.

## Sign in with Google

1. In your Google Cloud project's Google Auth Platform, configure an external application with the ApplyPilot name, homepage URL, and data information URL `https://job-application-agents.onrender.com/privacy`.
2. Request only `openid`, email, and profile scopes. This platform does not need Gmail, Drive, or Contacts access.
3. Create a **Web application** OAuth client. Set the authorized JavaScript origin to `https://job-application-agents.onrender.com`.
4. Set the authorized redirect URI to `https://YOUR_PROJECT.supabase.co/auth/v1/callback`, exactly matching the callback shown in Supabase's Google provider settings.
5. Enter the Google client ID and client secret directly in Supabase's Google provider settings and enable the provider. Do not put the Google secret in the frontend or repository.
6. For public sign-in, set the Google app audience/publishing status appropriately; a Testing app allows only its listed test users. Verify sign-in with a second Google account before declaring public access ready.

The interface discovers provider availability from Supabase's settings. The Google button remains unavailable while the provider is disabled. OAuth uses PKCE and a fixed callback URL.

## Test account

Once the project is ready, use Supabase Authentication → Users → Add user → Create user to create a confirmed test user. Use a fictional email such as `test@applypilot.example` and a unique password. Keep these credentials out of GitHub. The account can use the sample profile to exercise the sandbox workflow.

Alternatively, run `python scripts/create-test-account.py --output /absolute/private/path/test-login.json`. The helper prompts for a one-time Supabase admin key, creates a confirmed user through Supabase's Auth Admin API, generates a random password, and seeds only fictional sample facts. The admin key is not stored or needed by the deployed application. It requires `SUPABASE_URL` and `DATABASE_URL` in the local environment. The output file contains login credentials and must stay private.

## Validation before public account activation

- Email signup and confirmation link work for a non-team email address.
- Email login, logout, and password reset work.
- Google login works with a second account and returns to `/app`.
- Profile edits persist after logout, login, and redeployment.
- One account cannot read or resume another account's runs or screenshots.
- A workflow paused for missing facts or approval resumes after redeployment.
- Browser screenshots remain available after the local runtime directory is gone.

The public landing page remains usable while provider configuration is pending. Without managed account configuration, `/demo` is a visitor-scoped sample workspace; it is not represented as a real-user account. Setting managed account configuration disables anonymous workflow access.

## Primary documentation

- [Supabase Google authentication](https://supabase.com/docs/guides/auth/social-login/auth-google)
- [Database connection modes](https://supabase.com/docs/guides/database/connecting-to-postgres)
- [Supabase production checklist and SMTP](https://supabase.com/docs/guides/deployment/going-into-prod)
- [Supabase free plan](https://supabase.com/pricing)
