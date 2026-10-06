import { accessToken } from "./auth.js";
export async function api(path, body) {
  const token = await accessToken();
  const response = await fetch(path, {
    headers: {
      ...(token ? { Authorization: "Bearer " + token } : {}),
      ...(body === undefined ? {} : { "Content-Type": "application/json" }),
    },
    ...(body === undefined
      ? {}
      : {
          method: "POST",
          body: JSON.stringify(body),
        }),
    signal: AbortSignal.timeout(180000),
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401)
      window.dispatchEvent(new Event("applypilot:unauthorized"));
    const detail = data?.detail;
    throw new Error(
      typeof detail === "string"
        ? detail
        : detail
          ? JSON.stringify(detail)
          : "The service is unavailable. Please try again.",
    );
  }
  if (data === null)
    throw new Error("The service returned an unreadable response.");
  return data;
}

export async function imageBlob(path, signal) {
  const token = await accessToken();
  const response = await fetch(path, {
    headers: token ? { Authorization: "Bearer " + token } : {},
    signal,
  });
  if (!response.ok)
    throw new Error("Browser evidence is unavailable. Please try again.");
  return await response.blob();
}
