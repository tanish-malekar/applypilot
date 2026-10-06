import { useEffect, useState } from "react";
import {
  ArrowRight,
  ArrowUpRight,
  BriefcaseBusiness,
  Check,
  ChevronRight,
  CircleAlert,
  Clock3,
  FileText,
  History,
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
import { pretty, initials } from "./lib/ui.js";
import ProfileDialog from "./components/ProfileDialog.jsx";
import JobCard from "./components/JobCard.jsx";
import Workspace from "./components/Workspace.jsx";
import ApplicationHistory from "./components/ApplicationHistory.jsx";

export default function App() {
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
  const [missing, setMissing] = useState(false);
  const [view, setView] = useState("overview");

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const data = await api("/api/demo");
        const saved = await api("/api/runs");
        if (active) {
          setDemo(data);
          setApplicant(data.applicant);
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
  const reviews = runs.filter(
    (item) => item.status === "awaiting_review",
  ).length;
  async function acceptRun(result) {
    setRun(result);
    setRuns(await api("/api/runs"));
  }
  async function start() {
    if (!selectedJob || !applicant || busy) return;
    setBusy(true);
    setError("");
    setFeedback("");
    try {
      const profile = {
        ...applicant,
        ...(missing ? { work_authorized: null } : {}),
      };
      const result = await api("/api/runs", {
        applicant: profile,
        job: selectedJob,
      });
      await acceptRun(result);
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
    setFeedback("");
    setError("");
  }
  async function openRun(id) {
    if (busy) return;
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

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">
        Skip to workspace
      </a>
      <aside className="sidebar">
        <a href="#main" className="brand" onClick={() => setView("overview")}>
          <span className="brand-mark">
            <Send size={22} strokeWidth={1.8} />
          </span>
          ApplyPilot<span className="brand-dot">.</span>
        </a>
        <span className="nav-label">YOUR WORKSPACE</span>
        <nav aria-label="Main navigation">
          <button
            className={"nav-item " + (view === "overview" ? "active" : "")}
            onClick={() => setView("overview")}
          >
            <LayoutDashboard size={18} /> Overview <ChevronRight size={14} />
          </button>
          <button
            className={"nav-item " + (view === "applications" ? "active" : "")}
            onClick={() => setView("applications")}
          >
            <BriefcaseBusiness size={18} /> Applications{" "}
            <span className="nav-count">{runs.length}</span>
          </button>
          <button
            className="nav-item"
            disabled={!applicant || busy}
            onClick={() => setProfileOpen(true)}
          >
            <UserRound size={18} /> My profile <ArrowUpRight size={14} />
          </button>
        </nav>
        <div className="sidebar-bottom">
          <div className="copilot-note">
            <span className="note-icon">
              <Sparkles size={19} />
            </span>
            <b>A copilot, not autopilot.</b>
            <p>
              Your agents do the busywork.
              <br />
              You always make the final call.
            </p>
          </div>
          <div className="sandbox-note">
            <span />
            Sandbox workspace <ShieldCheck size={14} />
          </div>
          <a
            className="sidebar-link"
            href="https://github.com/tanish-malekar/applypilot"
            target="_blank"
            rel="noopener noreferrer"
          >
            About ApplyPilot <ArrowUpRight size={13} />
          </a>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <ChevronRight size={13} />
            <strong>{view === "overview" ? "Overview" : "Applications"}</strong>
          </div>
          <div className="topbar-right">
            <span className="review-enabled">
              <ShieldCheck size={14} /> Human review enabled
            </span>
            <button
              className="avatar-button"
              onClick={() => setProfileOpen(true)}
              disabled={!applicant || busy}
              aria-label="Edit applicant profile"
            >
              {initials(applicant?.name)}
            </button>
          </div>
        </header>
        <main id="main">
          <div className="hero">
            <div>
              <div className="eyebrow">
                <span className="small-line" /> YOUR APPLICATION COPILOT
              </div>
              <h1>
                Less busywork.
                <br />
                <span>More possibility.</span>
              </h1>
              <p>
                Find the right opportunity. Let your agents handle the details.
                <br className="desktop-break" /> Make your next move with
                confidence.
              </p>
            </div>
            <div className="hero-visual" aria-hidden="true">
              <div className="hero-orbit" />
              <div className="hero-orbit inner" />
              <div className="hero-core">
                <Send size={30} strokeWidth={1.4} />
              </div>
              <div className="visual-label discover">
                <Search size={14} /> Discover
              </div>
              <div className="visual-label prepare">
                <FileText size={14} /> Prepare
              </div>
              <div className="visual-label review">
                <ShieldCheck size={14} /> Review
              </div>
              <span className="visual-dot one" />
              <span className="visual-dot two" />
            </div>
          </div>
          <div className="metrics">
            <div className="metric">
              <span className="metric-icon violet">
                <BriefcaseBusiness size={19} />
              </span>
              <div>
                <span>Opportunities</span>
                <b>
                  {demo ? jobs.length : "—"}{" "}
                  <small>
                    {source === "sample" ? "sample roles" : "live roles"}
                  </small>
                </b>
              </div>
            </div>
            <div className="metric">
              <span className="metric-icon peach">
                <FileText size={19} />
              </span>
              <div>
                <span>Your applications</span>
                <b>
                  {runs.length} <small>in this workspace</small>
                </b>
              </div>
            </div>
            <div className="metric">
              <span className="metric-icon mint">
                <Clock3 size={19} />
              </span>
              <div>
                <span>Awaiting your review</span>
                <b>
                  {reviews}{" "}
                  <small>
                    {reviews === 1 ? "application" : "applications"}
                  </small>
                </b>
              </div>
              <span className="metric-status">You're in control</span>
            </div>
          </div>
          {error && (
            <div className="alert" role="alert">
              <CircleAlert size={18} />
              <span>{error}</span>
              <button
                className="icon-button"
                aria-label="Dismiss error"
                onClick={() => setError("")}
              >
                <X size={16} />
              </button>
            </div>
          )}
          {feedback && (
            <div className="feedback" role="status">
              <Check size={15} />
              {feedback}
            </div>
          )}
          <div className="workspace-grid">
            <div className="left-column">
              {view === "overview" ? (
                <section
                  className="panel opportunities"
                  aria-labelledby="opportunity-title"
                >
                  <div className="panel-heading">
                    <div>
                      <span className="eyebrow">EXPLORE WHAT'S NEXT</span>
                      <h2 id="opportunity-title">Your next opportunity</h2>
                    </div>
                    <span className="outline-icon">
                      <ArrowUpRight size={20} />
                    </span>
                  </div>
                  <div className="source-tabs" aria-label="Job source">
                    <button
                      className={source === "sample" ? "active" : ""}
                      onClick={samples}
                      disabled={busy || searching}
                    >
                      Sample roles <span>{demo?.jobs.length || 0}</span>
                    </button>
                    <button
                      className={source === "greenhouse" ? "active" : ""}
                      onClick={search}
                      disabled={busy || searching || !demo}
                    >
                      <span className="live-dot" />
                      Live Greenhouse
                    </button>
                  </div>
                  <form className="search-form" onSubmit={search}>
                    <label>
                      Company board
                      <input
                        value={board}
                        onChange={(event) => setBoard(event.target.value)}
                        required
                        placeholder="arvaintelligence"
                        disabled={busy || searching}
                      />
                    </label>
                    <label>
                      Keywords
                      <div className="search-input">
                        <Search size={15} />
                        <input
                          value={query}
                          onChange={(event) => setQuery(event.target.value)}
                          placeholder="Role or skill"
                          disabled={busy || searching}
                        />
                      </div>
                    </label>
                    <button
                      type="submit"
                      className="search-button"
                      disabled={!demo || busy || searching}
                      aria-label="Find jobs"
                    >
                      {searching ? (
                        <LoaderCircle className="spin" size={18} />
                      ) : (
                        <ArrowRight size={18} />
                      )}
                    </button>
                  </form>
                  <div className="list-label">
                    <span>
                      {source === "sample"
                        ? "Try the complete workflow with a sample role"
                        : "Live opportunities · " + jobs.length + " results"}
                    </span>
                    {searching && <LoaderCircle className="spin" size={13} />}
                  </div>
                  <div className="job-list">
                    {!demo && !error ? (
                      <div className="list-empty">
                        <LoaderCircle className="spin" size={22} />
                        <p>Loading your workspace…</p>
                      </div>
                    ) : jobs.length ? (
                      jobs.map((job, index) => (
                        <JobCard
                          key={job.id}
                          job={job}
                          index={index}
                          selected={job.id === selected}
                          onSelect={() => setSelected(job.id)}
                          disabled={busy || searching}
                        />
                      ))
                    ) : (
                      <div className="list-empty">
                        <Search size={25} />
                        <h3>No roles found.</h3>
                        <p>Try another keyword or company board.</p>
                        <button className="text-link" onClick={samples}>
                          Explore sample roles <ArrowRight size={14} />
                        </button>
                      </div>
                    )}
                  </div>
                  <div className="prepare-footer">
                    <div>
                      <ShieldCheck size={15} />
                      <span>You'll review before anything is submitted.</span>
                    </div>
                    <button
                      className="primary prepare-button"
                      onClick={start}
                      disabled={!selectedJob || !applicant || busy || searching}
                    >
                      {busy ? (
                        <>
                          <LoaderCircle className="spin" size={16} /> Preparing…
                        </>
                      ) : (
                        <>
                          Prepare application <ArrowRight size={17} />
                        </>
                      )}
                    </button>
                  </div>
                </section>
              ) : (
                <section className="panel applications">
                  <div className="panel-heading">
                    <div>
                      <span className="eyebrow">EVERY STEP, IN ONE PLACE</span>
                      <h2>Your applications</h2>
                    </div>
                    <History size={20} />
                  </div>
                  <p className="panel-description">
                    Open an application to review its checks, activity, and
                    outcome.
                  </p>
                  <ApplicationHistory
                    runs={runs}
                    onOpen={openRun}
                    busy={busy}
                  />
                  <button
                    className="text-link explore-link"
                    onClick={() => setView("overview")}
                  >
                    Explore opportunities <ArrowRight size={15} />
                  </button>
                </section>
              )}
              <div className="profile-summary">
                <span className="profile-avatar">
                  {initials(applicant?.name)}
                </span>
                <div>
                  <b>{applicant?.name || "Your profile"}</b>
                  <span>
                    {applicant?.degree ? pretty(applicant.degree) + " · " : ""}
                    {applicant?.location || "Complete your profile"}
                  </span>
                </div>
                <button
                  className="icon-button"
                  aria-label="Edit profile"
                  onClick={() => setProfileOpen(true)}
                  disabled={!applicant || busy}
                >
                  <ArrowUpRight size={18} />
                </button>
              </div>
              {view === "overview" && (
                <section className="panel recent-applications">
                  <div className="small-panel-heading">
                    <h2>Recent applications</h2>
                    <button
                      className="text-link"
                      onClick={() => setView("applications")}
                    >
                      View all <ArrowRight size={14} />
                    </button>
                  </div>
                  <ApplicationHistory
                    runs={runs.slice(0, 3)}
                    onOpen={openRun}
                    busy={busy}
                    compact
                  />
                </section>
              )}
            </div>
            <Workspace
              run={run}
              busy={busy}
              onResume={resume}
              selectedJob={selectedJob}
            />
          </div>
          <footer className="page-footer">
            <span>Made for your next chapter.</span>
            <span>
              ApplyPilot <span className="footer-dot">·</span> Live discovery.
              Reviewed sandbox applications.
            </span>
          </footer>
        </main>
      </div>
      <ProfileDialog
        applicant={applicant}
        open={profileOpen}
        onClose={() => setProfileOpen(false)}
        onSave={(value) => {
          setApplicant(value);
          setFeedback(
            "Profile updated. Your next application will use these facts.",
          );
        }}
        missing={missing}
        setMissing={setMissing}
      />
    </div>
  );
}
