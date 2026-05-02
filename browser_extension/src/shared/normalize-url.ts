// Optimistic URL normalization for client-side duplicate hints.
//
// The authoritative implementation lives in the Python backend at
// `apps/incidents/utils.py::normalize_url`. This TypeScript version MUST
// produce the same output for the same input — keep the param sets and
// rules in sync. The server result is always trusted; this version only
// exists so the side panel can avoid an extra round-trip when the URL is
// obviously a duplicate.

const STRIP_EXACT = new Set([
  "fbclid",
  "gclid",
  "ref",
  "_ga",
  "igshid",
  "mc_eid",
  "msclkid",
  "yclid",
]);
const STRIP_PREFIX = ["utm_"];

function isTrackingParam(name: string): boolean {
  const lc = name.toLowerCase();
  if (STRIP_EXACT.has(lc)) return true;
  return STRIP_PREFIX.some((p) => lc.startsWith(p));
}

export function normalizeUrl(raw: string): string {
  if (!raw) return "";
  let parsed: URL;
  try {
    parsed = new URL(raw.trim());
  } catch {
    return "";
  }
  if (!parsed.host) return "";

  const host = parsed.host.toLowerCase();
  let path = parsed.pathname || "/";
  if (path.length > 1 && path.endsWith("/")) {
    path = path.replace(/\/+$/, "");
  }

  const kept: string[] = [];
  for (const [k, v] of parsed.searchParams.entries()) {
    if (!isTrackingParam(k)) {
      kept.push(`${encodeURIComponent(k)}=${encodeURIComponent(v)}`);
    }
  }
  const query = kept.length > 0 ? `?${kept.join("&")}` : "";
  return `${parsed.protocol.toLowerCase()}//${host}${path}${query}`;
}
