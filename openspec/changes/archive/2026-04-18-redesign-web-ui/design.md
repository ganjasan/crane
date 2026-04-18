## Context

Crane is a Django 6.0.4 OSINT platform in early MVP. Models, views, URLs, forms, and templates are wired end-to-end (27 templates, 25+ views across 5 apps). The current UI is a horizontal top-bar with `max-w-7xl` centered content, Tailwind via CDN, Alpine + HTMX both via CDN, no static assets on disk. Navigation helpers are minimal: one context processor injects `user_org_memberships`; middleware attaches `request.organization` / `request.project`.

The first real deployment (ICF Bird Trade Central Asia) will invite volunteers shortly. Before that happens we want a visual system that signals "serious tool for serious work" rather than "Django admin reskin." Reference: Render, Linear, Notion — dark sidebar, light content, monochrome palette with a single accent.

Stakeholders:
- ICF/CACN coordinators and volunteers (first users) — need clear navigation, legible tables, no confusion between org and project scope.
- Future contributors — need a template system where adding a new page does not require copy-pasting 150 lines of Tailwind classes from a sibling.
- Maintainer (Artem) — needs a palette change to be a one-file edit, not a 27-file find-and-replace.

Constraints:
- No SPA. Django templates + server-rendered HTML is non-negotiable; interactivity stays within HTMX + Alpine.
- No Node.js runtime dependency. Tailwind must build without `npm install`.
- Zero-budget project — every dependency must be free/open-source.
- Existing HTMX partial at `templates/incidents/_list_rows.html` (returned on `HX-Request`) must keep working unchanged.

## Goals / Non-Goals

**Goals:**

- A recognizable, consistent visual system across all 27 pages (plus 404/403/500) that matches the "origami / monochrome slate" palette selected during discovery.
- A two-level sidebar that unambiguously shows *where you are* (org ↔ project) and lets you switch workspaces in one click.
- A template hierarchy where adding a new page is pick-a-base + pick-components, not inline-tailwind-soup.
- A Tailwind config where design tokens are named semantically (`crane-primary`, `crane-surface`) and consumed via `@apply` component classes, so a palette change is a single-file edit.
- A production-ready static-asset story: committed `crane.css`, purged to <20 KB, usable by `collectstatic` on Render.
- HTMX partials that are verifiably chrome-free with a type-checked boundary (`HtmxOnlyMixin` or `get_template_names()` convention).

**Non-Goals:**

- Dark mode for end users. Light-only in this iteration. Tokens will be named so that a future dark-mode PR can swap palette values without touching templates.
- A full component framework (shadcn-for-Django, django-components, django-cotton). Django's `{% include %}` with `{% with %}` variables covers ~90 % of what we need; the rest lives in `@apply` CSS classes.
- Responsive mobile polish beyond "sidebar collapses to an icon rail on <lg screens and becomes a hamburger overlay on <md." Pixel-perfect mobile layouts for every page are out of scope.
- Replacing any view logic, URL structure, or data model. This change is presentation-only; Python code changes are limited to nav helpers, one new mixin, and the context processor.
- Icon-font or icon library dependency. We inline a curated set of ~10 Heroicon SVG snippets as template files.

## Decisions

### 1. Template hierarchy: 4-file inheritance (`base` → `base_app` / `base_auth` / `base_minimal`)

**Decision:** `base.html` is a bare root (DOCTYPE, `<head>`, fonts, CSS link, global scripts, `{% block body %}`). Three shells extend it: `base_app.html` (sidebar + content), `base_auth.html` (split-screen card), `base_minimal.html` (centered narrow column for org_selector / org_create). Every page template extends exactly one shell.

**Alternatives considered:**
- Single base with flag blocks (`{% block sidebar %}{% endblock %}`): simpler but requires every auth page to override the sidebar block to empty, and any new shell requires touching the base.
- Two bases only (`base_app` / `base_auth`, no root): duplicates the `<head>` in two places; any asset added globally risks drifting.

