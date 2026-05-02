## Context

Crane already has a working capture endpoint (`POST /api/v1/incidents/capture`) and a per-user `APIToken` model. The web app's `/auth/account/` page exposes token generation. What's missing is the client surface volunteers actually live in — the page they're investigating. Today they leave the browser to log evidence, which compresses adoption and inflates per-incident effort.

Constraints:
- **Chrome MV3 only** for v1 (Firefox / Safari out of scope; will require porting if added later).
- **No npm runtime dependencies** in the shipped extension. Dev deps (build tooling, types) are fine.
- **No DRF on the backend.** The existing 1-endpoint API uses hand-rolled `JsonResponse` + a `token_required` decorator. New endpoints follow the same pattern — bringing DRF for 4 more endpoints adds a large dependency for no benefit at this scale.
- **No SPA framework in the side panel.** Three screens, a form, a list, a dropdown — vanilla DOM with a `render(state, root)` function is more readable than any framework's runtime.
- **No new models on the backend** (besides one column). Reuse `APIToken`, `Incident`, `Project`, `SearchSession`, `Platform`, `Language`, `KeywordCategory` as they exist.

Stakeholders:
- **Volunteers**: primary users; need fewer clicks to log evidence and less wasted effort on duplicates.
- **Coordinators**: benefit from higher capture volume and better coverage data (when v2 adds auto-session-logging).
- **Future maintainers / contributors**: the extension is a separate client codebase; it must be runnable end-to-end with `npm run dev` + Chrome's "Load unpacked" without learning Django internals.

## Goals / Non-Goals

**Goals:**

- One-click capture from any web page: open side panel → form pre-filled with current tab's URL + title + viewport screenshot → fill language + note → submit → `draft` Incident created in selected project.
- Passive duplicate detection: content script checks each new page's normalized URL against the user's accessible projects; renders an unobtrusive toast if a match exists.
- Active pre-flight duplicate check before capture: side panel calls `/api/v1/incidents/check` so the user is warned before submission.
- "Suggest next search" on demand: side panel button fetches top-3 stalest coverage cells for the active project; each suggestion is clickable and constructs a platform-specific search URL where possible (Telegram `t.me/s/?q=…`, generic Google `site:vk.com "term"`).
- Compile-time safety at the message-passing boundary: TypeScript strict mode, shared discriminated-union message types between background SW, side panel, and content script.
- Authentication onboarding under 60 seconds for a logged-in user: click Connect → `chrome.identity.launchWebAuthFlow` → land on `/auth/extension-link/` → instant redirect back with token → side panel shows project picker.

**Non-Goals:**

- **Firefox / Safari support.** Both require manifest variants, polyfills, and per-store distribution work. Future change.
- **Chrome Web Store publishing**, signed package distribution, or auto-update channel. v1 is "load unpacked from `dist/`".
- **Auto-detection of search activity** on platforms (e.g. parsing the user's typed query out of Telegram's search input). Suggestions are pull-only; the volunteer clicks "Get suggestions" themselves.
- **Auto-creation of `SearchSession` records** when a suggestion is clicked. The session is still logged manually via the web app. (Future v2 will close this loop.)
- **Full-page screenshot.** v1 captures the visible viewport via `chrome.tabs.captureVisibleTab`. Long-page captures require `chrome.scripting.executeScript` + scroll-and-stitch, which is fragile across sites.
- **Custom field editing** in the panel. The capture form has only core fields (URL, title, screenshot, language, note); `extra_fields` are filled via the existing web form (link returned in the capture response).
- **Offline queueing.** If the API is unreachable, the user sees an error and retries manually. No local IndexedDB queue.
- **Multi-token support** (different tokens for different uses). The existing one-to-one `APIToken` model is reused as-is; the extension shares the user's single token.
- **Per-project authentication scopes.** A token grants access to all projects the user is a member of. Project-level scoping is a future capability.

## Decisions

### 1. Repo location: `browser_extension/` at the monorepo root

**Decision:** The extension lives in a top-level `browser_extension/` directory inside the existing Django repo.

**Alternatives considered:**
- Separate Git repo (`crane-extension`): clean isolation but doubles the deploy/release coordination overhead and forces synchronizing API types via NPM publish or git submodule.
- Inside `apps/api/` or `apps/incidents/`: confuses Django's `INSTALLED_APPS` discovery (Django would try to import it) and pollutes Python tooling (pytest, ruff, mypy) with JS files.

