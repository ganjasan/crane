## 1. Tailwind build pipeline

- [ ] 1.1 Create `static/css/` and `static/fonts/` directories
- [ ] 1.2 Create `static/css/crane.src.css` with `@tailwind base/components/utilities` directives and an empty `@layer components` block
- [ ] 1.3 Create `tailwind.config.js` with content globs (`./templates/**/*.html`, `./apps/**/*.py`) and `theme.extend.colors` for all semantic tokens (`crane-primary`, `crane-surface`, `crane-sidebar`, `crane-border`, `crane-muted`, `crane-success`, `crane-danger`, `crane-warning`)
- [ ] 1.4 Update `run_dev.sh` to download `bin/tailwindcss` (linux-x64) if missing and run a one-shot build of `crane.src.css` → `crane.css --minify` before `runserver`
- [ ] 1.5 Add `bin/tailwindcss` to `.gitignore`; print the watch command on `run_dev.sh` startup
- [ ] 1.6 Ensure `STATICFILES_DIRS = [BASE_DIR / "static"]` in `crane/settings.py` (verify; it is already present)
- [ ] 1.7 Run one-shot build, commit `static/css/crane.css`, open the file and confirm purge worked (size < 20 KB)

## 2. @apply component classes

- [ ] 2.1 In `crane.src.css`, add `@layer components` classes: `.btn-primary`, `.btn-secondary`, `.btn-ghost`, `.btn-danger`
- [ ] 2.2 Add `.input-base`, `.select-base`, `.textarea-base`
- [ ] 2.3 Add `.card`, `.card-padded`
- [ ] 2.4 Add `.sidebar-link`, `.sidebar-link-active`, `.sidebar-section-label`
- [ ] 2.5 Add `.pill`, `.pill-success`, `.pill-warning`, `.pill-danger`, `.pill-muted`
- [ ] 2.6 Add `.table-chrome`
- [ ] 2.7 Rebuild; smoke-test each class by temporarily placing it on a visible element

## 3. Dependencies & static assets

- [ ] 3.1 Add `django-htmx` to `requirements.txt`; install locally
- [ ] 3.2 Register `django_htmx` in `INSTALLED_APPS`
- [ ] 3.3 Add `django_htmx.middleware.HtmxMiddleware` to `MIDDLEWARE` (before `OrgProjectMiddleware`)
- [ ] 3.4 Self-host the Inter font under `static/fonts/` (download the subset WOFF2 files); add `@font-face` declarations in `crane.src.css`
- [ ] 3.5 Create `templates/icons/` with the minimum icon set: home, folder, users, key, settings, file-text, tag, grid, import-export, chevron-down, chevron-right, log-out, plus, search, x, check, alert-circle

## 4. Nav tree and context processor

- [ ] 4.1 Create `apps/core/nav.py` with a `NavItem` dataclass (`label`, `url`, `icon_name`, `active_url_names: list[str]`, `active: bool`)
- [ ] 4.2 Implement `build_org_nav(request, org) -> list[NavItem]` returning Dashboard, Projects, Members, API Keys, Settings entries with correct `active_url_names`
- [ ] 4.3 Implement `build_project_nav(request, org, project) -> list[NavItem]` returning Incidents, Keywords, Coverage, Members, Settings
- [ ] 4.4 Extend `apps/core/context_processors.py` with `sidebar_nav` that picks the right builder based on `request.organization` / `request.project` and injects `sidebar_nav_items`, `sidebar_scope`, `sidebar_workspace_name`, `sidebar_back_url`
- [ ] 4.5 Register the new context processor in `crane/settings.py`
- [ ] 4.6 Write unit tests for `build_org_nav` and `build_project_nav` (GIVEN/WHEN/THEN docstrings): correct items, correct `active` resolution, project builder does not appear when project is missing

## 5. HTMX partial boundary

