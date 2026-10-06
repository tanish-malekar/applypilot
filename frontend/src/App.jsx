import { useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  ArrowUpRight,
  ChevronRight,
  CircleAlert,
  FileCheck2,
  FileText,
  HelpCircle,
  House,
  LogOut,
  LayoutDashboard,
  LoaderCircle,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  UserRound,
  X,
} from "lucide-react";
import { api } from "./api.js";
import { initials } from "./lib/ui.js";
import ProfileDialog from "./components/ProfileDialog.jsx";
import JobCard from "./components/JobCard.jsx";
import Workspace from "./components/Workspace.jsx";
import ApplicationHistory from "./components/ApplicationHistory.jsx";

function StudioDialog({ open, onClose, children }) {
  const dialog = useRef(null);
  useEffect(() => {
    if (open && !dialog.current.open) dialog.current.showModal();
    else if (!open && dialog.current.open) dialog.current.close();
  }, [open]);
  return (
    <dialog
      ref={dialog}
      className="studio-dialog"
      aria-label="Application workspace"
      onCancel={onClose}
      onClose={onClose}
    >
      <button
        className="icon-button studio-close"
        aria-label="Close application"
        onClick={onClose}
      >
        <X size={21} />
      </button>
      {children}
    </dialog>
  );
}

export default function App({ user, onSignOut, onHome }) {
  const [demo, setDemo] = useState(null);
  const [applicant, setApplicant] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [selected, setSelected] = useState("");
  const [source, setSource] = useState("sample");
  const [board, setBoard] = useState("arvaintelligence");
  const [query, setQuery] = useState("AI");
  const [run, setRun] = useState(null);
  const [runs, setRuns] = useState([]);
  const [busy, setBusy] = useState(false);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState("");
  const [feedback, setFeedback] = useState("");
  const [profileOpen, setProfileOpen] = useState(false);
  const [studioOpen, setStudioOpen] = useState(false);
  const [missing, setMissing] = useState(false);
  const [view, setView] = useState("overview");
  const [filter, setFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [helpOpen, setHelpOpen] = useState(false);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const data = await api("/api/demo");
        const saved = await api("/api/runs");
        const profile = await api("/api/profile");
        if (active) {
          setDemo(data);
          setApplicant(profile);
          setJobs(data.jobs);
          setSelected(data.jobs[0]?.id || "");
          setRuns(saved);
        }
      } catch (err) {
        if (active) setError(err.message);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, []);
  const selectedJob = jobs.find((job) => job.id === selected);
  const needsYou = (item) =>
    [
      "awaiting_review",
      "needs_information",
      "awaiting_information",
      "awaiting_facts",
    ].includes(item.status);
  const reviews = runs.filter(needsYou).length;
  const match = (job) =>
    (job.title + " " + job.company)
      .toLowerCase()
      .includes(filter.toLowerCase().trim());
  const visibleJobs = jobs.filter(match);
  const visibleRuns = runs.filter(
    (item) =>
      match(item.job) &&
      (statusFilter === "All" ||
        (statusFilter === "Needs you"
          ? needsYou(item)
          : statusFilter === "Submitted"
            ? item.status === "submitted"
            : [
                "ineligible",
                "blocked",
                "failed",
                "verification_failed",
                "rejected",
              ].includes(item.status))),
  );
  async function saveProfile(profile) {
    setApplicant(await api("/api/profile", profile));
  }
  async function acceptRun(result) {
    setRun(result);
    setRuns(await api("/api/runs"));
  }
  async function start(job = selectedJob) {
    if (!job || !applicant || busy) return;
    if (user && !applicant.name.trim()) {
      setProfileOpen(true);
      setFeedback(
        "Add your name and verified profile details before preparing an application.",
      );
      return;
    }
    setSelected(job.id);
    setRun(null);
    setStudioOpen(true);
    setBusy(true);
    setError("");
    setFeedback("");
    try {
      await acceptRun(
        await api("/api/runs", {
          applicant: {
            ...applicant,
            ...(missing ? { work_authorized: null } : {}),
          },
          job,
        }),
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }
  async function resume(answer) {
    if (!run || busy) return;
    setBusy(true);
    setError("");
    try {
      await acceptRun(await api("/api/runs/" + run.run_id + "/resume", answer));
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }
  async function search(event) {
    event?.preventDefault();
    if (searching || busy || !demo) return;
    setSearching(true);
    setError("");
    setFeedback("");
    try {
      const data = await api(
        "/api/jobs?board=" +
          encodeURIComponent(board.trim()) +
          "&query=" +
          encodeURIComponent(query.trim()),
      );
      setJobs(data.jobs);
      setSelected(data.jobs[0]?.id || "");
      setSource("greenhouse");
      setFilter("");
      setFeedback(
        data.jobs.length + " live opportunities from " + data.board + ".",
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setSearching(false);
    }
  }
  function samples() {
    if (!demo || busy || searching) return;
    setJobs(demo.jobs);
    setSelected(demo.jobs[0]?.id || "");
    setSource("sample");
    setFilter("");
    setFeedback("");
    setError("");
  }
  async function openRun(id) {
    if (busy) return;
    setStudioOpen(true);
    setBusy(true);
    setError("");
    try {
      setRun(await api("/api/runs/" + id));
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }
  const title =
    view === "overview"
      ? "Dashboard"
      : view === "jobs"
        ? "Browse jobs"
        : "Applications";
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">
        Skip to workspace
      </a>
      <aside className="sidebar">
        <a
          href="/"
          className="brand"
          onClick={(event) => {
            event.preventDefault();
            onHome?.();
          }}
        >
          <span className="brand-mark">
            <Send size={21} />
          </span>
          ApplyPilot
        </a>
        <span className="nav-label">WORKSPACE</span>
        <nav aria-label="Main navigation">
          <button
            className={"nav-item " + (view === "overview" ? "active" : "")}
            onClick={() => setView("overview")}
          >
            <LayoutDashboard size={20} /> Dashboard
          </button>
          <button
            className={"nav-item " + (view === "jobs" ? "active" : "")}
            onClick={() => setView("jobs")}
          >
            <Search size={20} /> Browse jobs
          </button>
          <button
            className={"nav-item " + (view === "applications" ? "active" : "")}
            onClick={() => setView("applications")}
          >
            <FileText size={20} /> Applications{" "}
            <span className="nav-count">{runs.length}</span>
          </button>
          <button
            className="nav-item"
            disabled={!reviews || busy}
            onClick={() => {
              setStatusFilter("Needs you");
              setView("applications");
            }}
          >
            <FileCheck2 size={20} /> Needs you{" "}
            <span className="nav-count">{reviews}</span>
          </button>
          <div className="nav-divider" />
          <button
            className="nav-item"
            disabled={!applicant || busy}
            onClick={() => setProfileOpen(true)}
          >
            <UserRound size={20} /> My profile
          </button>
        </nav>
        <div className="sidebar-bottom">
          <button className="nav-item" onClick={onHome}>
            <House size={19} /> Home
          </button>
          {user && (
            <button className="nav-item" onClick={onSignOut} disabled={busy}>
              <LogOut size={19} /> Log out
            </button>
          )}
          <div className="sandbox-label">
            <span /> Sandbox workspace
          </div>
          <button
            className="support-card"
            onClick={() => setHelpOpen(!helpOpen)}
            aria-expanded={helpOpen}
          >
            <span>
              <HelpCircle size={21} />
            </span>
            <div>
              <b>Help & support</b>
              <small>How ApplyPilot works</small>
            </div>
          </button>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <h1>{title}</h1>
          <label className="global-search">
            <Search size={21} />
            <input
              aria-label="Search by title or company"
              placeholder="Search by title, company..."
              value={filter}
              onChange={(event) => setFilter(event.target.value)}
            />
            {filter && (
              <button
                className="icon-button"
                aria-label="Clear search"
                onClick={() => setFilter("")}
              >
                <X size={16} />
              </button>
            )}
          </label>
          <div className="topbar-right">
            {user && (
              <button
                className="icon-button mobile-signout"
                aria-label="Log out"
                disabled={busy}
                onClick={onSignOut}
              >
                <LogOut size={18} />
              </button>
            )}
            <button
              className="icon-button help-button"
              aria-label="How it works"
              onClick={() => setHelpOpen(!helpOpen)}
            >
              <HelpCircle size={21} />
            </button>
            <button
              className="avatar-button"
              disabled={!applicant || busy}
              onClick={() => setProfileOpen(true)}
              aria-label="Edit applicant profile"
            >
              {initials(applicant?.name)}
            </button>
          </div>
        </header>
        <main id="main">
          {helpOpen && (
            <section className="help-panel">
              <div>
                <h2>A little help with your next move.</h2>
                <p>
                  Choose a sample role or browse a Greenhouse job board. Your
                  agents check your profile, prepare a fact-grounded statement,
                  and fill a sandbox application. Review the evidence before
                  approving. Employer applications are not submitted.
                </p>
                <a
                  className="text-link"
                  href="https://github.com/tanish-malekar/applypilot"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Read the guide <ArrowUpRight size={15} />
                </a>
              </div>
              <button
                className="icon-button"
                aria-label="Close help"
                onClick={() => setHelpOpen(false)}
              >
                <X size={20} />
              </button>
            </section>
          )}
          {view === "overview" && !filter && (
            <section className="hero">
              <div className="hero-copy">
                <span className="hero-eyebrow">
                  <Sparkles size={14} /> YOUR NEXT CHAPTER STARTS HERE
                </span>
                <h2>
                  Your ambition.
                  <br />A little less busywork.
                </h2>
                <p>
                  Find an opportunity. Let your agents prepare the details.
                  <br />
                  You stay in control of every application.
                </p>
                <button className="hero-button" onClick={() => setView("jobs")}>
                  Explore opportunities <ArrowRight size={17} />
                </button>
              </div>
              <div className="hero-art" aria-hidden="true">
                <div className="orbit-ring" />
                <div className="orbit-ring inner" />
                <span className="hero-star star-one">✧</span>
                <span className="hero-star star-two">✧</span>
                <div className="hero-document">
                  <div className="document-icon">
                    <UserRound size={23} />
                  </div>
                  <span className="art-line long" />
                  <span className="art-line" />
                  <span className="art-line long" />
                  <span className="art-line" />
                  <div className="art-ready">
                    <ShieldCheck size={16} /> Ready for your review
                  </div>
                </div>
                <div className="hero-stamp">
                  <ShieldCheck size={17} />
                  You make the final call
                </div>
                <div className="hero-plane">
                  <Send size={31} strokeWidth={1.4} />
                </div>
              </div>
            </section>
          )}
          {error && (
            <div className="error-banner" role="alert">
              <CircleAlert size={18} />
              <span>{error}</span>
              <button
                className="icon-button"
                onClick={() => setError("")}
                aria-label="Dismiss error"
              >
                <X size={16} />
              </button>
            </div>
          )}
          {busy && !studioOpen && (
            <button
              className="progress-banner"
              onClick={() => setStudioOpen(true)}
            >
              <LoaderCircle className="spin" size={17} /> Your agents are
              preparing the application.
              <span>
                View progress <ArrowRight size={15} />
              </span>
            </button>
          )}
          {feedback && (
            <p className="feedback" role="status">
              {feedback}
            </p>
          )}
          {view !== "applications" && (
            <section
              className="opportunities"
              aria-labelledby="opportunity-title"
            >
              <div className="section-heading">
                <div>
                  <h2 id="opportunity-title">
                    {filter ? "Search results" : "Top opportunities"}
                  </h2>
                  <span className="section-caption">
                    {source === "sample"
                      ? "Sample roles · explore the complete workflow"
                      : "Live roles from Greenhouse · sandbox preparation"}
                  </span>
                </div>
                <button
                  className="text-button"
                  onClick={() => setView(view === "jobs" ? "overview" : "jobs")}
                >
                  {view === "jobs" ? "Back to dashboard" : "Browse jobs"}
                  <ChevronRight size={17} />
                </button>
              </div>
              {view === "jobs" && (
                <div className="source-panel">
                  <div className="source-tabs">
                    <button
                      className={source === "sample" ? "active" : ""}
                      onClick={samples}
                      disabled={busy || searching}
                    >
                      Sample roles
                    </button>
                    <span>or find live jobs</span>
                  </div>
                  <form onSubmit={search}>
                    <label>
                      Greenhouse board
                      <input
                        value={board}
                        onChange={(event) => setBoard(event.target.value)}
                        placeholder="arvaintelligence"
                        required
                      />
                    </label>
                    <label>
                      Keyword
                      <input
                        value={query}
                        onChange={(event) => setQuery(event.target.value)}
                        placeholder="AI, engineer..."
                      />
                    </label>
                    <button
                      className="primary"
                      disabled={busy || searching || !demo}
                    >
                      {searching ? (
                        <LoaderCircle className="spin" size={16} />
                      ) : (
                        <Search size={16} />
                      )}{" "}
                      Search jobs
                    </button>
                  </form>
                </div>
              )}
              <div className="jobs-grid">
                {!demo && !error
                  ? [0, 1, 2].map((index) => (
                      <div
                        className="job-skeleton"
                        key={index}
                        aria-label="Loading opportunities"
                      />
                    ))
                  : visibleJobs.map((job, index) => (
                      <JobCard
                        key={job.id}
                        job={job}
                        index={index}
                        onPrepare={() => start(job)}
                        disabled={busy || searching}
                      />
                    ))}
              </div>
              {demo && !visibleJobs.length && (
                <div className="empty-state">
                  <Search size={25} />
                  <b>No opportunities found</b>
                  <p>Try another title, company, or Greenhouse board.</p>
                </div>
              )}
            </section>
          )}
          {view !== "jobs" && (
            <section
              className="applications"
              aria-labelledby="applications-title"
            >
              <div className="section-heading">
                <h2 id="applications-title">All applications</h2>
                <button
                  className="secondary"
                  disabled={
                    !runs.some((item) => item.status === "awaiting_review") ||
                    busy
                  }
                  onClick={() =>
                    openRun(
                      runs.find((item) => item.status === "awaiting_review")
                        .run_id,
                    )
                  }
                >
                  Review next <ArrowRight size={15} />
                </button>
              </div>
              <div
                className="application-filters"
                role="group"
                aria-label="Filter applications"
              >
                {["All", "Needs you", "Submitted", "Blocked"].map((label) => (
                  <button
                    key={label}
                    className={statusFilter === label ? "active" : ""}
                    onClick={() => setStatusFilter(label)}
                  >
                    {label}
                  </button>
                ))}
              </div>
              <ApplicationHistory
                runs={visibleRuns}
                filtered={runs.length > 0}
                onOpen={openRun}
                busy={busy}
              />
            </section>
          )}
          <footer className="page-footer">
            <span>
              <ShieldCheck size={14} /> Prepared by agents. Approved by you.
            </span>
            <span>Submissions stay in the sandbox.</span>
          </footer>
        </main>
      </div>
      <StudioDialog open={studioOpen} onClose={() => setStudioOpen(false)}>
        {error && (
          <p className="error-banner" role="alert">
            {error}
          </p>
        )}
        <Workspace
          run={run}
          busy={busy}
          onResume={resume}
          selectedJob={selectedJob}
        />
      </StudioDialog>
      <ProfileDialog
        applicant={applicant}
        open={profileOpen}
        onClose={() => setProfileOpen(false)}
        onSave={saveProfile}
        realAccount={Boolean(user)}
        missing={missing}
        setMissing={setMissing}
      />
    </div>
  );
}