**Rationale:** Three shells is the right number because we have three fundamentally different layouts. A root above them localizes the single source of truth for assets without adding a fourth file to reason about when debugging a specific page.

### 2. Component partials live in `templates/components/`, consumed via `{% include %}` with explicit `with` variables

**Decision:** Each component partial documents its variable contract in a top comment. Components are atomic (stat card, pill, page header — NOT wrapper-style). Wrapper chrome (cards, sidebar shell) lives in `@apply` CSS classes in `crane.src.css`.

**Alternatives considered:**
- `django-components` (proper named-slot components with TS-style props): powerful, but adds a dependency and a build-time templating layer for negligible payoff at 10 components.
- `django-cotton` (single-file components): similar payoff/cost tradeoff. Worth revisiting once component count exceeds 30.
- Template tags (`{% stat_card label="X" value="Y" %}`): Python-side registration plus `{% load %}` in every template. More friction for contributors who read the template file and have to jump to Python to understand what the tag renders.

**Rationale:** Django's `{% include %}` + `{% with %}` is universally readable without additional tooling. The 10 partials we need fit this pattern cleanly because they are widgets, not layouts.

### 3. `@apply` CSS classes for wrapper chrome, not for every utility

**Decision:** Source CSS (`static/css/crane.src.css`) defines component classes in `@layer components`:
- `.btn-primary`, `.btn-secondary`, `.btn-ghost`, `.btn-danger`
- `.input-base`, `.select-base`, `.textarea-base`
- `.card`, `.card-padded`
- `.sidebar-link`, `.sidebar-link-active`, `.sidebar-section-label`
- `.pill`, `.pill-success`, `.pill-warning`, `.pill-danger`, `.pill-muted`
- `.table-chrome` (applied to `<table>`, handles border/rounded/overflow)

**Alternatives considered:**
- No `@apply`, inline utilities everywhere: templates become unreadable for anyone who isn't fluent in Tailwind shorthand. Palette change is 27-file find-and-replace.
- `@apply` for everything including layout utilities: fights Tailwind's composition model and encourages CSS bloat.

**Rationale:** `@apply` used sparingly — only for semantically-named recurring chrome — gets the consistency benefits without fighting Tailwind. Layout classes (flex, grid, gap, padding) stay inline where Tailwind shines.

### 4. Design tokens via `tailwind.config.js` `theme.extend.colors`

**Decision:** Named tokens, not raw palette references, in `tailwind.config.js`:
```
crane-primary:  #0f172a   (slate-900)
crane-surface:  #f8fafc   (slate-50)
crane-sidebar:  #0f172a
crane-border:   #e2e8f0   (slate-200)
crane-muted:    #64748b   (slate-500)
crane-success:  #059669   (emerald-600)
crane-danger:   #dc2626   (red-600)
crane-warning:  #d97706   (amber-600)
```

**Alternatives considered:**
- Raw slate-900 / emerald-600 everywhere: fine today, but re-theming means grep-and-replace.
- CSS custom properties (`--crane-primary: #0f172a`) referenced via `rgb(var(--crane-primary))`: enables runtime theme switching. Worth it when we add dark mode; overkill now.

**Rationale:** Named tokens at the Tailwind config layer give us the single-edit-for-palette-change benefit without the CSS-var indirection cost. Dark-mode migration later is a one-day job of swapping token values behind a `dark:` variant or CSS-var flip.

### 5. Tailwind standalone CLI, binary downloaded by `run_dev.sh`, output committed

**Decision:** `bin/tailwindcss` (gitignored) is downloaded by `run_dev.sh` if missing (conditional curl). The build step runs before `runserver`. `static/css/crane.css` (compiled, minified) is committed so production (Render) does not need the binary. Developers editing templates run `./bin/tailwindcss -i static/css/crane.src.css -o static/css/crane.css --watch` in a second terminal; `run_dev.sh` prints the command on startup.

