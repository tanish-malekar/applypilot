import { Check, MapPin } from "lucide-react";
import { initials } from "../lib/ui.js";

export default function JobCard({ job, selected, onSelect, disabled, index }) {
  return (
    <label className={"job-card " + (selected ? "selected" : "")}>
      <input
        type="radio"
        name="job"
        checked={selected}
        onChange={onSelect}
        disabled={disabled}
        aria-label={job.title + " at " + job.company}
      />
      <span className={"company-logo tone-" + (index % 3)} aria-hidden="true">
        {initials(job.company)}
      </span>
      <div className="job-content">
        <div className="job-heading">
          <h3>{job.title}</h3>
          <span className="selection-mark">
            <Check size={12} />
          </span>
        </div>
        <p className="company-name">{job.company}</p>
        <div className="job-meta">
          <span>
            <MapPin size={12} />
            {job.source_location ||
              job.allowed_locations?.join(", ") ||
              "Location not specified"}
          </span>
          <span
            className={
              "source-label " + (job.source === "greenhouse" ? "live" : "")
            }
          >
            {job.source === "greenhouse" ? "Greenhouse" : "Sample role"}
          </span>
        </div>
        {job.skills?.length > 0 && (
          <div className="skill-tags">
            {job.skills.slice(0, 3).map((skill) => (
              <span key={skill}>{skill}</span>
            ))}
          </div>
        )}
      </div>
    </label>
  );
}
