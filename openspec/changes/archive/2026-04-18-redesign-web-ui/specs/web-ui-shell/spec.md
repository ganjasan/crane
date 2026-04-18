## ADDED Requirements

### Requirement: Three-tier application shell
The system SHALL provide three distinct application shells — `base_app` for authenticated in-app pages (with sidebar), `base_auth` for login/register/invitation flows (split-screen, no sidebar), and `base_minimal` for pages that need authentication but no sidebar (org selector, org create). All three SHALL extend a single root `base.html` that owns global `<head>` assets (CSS, fonts, HTMX, Alpine, CSRF).

#### Scenario: In-app page renders with sidebar shell
- **WHEN** an authenticated user navigates to an org or project page (e.g. `/acme/`, `/acme/bird-trade/incidents/`)
- **THEN** the page is rendered inside `base_app.html` with the dark sidebar on the left and the page content in a scrollable main area on the right

#### Scenario: Auth page renders without sidebar
- **WHEN** an unauthenticated user navigates to `/auth/login/` or `/auth/register/`
- **THEN** the page is rendered inside `base_auth.html` showing a split-screen layout with a brand panel on one side and the form card on the other, with no sidebar or in-app navigation

#### Scenario: Org selector renders in minimal shell
- **WHEN** an authenticated user navigates to `/` (the org selector)
- **THEN** the page is rendered inside `base_minimal.html` with a narrow centered column, topbar containing the logo and user menu, and no sidebar

### Requirement: Two-level sidebar navigation
The sidebar SHALL display a context-appropriate set of navigation items. When the current request has an organization but no project, the sidebar SHALL show organization-scope items (Dashboard, Projects, Members, API Keys, Settings). When the request has a project, the sidebar SHALL show project-scope items (Incidents, Keywords, Coverage, Members, Settings) plus a back-link to the organization scope.

#### Scenario: Organization-scope sidebar
- **WHEN** a user is on an org-scoped page (e.g. `/acme/`, `/acme/members/`)
- **THEN** the sidebar shows Dashboard, Projects, Members, API Keys, Settings under a "Workspace" label and the workspace switcher at the top displays the organization's name

#### Scenario: Project-scope sidebar
- **WHEN** a user is on a project-scoped page (e.g. `/acme/bird-trade/incidents/`)
- **THEN** the sidebar shows Incidents, Keywords, Coverage, Members, Settings under a "Project" label, includes a visible back-link to the organization scope, and the switcher displays the project name with the organization name as a smaller secondary line

#### Scenario: Active item highlighted
- **WHEN** a user is on an in-app page whose URL name belongs to a sidebar nav item
- **THEN** that sidebar item is visually marked as active (background tint and left-border accent)

### Requirement: Workspace switcher
The sidebar header SHALL include a dropdown that lists all organizations the current user belongs to. Clicking an entry SHALL navigate to that organization's dashboard.

#### Scenario: User with multiple organizations switches workspace
- **WHEN** a user belonging to two or more organizations opens the workspace switcher
- **THEN** the dropdown lists every organization they are a member of, and selecting one navigates the browser to that org's dashboard

#### Scenario: User with a single organization
- **WHEN** a user belongs to exactly one organization
- **THEN** the switcher still appears with the current org label but without a toggle chevron (no dropdown behavior)

### Requirement: Sidebar collapse
The sidebar SHALL be collapsible to an icon-only rail. The collapsed state SHALL persist across page navigations within the same browser using `localStorage`.

#### Scenario: User collapses sidebar
- **WHEN** a user clicks the "Collapse" control at the bottom of the sidebar
- **THEN** the sidebar width shrinks to show icons only (no labels), the main area expands to fill the freed space, and the collapsed state is written to `localStorage`

#### Scenario: Collapsed state persists
- **WHEN** a user collapses the sidebar and then navigates to another page
- **THEN** the new page also renders with the sidebar collapsed, without a flash of the expanded state

### Requirement: Responsive sidebar behavior
On viewport widths below the `lg` breakpoint (1024 px), the sidebar SHALL auto-collapse to the icon rail. On viewport widths below the `md` breakpoint (768 px), the sidebar SHALL be hidden by default and opened as an overlay via a hamburger button in the topbar.

#### Scenario: Medium screen
- **WHEN** the viewport is between 768 px and 1024 px wide
- **THEN** the sidebar shows as an icon rail with tooltips on hover

#### Scenario: Mobile screen
- **WHEN** the viewport is below 768 px wide
- **THEN** the sidebar is hidden and a hamburger icon appears in the topbar; tapping the hamburger opens the sidebar as a full-height overlay that dismisses on outside-click

### Requirement: Breadcrumb topbar
Every in-app page SHALL display a topbar showing a breadcrumb reflecting the current scope (Organization › Project › Section), a user avatar menu on the right, and optional page-level actions.

#### Scenario: Project page breadcrumb
- **WHEN** a user views the incidents list for project "bird-trade" in org "acme"
- **THEN** the topbar shows "acme › Bird Trade › Incidents" with each segment linking to its own page and a user-avatar dropdown on the far right

### Requirement: Split-screen auth layout
Login, register, and invitation-accept pages SHALL use a split-screen layout with a brand panel (logo, tagline, subtle artwork or pattern) on one side and the form card on the other. The design SHALL be distinct from the in-app shell so users perceive the auth flow as a separate context.

#### Scenario: Login page visual
- **WHEN** an unauthenticated user opens `/auth/login/`
- **THEN** the left (or right on narrow screens: stacked) panel shows the Crane logo and a short tagline, and the other panel shows the email/password form centered in a white card with a primary "Log in" button and a link to register

### Requirement: Error pages consistent with shell
The system SHALL provide 403, 404, and 500 templates. 403 and 404 SHALL render within `base_minimal.html` with a friendly message and a link back to a safe location. The 500 template SHALL be a self-contained HTML file with no template tags, so it renders even when the CSS build or context processors fail.

#### Scenario: 404 page
- **WHEN** an authenticated user navigates to a non-existent URL
- **THEN** they see a page saying "Page not found" with a link back to their org selector, styled consistently with the app

#### Scenario: 500 failsafe
- **WHEN** the application encounters an unhandled exception
- **THEN** users see a minimal "Something went wrong" page that renders from a static HTML template without depending on `{% load static %}` or context processors

### Requirement: HTMX partial rendering preserves chrome boundary
Views that return HTML fragments for HTMX requests SHALL do so without accidentally including the application shell. A view designed to serve only partials SHALL reject non-HTMX requests with HTTP 400. A view that serves both full pages and partials SHALL choose the template based on whether `request.htmx` is truthy, using a central mechanism (e.g. `get_template_names()` override) — not ad-hoc conditionals in response-building code.

#### Scenario: Dual-template view returns partial for HTMX request
- **WHEN** an HTMX filter request is sent to the incident list view with header `HX-Request: true`
- **THEN** the view returns only the `_list_rows.html` partial (no sidebar, no topbar, no DOCTYPE)

#### Scenario: Dual-template view returns full page for normal request
- **WHEN** a browser navigates directly to the incident list URL without an `HX-Request` header
- **THEN** the view returns the full `list.html` page wrapped in `base_app.html`

#### Scenario: Partial-only view blocks non-HTMX request
- **WHEN** a plain-browser GET is sent to a view decorated with `HtmxOnlyMixin`
- **THEN** the view responds with HTTP 400 and does not render any template