**Alternatives considered:**
- `django-tailwind`: requires Node + npm in dev and in Docker. Adds a 300-MB node_modules to the dev loop. Rejected given constraint.
- CDN Tailwind (current): no purge, no custom tokens, 4 MB payload. Acceptable for prototypes, not for a product we want people to trust.
- Not committing `crane.css`: forces CI/build step on Render. Adds deploy complexity for zero benefit when the artifact is ~15 KB.

**Rationale:** Committed build artifact is the simplest "it just works" story for Render and for anyone cloning the repo.

### 6. Nav tree as pure functions + context processor

**Decision:** `apps/core/nav.py` exports `build_org_nav(request, org) -> list[NavItem]` and `build_project_nav(request, org, project) -> list[NavItem]`. `NavItem` is a dataclass with `label`, `url`, `icon_name`, `active: bool`. `sidebar_nav` context processor (in `apps/core/context_processors.py`) decides which level to build based on `request.organization` / `request.project`, and injects `sidebar_nav_items`, `sidebar_scope` ("org" or "project"), `sidebar_workspace_name`, and `sidebar_back_url` (link up from project to org when in project scope).

Active detection: each `NavItem` owns a list of URL names that count as "active" for it. The builder compares against `request.resolver_match.url_name`. Example: the Incidents item is active for `incident_list`, `incident_detail`, `incident_create`, `incident_edit`.

**Alternatives considered:**
- Hardcoded HTML in `_sidebar.html`: fast to write, hard to maintain; nav logic scattered across template with `{% if current == 'x' or current == 'y' %}` chains.
- Template tag (`{% sidebar_nav %}` returning rendered HTML): tests become "render and assert HTML" instead of "call function, assert data."

**Rationale:** Data in Python, rendering in template. Pure functions are unit-testable without a test client.

### 7. HTMX partial boundary: `django-htmx` + `HtmxOnlyMixin` + `get_template_names()` convention

**Decision:** Add `django-htmx` dependency. Two patterns:

- **Partial-only views** (views whose sole purpose is rendering a partial — e.g., filter endpoints): subclass `HtmxOnlyMixin` which returns `HttpResponseBadRequest` if `not request.htmx`. Guarantees the view cannot accidentally render the full page shell.
- **Dual-template views** (views that render either the full page or just a partial based on request origin — e.g., `IncidentListView`): override `get_template_names(self)` to return `["incidents/_list_rows.html"]` if `self.request.htmx` else `["incidents/list.html"]`. No ad-hoc `if request.htmx: return render(...)` in `get_context_data`.

**Alternatives considered:**
- Hand-rolled `request.META.get("HTTP_HX_REQUEST")` checks: error-prone, no typed API, duplicates across views.
- Middleware that sets `request.htmx = bool(...)`: essentially what `django-htmx` provides, plus edge cases (boosted requests, OOB targets, current URL tracking). Not worth reinventing.

**Rationale:** `django-htmx` is ~200 lines, MIT-licensed, and codifies the same pattern every serious Django+HTMX project converges on. The cost is one dependency; the benefit is a typed `request.htmx` object with correctness for `hx-boost`, `hx-target`, and `hx-trigger` introspection.

### 8. Icons: inline SVG snippets under `templates/icons/`

**Decision:** A curated set of ~10 Heroicon v2 (outline) SVGs, each a standalone `.svg` or `.html` file. The sidebar includes them via `{% include "icons/"|add:item.icon_name|add:".html" %}`.

**Alternatives considered:**
- Icon font (Font Awesome, Lucide): 200 KB CSS for 10 icons, plus a network request.
- SVG sprite sheet: one extra fetch and a `<use xlink:href>` incantation. Fine but premature at 10 icons.
- JS-based (e.g., Lucide npm): requires a JS bundle.

**Rationale:** At 10 icons, inline SVG (~400 bytes each) is faster, simpler, and trivially customizable. If we hit 50 icons, revisit with a sprite.

### 9. Sidebar collapse state persisted via `localStorage`

