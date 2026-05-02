## 1. Backend: URL normalization

- [x] 1.1 Create `apps/incidents/utils.py` with `normalize_url(raw: str) -> str` (lowercase host, strip `utm_*`/`fbclid`/`gclid`/`ref`/`_ga`/`igshid`/`mc_eid`, strip trailing slash except `/`)
- [x] 1.2 Add `url_normalized = CharField(max_length=2048, blank=True, db_index=True)` to `Incident`
- [x] 1.3 Update `Incident.save()` to compute `self.url_normalized = normalize_url(self.url)` before super().save(), and update duplicate-detection query to filter on `url_normalized`
- [x] 1.4 Generate migration `apps/incidents/migrations/000X_incident_url_normalized.py` with `AddField` + `RunPython` backfill
- [x] 1.5 Write `apps/incidents/tests/test_url_utils.py` covering: utm strip, fbclid strip, lowercase host, trailing slash, bare `/` preserved, empty input
- [x] 1.6 Apply migration locally; verify backfill ran

## 2. Backend: CORS

- [x] 2.1 Add `django-cors-headers==4.3.1` (or current latest) to `requirements.txt`; install
- [x] 2.2 Add `corsheaders` to `INSTALLED_APPS` and `corsheaders.middleware.CorsMiddleware` as the first middleware in `crane/settings.py`
- [x] 2.3 Configure: `CORS_ALLOWED_ORIGIN_REGEXES = [r"^chrome-extension://.*$"]`, `CORS_URLS_REGEX = r"^/api/.*$"`, extend `CORS_ALLOW_HEADERS` with `authorization`
- [x] 2.4 Smoke-test from a dummy `chrome-extension://` Origin via curl `-H "Origin: chrome-extension://abc"` to `/api/v1/incidents/capture` OPTIONS

## 3. Backend: New API endpoints

- [x] 3.1 Add `IncidentCheckView` (POST) to `apps/api/views.py`: parse JSON body `{urls, project_id}`, verify membership, normalize each URL, batch query, return `{results: {url: {duplicate, record_id}}}`
- [x] 3.2 Add `ProjectListView` (GET) to `apps/api/views.py`: return `{projects: [{id, name, slug, org_name, org_slug, languages: [{code,name}]}]}` for `request.user`
- [x] 3.3 Add `CoverageSuggestView` (GET) to `apps/api/views.py`: query top-3 stalest `(Platform, Language, KeywordCategory)` cells, construct `search_url` when `Platform.url_pattern` permits, otherwise return `description`
- [x] 3.4 Register routes in `apps/api/urls.py`: `v1/incidents/check`, `v1/projects`, `v1/coverage/suggest`
- [x] 3.5 Write tests `apps/api/tests/test_check.py`, `test_projects.py`, `test_suggest.py` covering happy path, unauthenticated, non-member, empty results — GIVEN/WHEN/THEN docstrings

## 4. Backend: Extension auth-link page

- [x] 4.1 Add `ExtensionLinkView` to `apps/core/views.py`: extends `LoginRequiredMixin`, validates `ext_id` query param against regex `^[a-p]{32}$`, rotates user's `APIToken`, redirects to `https://{ext_id}.chromiumapp.org/?token={key}&email={email}`
- [x] 4.2 Wire `path("auth/extension-link/", ExtensionLinkView.as_view(), name="extension_link")` in `apps/core/urls.py`
- [x] 4.3 Verify exempt from `OrgProjectMiddleware` (path starts with `/auth/`)
- [x] 4.4 Write `apps/core/tests/test_extension_link.py`: authenticated → redirect; unauthenticated → login redirect; invalid ext_id → HTTP 400; existing token rotation

## 5. Extension scaffold

- [x] 5.1 Create `browser_extension/` directory with `manifest.json` (MV3, permissions: `sidePanel`, `storage`, `activeTab`, `tabs`, `scripting`, `identity`; host_permissions `<all_urls>`; service_worker `dist/background.js`; side_panel default_path `dist/sidepanel.html`; content_scripts on `<all_urls>` running `dist/content.js`)
- [x] 5.2 Create `browser_extension/package.json` with `devDependencies` only: `esbuild`, `@types/chrome`, `typescript`
- [x] 5.3 Create `browser_extension/tsconfig.json` with `strict`, `target: ES2022`, `moduleResolution: bundler`, `paths: {"@shared/*": ["src/shared/*"]}`
- [x] 5.4 Create `browser_extension/build.mjs`: esbuild API call with three entry points (`src/background/sw.ts`, `src/sidepanel/index.ts`, `src/content/index.ts`), output `dist/`, supports `--watch`
- [x] 5.5 Create `browser_extension/icons/` with 16/48/128 PNG of the Crane origami mark
- [x] 5.6 Create `browser_extension/.gitignore` for `dist/`, `node_modules/`
- [x] 5.7 Add `npm run build` and `npm run dev` scripts; verify cold build under 1s

## 6. Extension shared modules

