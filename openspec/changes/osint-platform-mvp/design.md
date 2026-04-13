## Context

ICF/CACN needs to replace a manual Google Sheet workflow for monitoring illegal bird trade on social media. Volunteers search platforms, take screenshots, fill in spreadsheet rows. No coverage tracking, no deduplication, no coordination.

We're building an open-source collaborative OSINT platform — generic enough for any domain (wildlife trade, artifact trafficking, IUU fishing), with ICF bird trade as the first deployment. See `Requirements/vision_and_scope_v3.md` and `proposal.md`.

**Current state:** Greenfield. No existing codebase.

**Constraints:**
- Zero budget — all tools free/open-source, free-tier hosting
- Single developer (Artem) with Claude Code
- Primary users are non-technical volunteers on phones with slow internet
- Multi-language (10+ languages including Kyrgyz, Tajik, Uzbek)

**Reference architecture:** Expecto project (`/home/artem/Documents/Projects/expecto`) provides a proven multi-tenancy pattern (Organization → Project, membership with roles, org-scoped queries). We adapt its isolation patterns to Django.

---

## Goals / Non-Goals

**Goals:**
- Replace Google Sheet with a structured incident database
- Provide search coverage tracking so coordinators see gaps
- Make volunteer workflow as frictionless as possible (one-click capture, quick form)
- Multi-tenant from day one (Organization → Project)
- Mobile-friendly, works on slow connections
- Deploy on Render free/starter tier
- Open-source, self-hostable

**Non-Goals:**
- No SPA / React frontend — server-rendered HTML + HTMX
- No automated scraping (Phase B)
- No ML/NLP classification (Phase B)
- No real-time features (WebSockets, live updates)
- No mobile native app — responsive web only
- No Auth0 / external auth provider — Django built-in auth (zero budget)
- No internationalization of UI in v1 — English UI, multilingual data

---

## Decisions

### D1: Django over FastAPI

**Choice:** Django 5.x

**Why:**
- Built-in auth, admin, ORM, forms, migrations — dramatically less boilerplate
- Django admin gives a "free" coordinator interface from day one
- Forms framework handles validation, dropdowns, file uploads natively
- Battle-tested permission system
- django-storages for S3, django-allauth for future social auth
- HTMX integrates naturally with Django's template engine

**Alternatives considered:**
- FastAPI + SQLAlchemy (as in expecto): More flexible, but requires building auth, admin, forms from scratch. Too much work for a solo dev with zero budget.
- Rails: Strong contender, but Artem's stack is Python.

### D2: HTMX + Alpine.js + Tailwind CSS for frontend

**Choice:** Server-rendered Django templates with HTMX for interactivity, Alpine.js for small client-side state, Tailwind for styling.

**Why:**
- No JavaScript build pipeline needed (Tailwind via CDN or standalone CLI)
- Pages work without JS (progressive enhancement) — critical for slow connections
- HTMX gives SPA-like UX (partial page updates) with zero client-side state management
- Alpine.js handles dropdowns, modals, toggles without a framework
- Small page sizes — important for mobile on 3G

**Alternatives considered:**
- React SPA: Heavy, requires API layer, build pipeline, client-side auth. Overkill.
- Vanilla JS: Works but painful for dynamic forms and partial updates.

### D3: Multi-tenancy via org_id FK (shared database)

**Choice:** Single database, `organization_id` foreign key on every tenant-scoped model. Adapted from expecto pattern.

**Why:**
- Simplest to implement and maintain
- Single database = single backup, single migration path
- Adequate for expected scale (tens of organizations, not thousands)
- Proven pattern in expecto

**Tenant isolation layers:**
1. **Database:** `organization_id` FK + org-scoped unique constraints
2. **ORM:** Custom manager/queryset that filters by org automatically
3. **Middleware:** Resolves current org + project from URL, attaches to `request`
4. **Views:** All querysets filtered through `request.organization`

**URL-based context (not header-based):**
```
/                                    → landing / org selector
/{org-slug}/                         → org dashboard
/{org-slug}/{project-slug}/          → project dashboard
/{org-slug}/{project-slug}/incidents → incident list
/{org-slug}/{project-slug}/keywords  → keyword bank
/{org-slug}/{project-slug}/coverage  → coverage matrix
```