**Decision:** A small Alpine component on the sidebar toggles a `collapsed` boolean and syncs it to `localStorage.crane_sidebar_collapsed`. On initial render, the sidebar reads the value and applies the corresponding class. Layout shift is avoided by the value being read synchronously in an `x-data` init function.

**Alternatives considered:**
- Cookie-based (server reads cookie, renders correct state): avoids initial-render flash. Requires cookie-parsing glue and doubles the abstraction.
- Per-user preference in DB: overengineered for an MVP.

**Rationale:** `localStorage` + Alpine is 20 lines of JS and good enough. If the flash becomes a real problem we switch to cookie.

## Risks / Trade-offs

- **Risk:** Tailwind purge removes dynamically-composed class names (e.g., `"bg-" + color`). → **Mitigation:** grep the templates during the reskin for string-interpolated classes and move them into partial variables; add a `safelist` section in `tailwind.config.js` for the few that cannot be rewritten.

- **Risk:** Committing `crane.css` creates merge conflicts on every palette or partial change. → **Mitigation:** document "regenerate before PR" in `CLAUDE.md`; consider `.gitattributes merge=union` if it becomes painful.

- **Risk:** The 25-template reskin sweep is the longest and most tedious step; risk of regressions in HTMX behavior (`_list_rows.html` edge cases), forms, and tricky layouts (coverage matrix). → **Mitigation:** order the sweep so `incidents/list.html` is done early and HTMX is smoke-tested first; save `coverage/matrix.html` (grid layout) for last when the component system is mature.

- **Risk:** `django-htmx` dependency churn or abandonment. → **Mitigation:** its surface area is small (~10 attributes, ~5 helpers); we could re-implement in 100 lines if needed.

- **Risk:** `@apply` can fight Tailwind's purge when used with variants (e.g., `hover:` inside `@apply`). → **Mitigation:** the Tailwind CLI v3+ handles this correctly; verify output after build.

- **Risk:** Sidebar on small screens — two-level nav plus workspace switcher plus project-level scope is a lot of chrome. → **Mitigation:** below `lg`, collapse to icon-only rail (48 px wide) with tooltips; below `md`, sidebar becomes an overlay triggered by a hamburger in the topbar.

- **Trade-off:** No dark mode now. We chose named tokens to keep the migration easy, but the shortest-path for contributors adding dark styles is blocked until we do that work.

- **Trade-off:** Four-file base hierarchy means three jumps to find where a global `<script>` gets loaded. Better than two (drift risk) and than five+ (overengineering).

## Migration Plan

No data migration. No downtime. Rollout is a single PR:

1. Land infrastructure (Tailwind binary script, `tailwind.config.js`, `crane.src.css`, empty `crane.css`, `run_dev.sh` changes, `STATICFILES_DIRS` fix in settings).
2. Land the three base shells and the sidebar partial behind the existing `base.html` — but rename it to `base_old.html` and replace `base.html` with the new root. Templates continue to extend `base.html` until switched.
3. Land the component partials (`_stat_card`, `_pill`, `_page_header`, etc.).
4. Sweep the 25 templates app-by-app, switching `extends` target and wiring components. Verify each app loads with `./run_dev.sh` + manual smoke test.
5. Delete `_nav.html` and `base_old.html` once zero templates reference them.
6. Update `CLAUDE.md` with the new workflow.

**Rollback:** Git revert the PR. Because views/URLs/models are untouched, a revert is safe with no data fixup needed.

## Open Questions

- Should we use Inter (Google Fonts) or self-host? → Default to self-hosting (`static/fonts/`) to avoid a DNS round-trip; small enough impact to revisit if problematic.
- Logo: keep the "C" text placeholder in the sidebar header, or commission a small origami-crane mark? → Keep text for this PR; track a ticket for the mark.
- Error pages (`404/403/500`) — do we reuse `base_minimal.html`, or does the 500 page need a zero-dependency failsafe (plain HTML, no `{% load static %}` in case the CSS build is broken)? → Use `base_minimal.html` for 404/403; make the 500 page a hand-rolled plain-HTML file so it still renders if static assets fail.
