import { ArrowLeft, Send } from "lucide-react";
export default function PrivacyPage({ navigate }) {
  return (
    <div className="privacy-page">
      <a
        className="brand"
        href="/"
        onClick={(event) => {
          event.preventDefault();
          navigate("/");
        }}
      >
        <span className="brand-mark">
          <Send size={20} />
        </span>
        ApplyPilot
      </a>
      <main>
        <button className="text-button" onClick={() => navigate("/")}>
          <ArrowLeft size={15} /> Back to home
        </button>
        <h1>Data & privacy</h1>
        <p className="privacy-intro">
          How your account and application information are used in ApplyPilot.
        </p>
        <section>
          <h2>Your account and workspace</h2>
          <p>
            Account sign-in is handled by Supabase. ApplyPilot uses your account
            ID, email, and available display name to open your workspace.
            Signing in with Google requests your basic identity and email; it
            does not request access to Gmail, Drive, or your contacts.
          </p>
          <p>
            Profile details you enter, missing facts you supply, application
            content, workflow history, submission receipts, and browser
            screenshots are stored for your account. Access to these records
            requires a valid session for that account. You can edit your profile
            from My profile.
          </p>
        </section>
        <section>
          <h2>Application preparation</h2>
          <p>
            The hosted AI workflow sends your name, education, experience,
            skills, accomplishments, location, and relevant job description to
            Groq to select supporting facts for application content. Email and
            work-authorization fields are used by the application form and
            eligibility checks. Avoid adding information that you do not want
            processed for this purpose.
          </p>
          <p>
            Render hosts the application service. When account storage is
            enabled, Supabase PostgreSQL stores your profile and workflows,
            including browser evidence. Authentication sessions are kept in your
            browser by the Supabase client so you can return to your account.
          </p>
        </section>
        <section>
          <h2>Optional workflow monitoring</h2>
          <p>
            When the maintainer enables LangSmith, it receives node names,
            status categories, and timings. Application text, identity,
            screenshots, credentials, and model prompts or responses are
            excluded from these traces. Monitoring has a fixed total usage cap.
          </p>
        </section>
        <section>
          <h2>Sandbox submissions</h2>
          <p>
            ApplyPilot discovers real job listings but prepares and submits
            applications in its own sandbox. It does not send your application
            to an employer. Your approval is required before a sandbox
            submission.
          </p>
        </section>
        <section>
          <h2>Questions about your data</h2>
          <p>
            ApplyPilot is maintained by{" "}
            <a
              href="https://github.com/tanish-malekar"
              target="_blank"
              rel="noopener noreferrer"
            >
              tanish-malekar
            </a>
            . Contact the maintainer through that profile for account or data
            questions.
          </p>
        </section>
      </main>
    </div>
  );
}
