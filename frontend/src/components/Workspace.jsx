import { useEffect, useState } from "react";
import { imageBlob } from "../api.js";
import {
  ArrowRight,
  ArrowUpRight,
  BriefcaseBusiness,
  Check,
  CheckCheck,
  ChevronRight,
  CircleAlert,
  FileCheck2,
  FileText,
  History,
  LoaderCircle,
  ShieldCheck,
  Sparkles,
  UserRound,
} from "lucide-react";
import Badge from "./Badge.jsx";
import { pretty } from "../lib/ui.js";

function BrowserEvidence({ path }) {
  const [url, setUrl] = useState(""),
    [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    let objectUrl;
    imageBlob(path, controller.signal)
      .then((blob) => {
        if (!controller.signal.aborted) {
          objectUrl = URL.createObjectURL(blob);
          setUrl(objectUrl);
        }
      })
      .catch((err) => {
        if (!controller.signal.aborted) setError(err.message);
      });
    return () => {
      controller.abort();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [path]);
  return error ? (
    <p className="auth-error" role="alert">
      {error}
    </p>
  ) : url ? (
    <img
      className="browser-evidence"
      src={url}
      alt="Application form filled and verified by the browser agent"
    />
  ) : (
    <p className="evidence-loading">Loading browser evidence…</p>
  );
}

function MissingFacts({ pending, onResume, busy }) {
  function submit(event) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const answers = Object.fromEntries(
      pending.fields.map((field) => {
        const value = data.get(field);
        return [
          field,
          ["work_authorized", "needs_sponsorship", "has_clearance"].includes(
            field,
          )
            ? value === "true"
            : field === "experience_years"
              ? Number(value)
              : value,
        ];
      }),
    );
    onResume(answers);
  }
  return (
    <div className="input-request">
      <div className="section-label">
        <UserRound size={16} /> A little help from you
      </div>
      <p>
        We need a few facts before continuing. Your answers will be remembered
        for this applicant.
      </p>
      <form onSubmit={submit}>
        {pending.fields.map((field) => (
          <label key={field}>
            {pretty(field)}
            {field === "degree" ? (
              <select
                name={field}
                aria-label={pretty(field)}
                required
                defaultValue=""
              >
                <option value="" disabled>
                  Choose your degree
                </option>
                <option value="high_school">High school</option>
                <option value="bachelors">Bachelor's</option>
                <option value="masters">Master's</option>
                <option value="phd">PhD</option>
              </select>
            ) : [
                "work_authorized",
                "needs_sponsorship",
                "has_clearance",
              ].includes(field) ? (
              <select
                name={field}
                aria-label={pretty(field)}
                required
                defaultValue=""
              >
                <option value="" disabled>
                  Choose an answer
                </option>
                <option value="true">Yes</option>
                <option value="false">No</option>
              </select>
            ) : (
              <input
                name={field}
                aria-label={pretty(field)}
                required
                type={
                  field === "graduation_date"
                    ? "date"
                    : field === "experience_years"
                      ? "number"
                      : "text"
                }
                min={field === "experience_years" ? 0 : undefined}
                step={field === "experience_years" ? "any" : undefined}
              />
            )}
          </label>
        ))}
        <button className="primary" disabled={busy}>
          Save facts & continue <ArrowRight size={16} />
        </button>
      </form>
    </div>
  );
}

