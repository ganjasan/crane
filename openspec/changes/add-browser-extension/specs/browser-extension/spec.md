## ADDED Requirements

### Requirement: One-click incident capture from any web page
The extension SHALL provide a side-panel surface that, when opened on any web page, pre-fills a capture form with the active tab's URL, page title, and a viewport screenshot. The volunteer SHALL be able to add a language (selected from the active project's configured languages) and a free-text note, then submit the form to create a `draft` Incident in the selected project.

#### Scenario: Volunteer captures a Telegram post
- **WHEN** a volunteer is viewing a Telegram channel post and opens the Crane side panel
- **THEN** the form is pre-filled with the post's URL, the channel/post title, and a screenshot of the visible viewport; after the volunteer picks a language and submits, the side panel shows a confirmation with the newly-created `record_id` and a link to open the full incident form in the Crane web app

#### Scenario: Capture without a screenshot
- **WHEN** a volunteer dismisses the auto-captured screenshot before submission
- **THEN** the form submits successfully without a screenshot, and the resulting Incident has no `screenshot` field set

### Requirement: Project context selector in the side panel
The side panel SHALL display a dropdown listing every project the authenticated user is a member of. Submitting the capture form sends the Incident to the currently selected project. The selection SHALL persist across browser sessions in `chrome.storage.local` so volunteers in a single project never need to re-pick.

#### Scenario: Single-project user
- **WHEN** a volunteer who is a member of exactly one project opens the panel for the first time
- **THEN** that project is pre-selected automatically and the dropdown shows a single non-toggleable option

#### Scenario: Multi-project user remembers last selection
- **WHEN** a volunteer member of three projects picks "Bird Trade Central Asia", captures an incident, closes the browser, and reopens the panel later
- **THEN** "Bird Trade Central Asia" is still selected

### Requirement: Active duplicate check before submit
Before posting a capture, the side panel SHALL call the duplicate-check API with the page URL. If a duplicate is found in the selected project, the panel SHALL show a clear warning identifying the existing `record_id`, the user who captured it, and the date — and SHALL offer three options: open the existing incident in a new tab, submit anyway, or cancel.

#### Scenario: Duplicate detected at submit time
- **WHEN** the volunteer clicks Submit and the URL (after normalization) matches an existing Incident in the selected project
- **THEN** the panel displays "Already captured as REC-014 by volunteer1@crane.local on Apr 15" with three buttons (Open / Submit anyway / Cancel) and does NOT post the capture until the volunteer chooses

#### Scenario: No duplicate
- **WHEN** the volunteer submits a URL with no normalized match in the selected project
- **THEN** the capture is posted immediately with no warning interstitial

### Requirement: Passive duplicate badge on browsed pages
A content script SHALL run on every page the user visits. On page load and on URL changes within single-page applications, it SHALL check the current URL against the duplicate-check API (using the user's accessible projects) and, if a match exists, render a small unobtrusive toast/badge in the page's viewport identifying the existing `record_id` and the date it was captured. The badge SHALL be dismissable.

#### Scenario: User browses to a previously-captured URL
- **WHEN** a volunteer navigates to a Telegram post that another team member already logged as REC-007 three days ago
- **THEN** within ~2 seconds of page load, a small badge appears in a corner of the page reading "Already in Crane · REC-007 · 3 days ago" with a close button

#### Scenario: SPA route change
- **WHEN** a volunteer browsing Twitter clicks from one tweet to another (URL changes via `history.pushState` without a page reload)
- **THEN** the badge re-evaluates against the new URL and either appears, updates, or hides accordingly

#### Scenario: Cache hit avoids network
- **WHEN** the same URL was checked within the last 5 minutes
- **THEN** the result is returned from the extension's local cache and no API request is made

### Requirement: Toolbar icon badge as global status indicator
The Chrome toolbar icon SHALL show a colored dot/badge reflecting current status: grey when not connected, green when connected and the current page has no duplicate, amber when the current page is a duplicate, red on auth or network error.

#### Scenario: Volunteer not connected
- **WHEN** the extension is installed but the user has not completed the connect flow
- **THEN** the toolbar icon shows a grey badge

#### Scenario: Active duplicate page
- **WHEN** the user is browsing a page whose URL matches an existing Incident
- **THEN** the toolbar icon shows an amber badge

### Requirement: On-demand suggestion of next coverage gaps
The side panel SHALL include a "Suggest next searches" button. Clicking it queries the suggestion API and displays the top-3 stalest coverage cells (platform × language × keyword category) for the active project. Each suggestion is clickable: where the platform supports a constructable search URL, the click opens that search in a new tab; otherwise the suggestion is shown as a description (e.g. "Search VK for Uzbek wildlife terms — 47 days since last session").

#### Scenario: Suggestions list refreshes
- **WHEN** the volunteer clicks "Suggest next searches"
- **THEN** the panel shows three rows ranked by oldest `MAX(SearchSession.date)`, each row containing the cell (platform, language, category) and either a constructed search URL or a free-text instruction

#### Scenario: Click suggestion with platform-search support
- **WHEN** a Telegram suggestion is clicked
- **THEN** a new tab opens at `https://t.me/s/?q=<example-keyword-from-category>` constructed from one active keyword in that category

### Requirement: Guided authentication onboarding
On first open, the side panel SHALL display a single "Connect to Crane" button. Clicking it SHALL open a Crane web page that authenticates the user (redirecting to login if needed), generates or rotates an `APIToken`, and returns the token to the extension via Chrome's `chrome.identity.launchWebAuthFlow` redirect-URL mechanism. After completion, the side panel SHALL transition to the project picker without any manual token paste step.

#### Scenario: Logged-in user connects in one click
- **WHEN** a user already authenticated to crane.app in their browser clicks "Connect to Crane"
- **THEN** a popup window briefly appears, the auth-link page processes the request, the popup closes, and the side panel within 3 seconds shows the project picker dropdown

#### Scenario: Unauthenticated user is redirected to login
- **WHEN** a user not currently logged into crane.app clicks "Connect to Crane"
- **THEN** the popup shows the Crane login page; after the user submits credentials, the auth-link flow completes and the side panel shows the project picker

#### Scenario: Re-connecting rotates the token
- **WHEN** a user disconnects and clicks "Connect to Crane" a second time
- **THEN** a new `APIToken` is generated server-side, the old token is invalidated, and the side panel reflects the new auth state

### Requirement: Extension is self-contained and loads without network dependencies at runtime
The shipped extension bundle SHALL contain no runtime npm dependencies. All third-party libraries used during development (TypeScript compiler, esbuild, type definitions) SHALL be `devDependencies` only. The extension SHALL function fully offline once the user is authenticated, with the exception of API calls to the configured Crane base URL.

#### Scenario: Audit of dependencies
- **WHEN** a contributor inspects `browser_extension/package.json`
- **THEN** the `dependencies` field is empty (or absent); only `devDependencies` are present

#### Scenario: Dist bundle has no external script tags
- **WHEN** the production build is inspected
- **THEN** `dist/` contains only the bundled JS, manifest, icons, and HTML — no references to CDN URLs or external script sources