- [ ] 5.1 Add `HtmxOnlyMixin` to `apps/core/mixins.py`: subclass of Django `View` that returns `HttpResponseBadRequest` when `not request.htmx`
- [ ] 5.2 Refactor `IncidentListView.get_template_names()` to return `["incidents/_list_rows.html"]` when `self.request.htmx` else `["incidents/list.html"]`; remove any ad-hoc partial branching
- [ ] 5.3 Write a regression test hitting `/incidents/` with and without the `HX-Request` header, asserting the correct template name is used

## 6. Base shell templates

- [ ] 6.1 Rename existing `templates/base.html` to `templates/_base_old.html` for reference (delete at the end)
- [ ] 6.2 Write the new `templates/base.html`: bare `<html>`, `<head>` with `<link rel="stylesheet" href="{% static 'css/crane.css' %}">`, HTMX + Alpine scripts, CSRF `hx-headers` body attr, `{% block body %}{% endblock %}`; no visible chrome
- [ ] 6.3 Write `templates/base_app.html`: extends `base`, two-column flex layout, includes `_sidebar.html`, flash messages container, `{% block content %}`, `{% block page_actions %}` placeholder
- [ ] 6.4 Write `templates/base_auth.html`: extends `base`, split-screen (brand panel + white card), `{% block content %}` inside the card
- [ ] 6.5 Write `templates/base_minimal.html`: extends `base`, narrow centered column, simple topbar (logo + user menu), `{% block content %}`
- [ ] 6.6 Delete `_base_old.html` after verification

## 7. Sidebar and topbar partials

- [ ] 7.1 Create `templates/_sidebar.html`: renders the workspace header, the back-link (if project scope), iterates `sidebar_nav_items`, renders the Alpine-powered workspace switcher dropdown using `user_org_memberships`
- [ ] 7.2 Add Alpine collapse behavior: `x-data` on the sidebar root reads/writes `localStorage.crane_sidebar_collapsed`; toggles width, hides labels, shows icon-only rail when collapsed
- [ ] 7.3 Add responsive behavior: auto-collapse below `lg`; hidden + hamburger overlay below `md`
- [ ] 7.4 Create `templates/_topbar.html`: breadcrumb based on `request.organization` / `request.project` / current page title, user avatar menu on right; included by `base_app.html` and `base_minimal.html`
- [ ] 7.5 Delete `templates/_nav.html`

## 8. Component partials

- [ ] 8.1 Create `templates/components/_page_header.html` (variables: `title`, `subtitle?`, actions via a `{% block page_actions %}` slot in the calling base)
- [ ] 8.2 Create `templates/components/_stat_card.html` (variables: `label`, `value`, `color_class?`, `href?`)
- [ ] 8.3 Create `templates/components/_pill.html` (variables: `text`, `variant` ∈ default/success/warning/danger/muted)
- [ ] 8.4 Create `templates/components/_empty_state.html` (variables: `icon?`, `heading`, `subtext?`, `action_label?`, `action_url?`)
- [ ] 8.5 Create `templates/components/_card.html` (thin wrapper — just `.card` + optional padded variant)
- [ ] 8.6 Create `templates/components/_flash_messages.html` (reads `messages`, renders coloured toast banners)
- [ ] 8.7 Create `templates/components/_form_field.html` (variables: `field` — bound Django form field)
- [ ] 8.8 Create `templates/components/_pagination.html` (variables: `page_obj`)
- [ ] 8.9 Create `templates/components/_filter_bar.html` (variables: `form`, `target_id` for HTMX)
- [ ] 8.10 Create `templates/components/_data_table.html` (variables: `tbody_id?`, `thead_template?` — outer chrome only)
- [ ] 8.11 Comment header at the top of each partial documenting variables, required/optional, and expected types

## 9. Auth pages reskin

- [ ] 9.1 Reskin `templates/auth/login.html`: extend `base_auth.html`, use brand panel + form card, render inputs with `input-base` and button with `btn-primary`
- [ ] 9.2 Reskin `templates/auth/register.html` in the same pattern
- [ ] 9.3 Reskin `templates/auth/invite_accept.html` (all three states: expired, existing user confirm, new user form)
- [ ] 9.4 Reskin `templates/auth/account_settings.html`: extend `base_app.html`, page header, token table, generate/revoke actions using `btn-primary` / `btn-danger`

