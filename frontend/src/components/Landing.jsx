import {
  ArrowRight,
  ArrowUpRight,
  Check,
  FileCheck2,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import preview from "../assets/dashboard-preview.jpg";

export default function Landing({ navigate, user, demoMode, accountsReady }) {
  const destination = user ? "/app" : accountsReady ? "/signup" : "/demo";
  const features = [
    [
      Search,
      "Find your next opportunity",
      "Browse live Greenhouse listings and inspect the original posting, all from one workspace.",
    ],
    [
      Sparkles,
      "Prepare with a little help",
      "Specialized agents check eligibility and assemble application content from your verified profile facts.",
    ],
    [
      FileCheck2,
      "See the work, not just a promise",
      "Review the filled form, uploaded text resume, grounding evidence, and browser screenshot.",
    ],
    [
      ShieldCheck,
      "Keep the final decision",
      "Resolve missing details, approve or reject each application, and follow its progress in your dashboard.",
    ],
  ];
  return (
    <div className="landing-page">
      <header className="landing-nav">
        <a
          className="brand"
          href="/"
          onClick={(event) => {
            event.preventDefault();
            navigate("/");
          }}
        >
          <span className="brand-mark">
            <Send size={21} />
          </span>
          ApplyPilot
        </a>
        <nav aria-label="Website navigation">
          <a href="#features">Features</a>
          <a href="#workspace-preview">The workspace</a>
          <a href="#how-it-works">How it works</a>
        </nav>
        <div className="landing-nav-actions">
          {!user && (
            <button className="text-button" onClick={() => navigate("/login")}>
              Log in
            </button>
          )}
          <button className="primary" onClick={() => navigate(destination)}>
            {user ? "Open dashboard" : "Get started"}
            <ArrowUpRight size={15} />
          </button>
        </div>
      </header>
      <main className="landing-main">
        <section className="landing-hero">
          <div className="landing-kicker">
            <span /> YOUR AMBITION, WITH A COPILOT
          </div>
          <h1>
            The next chapter is yours.
            <br />
            <span>Let’s clear the busywork.</span>
          </h1>
          <p>
            A calmer way to discover jobs, prepare grounded applications,
            <br className="desktop-break" /> and review every step. Your agents
            help. You make the final call.
          </p>
          <div className="landing-hero-actions">
            <button className="primary" onClick={() => navigate(destination)}>
              {user
                ? "Go to your workspace"
                : accountsReady
                  ? "Create your free account"
                  : "Explore the workspace"}
              <ArrowRight size={17} />
            </button>
            <a href="#workspace-preview" className="landing-outline">
              Explore the workspace <ArrowUpRight size={15} />
            </a>
          </div>
          <div className="landing-benefits">
            <span>
              <Check size={13} /> Human approval built in
            </span>
            <span>
              <Check size={13} /> Grounded in your facts
            </span>
            <span>
              <Check size={13} /> Browser evidence included
            </span>
          </div>
        </section>
        <section id="workspace-preview" className="landing-preview">
          <div className="preview-browserbar">
            <span />
            <span />
            <span />
            <b>applypilot · your application workspace</b>
          </div>
          <img
            src={preview}
            alt="ApplyPilot dashboard showing pastel job cards, profile navigation, and an application status table"
          />
          <div className="preview-caption">
            <span>
              <ShieldCheck size={14} /> An actual ApplyPilot dashboard
            </span>
            <span>Sample roles and sandbox outcomes shown.</span>
          </div>
        </section>
        <section id="features" className="landing-section">
          <div className="landing-section-intro">
            <span className="eyebrow">LESS FRICTION, MORE CLARITY</span>
            <h2>
              Everything you need
              <br />
              for a more deliberate next move.
            </h2>
            <p>
              From a job listing to a reviewed application, with evidence at
              every step.
            </p>
          </div>
          <div className="landing-feature-grid">
            {features.map(([Icon, title, description], index) => (
              <article
                key={title}
                className={"landing-feature feature-tone-" + index}
              >
                <span className="feature-icon">
                  <Icon size={23} strokeWidth={1.6} />
                </span>
                <h3>{title}</h3>
                <p>{description}</p>
              </article>
            ))}
          </div>
        </section>
        <section id="how-it-works" className="landing-workflow">
          <div>
            <span className="eyebrow">A WORKFLOW WITH YOU IN IT</span>
            <h2>
              Three steps.
              <br />
              One clear next move.
            </h2>
          </div>
          <ol>
            <li>
              <span>01</span>
              <div>
                <h3>Build your foundation</h3>
                <p>
                  Add your qualifications, experience, and verified
                  accomplishments.
                </p>
              </div>
            </li>
            <li>
              <span>02</span>
              <div>
                <h3>Choose an opportunity</h3>
                <p>
                  Explore a live job board or use a sample role to try the
                  workflow.
                </p>
              </div>
            </li>
            <li>
              <span>03</span>
              <div>
                <h3>Review, then decide</h3>
                <p>
                  Inspect the content and browser evidence before approving a
                  sandbox submission.
                </p>
              </div>
            </li>
          </ol>
        </section>
        <section className="landing-cta">
          <Sparkles size={24} />
          <h2>
            Your next move deserves
            <br />a little more breathing room.
          </h2>
          <p>Start with your profile. Take it one opportunity at a time.</p>
          <button className="primary" onClick={() => navigate(destination)}>
            {user
              ? "Open your dashboard"
              : accountsReady
                ? "Get started free"
                : "Try the sample workspace"}
            <ArrowRight size={17} />
          </button>
          {demoMode && (
            <button className="text-button" onClick={() => navigate("/demo")}>
              Try the sample workspace without an account{" "}
              <ArrowUpRight size={14} />
            </button>
          )}
        </section>
      </main>
      <footer className="landing-footer">
        <a
          className="brand"
          href="/"
          onClick={(event) => {
            event.preventDefault();
            navigate("/");
          }}
        >
          <span className="brand-mark">
            <Send size={17} />
          </span>
          ApplyPilot
        </a>
        <p>
          Live job discovery. Reviewed preparation. Submissions stay in our
          sandbox.
        </p>
        <button className="text-button" onClick={() => navigate("/privacy")}>
          Data & privacy
        </button>
        <a
          href="https://github.com/tanish-malekar/applypilot"
          target="_blank"
          rel="noopener noreferrer"
        >
          About the project <ArrowUpRight size={13} />
        </a>
      </footer>
    </div>
  );
}
