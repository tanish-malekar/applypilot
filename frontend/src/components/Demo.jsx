import { useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  RotateCcw,
  Send,
  ShieldCheck,
} from "lucide-react";
import Workspace from "./Workspace.jsx";
import recording from "../demo/recording.json";
import evidence from "../demo/form-evidence.png";
import "../demo/demo.css";

export default function Demo({ navigate }) {
  const [tab, setTab] = useState("review");
  const [decision, setDecision] = useState(null);
  const profile = recording.applicant;
  const run =
    decision === true
      ? recording.submitted
      : decision === false
        ? { ...recording.review, status: "rejected", pending: [] }
        : recording.review;
  const tabs = [
    ["profile", "1. Sample profile"],
    ["form", "2. Filled form"],
    ["review", "3. Review & approve"],
  ];
  return (
    <div className="demo-page">
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
        <button className="text-button" onClick={() => navigate("/")}>
          <ArrowLeft size={16} /> Home
        </button>
        <button className="primary" onClick={() => navigate("/signup")}>
          Create an account <ArrowRight size={16} />
        </button>
      </header>
      <main className="demo-main">
        <div className="demo-intro">
          <span className="eyebrow">INTERACTIVE DEMO · NO SIGNUP NEEDED</span>
          <h1>Your first application. Already prepared.</h1>
          <p>
            Meet Alex, our fictional applicant. Explore the filled form, read
            the documents, and try approving the application.
          </p>
          <div className="demo-note">
            <ShieldCheck size={18} />
            <span>
              Real recorded sandbox results. This walkthrough runs in your
              browser, uses no personal details, and sends no applications.
            </span>
          </div>
        </div>
        <div className="demo-controls">
          <div role="tablist" aria-label="Demo steps">
            {tabs.map(([id, label]) => (
              <button
                key={id}
                id={"demo-tab-" + id}
                role="tab"
                aria-selected={tab === id}
                aria-controls="demo-panel"
                onClick={() => setTab(id)}
                className={tab === id ? "primary" : "secondary"}
              >
                {label}
              </button>
            ))}
          </div>
          <button
            className="text-button"
            onClick={() => {
              setDecision(null);
              setTab("review");
            }}
          >
            <RotateCcw size={15} /> Restart demo
          </button>
        </div>
        <section
          id="demo-panel"
          role="tabpanel"
          aria-labelledby={"demo-tab-" + tab}
        >
          {tab === "profile" ? (
            <div className="demo-card">
              <span className="eyebrow">EVERYTHING IS PREFILLED</span>
              <h2>{profile.name}</h2>
              <p>
                {profile.email} · {profile.location}
              </p>
              <dl className="demo-facts">
                <div>
                  <dt>Education</dt>
                  <dd>Master’s · graduating May 2027</dd>
                </div>
                <div>
                  <dt>Experience</dt>
                  <dd>{profile.experience_years} year</dd>
                </div>
                <div>
                  <dt>Skills</dt>
                  <dd>{profile.skills.join(", ")}</dd>
                </div>
                <div>
                  <dt>Verified accomplishment</dt>
                  <dd>{profile.accomplishments[0]}</dd>
                </div>
              </dl>
              <button className="primary" onClick={() => setTab("form")}>
                See the filled form <ArrowRight size={16} />
              </button>
            </div>
          ) : tab === "form" ? (
            <div className="demo-card">
              <span className="eyebrow">BROWSER AUTOFILL IN ACTION</span>
              <h2>The form, filled and checked.</h2>
              <p>
                This screenshot was captured from a real Playwright run using
                Alex’s sample profile.
              </p>
              <div className="demo-checks">
                {recording.review.eligibility.checks.map((check) => (
                  <span key={check.name}>
                    <Check size={14} />
                    {check.name.replaceAll("_", " ")}
                  </span>
                ))}
              </div>
              <img
                className="browser-evidence"
                src={evidence}
                alt="Recorded sandbox form filled for fictional applicant Alex Morgan"
              />
              <button className="primary" onClick={() => setTab("review")}>
                Review the application <ArrowRight size={16} />
              </button>
            </div>
          ) : (
            <>
              {decision === false && (
                <p className="demo-note" role="status">
                  Demo application rejected. Nothing was sent. Restart the demo
                  to try approval.
                </p>
              )}
              {decision === true && (
                <p className="demo-note" role="status">
                  You completed the demo. The recorded sandbox receipt is below;
                  no new application was sent.
                </p>
              )}
              <Workspace
                run={run}
                busy={false}
                onResume={({ approved }) => setDecision(approved)}
                selectedJob={run.job}
                demoEvidence={evidence}
              />
            </>
          )}
        </section>
      </main>
    </div>
  );
}
