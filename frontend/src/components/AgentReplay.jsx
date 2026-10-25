import { useEffect, useRef, useState } from "react";
import {
  Check,
  FileText,
  MousePointer2,
  Pause,
  Play,
  RotateCcw,
  ShieldCheck,
} from "lucide-react";
import recording from "../demo/recording.json";
import "../demo/replay.css";

const fields = recording.review.browser.fields;
const steps = [
  ["name", "Full name", fields.name],
  ["email", "Email address", fields.email],
  ["location", "Location", fields.location],
  ["work_authorized", "Authorized to work", fields.work_authorized],
  ["needs_sponsorship", "Need sponsorship", fields.needs_sponsorship],
  ["resume", "Upload resume", "alex-morgan-resume.txt"],
  ["cover_letter", "Cover letter", fields.cover_letter],
  ["application_answers", "Application questions", fields.application_answers],
  ["verify", "Check the completed form", ""],
  ["approval", "Human approval recorded", ""],
  ["submit", "Click Submit application", ""],
  ["done", "Sandbox submission confirmed", ""],
];
const duration = 1200;

export default function AgentReplay({ onReview }) {
  const [elapsed, setElapsed] = useState(0);
  const [playing, setPlaying] = useState(
    () => !window.matchMedia("(prefers-reduced-motion: reduce)").matches,
  );
  const [speed, setSpeed] = useState(1);
  const viewport = useRef(null);
  const player = useRef(null);
  const targets = useRef({});
  const index = Math.min(Math.floor(elapsed / duration), steps.length - 1);
  const phase = steps[index][0];
  const finished = phase === "done";
  useEffect(() => {
    // Keep the entire browser visible so the Submit click is not below the fold.
    player.current?.scrollIntoView({ block: "start", behavior: "instant" });
  }, []);
  useEffect(() => {
    if (!playing || finished) return;
    const timer = setInterval(
      () =>
        setElapsed((value) =>
          Math.min(value + 80 * speed, duration * (steps.length - 1)),
        ),
      80,
    );
    return () => clearInterval(timer);
  }, [playing, finished, speed]);
  useEffect(() => {
    const target = targets.current[phase] || targets.current.submit;
    if (!target || !viewport.current) return;
    const top = target.offsetTop - 24;
    viewport.current.scrollTo({ top: Math.max(0, top), behavior: "instant" });
  }, [phase]);
  function valueAt(position) {
    if (index > position) return String(steps[position][2]);
    if (index < position) return "";
    const progress = Math.min(1, (elapsed % duration) / (duration * 0.65));
    const text = String(steps[position][2]);
    return text.slice(0, Math.ceil(progress * text.length));
  }
  function restart() {
    setElapsed(0);
    setPlaying(true);
  }
  return (
    <section
      ref={player}
      className="agent-replay"
      aria-label="Agent browser replay"
    >
      <div className="replay-toolbar">
        <div>
          <span className="eyebrow">WATCH THE AGENT WORK</span>
          <h2>From blank form to submitted.</h2>
        </div>
        <div className="replay-actions">
          <button
            className="secondary"
            onClick={() => (finished ? restart() : setPlaying(!playing))}
          >
            {playing && !finished ? <Pause size={15} /> : <Play size={15} />}
            {finished ? "Play again" : playing ? "Pause replay" : "Play replay"}
          </button>
          <button
            className="text-button"
            onClick={() => setSpeed(speed === 1 ? 2 : 1)}
            aria-label="Change replay speed"
          >
            {speed}× speed
          </button>
          <button className="text-button" onClick={restart}>
            <RotateCcw size={15} /> Restart animation
          </button>
        </div>
      </div>
      <p className="replay-caption">
        Animated replay of the fictional sandbox example. Sample human approval
        appears before Submit; no application is sent from this demo.
      </p>
      <div className="replay-layout">
        <aside className="replay-activity" aria-label="Replay steps">
          {steps.map(([key, label], position) => (
            <div
              key={key}
              className={
                position === index
                  ? "replay-step active"
                  : position < index
                    ? "replay-step complete"
                    : "replay-step"
              }
            >
              <span>
                {position < index ? <Check size={13} /> : position + 1}
              </span>
              {label}
            </div>
          ))}
        </aside>
        <div className="replay-browser">
          <div className="replay-browserbar">
            <i />
            <i />
            <i />
            <span>Northstar Demo Labs · application sandbox</span>
          </div>
          <div className="replay-live-status" role="status" aria-live="polite">
            <span className={finished ? "" : "replay-dot"} />
            {steps[index][1]}
            {finished && <Check size={16} />}
          </div>
          {finished ? (
            <div className="replay-success">
              <span>
                <Check size={34} />
              </span>
              <h3>Application submitted</h3>
              <p>
                Replay complete. The sample agent filled the form, verified the
                fields, waited for approval, and clicked Submit.
              </p>
              <code>{recording.submitted.receipt}</code>
              <small>Recorded sandbox receipt · no new submission</small>
              <button className="primary" onClick={onReview}>
                Inspect the documents & evidence
              </button>
            </div>
          ) : (
            <div className="replay-form-scroll" ref={viewport}>
              <div className="replay-form-heading">
                <span className="eyebrow">NORTHSTAR DEMO LABS</span>
                <h3>Applied ML Engineer Intern</h3>
                <p>Application form · fictional candidate</p>
              </div>
              {steps.slice(0, 8).map(([key, label], position) => (
                <div
                  key={key}
                  ref={(node) => {
                    targets.current[key] = node;
                  }}
                  className={
                    "replay-field " + (phase === key ? "is-filling" : "")
                  }
                >
                  <label htmlFor={"replay-" + key}>
                    {label}
                    {index > position && <Check size={14} />}
                  </label>
                  {phase === key && (
                    <span className="agent-pointer">
                      <MousePointer2 size={23} fill="currentColor" />
                      <b>Agent</b>
                    </span>
                  )}
                  {key === "resume" ? (
                    <div className="replay-upload" data-demo-field={key}>
                      <FileText size={20} />
                      {valueAt(position) || "Choose a file…"}
                      {index > position && <span>Uploaded</span>}
                    </div>
                  ) : ["cover_letter", "application_answers"].includes(key) ? (
                    <textarea
                      id={"replay-" + key}
                      data-demo-field={key}
                      readOnly
                      tabIndex={-1}
                      value={valueAt(position)}
                      placeholder="Waiting for agent…"
                    />
                  ) : (
                    <input
                      id={"replay-" + key}
                      data-demo-field={key}
                      readOnly
                      tabIndex={-1}
                      value={valueAt(position)}
                      placeholder="Waiting for agent…"
                    />
                  )}
                </div>
              ))}
              <div
                className="replay-submit-area"
                ref={(node) => {
                  targets.current.submit = node;
                }}
              >
                {index >= 8 && (
                  <p className="replay-verified">
                    <ShieldCheck size={16} /> All fields checked against Alex’s
                    profile.
                  </p>
                )}
                {index >= 9 && (
                  <p className="replay-approved">
                    <Check size={16} /> Sample human approval received
                  </p>
                )}
                {phase === "submit" && (
                  <span className="agent-pointer submit-pointer">
                    <MousePointer2 size={25} fill="currentColor" />
                    <b>Agent clicks</b>
                  </span>
                )}
                <button
                  type="button"
                  tabIndex={-1}
                  aria-disabled="true"
                  className={
                    "primary replay-submit " +
                    (phase === "submit" ? "is-clicking" : "")
                  }
                >
                  Submit application
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
      <progress
        aria-label="Replay progress"
        value={index}
        max={steps.length - 1}
      />
    </section>
  );
}