Why URL-based instead of expecto's `X-Organization-Id` header:
- No API client to configure — works in plain browser
- Bookmarkable — volunteer can bookmark their project page
- Shareable — coordinator sends a link, it just works
- SEO-friendly (not that we need SEO, but it's cleaner)

### D4: Role model — simplified from expecto

**Choice:** Three-level roles, no PermissionGrant table in MVP.

**Organization roles:**
| Role | Can do |
|------|--------|
| owner | Everything + delete org + manage billing (future) |
| admin | Manage members, create projects, configure org |
| member | Access projects they're assigned to |

**Project roles:**
| Role | Can do |
|------|--------|
| coordinator | Full project access: manage members, keywords, assignments, review incidents, see dashboard |
| volunteer | Submit incidents, log searches, propose keywords, see own submissions |

Stored as:
```python
class OrganizationMembership:
    user, organization, role  # owner/admin/member

class ProjectMembership:
    user, project, role  # coordinator/volunteer
```

**Why simpler than expecto:**
- Expecto has API keys, data providers, fine-grained PermissionGrants — we don't need any of that
- Three roles cover all use cases described in V&S
- Can always add PermissionGrant-style granularity later if needed

### D5: Data model — core + JSONField extensions

**Choice:** Core incident fields as proper columns, project-specific fields in a JSONField.

```python
class Incident(models.Model):
    # Core (every domain)
    organization = FK(Organization)
    project = FK(Project)
    record_id = CharField(unique per project, auto-generated)
    platform = FK(Platform)
    url = URLField()
    screenshot = FileField()  # → S3
    date_of_post = DateField(null=True)
    date_collected = DateTimeField(auto_now_add=True)
    collected_by = FK(User)
    location_mentioned = CharField()
    probable_location = CharField()
    language = CharField()
    keywords_matched = M2M(Keyword)
    confidence = CharField(choices=[high, medium, low])
    notes = TextField()
    status = CharField(choices=[draft, submitted, reviewed, flagged])

    # Domain-specific (configured per project)
    extra_fields = JSONField(default=dict)
    # For ICF: {"species_name": "Demoiselle Crane", "scientific_name": "Anthropoides virgo",
    #           "trade_term": "Koonj", "species_group": "crane", "purpose": "pet",
    #           "quantity": 3, "price": "Rs 35000", "seller_type": "individual",
    #           "media_evidence": true, "image_verification": "high", "trade_type": "sale"}
```

**Why JSONField:**
- Core fields get proper columns, indexes, constraints — they're queried heavily
- Domain fields vary per project and evolve quickly — JSON avoids constant migrations
- Django's JSONField supports lookups: `Incident.objects.filter(extra_fields__species_name="Demoiselle Crane")`
- PostgreSQL JSONB is fast with GIN indexes

**Alternative considered:**
- EAV (Entity-Attribute-Value): Flexible but terrible query performance and complex code.
- Separate model per domain: Not configurable, requires code changes per deployment.

### D6: Project-specific schema configuration

**Choice:** A `ProjectFieldConfig` model that defines which extra fields appear in the annotation form for a given project.

```python
class ProjectFieldConfig(models.Model):
    project = FK(Project)
    field_name = CharField()       # "species_name"
    field_type = CharField()       # "choice", "text", "number", "boolean"
    label = CharField()            # "Species Name"
    required = BooleanField()
    choices = JSONField(null=True)  # ["Demoiselle Crane", "Siberian Crane", ...]
    order = IntegerField()
```

The annotation form is dynamically generated from this configuration. Coordinator sets it up once, volunteers see the right fields.

### D7: Keyword bank with effectiveness tracking

```python
class Keyword(models.Model):
    project = FK(Project)
    term = CharField()
    language = CharField()
    category = CharField()     # sale, purchase, hunting, transport, slang
    platform_relevance = JSONField()  # ["facebook", "telegram"]
    added_by = FK(User)
    date_added = DateTimeField(auto_now_add=True)
    status = CharField()       # active, deprecated, candidate
    shared = BooleanField()    # visible to other projects in same org

    @property
    def match_count(self):
        return self.incident_set.count()
```

Keywords can be shared across projects within the same organization. Volunteers can propose keywords (status=candidate), coordinators approve (status=active).

### D8: Search coverage tracking

```python
class SearchSession(models.Model):
    project = FK(Project)
    volunteer = FK(User)
    platform = FK(Platform)
    language = CharField()
    keyword_categories = JSONField()  # ["sale", "hunting"]
    date = DateField()
    duration_minutes = IntegerField(null=True)
    incidents_found = IntegerField(default=0)
    notes = TextField(blank=True)
```

The coverage matrix view aggregates SearchSessions into a heatmap:
- Rows: platform × language
- Columns: keyword categories
- Cells: last searched date, color-coded (green=recent, yellow=stale, red=never)

Coordinator clicks a gap → creates an assignment.

### D9: Screenshot storage

**Choice:** django-storages with AWS S3.

**Why S3:**
- Industry standard, reliable, well-documented
- django-storages has first-class S3 support
- Same code works with any S3-compatible backend (MinIO for self-hosted)
- Free tier: 5 GB storage, 20K GET, 2K PUT/month — sufficient for MVP

**Future: pluggable storage backends.** Organizations should be able to connect their own storage (Google Drive, Dropbox, etc.) for screenshots and export data to their own systems (Google Sheets). This is a post-MVP feature but the architecture should not preclude it — django-storages backend abstraction makes this achievable.

**Fallback:** Local filesystem via Django's default FileSystemStorage for development.

### D10: Browser extension — immediate next step after web MVP

**Choice:** Build the web application first, then the browser extension as the next priority.

**Why web first:**
- Web app is the foundation — extension submits to its API
- Volunteers can start with manual screenshots + web form
- Need API endpoints defined before extension can call them

**Extension architecture:**
- Manifest V3 (Chrome + Firefox)
- Content script: "Capture" button overlay on supported platforms
- Captures: `html2canvas` screenshot, current URL, page metadata
- Posts to `/api/v1/incidents/capture` endpoint with auth token
- Opens annotation form in popup or new tab
- This is a high-priority follow-up, not a distant future item

### D11: Authentication

**Choice:** Django built-in auth with email as username.

**Signup flow:**
1. Coordinator creates organization + project
2. Coordinator invites volunteers by email → generates invite link
3. Volunteer clicks link → creates account → auto-added to project as volunteer

**Why not Auth0/social auth in MVP:**
- Zero budget
- Volunteers may not have Google/GitHub accounts
- Simple email + password is universally understood
- django-allauth can be added later for social auth

### D12: Deployment on Render

**Choice:** Render platform.

```
Services:
  - Web Service: Django + gunicorn (free tier or Starter $7/mo)
  - Database: Render PostgreSQL (free tier: 256 MB, 90-day retention)
  - Static/media: AWS S3 (screenshots + static files)
```

**Why Render:**
- Zero-config deployment from Git (push to deploy)
- Free tier available for getting started
- Managed PostgreSQL — no database administration
- Auto-SSL, custom domains
- Easy scaling when needed
- render.yaml Blueprint for reproducible infrastructure

**Self-hosted option:** Docker Compose remains available for organizations that want to run their own instance. The app is standard Django — it runs anywhere.

---

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| JSONField for domain fields loses type safety | ProjectFieldConfig validates at form level; core fields stay as proper columns |
| URL-based multi-tenancy adds middleware complexity | Well-tested pattern in Django (django-tenants uses similar approach); middleware is ~30 lines |
| No JS build pipeline means limited interactivity | HTMX + Alpine.js cover 95% of needs; browser extension is separate JS project |
| Render free tier has cold starts / spin-down | Acceptable for MVP; upgrade to Starter ($7/mo) when volunteers are active daily |
| Django admin as coordinator tool is limited | Custom views for coverage matrix and dashboards; admin handles CRUD well enough for MVP |
| No custom storage backends in MVP | Architecture uses django-storages abstraction; Google Drive/Sheets integration is a clean post-MVP add |
| No offline support in web MVP | Annotation form is lightweight; works on 2G. True offline (service worker) is Phase A.2 |

---

## Migration Plan

Not applicable — greenfield project. Deployment steps:

1. `django-admin startproject` with standard layout
2. Define models, create migrations
3. Seed ICF bird trade data (species taxonomy, keyword bank from Technical Specifications)
4. Deploy to Render via render.yaml Blueprint
5. Coordinator creates org + project, invites test volunteers
6. Iterate based on feedback

**Rollback:** Git revert + Render auto-redeploys from main branch.

---

## Open Questions

1. **Domain name / hosting:** Does ICF/CACN have a domain they want to use, or do we pick one?
2. **Existing Google Sheet data:** Is there data in the current sheet that needs to be migrated?
3. **Volunteer devices:** Primarily phones or laptops? This affects form layout priorities.
4. **Offline requirements:** How unreliable is connectivity for volunteers in Central Asia? Do we need service worker / PWA from day one?
5. **Evidence retention:** How long should screenshots be stored? Any legal requirements on retention period?
