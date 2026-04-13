## Why

Distributed volunteer teams monitoring online platforms for illegal activity (wildlife trade, artifact trafficking, etc.) work with spreadsheets, shared folders, and chat groups. There is no way to know what has been searched and what hasn't. Each new volunteer starts from scratch. Each new region or language requires reinventing the workflow. No open-source platform exists for collaborative, systematic OSINT by non-technical distributed teams. ICF/CACN needs this now — their interns are already working with a manual Google Sheet that doesn't scale.

## What Changes

This is a greenfield MVP. A web platform with:

- **Multi-tenant hierarchy**: Organization → Project, with members and roles
- **Incident database**: Structured evidence records with core schema + project-specific extensions, replacing the Google Sheet
- **Evidence capture**: Browser extension for one-click screenshot + URL + metadata capture
- **Annotation form**: Mobile-friendly structured form with dropdowns, works offline, syncs later
- **Multilingual keyword bank**: Collaborative, per-language, per-category, with effectiveness tracking
- **Search coverage matrix**: Tracks who searched what, where, when — exposes gaps, enables systematic coordination
- **Coordinator dashboard**: Coverage gaps, volunteer activity, incident trends at a glance
- **Project configuration**: Domain-specific fields, species taxonomies, keyword seed data — all configurable per project

First deployment: ICF Bird Trade monitoring (Central Asian + South Asian Flyway).

## Capabilities

### New Capabilities

- `multi-tenancy`: Organization → Project hierarchy. Members with roles (admin, coordinator, volunteer). Invitation flow. A user can belong to multiple organizations and projects.
- `incident-database`: Core evidence records (platform, URL, screenshot, dates, location, language, keywords, confidence, notes) + project-specific extension fields. CRUD, search, filtering, deduplication detection.
- `evidence-capture`: Browser extension (Chrome/Firefox) for one-click capture — auto-captures screenshot, URL, timestamp, platform detection, volunteer ID. Opens annotation form after capture.
- `annotation-form`: Structured form with core + domain-specific fields. Dropdowns populated from project config (species, trade types, etc.). Mobile-friendly. Offline-capable with sync.
- `keyword-bank`: Per-project multilingual keyword management. Fields: term, language, category, platform relevance, added by, date, match count, status. Volunteers can propose new keywords. Shareable across projects within an organization.
- `search-coverage`: Matrix of (platform × language × keyword category × time period). Volunteers log what they searched. Coordinator sees gaps. Drives assignment suggestions.
- `coordinator-dashboard`: Visual overview — coverage heatmap, volunteer activity, incidents per period, data quality flags, unreviewed entries queue.
- `project-config`: Admin UI for configuring project-specific data schema extensions, species/item taxonomies, keyword seed import, platform list, geographic scope.

### Modified Capabilities

(none — greenfield project)

## Impact

- **New codebase**: Django + HTMX backend, PostgreSQL database, browser extension
- **Infrastructure**: Render (web + DB), AWS S3 for screenshots
- **Users**: ICF/CACN volunteers (first deployment), potentially other organizations later
- **Dependencies**: Zero budget constraint — all components must be free/open-source
- **External systems**: Social media platforms (read-only, public posts only)
