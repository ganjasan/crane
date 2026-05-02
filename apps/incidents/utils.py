"""URL utilities for Incident deduplication.

`normalize_url` is the canonical normalization used by `Incident.save()` and
the `/api/v1/incidents/check` endpoint. The browser extension MUST mirror
this logic in TypeScript (`browser_extension/src/shared/normalize-url.ts`)
so the optimistic client-side check matches the authoritative server-side
result. The Python implementation here is the source of truth.
"""
from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

# Tracking-only query parameters stripped during normalization.
# Lowercase comparison is applied; prefix matches handled separately.
_STRIP_PARAMS_EXACT = frozenset({
    "fbclid",
    "gclid",
    "ref",
    "_ga",
    "igshid",
    "mc_eid",
    "msclkid",
    "yclid",
})
_STRIP_PARAMS_PREFIX = ("utm_",)


def _is_tracking_param(name: str) -> bool:
    name_lc = name.lower()
    if name_lc in _STRIP_PARAMS_EXACT:
        return True
    return any(name_lc.startswith(p) for p in _STRIP_PARAMS_PREFIX)


def normalize_url(raw: str) -> str:
    """Return a canonical form of `raw` suitable for duplicate matching.

    Returns empty string if `raw` is empty or unparseable.
    """
    if not raw:
        return ""

    try:
        parts = urlsplit(raw.strip())
    except ValueError:
        return ""

    if not parts.netloc:
        return ""

    host = parts.netloc.lower()
    path = parts.path
    if path.endswith("/") and path != "/":
        path = path.rstrip("/")

    kept = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not _is_tracking_param(k)]
    query = urlencode(kept) if kept else ""

    return urlunsplit((parts.scheme.lower(), host, path, query, ""))
