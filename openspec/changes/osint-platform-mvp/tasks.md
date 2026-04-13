## 1. Project Bootstrap

- [x] 1.1 Create Django project (`osint_platform`) with standard layout: apps/, templates/, static/, manage.py
- [x] 1.2 Configure settings: PostgreSQL, AWS S3 via django-storages, HTMX, Tailwind CSS (standalone CLI)
- [x] 1.3 Create `render.yaml` Blueprint (web service + PostgreSQL)
- [x] 1.4 Create Dockerfile + docker-compose.yml for local development (Django + PostgreSQL)
- [x] 1.5 Set up initial migration and create superuser command

## 2. Multi-Tenancy: Models & Middleware

- [x] 2.1 Create `core` app with Organization model (name, slug, description)
- [x] 2.2 Create User model (extend AbstractUser, email as username)
- [x] 2.3 Create OrganizationMembership model (user, organization, role: owner/admin/member)
- [x] 2.4 Create Project model (organization FK, name, slug, description) with org-scoped uniqueness
- [x] 2.5 Create ProjectMembership model (user, project, role: coordinator/volunteer)
- [x] 2.6 Write OrgProjectMiddleware: resolve org + project from URL `/{org-slug}/{project-slug}/`, attach to `request.organization` and `request.project`, enforce membership
- [ ] 2.7 Create OrgScopedManager — custom queryset that auto-filters by `request.organization`
- [x] 2.8 Write permission mixins: `RequireOrgRole(role)`, `RequireProjectRole(role)`

## 3. Multi-Tenancy: Views & Auth