export default function Workspace({ run, busy, onResume, selectedJob }) {
  const pending = run?.pending?.[0];
  return (
    <section className="panel workspace" aria-labelledby="studio-title">
      <div className="panel-heading">
        <div className="heading-with-icon">
          <span className="mini-icon">
            <Sparkles size={17} />
          </span>
          <h2 id="studio-title">Application studio</h2>
        </div>
        <Badge status={busy ? "working" : run?.status || "ready"}>
          {busy ? "Working" : run ? undefined : "Ready"}
        </Badge>
      </div>
      {busy ? (
        <div className="workspace-loading" role="status">
          <div className="studio-orb">
            <LoaderCircle className="spin" size={32} />
          </div>
          <h3>Your agents are on it.</h3>
          <p>
            Checking facts, preparing content, and verifying the application.
            This can take a moment.
          </p>
          <div className="loading-lines">
            <span />
            <span />
            <span />
          </div>
        </div>
      ) : !run ? (
        <div className="workspace-empty">
          <div className="studio-illustration" aria-hidden="true">
            <div className="orbit orbit-one" />
            <div className="orbit orbit-two" />
            <div className="studio-orb">
              <FileCheck2 size={36} strokeWidth={1.4} />
            </div>
            <span className="floating-check">
              <Check size={14} />
            </span>
            <span className="floating-spark">
              <Sparkles size={16} />
            </span>
          </div>
          <span className="eyebrow">A LITTLE LESS ON YOUR PLATE</span>
          <h3>
            Your next application
            <br />
            starts here.
          </h3>
          <p>
            Choose an opportunity. We'll prepare the details.
            <br className="desktop-break" /> You make the final call.
          </p>
          <div className="studio-steps">
            <div>
              <span>01</span>
              <b>Check fit</b>
            </div>
            <ChevronRight size={14} />
            <div>
              <span>02</span>
              <b>Prepare</b>
            </div>
            <ChevronRight size={14} />
            <div>
              <span>03</span>
              <b>Review</b>
            </div>
          </div>
          <div className="studio-selected">
            <BriefcaseBusiness size={15} />
            <span>
              {selectedJob ? selectedJob.title : "Select a role to get started"}
            </span>
          </div>
        </div>
      ) : (
        <div className="run-content">
          <div className="run-heading">
            <span className="eyebrow">{run.job.company}</span>
            <h3>{run.job.title}</h3>
            {run.job.source_url && (
              <a
                className="text-link"
                href={run.job.source_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                Original job posting <ArrowUpRight size={14} />
              </a>
            )}
          </div>
          {run.job.source === "greenhouse" && (
            <p className="notice">
              Checks cover extracted requirements. Review the original posting
              for additional criteria.
            </p>
          )}
          {run.eligibility && (
            <div className="checks">
              {run.eligibility.checks.map((check) => (
                <div className={"check-card " + check.status} key={check.name}>
                  <div>
                    {check.status === "pass" ||
                    check.status === "not_applicable" ? (
                      <Check size={13} />
                    ) : (
                      <CircleAlert size={13} />
                    )}
                    <b>{pretty(check.name)}</b>
                    <span>{pretty(check.status)}</span>
                  </div>
                  <p>{check.evidence}</p>
                </div>
              ))}
            </div>
          )}
          {run.content && (
            <div className="document">
              <div className="document-header">
                <FileText size={16} />
                <b>Application statement</b>
                <span>{run.content.fact_ids.length} cited facts</span>
              </div>
              <div className="document-text">{run.content.text}</div>
              <details className="evidence">
                <summary>View grounding evidence</summary>
                <p>
                  Content mode: {run.content.mode}. Each line comes from a
                  verified profile fact.
                </p>
                <ul>
                  {run.content.fact_ids.map((id) => (
                    <li key={id}>{run.content.facts[id]}</li>
                  ))}
                </ul>
              </details>
            </div>
          )}
          {run.verification && (
            <div
              className={
                "verification " +
                (run.verification.passed ? "verified" : "failed")
              }
            >
              <ShieldCheck size={16} />
              <span>
                {run.verification.passed
                  ? "Application content and form fields verified."
                  : run.verification.errors.join("; ")}
              </span>
            </div>
          )}
          {pending?.kind === "review" && (
            <div className="review-block">
              <h4>You're in the pilot's seat.</h4>
              <p>
                Review the content and browser evidence before approving the
                sandbox submission.
              </p>
              <div className="actions">
                <button
                  className="primary"
                  onClick={() => onResume({ approved: true })}
                  disabled={busy}
                >
                  Approve sandbox submission <Check size={16} />
                </button>
                <button
                  className="secondary"
                  onClick={() => onResume({ approved: false })}
                  disabled={busy}
                >
                  Reject
                </button>
              </div>
            </div>
          )}
          {pending && pending.kind !== "review" && (
            <MissingFacts pending={pending} onResume={onResume} busy={busy} />
          )}
          {run.receipt && (
            <div className="receipt">
              <CheckCheck size={19} />
              <div>
                <b>Application submitted to the sandbox</b>
                <code>{run.receipt}</code>
              </div>
            </div>
          )}
          {run.browser?.screenshot && (
            <details className="disclosure">
              <summary>
                <span>
                  <FileCheck2 size={16} /> Browser evidence
                </span>
                <ChevronRight size={16} />
              </summary>
              <BrowserEvidence
                path={
                  "/api/runs/" +
                  run.run_id +
                  "/screenshot?t=" +
                  run.trace.length
                }
              />
            </details>
          )}
          <details className="disclosure">
            <summary>
              <span>
                <History size={16} /> Agent activity
              </span>
              <span className="activity-count">{run.trace.length} events</span>
            </summary>
            <ol className="agent-timeline">
              {run.trace.map((event, index) => (
                <li key={index}>
                  <span className="timeline-dot" />
                  <div>
                    <b>{pretty(event.agent)}</b>
                    <p>{event.message}</p>
                  </div>
                  <time>
                    {new Date(event.at).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </time>
                </li>
              ))}
            </ol>
          </details>
          {run.job.description && (
            <details className="disclosure">
              <summary>
                <span>
                  <BriefcaseBusiness size={16} /> Job description
                </span>
                <ChevronRight size={16} />
              </summary>
              <p className="job-description">{run.job.description}</p>
            </details>
          )}
        </div>
      )}
      <div className="workspace-footer">
        <ShieldCheck size={14} /> Human approval, every time. Submissions stay
        in our sandbox.
      </div>
    </section>
  );
}
