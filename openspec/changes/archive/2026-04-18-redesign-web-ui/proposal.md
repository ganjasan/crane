## Why

The current web UI is a functional but generic Django-admin-style layout (horizontal top-bar, centered `max-w-7xl` content, CDN Tailwind, indigo accents). All 27 templates and 25+ views are already wired, but the visual system feels like a tech demo — not a tool journalists and investigators would trust for serious OSINT work. Before we invite the first ICF volunteers, we want the interface to read as a purposeful product: a dark sidebar SaaS shell (in the vein of Render, Linear, Notion) with a monochrome-slate "origami crane" palette, a component-based template system, and a real Tailwind build pipeline.

## What Changes

- **Replace horizontal top-bar with a two-level dark sidebar** (organization context ↔ project context, Render-style), with a workspace switcher and breadcrumb-aware topbar.
- **Introduce a 3-tier template hierarchy**: `base.html` (root shell) → `base_app.html` (sidebar layout) / `base_auth.html` (split-screen auth) / `base_minimal.html` (org selector, org create — no sidebar).
- **Extract reusable component partials**: `_stat_card`, `_pill`, `_page_header`, `_empty_state`, `_card`, `_flash_messages`, `_form_field`, `_pagination`, `_filter_bar`, `_data_table`.
- **Replace CDN Tailwind with standalone CLI build** producing committed `static/css/crane.css`, with a `tailwind.config.js` exposing semantic tokens (`crane-primary`, `crane-surface`, `crane-sidebar`, `crane-border`, `crane-muted`, `crane-success`, `crane-danger`, `crane-warning`).
- **Introduce `@apply` component classes** in source CSS (`.btn-primary`, `.btn-secondary`, `.card`, `.input-base`, `.sidebar-link`, `.sidebar-link-active`) so page templates carry semantic class names instead of 200+ character utility chains.
- **Add a nav-tree abstraction**: `apps/core/nav.py` exposes pure functions building nav sections from `request.organization` / `request.project`; a new `sidebar_nav` context processor injects them into every template.
- **Harden HTMX partial rendering**: add `django-htmx` dependency, add `HtmxOnlyMixin` in `apps/core/mixins.py` for views that only serve partials, standardize the `get_template_names()` pattern so full-page views return the partial when `request.htmx` is truthy and the full shell otherwise.
- **Introduce an icon system**: SVG snippets under `templates/icons/` included by name, used by the sidebar and component partials.
- **Redesign all 4 auth pages** (login, register, invite accept, account settings) into a split-screen brand-panel layout.
- **Reskin all 25 app pages** (org_*, project_*, incidents, keywords, coverage, members, settings) against the new shell, palette, and component partials.
- **Add 404/403/500 error templates** consistent with the new shell.

## Capabilities

### New Capabilities

- `web-ui-shell`: The application's visual shell and navigation system — base layouts, dark sidebar with two-level (org/project) navigation, workspace switcher, topbar, split-screen authentication pages, and error pages. Defines how users move between contexts and perceive the application as a product.

- `ui-design-system`: The design tokens, theme configuration, reusable component partials, and build pipeline that guarantee visual consistency across all pages. Defines the contract between design decisions (colors, spacing, component behavior) and their implementation (Tailwind tokens, `@apply` classes, partial signatures).

### Modified Capabilities

(none — no canonical specs exist yet; `osint-platform-mvp` is still an open change)

## Impact

- **Affected code**:
  - `templates/` — every file (base rewrites + new partials + reskin sweep across 25+ pages)
  - `apps/core/` — new `nav.py`, extended `context_processors.py`, new `HtmxOnlyMixin` in `mixins.py`
  - `crane/settings.py` — add `STATICFILES_DIRS`, register new context processor, add `django_htmx` app
  - Views that return HTMX partials (`apps/incidents/views.py` currently; pattern scales) — adopt `get_template_names()` convention
- **New dependencies**:
  - `django-htmx` (Python, ~200 LOC, MIT) — typed `request.htmx` object and helpers
  - Tailwind standalone CLI binary (`bin/tailwindcss`, gitignored binary, downloaded in `run_dev.sh`)
- **Infrastructure**:
  - `run_dev.sh` adds a Tailwind build step; documented `--watch` command for active template editing
  - `static/` directory created (currently referenced by `STATICFILES_DIRS` but missing on disk)
  - `static/css/crane.css` compiled artifact committed so production deploys (Render) don't need the binary
- **Users**: No functional change — same pages, same data, same workflows. Only presentation changes. No migration needed; existing sessions continue working.
- **Docs**: `CLAUDE.md` will need a short paragraph on Tailwind build workflow and the template hierarchy.
