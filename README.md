<p align="center">
  <img src="static/favicon.svg" alt="Crane logo" width="128" height="128">
</p>

<h1 align="center">Crane</h1>

<p align="center">
  Open-source collaborative OSINT platform for capturing, organizing,
  and analyzing online evidence.
</p>

Multi-tenant Django app (Org → Project → Incident) with a Chrome
browser extension for one-click capture.

- **Backend**: Django 6.0.4, Python 3.12, PostgreSQL 16
- **Frontend**: Tailwind CSS v4 (standalone CLI, no Node) + HTMX + Alpine.js
- **Extension**: Chrome MV3, TypeScript, esbuild

See [`CLAUDE.md`](CLAUDE.md) for architecture and conventions.

## Prerequisites

- Python 3.12
- Docker + Docker Compose (PostgreSQL runs in a container on port **5433**)
- Node.js 18+ — only if you build the browser extension

Linux is the supported dev OS; the Tailwind binary download in
`run_dev.sh` is `tailwindcss-linux-x64`.

## Quick start

```bash
./run_dev.sh
```

The script is idempotent and does the following:

1. Downloads the Tailwind standalone binary into `bin/` (first run only).
2. Builds `static/css/crane.css`.
3. Starts the PostgreSQL container (`docker compose up -d db`).
4. Creates `.venv/` and installs `requirements.txt`.
5. Runs migrations.
6. Creates a superuser `admin@crane.local` / `admin` if none exists.
7. Starts `manage.py runserver` on `http://localhost:8000`.

After it boots:

- App: <http://localhost:8000>
- Admin: <http://localhost:8000/admin/> (`admin@crane.local` / `admin`)

### Clean reset with demo data

```bash
./run_dev.sh --clean
```

Drops the PostgreSQL volume, recreates the database, runs migrations,
and seeds the **International Crane Foundation** demo organization with
the **Bird Trade Central Asia** project, reference data (platforms,
languages, keyword categories, custom fields, keywords), and these
test accounts:

| Email                       | Password      | Org role | Project role |
| --------------------------- | ------------- | -------- | ------------ |
| `admin@crane.local`         | `admin`       | OWNER    | COORDINATOR  |
| `coordinator@crane.local`   | `coordinator` | MEMBER   | COORDINATOR  |
| `volunteer1@crane.local`    | `volunteer1`  | MEMBER   | VOLUNTEER    |
| `volunteer2@crane.local`    | `volunteer2`  | MEMBER   | VOLUNTEER    |

## Manual setup

If you'd rather skip the script:

```bash
docker compose up -d db
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL=postgres://crane:crane@localhost:5433/crane
python manage.py migrate --run-syncdb
python manage.py createsuperuser
python manage.py seed_icf       # optional — demo data
python manage.py runserver
```

The full Docker stack (web + db) also works if you don't want a local
venv:

```bash
docker compose up
```

## Common tasks

### Database

```bash
python manage.py makemigrations
python manage.py migrate --run-syncdb
python manage.py seed_icf                # ICF demo org + 3 test accounts
python manage.py seed_icf --admin-email me@example.com --admin-password s3cret
```

To wipe the DB and start over: `docker compose down -v` (or use
`./run_dev.sh --clean`).

### Tailwind CSS

```bash
# One-shot build (run_dev.sh does this for you)
./bin/tailwindcss -i static/css/crane.src.css -o static/css/crane.css --minify

# Watch while editing templates
./bin/tailwindcss -i static/css/crane.src.css -o static/css/crane.css --watch
```

Design tokens live in the `@theme` block of `static/css/crane.src.css`;
reusable component classes are under `@layer components`. Compiled
`crane.css` is committed so Render deploys don't need the binary.

### Tests

Test docstrings follow **GIVEN / WHEN / THEN**.

```bash
python manage.py test                               # all
python manage.py test apps.core                     # one app
python manage.py test apps.core.tests.TestFoo       # one class
python manage.py test apps.core.tests.TestFoo.test_bar  # one method
```

## Browser extension

The Chrome MV3 extension lives under [`browser_extension/`](browser_extension/)
as a separate TypeScript codebase (not a Django app). It authenticates
via `chrome.identity.launchWebAuthFlow` against `/auth/extension-link/`
and talks to `/api/v1/`.

```bash
cd browser_extension
npm install              # one-time
npm run build            # one-shot → dist/
npm run dev              # watch mode
npm run typecheck        # tsc --noEmit
```

Load it into Chrome 114+ via `chrome://extensions` → **Developer
mode** → **Load unpacked** → select `browser_extension/` (the folder
with `manifest.json`, not `dist/`). See
[`browser_extension/README.md`](browser_extension/README.md) for the
full install/auth flow and message-protocol notes.

URL normalization rules in `browser_extension/src/shared/normalize-url.ts`
must stay in sync with `apps.incidents.utils.normalize_url`.

## Project layout

```
apps/
  core/         # User, Organization, Project, memberships, middleware, nav
  incidents/    # Incident model, capture views, duplicate detection
  keywords/     # Keyword model with status workflow
  coverage/     # SearchSession tracking
  api/          # /api/v1/ endpoints used by the extension
templates/
  base.html, base_app.html, base_auth.html, base_minimal.html
  components/   # _page_header, _stat_card, _pill, _empty_state, ...
  icons/        # inline SVG snippets
static/css/
  crane.src.css # Tailwind source (with @theme + @layer components)
  crane.css     # compiled output (committed)
browser_extension/  # Chrome MV3 extension (separate TypeScript codebase)
openspec/changes/   # feature planning (proposals, specs, tasks.md)
```

## URL structure

Tenant-aware routes follow `/{org-slug}/{project-slug}/...`. The
`OrgProjectMiddleware` (`apps/core/middleware.py`) resolves
`request.organization` and `request.project` from URL kwargs and
enforces membership. Exempt paths: `/auth/`, `/admin/`, `/api/`,
`/static/`, `/media/`, `/`.

## Deployment

Production uses Render with `render.yaml` (PostgreSQL via
`DATABASE_URL`, optional S3 media storage via `AWS_STORAGE_BUCKET_NAME`
and `django-storages`). The compiled `static/css/crane.css` is
committed so Render builds don't need the Tailwind binary.
