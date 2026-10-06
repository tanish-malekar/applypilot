import { statusNames, pretty } from "../lib/ui.js";

export default function Badge({ status = "ready", children }) {
  return (
    <span className={"status " + status}>
      <i />
      {children || statusNames[status] || pretty(status)}
    </span>
  );
}
