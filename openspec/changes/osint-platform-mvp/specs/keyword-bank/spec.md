## ADDED Requirements

### Requirement: Keyword CRUD within project
The system SHALL allow coordinators to create, edit, and delete keywords. Each keyword has: term, language, category (sale/purchase/hunting/transport/slang/market/species-specific), platform_relevance (list of platforms), and status (active/deprecated/candidate).

#### Scenario: Coordinator adds keyword
- **WHEN** a coordinator creates a keyword with term "crane for sale", language "English", category "sale"
- **THEN** the keyword is created with status "active" and attributed to the coordinator

#### Scenario: Coordinator deprecates keyword
- **WHEN** a coordinator changes a keyword's status from "active" to "deprecated"
- **THEN** the keyword no longer appears in volunteer search playbooks but remains in the database for historical reference

### Requirement: Volunteers propose keywords
The system SHALL allow volunteers to propose new keywords they discover during monitoring. Proposed keywords are created with status "candidate" and require coordinator approval to become "active".

#### Scenario: Volunteer proposes a keyword
- **WHEN** a volunteer submits a new keyword "koonj bechna hai" with language "Urdu" and category "sale"
- **THEN** the keyword is created with status "candidate" and the coordinator is notified

#### Scenario: Coordinator approves candidate
- **WHEN** a coordinator changes a candidate keyword's status to "active"
- **THEN** the keyword appears in search playbooks and can be linked to incidents

### Requirement: Effectiveness tracking
The system SHALL track how many incidents each keyword has been linked to (match_count). The keyword list view SHALL be sortable by match_count to identify the most and least effective keywords.

#### Scenario: Keyword linked to incident
- **WHEN** a volunteer creates an incident and selects "crane for sale" as the matched keyword
- **THEN** the match_count for "crane for sale" increments by one

#### Scenario: Sort by effectiveness
- **WHEN** a coordinator views the keyword bank sorted by match_count descending
- **THEN** keywords with the most incident matches appear first

### Requirement: Filter and search keywords
The system SHALL allow filtering keywords by: language, category, status, platform_relevance. Text search SHALL match against the term field.

#### Scenario: Filter by language
- **WHEN** a coordinator filters keywords by language "Kyrgyz"
- **THEN** only Kyrgyz-language keywords are shown

### Requirement: Keyword sharing across projects
The system SHALL allow keywords to be marked as "shared" within an organization. Shared keywords are visible (read-only) to all projects in the same organization.

#### Scenario: Share keyword across projects
- **WHEN** a coordinator marks keyword "crane for sale" as shared in org "ICF"
- **THEN** the keyword appears in keyword banks of all projects under org "ICF"

### Requirement: Bulk keyword import
The system SHALL allow coordinators to import keywords from a CSV file with columns: term, language, category. This enables seeding a new project with an existing keyword list.

#### Scenario: Import keyword CSV
- **WHEN** a coordinator uploads a CSV with 50 keywords
- **THEN** the system creates all 50 keywords with status "active", skipping duplicates (same term + language in the same project)