- [x] 6.1 Create `src/shared/types.ts`: discriminated-union message types (`CaptureRequest/Response`, `CheckUrlRequest/Response`, `SuggestRequest/Response`, `GetStateRequest/Response`, `AuthUpdate`, `AuthClear`); API DTOs (`ProjectSummary`, `LanguageSummary`, `SuggestItem`)
- [x] 6.2 Create `src/shared/normalize-url.ts`: TS mirror of Python `normalize_url` with comment pointing at counterpart
- [x] 6.3 Create `src/shared/storage.ts`: typed wrappers for `chrome.storage.local` (keys `craneToken`, `craneBaseUrl`, `craneUserEmail`, `craneLastProjectId`, `craneUrlCache`)
- [x] 6.4 Create `src/shared/api-client.ts`: `ApiClient` class with `checkDuplicate`, `capture`, `getProjects`, `getSuggestions`; reads token from storage on each call; throws typed errors on 401/4xx/5xx

## 7. Extension background service worker

- [x] 7.1 Create `src/background/sw.ts`: register `chrome.runtime.onMessage` dispatch table mapping each message `type` to a handler
- [x] 7.2 Implement `handleCapture`: convert dataURL screenshot → Blob → FormData → ApiClient.capture
- [x] 7.3 Implement `handleCheckUrl` with 5-min `chrome.storage.local` cache; on cache miss call ApiClient
- [x] 7.4 Implement `handleGetSuggestions` (passthrough to ApiClient)
- [x] 7.5 Implement `handleGetProjects` (passthrough)
- [x] 7.6 Implement auth handler: invoke `chrome.identity.launchWebAuthFlow` with `https://<base>/auth/extension-link/?ext_id=<chrome.runtime.id>`; parse `token` and `email` from redirect URL; persist to storage; broadcast `AuthUpdate` to side panel
- [x] 7.7 Subscribe to `chrome.tabs.onUpdated` (status=`complete` OR url change); on URL change in active tab → message active content script with new URL; update toolbar icon badge color/text

## 8. Extension side panel

- [x] 8.1 Create `src/sidepanel/index.html`: minimal shell with `<div id="root">` and `<script src="sidepanel.js" type="module">`
- [x] 8.2 Create `src/sidepanel/index.ts`: holds module-scope `state` object, exports `setState(partial)` that triggers `render(state, root)`
- [x] 8.3 Create `src/sidepanel/render.ts` with three screen renderers: `renderConnect`, `renderCapture`, `renderSuggest`; top-level `render` switches by `state.screen`
- [x] 8.4 Create `src/sidepanel/styles.css`: ~50 lines, mirror crane palette tokens (slate-900 sidebar accents, slate-50 surface, indigo primary inverse), no Tailwind dep
- [x] 8.5 Wire `Connect` button → send `INITIATE_AUTH` message; on `AuthUpdate` from background → fetch projects → switch screen to `capture`
- [x] 8.6 Wire capture form: project dropdown (populated from `getProjects`), language dropdown (populated from selected project's `languages`), note textarea, screenshot preview, submit button → send `CaptureRequest`; on response show success card with `formUrl` link
- [x] 8.7 Wire `Suggest next searches` button → send `GetSuggestions` → render list of 3 items with click → `chrome.tabs.create({url: search_url})`
- [x] 8.8 Wire pre-flight duplicate check: on submit click → send `CheckUrl` first; if duplicate → show warning UI with three buttons (Open / Submit anyway / Cancel) before calling capture

## 9. Extension content script

- [x] 9.1 Create `src/content/index.ts`: on injection, send `CheckUrl` message with `window.location.href`
- [x] 9.2 If response has `duplicate: true`, inject a fixed-position toast `<div>` into `document.body` (inline styles, max-z-index, dismissable close button) with text "Already in Crane · {record_id} · {date}"
- [x] 9.3 Listen for messages from background SW (`PAGE_URL_CHANGED` from SPA route changes) and re-evaluate
- [x] 9.4 Auto-dismiss toast after 8 seconds OR persist until close — decide based on UX feel during manual testing

## 10. Toolbar icon badge

- [x] 10.1 In background SW, update `chrome.action.setBadgeText` and `chrome.action.setBadgeBackgroundColor` based on auth state and last duplicate-check result for the active tab
- [x] 10.2 States: grey (not connected) — no badge text, default icon; green (connected, current page fresh) — empty badge with green color; amber (current page is duplicate) — badge text "!" with amber color; red (auth or network error) — badge text "!" with red color

## 11. Manual end-to-end test

- [x] 11.1 `npm run build` in `browser_extension/`; load `dist/` as unpacked extension in Chrome
- [ ] 11.2 With `./run_dev.sh` running, override `craneBaseUrl` to `http://localhost:8000` via `chrome.storage.local.set` in extension devtools
- [ ] 11.3 Click extension icon → side panel opens → click Connect → log in as `coordinator@crane.local` / `coordinator` → verify token stored, project picker appears
- [ ] 11.4 Navigate to a Telegram public channel post; capture incident; verify it appears in `/icf/bird-trade-central-asia/incidents/`
- [ ] 11.5 Re-visit same URL; verify content-script badge appears within 2s and toolbar icon shows amber
- [ ] 11.6 Click "Suggest next searches"; verify 3 cells returned, one click opens platform search

## 12. Documentation and verification

- [x] 12.1 Update `CLAUDE.md`: add browser_extension section (build commands, dev workflow, manifest overview, message protocol pointer)
- [x] 12.2 Add `browser_extension/README.md` with install instructions for both dev (Load unpacked) and contributor onboarding
- [x] 12.3 Run `openspec validate add-browser-extension` and resolve any warnings
- [x] 12.4 Open PR with screenshots: side panel three screens, content-script toast, capture round-trip