- [ ] 3.1 Registration view (email + password)
- [ ] 3.2 Login / logout views (Django built-in auth)
- [ ] 3.3 Organization creation view (post-registration)
- [ ] 3.4 Organization settings view (name, description — owner/admin only)
- [ ] 3.5 Organization member list + invite form (owner/admin only)
- [x] 3.6 Invitation model (email, org, project, role, token, expires_at) + send invite email
- [ ] 3.7 Accept invitation view (creates account if needed, adds membership)
- [ ] 3.8 Project creation view (within org — admin/owner only)
- [ ] 3.9 Project member list + assign role view (coordinator only)
- [ ] 3.10 Org selector page (`/` — list user's organizations)
- [ ] 3.11 Org dashboard page (`/{org-slug}/` — list projects)

## 4. Project Configuration

- [x] 4.1 Create Platform model (project FK, name, url_pattern for auto-detection)
- [x] 4.2 Create Language model (project FK, name, code)
- [x] 4.3 Create KeywordCategory model (project FK, name, slug)
- [x] 4.4 Create ProjectFieldConfig model (project FK, field_name, label, type, required, choices JSON, order)
- [x] 4.5 Create ProjectSettings model (project FK, record_id_prefix)
- [ ] 4.6 Project configuration view: manage platforms, languages, categories, custom fields (coordinator only)
- [ ] 4.7 Seed data import view: upload CSV for species list / keyword bank / platforms (coordinator only)

## 5. Incident Database

- [x] 5.1 Create `incidents` app
- [x] 5.2 Create Incident model: core fields (record_id, platform FK, url, screenshot FileField, date_of_post, date_collected, collected_by FK, location_mentioned, probable_location, language, confidence, notes, status) + extra_fields JSONField + organization FK + project FK
- [x] 5.3 Auto-generate record_id on save using project's prefix + sequential counter
- [ ] 5.4 Incident list view with filtering (platform, language, status, confidence, date range, collected_by) and text search — HTMX-powered
- [ ] 5.5 Incident detail view (read-only, shows all fields + screenshot)
- [ ] 5.6 Incident status workflow: draft→submitted (volunteer), submitted→reviewed (coordinator), any→flagged (coordinator)
- [x] 5.7 Duplicate detection: on save, check for existing incident with same URL in project, flag as potential duplicate
- [ ] 5.8 CSV export view: export filtered incidents with core + extra_fields flattened as columns (coordinator only)

## 6. Annotation Form

- [ ] 6.1 Build dynamic form class that reads ProjectFieldConfig and generates Django form fields at runtime
- [ ] 6.2 Create incident form view (new incident — manual entry): core fields + dynamic project-specific fields
- [ ] 6.3 Create incident edit view (edit draft / existing incident)
- [ ] 6.4 Pre-fill logic: if coming from extension capture, pre-fill platform, URL, screenshot from API-created draft
- [ ] 6.5 Save as draft button (skips required field validation)
- [ ] 6.6 Submit button (validates all required fields, sets status to "submitted")
- [ ] 6.7 Mobile-responsive form layout with Tailwind (stacked fields, large tap targets, 320px min)

## 7. Keyword Bank

- [x] 7.1 Create `keywords` app
- [x] 7.2 Create Keyword model (project FK, organization FK, term, language, category FK, platform_relevance JSON, added_by FK, date_added, status, shared boolean)
- [ ] 7.3 Keyword list view with filtering (language, category, status, platform) + text search + sort by match_count
- [ ] 7.4 Keyword create/edit view (coordinator: any status; volunteer: status=candidate only)
- [ ] 7.5 Keyword approval workflow: coordinator can change candidate→active or candidate→deprecated
- [ ] 7.6 Match count: M2M relation Incident↔Keyword, display count on keyword list
- [ ] 7.7 Keyword sharing: shared=true makes keyword visible (read-only) to all projects in org
- [ ] 7.8 Bulk import view: upload CSV (term, language, category), create keywords, skip duplicates

## 8. Search Coverage

- [x] 8.1 Create `coverage` app
- [x] 8.2 Create SearchSession model (project FK, volunteer FK, platform FK, language, keyword_categories JSON, date, duration_minutes, incidents_found, notes)
- [ ] 8.3 Log search form: compact form with platform, language, categories (multi-select), date (default today), incidents found, notes
- [ ] 8.4 Coverage matrix view: rows = platform × language, columns = keyword categories, cells = last search date, color-coded (green/yellow/red) — HTMX-powered
- [ ] 8.5 Matrix filtering: filter by platform, language, or category
- [ ] 8.6 Click gap cell → opens assignment creation form pre-filled with platform, language, category
- [ ] 8.7 Volunteer activity summary view: table with volunteer name, total sessions, incidents found, last active date

## 9. Coordinator Dashboard

- [ ] 9.1 Project dashboard view (`/{org-slug}/{project-slug}/`)
- [ ] 9.2 Summary cards: total incidents, incidents this week, active volunteers, coverage score (% cells searched in 30 days)
- [ ] 9.3 Recent incidents feed: last 20 incidents with status, platform, volunteer, date — links to detail
- [ ] 9.4 Review queue widget: count of status=submitted incidents, link to filtered list
- [ ] 9.5 Compact coverage heatmap widget (top gaps)
- [ ] 9.6 Keyword candidates widget: count of status=candidate keywords, link to filtered keyword bank
- [ ] 9.7 Data quality flags: incidents missing required extra_fields, no screenshot, duplicate URL

## 10. Evidence Capture API

- [ ] 10.1 Create `api` app with DRF or plain Django views
- [ ] 10.2 API token model: personal token per user, generated from account settings
- [ ] 10.3 Token authentication middleware for API endpoints
- [ ] 10.4 `POST /api/v1/incidents/capture` endpoint: accepts screenshot (file), URL, platform, title, timestamp; creates draft incident; returns incident ID + annotation form URL
- [ ] 10.5 Account settings page: generate / revoke API token

## 11. Browser Extension

- [ ] 11.1 Scaffold Chrome extension (Manifest V3): manifest.json, popup, content script
- [ ] 11.2 Extension settings: API token input, platform base URL
- [ ] 11.3 Content script: inject "Capture" floating button on supported platforms
- [ ] 11.4 Capture logic: html2canvas screenshot, extract URL, page title, detect platform from URL patterns
- [ ] 11.5 Submit capture to platform API endpoint, show success/error
- [ ] 11.6 On success: open annotation form URL in new tab
- [ ] 11.7 Firefox compatibility (manifest adjustments)

## 12. Templates & Styling

- [ ] 12.1 Base template with navigation: org switcher, project nav, user menu
- [ ] 12.2 Tailwind CSS setup (standalone CLI or CDN)
- [ ] 12.3 HTMX setup: include htmx.js, configure Django for partial responses
- [ ] 12.4 Mobile-responsive layout: sidebar collapses to hamburger menu on small screens
- [ ] 12.5 Common components: card, table with sort/filter, form layout, status badge, heatmap cell

## 13. Seed Data & First Deployment

- [ ] 13.1 Management command: seed ICF org + "Bird Trade Central Asia" project
- [ ] 13.2 Seed platforms: Facebook, Instagram, Telegram, TikTok, YouTube, X, VK, OLX, Lalafo
- [ ] 13.3 Seed languages: English, Russian, Hindi, Urdu, Kyrgyz, Tajik, Uzbek, Kazakh, Pashto, Bengali
- [ ] 13.4 Seed keyword categories: sale, purchase, hunting, transport, slang, market, species-specific
- [ ] 13.5 Seed project field config: species_name (choice), scientific_name (text), trade_term (text), species_group (choice), purpose (choice), quantity (number), price (text), seller_type (choice), media_evidence (boolean), image_verification (choice), trade_type (choice)
- [ ] 13.6 Seed species list from Technical Specifications (5 cranes + waterbird groups)
- [ ] 13.7 Seed keyword bank from Technical Specifications (English keywords as starting set)
- [ ] 13.8 Deploy to Render, verify all views work end-to-end
- [ ] 13.9 Create test accounts: one coordinator, two volunteers — run through full workflow
