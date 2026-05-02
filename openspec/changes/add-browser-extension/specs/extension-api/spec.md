## ADDED Requirements

### Requirement: URL normalization on Incident
Every `Incident` SHALL have a `url_normalized` column populated automatically from `url` on every save. Normalization SHALL: parse the URL, lowercase the hostname, remove tracking query parameters (`utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term`, `fbclid`, `gclid`, `ref`, `_ga`, `igshid`, `mc_eid`), strip a trailing slash from the path (except when the path is `/`), and reassemble the URL. The duplicate-detection logic in `Incident.save()` SHALL match against `url_normalized`, not the raw `url`. A data migration SHALL backfill `url_normalized` for all existing rows.

#### Scenario: Tracking parameters are stripped
- **WHEN** an Incident is saved with `url = "https://t.me/channel/123?utm_source=newsletter&utm_campaign=may2026"`
- **THEN** `url_normalized` is `"https://t.me/channel/123"`

#### Scenario: Trailing slash is normalized
- **WHEN** an Incident is saved with `url = "https://vk.com/wall12345_678/"`
- **THEN** `url_normalized` is `"https://vk.com/wall12345_678"` (no trailing slash)

#### Scenario: Hostname case is normalized
- **WHEN** an Incident is saved with `url = "https://VK.COM/wall12345"`
- **THEN** `url_normalized` is `"https://vk.com/wall12345"`

#### Scenario: Duplicate detection uses normalized URL
- **WHEN** an Incident is saved with `url = "https://t.me/channel/123?fbclid=abc"` in a project that already contains `url = "https://t.me/channel/123?utm_source=x"`
- **THEN** the new Incident's `duplicate_of` field is set to the existing one (both normalize to the same `url_normalized`)

### Requirement: POST /api/v1/incidents/check
The system SHALL provide an API endpoint that accepts a Bearer-token-authenticated POST with a JSON body containing a list of URLs and a project identifier, and returns whether each URL (after normalization) matches an existing Incident in that project.

#### Scenario: Successful batch check
- **WHEN** a request is sent with `{ "urls": ["https://t.me/channel/123?utm_source=x", "https://vk.com/wall1_2"], "project_id": "<uuid>" }` and a valid Bearer token belonging to a member of that project
- **THEN** the response is HTTP 200 with body `{ "results": { "https://t.me/channel/123?utm_source=x": { "duplicate": true, "record_id": "REC-014" }, "https://vk.com/wall1_2": { "duplicate": false, "record_id": null } } }`

#### Scenario: Missing or invalid token
- **WHEN** a request is sent without an `Authorization: Bearer <token>` header
- **THEN** the response is HTTP 401 with `{ "error": "Missing or invalid Authorization header" }`

#### Scenario: Token belongs to a non-member
- **WHEN** the token's user is not a member of the requested project
- **THEN** the response is HTTP 403 with an error message; no incidents are leaked

### Requirement: GET /api/v1/projects
The system SHALL provide an API endpoint that returns the authenticated user's accessible projects, including each project's organization slug and configured language list. This endpoint powers the side panel's project selector and the in-form language dropdown.

#### Scenario: Returns user's projects
- **WHEN** a request is sent with a valid Bearer token for a user who is a member of two projects across one organization
- **THEN** the response is HTTP 200 with `{ "projects": [{ "id": "<uuid>", "name": "Bird Trade CA", "slug": "bird-trade-central-asia", "org_name": "ICF", "org_slug": "icf", "languages": [{"code":"ru","name":"Russian"}, ...] }, ...] }`

#### Scenario: User with no projects
- **WHEN** the user belongs to an organization but no projects within it
- **THEN** the response is HTTP 200 with `{ "projects": [] }`

### Requirement: GET /api/v1/coverage/suggest
The system SHALL provide an API endpoint that returns the top-3 stalest coverage cells for a given project, ranked by the oldest `MAX(SearchSession.date)` per `(Platform, Language, KeywordCategory)` triple. Cells with no recorded session SHALL be ranked first.

