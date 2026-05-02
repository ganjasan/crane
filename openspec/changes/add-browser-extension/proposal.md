## Why

Volunteers monitoring social platforms for bird-trade evidence currently leave the browser, log into the Crane web app, and recreate URL + screenshot + metadata by hand for every find. This is the dominant friction point in the search loop — a 30-second manual paste per incident across hundreds of finds per week. We need to compress capture to one click on the page where the evidence lives.

A browser extension also unlocks two compounding capabilities the web app cannot offer: a passive "this page is already in the database" badge that prevents duplicate work across the team, and an in-context "next coverage gap to search" suggester that closes the search-coverage loop without context-switching. Both feed directly into the project's two stated goals — maximize signal volume and grow a dictionary that becomes searchable programmatically over time.

## What Changes

- **New deliverable: Chrome MV3 browser extension** at `browser_extension/` (TypeScript + esbuild, no UI framework). Three surfaces:
  - Side panel (Chrome 114+) for capture form, project picker, suggestion list
  - Content script that injects a small "already captured" toast when the current URL is in the database
  - Toolbar icon badge as global status indicator (green = fresh, amber = duplicate, grey = not connected)
- **New auth flow**: extension uses `chrome.identity.launchWebAuthFlow` to open `/auth/extension-link/?ext_id=<chrome.runtime.id>`; the page (login-required) generates or rotates an `APIToken` and redirects to the canonical Chromium auth-redirect URL with the token in the query string.
- **Four new backend API endpoints** under `/api/v1/`:
  - `POST /incidents/check` — accepts `{ urls: [...], project_id }`, returns per-URL duplicate status (matched on `url_normalized`)
  - `GET /projects` — returns the authenticated user's accessible projects for the panel's dropdown
  - `GET /coverage/suggest?project_id=...` — top-3 stalest coverage cells (platform × language × keyword category)
  - The existing `POST /incidents/capture` is reused unchanged
- **URL normalization on Incident**: new `Incident.url_normalized` column (db_indexed), populated in `Incident.save()` via a `normalize_url()` utility that strips tracking params (`utm_*`, `fbclid`, `gclid`, `ref`, `_ga`, `igshid`, `mc_eid`), lowercases host, and removes trailing slash. Existing rows are backfilled by data migration. The existing exact-URL duplicate detection in `save()` is updated to compare `url_normalized` instead.
- **CORS** for `chrome-extension://*` origin scoped to `/api/*` paths via `django-cors-headers`.
- **Reuse of the existing `APIToken` model** — no new fields. The `ext_id` lives only in the auth-link query string for binding the redirect to a specific extension install; it is not persisted server-side.

## Capabilities

### New Capabilities

- `browser-extension`: The Chrome MV3 extension itself — its three UI surfaces (side panel, content script, icon badge), auth onboarding, and the user-visible behaviors of capture / suggest / duplicate-warning.

- `extension-api`: The backend HTTP contract that the extension speaks — auth-link page, four `/api/v1/` endpoints, CORS policy for the `chrome-extension://` origin, URL normalization semantics, and authentication model.

### Modified Capabilities

(none — `web-ui-shell` and `ui-design-system` are untouched; the extension is a separate client.)

## Impact

- **New code**:
  - `browser_extension/` — entire subtree (TypeScript sources, manifest, esbuild config, tsconfig, package.json with dev-only deps)
  - `apps/incidents/utils.py` — `normalize_url()`
  - `apps/incidents/migrations/000X_incident_url_normalized.py`
  - `apps/api/views.py` — 3 new view classes
  - `apps/api/urls.py` — 3 new routes
  - `apps/core/views.py` — `ExtensionLinkView`
  - `apps/core/urls.py` — `auth/extension-link/` route
- **Modified code**:
  - `apps/incidents/models.py` — `url_normalized` column, save() update
  - `crane/settings.py` — `corsheaders` app + middleware + scoped CORS settings
  - `requirements.txt` — `django-cors-headers`
- **New runtime dependencies (Python)**: `django-cors-headers` (one entry, MIT-licensed, ~200 LOC)
- **New dev dependencies (JS)**: `esbuild`, `@types/chrome` — both devDependencies, no runtime npm packages in the shipped extension
- **Distribution**: extension is loaded unpacked from `browser_extension/dist/` in dev; production publishing to Chrome Web Store is out of scope for this change (a future change will handle CWS submission, manifest hardening, and store listing)
- **Users**: volunteers install the extension once, connect once via the auth-link flow, then capture incidents from any page. No change to existing web-app workflows.
- **No data migration risk**: `url_normalized` backfill is idempotent and runs in a transaction; reverting the migration drops only the new column.
