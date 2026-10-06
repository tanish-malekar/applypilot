import { ArrowUpRight, MapPin } from "lucide-react";
import { initials } from "../lib/ui.js";

export default function JobCard({ job, onPrepare, disabled, index }) {
  return (
    <article className={"job-card tone-" + (index % 4)}>
      <div className="job-face">
        <div className="job-topline">
          <span>{job.company}</span>
          <ArrowUpRight size={20} />
        </div>
        <h3>{job.title}</h3>
        <div className="job-meta">
          <MapPin size={14} />
          <span>
            {job.source_location ||
              job.allowed_locations?.join(", ") ||
              "Location not specified"}
          </span>
        </div>
        <div className="skill-tags">
          {job.skills?.slice(0, 3).map((skill) => (
            <span key={skill}>{skill}</span>
          ))}
        </div>
      </div>
      <div className="job-footer">
        <span className="company-logo" aria-hidden="true">
          {initials(job.company)}
        </span>
        <span className="job-source">
          {job.source === "greenhouse" ? "Greenhouse" : "Sample role"}
        </span>
        <button
          className="apply-button"
          onClick={onPrepare}
          disabled={disabled}
          aria-label={"Prepare application for " + job.title}
        >
          Prepare <ArrowUpRight size={14} />
        </button>
      </div>
    </article>
  );
}
