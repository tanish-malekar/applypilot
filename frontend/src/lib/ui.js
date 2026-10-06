export const statusNames = {
  awaiting_review: "Ready for review",
  submitted: "Submitted",
  rejected: "Rejected",
  ineligible: "Not eligible",
  awaiting_information: "Needs your input",
  awaiting_facts: "Needs your input",
  verification_failed: "Verification failed",
  needs_information: "Needs your input",
  failed: "Needs attention",
  blocked: "Blocked",
};
export const pretty = (value = "") => value.replaceAll("_", " ");
export const initials = (name = "") =>
  name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase() || "AP";
export const profileFields = [
  ["name", "Full name", "text"],
  ["email", "Email", "email"],
  ["degree", "Degree", "degree"],
  ["graduation_date", "Graduation date", "date"],
  ["experience_years", "Years of experience", "number"],
  ["location", "Location", "text"],
  ["work_authorized", "Authorized to work", "boolean"],
  ["needs_sponsorship", "Needs sponsorship", "boolean"],
  ["has_clearance", "Has security clearance", "boolean"],
  ["skills", "Skills · separated by commas", "skills"],
  ["accomplishments", "Accomplishments · one per line", "accomplishments"],
];
