import { ChevronRight, FileText } from "lucide-react";
import { initials } from "../lib/ui.js";
import Badge from "./Badge.jsx";

function updatedAt(item) {
  const date = item.trace?.at(-1)?.at;
  return date
    ? new Date(date).toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
      })
    : "—";
}
export default function ApplicationHistory({ runs, onOpen, busy, filtered }) {
  return (
    <div className="application-table-wrap">
      <table className="application-table">
        <thead>
          <tr>
            <th>Position</th>
            <th>Resume</th>
            <th>Statement</th>
            <th>Status</th>
            <th>Updated</th>
            <th>
              <span className="sr-only">Open application</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {runs.map((item, index) => (
            <tr key={item.run_id}>
              <td>
                <button
                  className="history-item"
                  disabled={busy}
                  onClick={() => onOpen(item.run_id)}
                >
                  <span
                    className={"history-logo tone-" + (index % 4)}
                    aria-hidden="true"
                  >
                    {initials(item.job.company)}
                  </span>
                  <span>
                    <b>{item.job.company}</b>
                    <small>{item.job.title}</small>
                  </span>
                </button>
              </td>
              <td>
                <span
                  className={
                    item.browser?.upload?.includes("resume.txt")
                      ? "artifact-ready"
                      : "artifact-waiting"
                  }
                >
                  {item.browser?.upload?.includes("resume.txt") ? "Ready" : "—"}
                </span>
              </td>
              <td>
                <span
                  className={
                    item.content ? "artifact-ready" : "artifact-waiting"
                  }
                >
                  {item.content ? "Ready" : "—"}
                </span>
              </td>
              <td>
                <Badge status={item.status} />
              </td>
              <td className="table-date">{updatedAt(item)}</td>
              <td>
                <button
                  className="icon-button"
                  disabled={busy}
                  onClick={() => onOpen(item.run_id)}
                  aria-label={"Open " + item.job.title}
                >
                  <ChevronRight size={18} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {!runs.length && (
        <div className="history-empty">
          <span className="empty-icon">
            <FileText size={24} />
          </span>
          <b>
            {filtered
              ? "No applications match this view."
              : "Your next chapter starts with one application."}
          </b>
          <p>
            {filtered
              ? "Try another status or search term."
              : "Prepared applications and their progress will appear here."}
          </p>
        </div>
      )}
    </div>
  );
}
