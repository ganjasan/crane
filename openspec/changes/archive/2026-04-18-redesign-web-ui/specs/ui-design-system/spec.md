## ADDED Requirements

### Requirement: Semantic Tailwind design tokens
The Tailwind configuration SHALL define semantic color tokens under `theme.extend.colors`. All page templates and component partials SHALL reference these semantic tokens (e.g. `bg-crane-surface`, `text-crane-muted`) rather than raw palette values (e.g. `bg-slate-50`, `text-slate-500`). Exception: `bg-white` / `text-white` on light chrome are permitted.

#### Scenario: Palette change is a single-file edit
- **WHEN** a maintainer changes the value of `crane-primary` in `tailwind.config.js` and rebuilds
- **THEN** every page and component using `crane-primary` reflects the new value without any other file being modified

#### Scenario: Required tokens exist
- **WHEN** a developer inspects `tailwind.config.js`
- **THEN** the following tokens are defined: `crane-primary`, `crane-surface`, `crane-sidebar`, `crane-border`, `crane-muted`, `crane-success`, `crane-danger`, `crane-warning`

### Requirement: Component CSS classes via @apply
The source stylesheet SHALL define a curated set of component classes under `@layer components` that encapsulate recurring chrome: button variants (`.btn-primary`, `.btn-secondary`, `.btn-ghost`, `.btn-danger`), form field bases (`.input-base`, `.select-base`, `.textarea-base`), card containers (`.card`, `.card-padded`), sidebar link states (`.sidebar-link`, `.sidebar-link-active`, `.sidebar-section-label`), status pills (`.pill`, `.pill-success`, `.pill-warning`, `.pill-danger`, `.pill-muted`), and table chrome (`.table-chrome`). Page templates SHALL use these classes instead of inline utility chains for these concerns.

#### Scenario: Button uses semantic class
- **WHEN** a developer writes a primary call-to-action button in any template
- **THEN** the element uses the `btn-primary` class, not a chain of utility classes like `bg-crane-primary text-white rounded-md px-4 py-2 text-sm font-medium`

#### Scenario: Form input uses semantic class
- **WHEN** a developer renders a text input
- **THEN** the element uses the `input-base` class for baseline styling, with layout utilities (width, margin) composed alongside

### Requirement: Reusable component partials
The system SHALL provide component partials under `templates/components/` that encapsulate widgets reused across three or more pages: `_stat_card.html`, `_pill.html`, `_page_header.html`, `_empty_state.html`, `_card.html`, `_flash_messages.html`, `_form_field.html`, `_pagination.html`, `_filter_bar.html`, `_data_table.html`. Each partial SHALL document its input variables in a top-of-file comment. Partials SHALL be consumed via `{% include "components/<name>.html" with var=value ... %}`.

#### Scenario: Stat card used on dashboard
- **WHEN** a developer renders a stat card showing "Total incidents: 142"
- **THEN** they use `{% include "components/_stat_card.html" with label="Total incidents" value="142" href=incidents_url %}` rather than inline HTML

#### Scenario: Partial documents its variables
- **WHEN** a developer opens `templates/components/_stat_card.html`
- **THEN** the top of the file lists every accepted variable with its type and whether it is required or optional

#### Scenario: Pill renders for every status variant
- **WHEN** a developer calls `{% include "components/_pill.html" with text="Verified" variant="success" %}`
- **THEN** the pill renders green; substituting `variant` with `warning`, `danger`, `muted`, or `default` renders the respective styles

### Requirement: Sidebar navigation driven by data
The sidebar template SHALL render its navigation items from a data structure produced by a Python builder (`apps.core.nav.build_org_nav` and `apps.core.nav.build_project_nav`). The data structure SHALL be injected into template context by a `sidebar_nav` context processor that decides which builder to call based on the current `request.organization` and `request.project`.

#### Scenario: Adding a new nav item is a one-file change
- **WHEN** a developer adds "Reports" as an org-scoped nav item
- **THEN** the change consists of adding one entry to the list returned by `build_org_nav`; no sidebar template edits are required

#### Scenario: Active detection is centralized
- **WHEN** a user is on any URL whose URL name is registered to a nav item
- **THEN** `request.resolver_match.url_name` is compared against the item's `active_url_names` list inside the builder, and the `active` flag is set on the returned `NavItem`; the template iterates the list without inline `{% if %}` chains against URL names

### Requirement: Tailwind build pipeline produces committed artifact
The project SHALL use Tailwind standalone CLI (downloaded binary, no Node/npm) to compile `static/css/crane.src.css` into `static/css/crane.css`. The compiled file SHALL be minified, purged against templates, and committed to source control so production deployments do not require the build step. Development workflow SHALL support a watch mode invoked explicitly by the developer.

#### Scenario: First-run build
- **WHEN** a developer clones the repo and runs `./run_dev.sh`
- **THEN** the script downloads `bin/tailwindcss` if missing, runs a one-shot build to produce `static/css/crane.css`, and then starts the Django dev server

#### Scenario: Watch mode available
- **WHEN** a developer is actively editing templates
- **THEN** they can run `./bin/tailwindcss -i static/css/crane.src.css -o static/css/crane.css --watch` in a second terminal to auto-rebuild on file changes

#### Scenario: Production deploy uses committed artifact
- **WHEN** the application is deployed to Render
- **THEN** the compiled `static/css/crane.css` is picked up by `collectstatic` with no Node.js or Tailwind binary required on the build host

### Requirement: Icon set under version control
The system SHALL include a curated set of SVG icons under `templates/icons/` — each icon a small standalone HTML/SVG file, included by name (e.g. `{% include "icons/home.html" %}`). The set SHALL cover every icon used in the sidebar and component partials (minimum: home, folder, users, key, settings, file-text, tag, grid, import-export, chevron-down, log-out).

#### Scenario: Sidebar icon resolves
- **WHEN** the sidebar renders an item whose `icon_name` is `"users"`
- **THEN** `templates/icons/users.html` is included and the SVG appears inline

#### Scenario: Adding a new icon
- **WHEN** a new nav item or component needs an icon not yet available
- **THEN** the developer adds the corresponding `<name>.html` file to `templates/icons/` and references it by name — no JS bundle or npm install required
