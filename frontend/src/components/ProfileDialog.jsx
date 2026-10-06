import { useEffect, useRef, useState } from "react";
import { X, Check, ShieldCheck } from "lucide-react";
import { profileFields } from "../lib/ui.js";

export default function ProfileDialog({
  applicant,
  open,
  onClose,
  onSave,
  missing,
  setMissing,
  realAccount,
}) {
  const dialog = useRef(null);
  const [draft, setDraft] = useState({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    if (open && applicant) {
      setDraft(
        Object.fromEntries(
          profileFields.map(([key, , type]) => [
            key,
            Array.isArray(applicant[key])
              ? applicant[key].join(type === "skills" ? ", " : "\n")
              : String(applicant[key] ?? ""),
          ]),
        ),
      );
      if (!dialog.current.open) dialog.current.showModal();
    } else if (dialog.current?.open) dialog.current.close();
  }, [open, applicant]);
  async function save(event) {
    event.preventDefault();
    const updated = { ...applicant };
    for (const [key, , type] of profileFields) {
      const value = String(draft[key] ?? "").trim();
      updated[key] =
        type === "skills" || type === "accomplishments"
          ? value
              .split(type === "skills" ? "," : "\n")
              .map((text) => text.trim())
              .filter(Boolean)
          : type === "boolean"
            ? value === ""
              ? null
              : value === "true"
            : type === "number"
              ? value === ""
                ? null
                : Number(value)
              : value || null;
    }
    setSaving(true);
    setError("");
    try {
      await onSave(updated);
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }
  return (
    <dialog
      ref={dialog}
      onCancel={onClose}
      onClose={onClose}
      className="profile-dialog"
      aria-labelledby="profile-title"
    >
      <div className="dialog-header">
        <div>
          <span className="eyebrow">YOUR FOUNDATION</span>
          <h2 id="profile-title">Applicant profile</h2>
        </div>
        <button
          className="icon-button"
          onClick={onClose}
          aria-label="Close profile"
        >
          <X size={20} />
        </button>
      </div>
      <p className="dialog-description">
        Your agents work from these facts. Start with the sample profile or add
        your own verified details.
      </p>
      {error && (
        <p className="auth-error" role="alert">
          {error}
        </p>
      )}
      <form onSubmit={save}>
        <div className="profile-fields">
          {profileFields.map(([key, label, type]) => (
            <label
              key={key}
              className={
                type === "skills" || type === "accomplishments" ? "wide" : ""
              }
            >
              {label}
              {type === "boolean" || type === "degree" ? (
                <select
                  value={draft[key] ?? ""}
                  onChange={(event) =>
                    setDraft({ ...draft, [key]: event.target.value })
                  }
                >
                  <option value="">Unknown</option>
                  {(type === "boolean"
                    ? [
                        ["true", "Yes"],
                        ["false", "No"],
                      ]
                    : [
                        ["high_school", "High school"],
                        ["bachelors", "Bachelor's"],
                        ["masters", "Master's"],
                        ["phd", "PhD"],
                      ]
                  ).map(([value, text]) => (
                    <option key={value} value={value}>
                      {text}
                    </option>
                  ))}
                </select>
              ) : type === "accomplishments" ? (
                <textarea
                  value={draft[key] ?? ""}
                  onChange={(event) =>
                    setDraft({ ...draft, [key]: event.target.value })
                  }
                  rows={3}
                />
              ) : (
                <input
                  type={type === "skills" ? "text" : type}
                  value={draft[key] ?? ""}
                  onChange={(event) =>
                    setDraft({ ...draft, [key]: event.target.value })
                  }
                  required={key === "name" || key === "email"}
                  min={type === "number" ? 0 : undefined}
                  step={type === "number" ? "any" : undefined}
                />
              )}
            </label>
          ))}
        </div>
        <details className="advanced">
          <summary>Explore the workflow</summary>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={missing}
              onChange={(event) => setMissing(event.target.checked)}
            />{" "}
            Try a missing work-authorization fact
          </label>
          <p>
            Your agents will ask for the missing fact, or reuse it if you
            supplied it earlier.
          </p>
        </details>
        <div className="dialog-footer">
          <span>
            <ShieldCheck size={15} />{" "}
            {realAccount
              ? "Saved privately to your account."
              : "Use fictional data in the sample workspace."}
          </span>
          <button className="primary" type="submit" disabled={saving}>
            Save profile <Check size={16} />
          </button>
        </div>
      </form>
    </dialog>
  );
}
