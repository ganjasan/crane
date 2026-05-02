# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Crane is an open-source collaborative OSINT platform built with Django 6.0.4 (Python 3.12). It enables teams to capture, organize, and analyze online evidence through a multi-tenant architecture.

Frontend: Tailwind CSS v4 (standalone CLI, no Node) + HTMX + Alpine.js. Dark sidebar SaaS layout with monochrome-slate palette. All 27 app pages + 4 auth pages are wired; base shells live under `templates/` (see Template hierarchy below).

## Commands

### Development

```bash
# Quick start (starts PostgreSQL via Docker, creates venv, installs deps, runs migrations, starts server)
./run_dev.sh

# Manual setup
docker compose up -d db   # PostgreSQL on port 5433
source .venv/bin/activate
export DATABASE_URL=postgres://crane:crane@localhost:5433/crane
pip install -r requirements.txt
python manage.py migrate --run-syncdb
python manage.py runserver
# Admin: http://localhost:8000/admin/ (admin@crane.local / admin)
```

### Docker

```bash
docker-compose up          # Django + PostgreSQL (full stack)
docker-compose up -d db    # PostgreSQL only (port 5433)
```

### Django Management

```bash
python manage.py makemigrations
python manage.py migrate --run-syncdb
python manage.py createsuperuser
python manage.py collectstatic --noinput
python manage.py seed_icf   # populate ICF demo org + 3 test accounts
```

Seeded test accounts (password = username local part): `coordinator@crane.local`, `volunteer1@crane.local`, `volunteer2@crane.local`.

### Tailwind CSS

```bash
# Build once (also runs automatically from run_dev.sh)
./bin/tailwindcss -i static/css/crane.src.css -o static/css/crane.css --minify

# Watch while editing templates
./bin/tailwindcss -i static/css/crane.src.css -o static/css/crane.css --watch
```

The standalone binary is downloaded on first `run_dev.sh` into `bin/` (gitignored). Compiled `static/css/crane.css` is committed so Render deploys don't need the binary. Design tokens live in the `@theme` block of `crane.src.css` (e.g. `--color-crane-primary`, `--color-crane-surface`). Reusable component classes are defined under `@layer components` (e.g. `.btn-primary`, `.card`, `.sidebar-link`, `.pill-success`).

### Tests

Use Django's test runner. Test docstrings follow the GIVEN/WHEN/THEN pattern.

```bash
python manage.py test                          # all tests
python manage.py test apps.core                # single app
python manage.py test apps.core.tests.TestFoo  # single test class
python manage.py test apps.core.tests.TestFoo.test_bar  # single test method
```

### Browser extension

The Chrome MV3 extension lives under `browser_extension/` (a separate
TypeScript codebase, not a Django app). Build with esbuild:

```bash
cd browser_extension
npm install            # one-time, dev deps only
npm run build          # one-shot → dist/
npm run dev            # watch mode
npm run typecheck      # tsc --noEmit
```

Three entry points compile to `dist/{background,sidepanel,content}.js`. The
extension authenticates via `chrome.identity.launchWebAuthFlow` against
`/auth/extension-link/`, then talks to the API endpoints under `/api/v1/`
(`incidents/capture`, `incidents/check`, `projects`, `coverage/suggest`).
URL normalization rules in `src/shared/normalize-url.ts` mirror
`apps/incidents/utils.normalize_url` — keep both in sync. Message protocol
(discriminated unions in `src/shared/types.ts`) is documented in
`browser_extension/README.md`.

## Architecture

### Multi-Tenant Hierarchy

```
User (email-based auth, no username)
 └── Organization (UUID PK, slug)
      └── Project (UUID PK, slug unique per org)
           ├── Incident (evidence records with auto-generated record_id)
           ├── Keyword (multilingual, with status workflow)
           └── SearchSession (coverage tracking)
```

### Django Apps

- **apps.core** — User model (`AUTH_USER_MODEL = "core.User"`), Organization, Project, memberships, permissions, middleware, configuration models (Platform, Language, KeywordCategory, ProjectFieldConfig, ProjectSettings, Invitation)
- **apps.incidents** — Incident model with auto-generated `record_id`, duplicate detection on save, `extra_fields` JSONField for project-specific data
- **apps.keywords** — Keyword model with status tracking (active/deprecated/candidate) and platform relevance
- **apps.coverage** — SearchSession model for tracking volunteer search activity

### Key Patterns

**Middleware-based multi-tenancy** (`apps/core/middleware.py`): `OrgProjectMiddleware` resolves `org_slug` and `project_slug` from URL path, attaches `request.organization` and `request.project`, enforces membership. Exempt paths: `/auth/`, `/admin/`, `/api/`, `/static/`, `/media/`, `/`.

**Permission mixins** (`apps/core/mixins.py`): `OrgRequiredMixin`, `ProjectRequiredMixin`, `RequireOrgRole`, `RequireProjectRole`. Superusers bypass all checks.

**Custom User model**: Email is `USERNAME_FIELD` (no username field). Use `UserManager` for `create_user`/`create_superuser`.

**Incident record IDs**: Auto-generated as `{prefix}-{seq:03d}` using `ProjectSettings.record_id_prefix` (default "REC").

**Duplicate detection**: On Incident save, checks for existing incident with same URL in the same project; sets `duplicate_of` FK.

### Database

- **Development**: PostgreSQL via Docker on port 5433 (`DATABASE_URL=postgres://crane:crane@localhost:5433/crane`)
- **Production**: PostgreSQL via `DATABASE_URL` env var (Render)
- **Media storage**: Local `/media/` in dev; S3 via `django-storages` if `AWS_STORAGE_BUCKET_NAME` is set

### URL Structure

Views follow the pattern `/{org-slug}/{project-slug}/...` with named URL parameters so middleware can resolve the tenant context. Auth at `/auth/*`, admin at `/admin/`, API at `/api/*`, org selector at `/`.

### Template Hierarchy

```
base.html                 (root shell: <head>, crane.css, HTMX/Alpine, CSRF headers)
├── base_app.html         (sidebar + topbar + main — for authenticated in-app pages)
├── base_auth.html        (split-screen brand panel + form card — login/register/invite)
└── base_minimal.html     (narrow centered column + simple topbar — org selector, org create, errors)
```

**Sidebar** (`templates/_sidebar.html`) renders items from a data structure built by `apps.core.nav.build_org_nav` / `build_project_nav` and injected by the `sidebar_nav` context processor. Active state is resolved against `request.resolver_match.url_name`.

**Component partials** under `templates/components/`: `_page_header`, `_stat_card`, `_pill`, `_empty_state`, `_form_field`, `_flash_messages`, `_pagination`, `_filter_bar`. Each documents variables in its top comment.

**Icons** under `templates/icons/` as inline SVG snippets — included as `{% include "icons/"|add:name|add:".html" %}`.

**HTMX partials** (e.g. `templates/incidents/_list_rows.html`) must NOT extend a base. For views whose sole purpose is a partial, mix in `apps.core.mixins.HtmxOnlyMixin` — returns 400 on non-HTMX requests. For dual-template views (full page on normal GET, partial on `HX-Request`), override `get_template_names()` using `self.request.htmx`.

## OpenSpec

Feature planning lives in `/openspec/changes/`. Refer to `tasks.md` for the implementation checklist and individual specs in the `specs/` directory for feature details.
