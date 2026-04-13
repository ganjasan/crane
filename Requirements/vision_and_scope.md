# Vision and Scope: Open Source Collaborative OSINT Platform

**Version:** 3.0
**Date:** 2026-04-13

---

# Part I — The Platform

## 1. Problem Statement

Organizations worldwide need to monitor public online platforms for specific signals: illegal wildlife trade, trafficking of cultural artifacts, illegal logging, counterfeit goods, IUU fishing, and more. These monitoring efforts share a common pattern:

- **Distributed volunteers** — native speakers who know the language, culture, and platforms where activity happens
- **Manual search** — guided by keyword lists and playbooks, across multiple platforms and languages
- **Evidence capture** — screenshots, URLs, timestamps, structured metadata
- **Coordination** — knowing what has been searched and what hasn't, avoiding duplication, balancing effort
- **Reporting** — aggregated intelligence for enforcement agencies, policymakers, or the public

Today, these efforts are ad hoc. Teams use spreadsheets, shared folders, and chat groups. There is no way to know what has been covered and what hasn't. Each new volunteer requires manual onboarding. Each new region or language starts from scratch.

**Existing OSINT tools do not solve this problem.** Maltego, SpiderFoot, and Hunchly are designed for individual technical analysts conducting investigations. They do not support:

- Non-technical users who need guided workflows
- Distributed teams that need coordinated coverage
- Multilingual keyword management as a first-class concept
- Systematic search tracking (what was searched, when, by whom, on which platform)
- Structured evidence collection with domain-specific annotation

**The gap:** There is no open-source platform for collaborative, systematic OSINT by non-technical distributed teams.

---

## 2. Vision Statement

> An open-source platform that enables distributed teams of non-technical volunteers to **systematically monitor online platforms, capture structured evidence, and produce actionable intelligence** — turning ad hoc manual searches into coordinated operations with full coverage tracking.

---

## 3. Platform Architecture

### 3.1 Hierarchy

```
Platform
└── Organization (ICF, WWF, Forest Watch, ...)
     ├── Members & Roles (admin, coordinator, volunteer)
     └── Project (Bird Trade Central Asia, Timber Trade SE Asia, ...)
          ├── Data Schema (core fields + project-specific extensions)
          ├── Keyword Banks (per language, per category)
          ├── Search Playbooks (platform × language × keyword set)
          ├── Coverage Matrix (assignments, completions, gaps)
          ├── Evidence Store (screenshots, captures)
          ├── Volunteer Assignments (who does what, when)
          └── Reports & Dashboards
```

### 3.2 Core Data Schema

Every evidence record, regardless of domain, contains:

| Field | Description | Captured by |
|-------|-------------|-------------|
| Record ID | Unique identifier | Auto-generated |
| Platform | Where the post was found | Auto-detected from URL |
| URL | Direct link to the post | Auto-captured |
| Screenshot | Visual evidence | Auto-captured (extension) |
| Date of Post | When the original post appeared | Volunteer enters |
| Date Collected | When evidence was captured | Auto-timestamped |
| Location Mentioned | Location stated in the post | Volunteer enters |
| Probable Location | Inferred from profile/language | Volunteer enters |
| Language Used | Language of the post | Volunteer selects |
| Keywords Matched | Which keyword led to this find | Auto / volunteer |
| Confidence | Volunteer's confidence in relevance | Volunteer selects |
| Notes | Free-text context | Volunteer enters |

**Project-specific extensions** add domain fields. For wildlife trade: species, price, quantity, seller type, trade type. For timber trade: wood species, volume, certification claims. The core is always the same.

### 3.3 Keyword Bank

A structured, collaborative, multilingual resource:

| Field | Description |
|-------|-------------|
| Term | The keyword or phrase |
| Language | Language of the term |
| Category | Domain-specific grouping (e.g., "sale", "hunting", "transport") |
| Platform Relevance | Which platforms this keyword is effective on |
| Added By | Who contributed the keyword |
| Date Added | When it was added |
| Match Count | How many evidence records this keyword has led to |
| Status | Active / deprecated / candidate |