#### Scenario: Stalest cells returned first
- **WHEN** a project has 9 valid (Platform, Language, Category) cells, three of which have never been searched and the others have varying last-session dates
- **THEN** the response returns the three never-searched cells first

#### Scenario: Each suggestion includes a search URL when constructable
- **WHEN** the suggestion involves a Platform whose `url_pattern` includes a search-query placeholder
- **THEN** the response includes a `search_url` field with a constructed URL using one active keyword from the suggested category; otherwise `search_url` is `null` and a `description` field is provided

#### Scenario: Authentication and membership checks
- **WHEN** the request lacks a valid Bearer token, or the token's user is not a member of the requested project
- **THEN** the response is HTTP 401 or 403 respectively

### Requirement: Extension authentication link page
The system SHALL provide a `/auth/extension-link/` page that requires login, accepts an `ext_id` query parameter (validated as a 32-char alphanumeric Chrome extension ID), generates or rotates the user's `APIToken`, and HTTP-redirects to `https://<ext_id>.chromiumapp.org/?token=<key>&email=<user-email>`. This URL is intercepted by Chrome's `chrome.identity.launchWebAuthFlow` so the token never appears in the browser address bar or history.

#### Scenario: Authenticated user completes the link flow
- **WHEN** a logged-in user navigates to `/auth/extension-link/?ext_id=abcdefghijklmnop` (32 valid chars)
- **THEN** an `APIToken` is created or rotated for the user, and the response is a 302 redirect to `https://abcdefghijklmnop.chromiumapp.org/?token=<the-token>&email=<the-email>`

#### Scenario: Unauthenticated user is sent to login
- **WHEN** a user not logged in navigates to `/auth/extension-link/?ext_id=...`
- **THEN** Django's `LoginRequiredMixin` redirects them to `/auth/login/?next=/auth/extension-link/?ext_id=...`; after login they are returned to the link flow

#### Scenario: Invalid ext_id is rejected
- **WHEN** a request includes `ext_id=<not-a-valid-extension-id>` (e.g. wrong length, wrong characters)
- **THEN** the response is HTTP 400 with an error message and no token is generated

### Requirement: CORS configured for chrome-extension origin scoped to /api/
The backend SHALL allow cross-origin requests from any `chrome-extension://*` origin, but only for paths under `/api/`. The web app's other paths SHALL NOT receive CORS allowance headers. The CORS configuration SHALL accept the `Authorization` header in addition to defaults so Bearer-token requests succeed.

#### Scenario: Extension API request succeeds with CORS
- **WHEN** an extension at `chrome-extension://abcdef.../` sends `OPTIONS /api/v1/incidents/check` with `Origin: chrome-extension://abcdef...`
- **THEN** the preflight response includes `Access-Control-Allow-Origin: chrome-extension://abcdef...` and `Access-Control-Allow-Headers` includes `authorization`

#### Scenario: Non-API path does not get CORS
- **WHEN** the same extension sends `OPTIONS /icf/` (an app page)
- **THEN** the response does NOT include `Access-Control-Allow-Origin`, blocking cross-origin reads

### Requirement: Auth and bearer-token semantics unchanged
The extension SHALL authenticate API calls via the existing `Authorization: Bearer <token>` header and the existing one-to-one `APIToken` model. No new user-facing token-management surface is introduced for v1; users manage their token via `/auth/account/` or implicitly via the connect flow (which rotates).

#### Scenario: Same token works for web and extension
- **WHEN** a user generates an APIToken via the existing `/auth/account/` page and pastes it into a script that POSTs to `/api/v1/incidents/capture`
- **THEN** the request succeeds (the extension does not change the authentication contract)

#### Scenario: Reconnecting via extension invalidates previous token
- **WHEN** a user with an existing APIToken completes the extension connect flow again
- **THEN** the previous token's `key` is rotated; subsequent requests using the old key return HTTP 401