**Rationale:** Monorepo with a top-level subdirectory is the lightest-weight setup that keeps the API contract co-evolvable. Django ignores the directory automatically (it's not in `INSTALLED_APPS`). The shared API types live in TypeScript; the Python side is documented through the OpenSpec capability spec.

### 2. Build pipeline: esbuild via plain `build.mjs` script (no Vite, no webpack)

**Decision:** A single `browser_extension/build.mjs` invokes the esbuild Node API directly. Three entry points: background service worker (ESM), side panel (ESM), content script (IIFE — MV3 forbids ES modules in content scripts). Output to `browser_extension/dist/`. `--watch` flag for dev. Build is sub-second cold.

**Alternatives considered:**
- **Vite**: excellent for SPA dev but its dev server doesn't apply cleanly to MV3 (no HMR for service workers, content scripts always need a page reload). The production build (`vite build`) works but is a bigger config surface for the same output.
- **Webpack**: works but is slow and config-heavy. Industry standard but overkill for 3 entry points and zero runtime deps.
- **Parcel**: zero-config is appealing, but its caching is opinionated and CSP-strict MV3 sometimes trips on its bundling tricks.
- **No build (raw JS in `chrome-extension://`)**: forfeits TypeScript and shared type files — chrome.* callback shapes become runtime bugs.

**Rationale:** esbuild is the smallest, fastest, most predictable tool that solves our exact problem (compile TS → JS, bundle three entry points, produce IIFE for one and ESM for two). One config file, one dependency, zero ongoing maintenance.

### 3. UI strategy in the side panel: vanilla DOM with `render(state, root)`

**Decision:** No framework. State is a single TypeScript object held in module scope; on every state change a top-level `render(state, root)` function diffs at the screen level (replaces `root.innerHTML` when `state.screen` changes) and does targeted updates within a screen (set `el.textContent`, toggle `hidden` attribute). Event listeners are attached once via delegation on `root`.

**Alternatives considered:**
- **Preact + signals** (~3 KB gz): more reactive, JSX is familiar, but adds a runtime + signals + JSX compilation step. Worth it for rich UIs; we have 3 screens and 5 interactive elements.
- **SolidJS**: smaller compiled output but unfamiliar mental model for a contributor coming from React.
- **Lit**: web components are clean but bring a base class and template tag overhead.
- **HTMX** (since it's already loaded by the main app): not designed to live inside a Chrome extension; needs an HTTP server to swap from, which the side panel doesn't have.

**Rationale:** The side panel is a small UI with a known maximum complexity. A `render()` function is the cheapest abstraction that gets the job done; we're trading a tiny amount of DOM verbosity for zero framework lock-in and zero bundle weight.

### 4. Authentication: `chrome.identity.launchWebAuthFlow`

**Decision:** Side panel calls `chrome.identity.launchWebAuthFlow` with `https://<crane-host>/auth/extension-link/?ext_id=<chrome.runtime.id>`. The Django view is `LoginRequiredMixin`; if the user isn't logged in, Django redirects them to `/auth/login/?next=...` and back. Once logged in, the view rotates the user's `APIToken` (or creates one if none exists) and HTTP-redirects to `https://<chrome.runtime.id>.chromiumapp.org/?token=<key>&email=<email>`. Chrome intercepts that URL (it's a magic redirect target tied to the extension ID), `launchWebAuthFlow` resolves with that URL, the side panel parses out token and email and stores them in `chrome.storage.local`.

**Alternatives considered:**
- **Manual paste of token**: 5+ steps, error-prone, alienates non-technical volunteers.
- **PostMessage from the auth-link page** to a content script that the background SW injected: works but requires explicit content script injection, browser tab management, and message routing. Three moving parts vs one for `launchWebAuthFlow`.
- **`chrome.runtime.onMessageExternal`** with the auth-link page calling `chrome.runtime.sendMessage(extId, ...)`: requires the manifest to declare `externally_connectable` with the crane host, which couples the manifest to the deployment URL (breaks dev with localhost).

**Rationale:** `launchWebAuthFlow` is the canonical Chrome auth pattern (used by every OAuth-style sign-in extension). It handles the popup window, intercepts the magic redirect URL, and does not require the manifest to know the production URL. The token lives only in the URL fragment that Chrome intercepts before navigation — not in browser history, not in DOM.

### 5. URL normalization: function in `apps/incidents/utils.py`, called in `Incident.save()`

**Decision:** `normalize_url(raw: str) -> str` lives in `apps/incidents/utils.py`. `Incident.save()` sets `self.url_normalized = normalize_url(self.url)` before calling `super().save()`. The existing duplicate-detection logic in `save()` is updated to query `Incident.objects.filter(project=..., url_normalized=...)` instead of the raw URL. The `IncidentCheckView` API endpoint normalizes incoming URLs before its lookup. A data migration backfills `url_normalized` for existing rows.

**Alternatives considered:**
- **`pre_save` signal in `apps/incidents/signals.py`**: works but adds an indirection (the field's value is no longer obvious from reading `models.py`). Signals are right when the field is computed from outside the model (e.g. by a cron task); for a value that's always derived from another field on the same row, the `save()` override is more discoverable.
- **Computed property** (no column): forces every duplicate query to recompute and prevents indexing. Defeats the purpose.
- **Trigger in PostgreSQL**: pure-DB, but invisible to Django ORM and breaks `manage.py makemigrations` discoverability.

**Rationale:** `save()` override colocates the computation with the field declaration. One file, one place to look.

### 6. CORS: `django-cors-headers` scoped to `/api/*` and `chrome-extension://*`

**Decision:** Install `django-cors-headers`. Add to `INSTALLED_APPS` and `MIDDLEWARE` (first, before `CommonMiddleware`). Set:
```
CORS_ALLOWED_ORIGIN_REGEXES = [r"^chrome-extension://.*$"]
CORS_URLS_REGEX = r"^/api/.*$"
CORS_ALLOW_HEADERS = [...defaults..., "authorization"]
```

**Alternatives considered:**
- **Hand-rolled middleware in `apps/api/cors.py`**: avoids the dep but has to handle preflight `OPTIONS`, the `Vary: Origin` response header, and `Access-Control-Allow-Credentials` interactions. Re-implementing those edge cases correctly is the same code as the library.
- **Permissive `CORS_ALLOW_ALL_ORIGINS = True`**: opens the API to every origin including malicious sites — the extension's bearer token would be at risk of XSS exfiltration.

**Rationale:** `django-cors-headers` is a single dependency (~200 LOC, MIT, maintained, broadly used) that handles preflight correctly. Scoping by both origin regex and URL regex keeps the policy tight.

### 7. Side panel persistence: `chrome.storage.local`, not `chrome.storage.sync`

**Decision:** Token, last-used project, base URL, and the duplicate-check cache live in `chrome.storage.local`.

**Alternatives considered:**
- **`chrome.storage.sync`**: 100 KB total quota, syncs across user's Chrome profiles. Token-syncing across browsers may be nice but is also a security expansion (token in Google's cloud).
- **`chrome.storage.session`**: cleared on browser close, would require re-auth every session. Hostile UX.

**Rationale:** `local` is per-install, persists across SW restarts, and stays out of cloud sync. Token re-auth happens only when the user uninstalls or revokes.

### 8. Duplicate-check cache: 5-minute TTL in `chrome.storage.local`

**Decision:** Background SW caches `{ url_normalized: { isDuplicate, ts } }` in `chrome.storage.local`. Entries expire after 5 minutes. Content script's passive check first reads the cache; on miss, sends a `CHECK_URL` message and the background fetches.

**Alternatives considered:**
- **No cache**: every page load triggers an API request. With SPA-routed sites (Twitter, LinkedIn) this can be 10+ requests per minute per tab.
- **In-memory cache only**: lost on SW termination (which Chrome does aggressively in MV3, often within 30s of inactivity).
- **Longer TTL**: false positives compound — a deleted incident still shows as duplicate.

**Rationale:** 5 minutes balances request volume against staleness. A volunteer who just captured a URL won't see "duplicate" appear for 5 min, but that's fine — they know they captured it.

### 9. Suggestion algorithm v1: stalest coverage cells

**Decision:** `GET /api/v1/coverage/suggest?project_id=X` returns the top-3 cells of the project's coverage matrix sorted by `(MAX(SearchSession.date) NULLS FIRST, COALESCE(MAX(date), '1970-01-01'))`. A cell is a `(Platform, Language, KeywordCategory)` triple defined by the project's configuration. Each result includes a constructed search URL when the platform has a `url_pattern` that suggests a search format (Telegram, Google site:VK, etc.); otherwise just a description.

**Alternatives considered:**
- **Effectiveness-weighted**: prefer cells whose past sessions yielded incidents with `confidence >= medium`. Better signal but requires Keyword–Session linkage that doesn't fully exist yet.
- **Volunteer-personalized**: prefer cells the volunteer has historically filled. Conservative, doesn't push them out of comfort zones.
- **ML-ranked**: out of scope.

**Rationale:** "Stalest cell" is the simplest objective signal that maps directly to "where coverage is weakest". It's also what the existing project-dashboard "coverage gaps" widget uses, so the UI is consistent across web and extension.

## Risks / Trade-offs

- **Risk: Chrome `chromiumapp.org` redirect URL breaks if Google deprecates `chrome.identity` API.** → **Mitigation:** the API is documented and stable for years; if deprecated, fall back to the postMessage approach (separate change, ~3h work).

- **Risk: `<all_urls>` host permission triggers a scary install warning** ("can read and change all your data on websites you visit"). → **Mitigation:** unavoidable for the passive duplicate-badge feature. Document clearly in the install flow.

- **Risk: SPA-routed pages (Twitter/X, LinkedIn) don't fire content-script reload on virtual navigation.** → **Mitigation:** content script listens for `chrome.runtime.onMessage` from the background SW which subscribes to `chrome.tabs.onUpdated` with `changeInfo.url` — fires on history-state pushes too. Re-checks on each detected URL change.

- **Risk: URL normalization rules drift between TypeScript (extension client-side optimistic check) and Python (authoritative server check).** → **Mitigation:** keep the TS version intentionally minimal — only strip the same canonical params, no other transformations. Add a comment in both files pointing at the counterpart. The Python normalizer is authoritative; the TS one is for optimistic UX only.

- **Risk: `launchWebAuthFlow` requires the redirect URL to be `https://<extension-id>.chromiumapp.org/...`. In dev with `http://localhost:8000`, the Django view must construct this correctly using `request.GET["ext_id"]`.** → **Mitigation:** the view validates that `ext_id` matches a known pattern (32-char alphanumeric Chrome extension ID) before constructing the redirect.

- **Risk: Single `APIToken` per user means revoking the token logs out both the API user and the extension.** → **Mitigation:** acceptable for v1. Multi-token support is a future capability with its own change.

- **Risk: Capture form's "language" dropdown needs the project's `Language` list, but the extension doesn't know the project until the user picks one.** → **Mitigation:** when the project is selected, the extension fetches `/api/v1/projects/<id>/languages` (a tiny extra endpoint) — or, simpler for v1, the extension asks the API to return the project's languages alongside the project list in `/api/v1/projects` (one extra field per project). Decided: include in `/api/v1/projects` response.

- **Trade-off: No automated UI tests for the extension.** Vitest + happy-dom would cover panel logic but not the chrome.* boundary; Playwright on a real Chrome with the extension loaded is the only realistic full-coverage test, and it's heavy. v1 relies on manual QA + backend tests for the API contract. A future change can add Vitest unit tests if the panel grows.

- **Trade-off: TypeScript adds ~1h setup vs raw JS, but eliminates a class of message-passing bugs.** This is the strongest argument for the extra tooling complexity; the chrome.* API surface is large and easy to misuse.

## Migration Plan

No data loss. Rollout is one PR landed in three sequential commits for ease of review:

1. **Backend first** (~5h): `normalize_url` utility + `url_normalized` column + migration with backfill. New API endpoints. CORS. `ExtensionLinkView`. Verify with `curl` smoke tests.

2. **Extension scaffold + auth** (~3h): `manifest.json`, `build.mjs`, `tsconfig.json`, shared types, background SW with the auth flow only. Side panel "Connect" screen. Manual end-to-end check: install → connect → token visible in `chrome://extensions` → `chrome.storage.local`.

3. **Capture + duplicate + suggest** (~11h): API client, screenshot, side panel capture form, content-script duplicate badge, suggest panel.

**Rollback:** revert the PR. The migration drops `url_normalized` cleanly. CORS settings are inert when no `chrome-extension://` origin requests come in.

## Open Questions

- **Should the auth-link page show the org/project list and let the user pick a default project?** v1 is "auth completes → side panel shows project dropdown empty until first selection". A pre-selection on the web side would shave a few seconds but adds a UI surface. **Decision: no for v1.** First-time users pick in the side panel; subsequent uses remember last selection.

- **Should the extension support multiple Crane instances** (e.g. dev local + prod)? **Decision: no.** Single base URL, configured during connect. Power users can re-connect to switch.

- **Should the extension include a Crane logo on the toolbar icon vs a generic camera/clip icon?** **Decision: Crane origami mark** (consistent with the brand work in `templates/icons/crane.html`). Render at 16/48/128 PNG.

- **Production publishing to Chrome Web Store** — out of scope for this change. Document the next change as `publish-extension-to-cws` covering: privacy policy, manifest hardening (`minimum_chrome_version`), promotional screenshots, listing copy, $5 dev fee.