Keywords can be shared across projects within an organization (e.g., "crane for sale" is useful for any crane-related project). Volunteers contribute new terms they discover during monitoring — the bank is a living resource.

### 3.4 Search Coverage Matrix

The key innovation that makes volunteer work **systematic** rather than ad hoc.

The platform tracks a matrix of:

| Dimension | Example Values |
|-----------|---------------|
| Platform | Facebook, Telegram, VK, OLX, TikTok, ... |
| Language / Region | Kyrgyz, Hindi, Russian, Bengali, ... |
| Keyword Category | Sale, purchase, hunting, transport, slang, ... |
| Time Period | Current week / month |

The coordinator sees at a glance:
- Which cells have been searched recently and which are stale
- Which volunteers are most productive on which platforms
- Where to direct effort next

This transforms monitoring from "everyone searches whatever they feel like" into **targeted, gap-driven intelligence collection**.

---

## 4. Generic Workflow

The same 8-step cycle regardless of domain:

```
┌─────────────────────────────────────────────────────────┐
│ 1. Coordinator creates search assignments               │
│    (platform × language × keyword set × volunteer)      │
│                        ↓                                │
│ 2. Volunteer receives assignment with playbook           │
│    (step-by-step guide for this platform/language)       │
│                        ↓                                │
│ 3. Volunteer searches using keyword bank                 │
│                        ↓                                │
│ 4. Finds relevant post → one-click evidence capture      │
│    (screenshot + URL + metadata, automatic)              │
│                        ↓                                │
│ 5. Structured annotation form                            │
│    (pre-filled where possible, domain-specific fields)   │
│                        ↓                                │
│ 6. Coverage matrix updated                               │
│    ("I searched these keywords on this platform today")  │
│                        ↓                                │
│ 7. Deduplication & aggregation                           │
│    (same post captured by two volunteers → merged)       │
│                        ↓                                │
│ 8. Reporting & analysis                                  │
│    (dashboards, exports, trend analysis)                 │
└─────────────────────────────────────────────────────────┘
```

---

## 5. What Makes This Different

| Existing OSINT Tools | This Platform |
|---------------------|---------------|
| For technical analysts | For non-technical volunteers |
| Individual use | Collaborative, team-based |
| Investigation-driven (start from a lead) | Systematic monitoring (cover everything) |
| No coverage tracking | Coverage matrix is a core concept |
| English-centric | Multilingual keyword banks as first-class feature |
| Desktop-first | Mobile-friendly, works on slow internet |
| Commercial or complex setup | Open-source, single VPS deployment |

---

## 6. Scalability Model

The platform is domain-agnostic. Different organizations configure it for their specific monitoring needs:

| Domain | What They Monitor | Project-Specific Fields |
|--------|------------------|------------------------|
| Wildlife trade | Illegal sale of protected species | Species, scientific name, trade term, CITES appendix |
| Timber trade | Illegal logging & timber sales | Wood species, volume, certification claims |
| Cultural artifacts | Trafficking of antiquities | Period, origin, artifact type, provenance claims |
| IUU fishing | Illegal catch sales | Fish species, catch method, vessel info |
| Counterfeit goods | Fake branded products | Brand, product type, price vs. authentic |
| Plant trade | CITES-listed orchids, cacti | Plant species, CITES appendix, wild vs. cultivated |

Same platform. Same workflow. Same codebase. Different configurations.

---

---

# Part II — First Deployment: ICF Illegal Bird Trade Monitoring

## 7. Project Context

