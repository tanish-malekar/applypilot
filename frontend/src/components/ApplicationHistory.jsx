import { FileText, BriefcaseBusiness, ChevronRight } from "lucide-react";
import Badge from "./Badge.jsx";

export default function ApplicationHistory({ runs, onOpen, busy, compact }) {
  if (!runs.length)
    return (
      <div className={"history-empty " + (compact ? "compact" : "")}>
        <FileText size={22} />
        <div>
          <b>A fresh start.</b>
          <p>Your applications will appear here as you prepare them.</p>
        </div>
      </div>
    );
  return (
    <div className="history-list">
      {runs.map((item) => (
        <button
          key={item.run_id}
          className="history-item"
          disabled={busy}
          onClick={() => onOpen(item.run_id)}
        >
          <span className="history-icon">
            <BriefcaseBusiness size={17} />
          </span>
          <div>
            <b>{item.job.title}</b>
            <span>{item.job.company}</span>
          </div>
          <Badge status={item.status} />
          <ChevronRight size={16} />
        </button>
      ))}
    </div>
  );
}