## 10. Org-level page sweep

- [ ] 10.1 Reskin `templates/core/org_selector.html`: extend `base_minimal.html`, card grid of org memberships + "Create org" CTA
- [ ] 10.2 Reskin `templates/core/org_dashboard.html`: extend `base_app.html`, page header, stat cards for project count/member count, project grid
- [ ] 10.3 Reskin `templates/core/org_create.html`: extend `base_app.html`, single-column form
- [ ] 10.4 Reskin `templates/core/org_settings.html`: extend `base_app.html`, tabbed header (General / Members / API Keys / Import & Export if applicable), form with `_form_field` partial
- [ ] 10.5 Reskin `templates/core/org_members.html`: extend `base_app.html`, member table with `_pill` for role, invite form section, pending invites table

## 11. Project-level page sweep

- [ ] 11.1 Reskin `templates/core/project_create.html`
- [ ] 11.2 Reskin `templates/core/project_dashboard.html` (most complex page — 4 stat cards via `_stat_card`, recent incidents table, review queue alert via `_empty_state`, keyword candidates widget, coverage gaps list, data quality flags)
- [ ] 11.3 Reskin `templates/core/project_settings.html` (tabbed sections for platforms / languages / categories / custom fields / record ID prefix)
- [ ] 11.4 Reskin `templates/core/project_members.html`
- [ ] 11.5 Reskin `templates/core/seed_import.html`

## 12. Incidents app reskin

- [ ] 12.1 Reskin `templates/incidents/list.html`: page header with "Create incident" action, `_filter_bar` with HTMX target, `_data_table` wrapper
- [ ] 12.2 Update `templates/incidents/_list_rows.html`: verify it still does NOT extend any base; use `_pill` component for status
- [ ] 12.3 Reskin `templates/incidents/detail.html`: two-column layout (main content + metadata sidebar), extra fields section, duplicate-of link, status change controls
- [ ] 12.4 Reskin `templates/incidents/form.html`: use `_form_field` partial for every field, extra-fields section rendered dynamically

## 13. Keywords app reskin

- [ ] 13.1 Reskin `templates/keywords/list.html`: filter bar, status pills, inline status-change buttons (coordinator only)
- [ ] 13.2 Reskin `templates/keywords/form.html`
- [ ] 13.3 Reskin `templates/keywords/import.html`

## 14. Coverage app reskin

- [ ] 14.1 Reskin `templates/coverage/matrix.html`: adapt the platform × language grid to the new palette (color coding preserved: emerald / amber / red by recency)
- [ ] 14.2 Reskin `templates/coverage/log_search.html`
- [ ] 14.3 Reskin `templates/coverage/volunteer_activity.html`

## 15. Error pages and polish

- [ ] 15.1 Create `templates/404.html` extending `base_minimal.html`
- [ ] 15.2 Create `templates/403.html` extending `base_minimal.html`
- [ ] 15.3 Create `templates/500.html` as a hand-written static HTML file (no `{% load static %}`, no context processors) with inline critical CSS
- [ ] 15.4 Wire custom error handlers in `crane/urls.py` (`handler404`, `handler403`, `handler500`) if not already Django's default lookup
- [ ] 15.5 Fix `OrgDashboardView` to include `LoginRequiredMixin` (the probable-crash gotcha surfaced during exploration)

## 16. Documentation and verification

- [ ] 16.1 Update `CLAUDE.md` with the new template hierarchy, Tailwind build workflow, and nav extension guide
- [ ] 16.2 Smoke-test every page locally (`python manage.py seed_icf` then walk through all 27+ pages)
- [ ] 16.3 Verify no templates reference deleted `_nav.html`
- [ ] 16.4 Run `openspec validate redesign-web-ui` and fix any warnings
- [ ] 16.5 Open a PR with screenshots of before/after for at least 4 representative pages (org_dashboard, incident_list, auth_login, coverage_matrix)