The Central Asian Flyway supports **279 waterbird populations**, including **29 globally threatened species**. Population declines of 50–80% since 2000 are documented for many species (State of India's Birds 2023).

Illegal trade in cranes and waterbirds has shifted to online platforms where traders use anonymous networks, codewords, and emojis to evade detection.

The project is initiated by the **International Crane Foundation (ICF)** together with the **Central Asian Conservation Network (CACN)**, **YGPE**, and **Жаратылыш фонду**.

**Budget: zero.** The team is a distributed network of native-speaker volunteer interns and one developer with Claude Code.

---

## 8. Project-Specific Configuration

### 8.1 Organization

**ICF / CACN** — first organization on the platform.

### 8.2 Project: Bird Trade — Central Asian & South Asian Flyway

**Geographic scope:**
- Central Asia: Kazakhstan, Kyrgyzstan, Tajikistan, Turkmenistan, Uzbekistan, Afghanistan
- South Asia: Bangladesh, India, Pakistan

**Platforms to monitor:**
Facebook, Instagram, Telegram, TikTok, YouTube, X/Twitter, VK, OLX, Lalafo, and other websites or forums where birds are traded.

### 8.3 Domain-Specific Data Fields

In addition to the core schema, each evidence record includes:

| Field | Description | Example |
|-------|-------------|---------|
| Species Name | Common name of the species | Demoiselle Crane |
| Scientific Name | Taxonomic name | *Anthropoides virgo* |
| Common Trade Term | Local or slang name used in the post | "Koonj" |
| Species Group | Crane / Waterbird / Other bird | Crane |
| Purpose of Trade | Reason mentioned or inferred | Pet, meat, hunting, falconry |
| Quantity | Number of birds mentioned | 3 |
| Price | Price mentioned (with currency) | Rs 35,000 |
| Seller Type | Individual / trader / market / unknown | Individual |
| Media Evidence | Photo / video present in post | Yes |
| Image Verification | Confidence of species ID | High / Medium / Low |
| Trade Type | Sale / wanted / exchange / hunting | Sale |

### 8.4 Priority Species

**Cranes (Primary Focus):**

| Species | Scientific Name |
|---------|----------------|
| Siberian Crane | *Leucogeranus leucogeranus* |
| Demoiselle Crane | *Anthropoides virgo* |
| Eurasian Crane | *Grus grus* |
| Black-necked Crane | *Grus nigricollis* |
| Sarus Crane | *Grus antigone* |

**Ducks & Geese:** Bar-headed Goose, Greylag Goose, Ruddy Shelduck, Common Teal, Northern Pintail, Northern Shoveler, Gadwall, Eurasian Wigeon, Common Pochard, Ferruginous Duck, Tufted Duck, Red-crested Pochard, Baikal Teal, Falcated Duck.

**Waders & Shorebirds:** Black-tailed Godwit, Ruff, Common Snipe, Wood Sandpiper, Eurasian Curlew, Whimbrel, Marsh Sandpiper, Green Sandpiper, Temminck's Stint.

**Large Waterbirds:** Eurasian Spoonbill, Asian Openbill Stork, Painted Stork, Black-headed Ibis, Black Stork, White Stork, Great White Pelican, Dalmatian Pelican.

**Other Wetland Birds:** Purple/Grey-headed Swamphen, Common Coot, Common Moorhen, Pheasant-tailed Jacana, Bronze-winged Jacana, Little Cormorant.

### 8.5 Keyword Bank Seed Data

Initial keywords from the Technical Specifications document, organized by category:

**Direct sale:** crane for sale, cranes for sale, crane bird for sale, live crane for sale, sarus crane for sale, demoiselle crane for sale, crane chicks for sale, crane pair for sale, waterbirds for sale, wild birds for sale, exotic birds for sale, migratory birds for sale, wetland birds for sale.

**Purchase / demand:** buy crane, looking for crane, want to buy crane, crane wanted, crane bird needed, waterbird wanted, want to buy wild birds, looking for migratory birds, need crane pair, crane breeder.

**Price / advertisement:** crane price, crane bird price, sarus crane price, crane pair price, crane chicks price, best price crane, crane available now, crane ready for sale, cheap crane bird, crane deal.

**Market / trade networks:** bird market, wild bird market, live bird market, migratory bird market, crane bird market, exotic bird market, bird trader, bird dealer, bird supplier.

**Capture / hunting:** crane hunting, crane trapping, crane caught, captured crane, wild crane caught, migratory bird hunting, wetland bird hunting, crane hunting video, crane trap.

**Transport / shipment:** crane shipment, bird shipping available, crane delivery, live bird transport, crane export, crane import, birds transported.

**Social media slang:** available, inbox, DM for price, ready, contact, pair ready, breeder pair, farm birds.

**Languages to cover:** English, Russian, Hindi, Urdu, Kyrgyz, Tajik, Uzbek, Kazakh, Pashto, Bengali, local slang variants.

These are the seed data. The keyword bank grows as volunteers discover new terms during monitoring.

### 8.6 Out of Scope

- Dark web monitoring
- Private/encrypted channel infiltration (WhatsApp groups, private Telegram chats)
- Direct law enforcement actions or contact with sellers
- Automated species identification from images (Phase B consideration)

---

## 9. Stakeholders

| Stakeholder | Role | Key Need |
|-------------|------|----------|
| ICF | Project initiator | Conservation impact, policy data |
| CACN Steering Committee | Governance | Regional coordination, scientific rigor |
| Ella Mikusheva | WG Coordinator — Internship Programme | Clear protocols, quality control |
| Dr Madhumita Panigrahi | WG Coordinator — Database | Standardized data, interoperability |
| Katherine Hall & Khurshed Alimov | CACN Co-chairs | Strategic alignment |
| Dr Ramesh Kumar Selvaraj | Science Coordinator | Technical oversight, methodology |
| Project Coordinator | Operations | Unified database, reporting |
| Native-speaker Volunteers | **Primary intelligence source** | Minimal-friction tools, clear playbooks, immediate feedback |
| Developer (Artem) | Platform development & infrastructure | Maintainable, evolvable, open-source |

---

## 10. Phase A — Volunteer Tooling (Now)

### 10.1 The Problem Today

A volunteer gets an assignment: "search Facebook for crane trade in Kyrgyzstan." They open Facebook, type something, scroll, maybe find something, take a screenshot, paste it into a shared folder, fill out a spreadsheet row. Next week a new intern does the same thing with different keywords and misses what the first one found.

**Result:** inconsistent coverage, lost context, no way to know what's been searched and what hasn't.

### 10.2 What We Build

**A. Shared Incident Database** — replaces the Google Sheet

All evidence from all volunteers flows into one database:
- Structured records with core + domain-specific fields
- Deduplication (same post captured by two volunteers → merged)
- Search log: what was searched, when, by whom, on which platform
- Replaces manual spreadsheet with a purpose-built tool

**B. Quick Annotation Form** — appears after evidence capture

Pre-filled where possible. Volunteer adds:
- Species (dropdown with common + trade names in their language)
- Price, quantity, location (if visible)
- Trade type, confidence level
- Free-text notes

Designed for phone and slow internet. Works offline, syncs later.

**C. Multilingual Keyword Bank** — living, collaborative resource

- Structured keyword lists per language, grouped by category
- Volunteers contribute new terms they discover
- Effectiveness tracking: which keywords actually find trade posts?
- Shareable across projects

**D. Search Coverage Matrix + Coordinator Dashboard**

- Visual matrix: platform × language × keyword category × time period
- Coordinator sees gaps at a glance and directs volunteer effort
- Activity tracking per volunteer
- Incidents per week/month trends

**E. One-Click Evidence Capture** — browser extension / bookmarklet

Volunteer finds a suspicious post → clicks one button → system captures:
- Full-page screenshot (including username, date, image)
- URL
- Timestamp
- Platform (auto-detected)
- Volunteer ID

No manual screenshot + rename + upload + spreadsheet entry. One click.

**F. Onboarding Kit**

- 15-minute video walkthrough
- One-page quick-start guide per platform
- Practice exercise: "find these 3 known trade posts"
- FAQ: what counts as trade evidence, what to skip

---

## 11. Phase B — Automation (Future)

Built on the data accumulated in Phase A:

| Accumulated Asset | Enables |
|-------------------|---------|
| Hundreds of labeled trade posts | Train/prompt LLM classifier ("is this trade-related?") |
| Keyword bank with effectiveness data | Automated keyword search on platforms with APIs (Telegram, VK) |
| Known seller accounts | Automated monitoring of specific accounts for new posts |
| Platform-specific patterns | Targeted scrapers for high-yield sources (OLX, Lalafo) |
| Species name ↔ trade term mappings | Automated entity extraction from post text |
| Screenshot corpus with species labels | Potential image classification model |
| Search coverage data | Smart task assignment: auto-suggest what to search next |

**Phase B does not replace volunteers.** It amplifies them — automation handles the high-volume, repetitive searches while volunteers focus on nuanced cases, new platforms, and cultural context that machines miss.

---

## 12. Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Database | PostgreSQL | Structured, reliable, free, extensible schema |
| Web application | Django + HTMX | Built-in auth, admin, forms, ORM; lightweight frontend |
| Browser extension | Chrome/Firefox extension | One-click evidence capture |
| Keyword bank | DB table with web UI | Collaborative, version-tracked, searchable |
| Screenshot storage | AWS S3 | Industry standard, django-storages integration |
| Deployment | Render | Zero-config from Git, free tier available, managed DB |
| Development | Claude Code | Rapid development by single developer |

The platform is open-source and self-hostable (Docker Compose). Organizations can connect their own storage backends (Google Drive, Google Sheets) for data export and evidence storage.

---

## 13. Success Criteria (ICF Deployment)

| Metric | Target |
|--------|--------|
| Documented trade incidents | 100+ in first 3 months |
| Search coverage | All platform–language combinations searched at least monthly |
| Volunteer retention | 70%+ of onboarded volunteers active after 2 months |
| Keyword bank growth | 500+ keywords across all languages |
| Platform coverage | At least 5 platforms with regular monitoring |
| Species coverage | All 5 priority crane species detected at least once |
| Geographic coverage | Incidents documented from at least 4 countries |
| Report delivered | Analytical report within 6 months |
| Data quality | 90%+ of records have all mandatory fields filled |
| Google Sheet replaced | Team fully transitioned to platform within 1 month of launch |

---

## 14. Constraints and Risks

| Risk | Mitigation |
|------|------------|
| Volunteer motivation drops | Show impact: weekly stats, "your find led to X"; keep tasks short and clear |
| Inconsistent data quality | Structured forms with dropdowns minimize free-text; coordinator reviews flagged entries |
| Posts deleted before capture | Browser extension captures screenshot immediately; don't rely on URLs persisting |
| Traders shift to private channels | Log references to private channels; focus on public entry points |
| Platform blocks or UI changes | Extension is lightweight, easy to update; manual fallback always works |
| Single developer bus factor | Open-source, clean code, documented architecture; Claude Code can onboard a new developer |
| Keyword lists incomplete for some languages | Recruit native speakers; use Claude to generate candidates; validate with volunteers |
| Zero budget | Use only free/open-source tools; Render free tier + AWS S3 free tier |
| Scope creep into automation too early | Phase A must prove value before Phase B begins; resist premature optimization |

---

## 15. Ethical and Data Protection Guidelines

- Only publicly available posts are monitored
- No infiltration of private groups or encrypted channels
- Personal data minimized — store seller identifiers only when trade evidence is confirmed
- Screenshots exclude private contact information where possible
- Data used only for research and conservation enforcement support
- Evidence maintains chain-of-custody integrity for potential use by authorities
- Volunteers briefed on ethical guidelines during onboarding
- Platform provides audit trail: who accessed what data, when
