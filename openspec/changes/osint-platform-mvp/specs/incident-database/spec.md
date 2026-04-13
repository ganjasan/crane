## ADDED Requirements

### Requirement: Incident record with core fields
The system SHALL store incident records with the following core fields: record_id (auto-generated, unique per project), platform, url, screenshot (file), date_of_post, date_collected (auto-timestamped), collected_by (current user), location_mentioned, probable_location, language, confidence (high/medium/low), notes, status (draft/submitted/reviewed/flagged).

#### Scenario: Create incident with core fields
- **WHEN** a volunteer submits an incident form with platform "Facebook", URL, screenshot, and location "Lahore"
- **THEN** the system creates a record with auto-generated record_id, date_collected set to now, collected_by set to the volunteer, and status "submitted"

#### Scenario: Auto-generated record ID
- **WHEN** an incident is created in project "Bird Trade Central Asia" which already has 42 incidents
- **THEN** the record_id is auto-generated in a sequential format (e.g., "BTCA-043")

### Requirement: Domain-specific extension fields
The system SHALL support project-specific fields stored in a JSON field (`extra_fields`). The structure of extra_fields is defined by the project's field configuration (see `project-config` capability).

#### Scenario: Incident with domain-specific fields
- **WHEN** a volunteer submits an incident in a bird trade project with extra_fields {"species_name": "Demoiselle Crane", "price": "Rs 35000", "trade_type": "sale"}
- **THEN** the system stores the extra_fields as JSON alongside the core fields

#### Scenario: Query by extra field
- **WHEN** a coordinator filters incidents by species_name = "Demoiselle Crane"
- **THEN** the system returns only incidents where extra_fields contains that species

### Requirement: Incident list with filtering and search
The system SHALL provide an incident list view with filtering by: platform, language, status, confidence, date range, collected_by. The list SHALL support text search across notes, location, and URL.

#### Scenario: Filter by platform and status
- **WHEN** a coordinator views incidents filtered by platform "Telegram" and status "submitted"
- **THEN** only Telegram incidents with status "submitted" are shown

#### Scenario: Search by keyword in notes
- **WHEN** a coordinator searches for "negotiation"
- **THEN** incidents containing "negotiation" in their notes field are returned

### Requirement: Incident status workflow
The system SHALL support the following status transitions: draft → submitted → reviewed, and any status → flagged. Volunteers can move draft → submitted. Coordinators can move submitted → reviewed or any → flagged.

#### Scenario: Volunteer submits draft
- **WHEN** a volunteer changes an incident from "draft" to "submitted"
- **THEN** the status is updated and the incident appears in the coordinator's review queue

#### Scenario: Coordinator reviews incident
- **WHEN** a coordinator changes an incident from "submitted" to "reviewed"
- **THEN** the status is updated and the incident is marked as verified

#### Scenario: Volunteer cannot review
- **WHEN** a volunteer tries to change status to "reviewed"
- **THEN** the system denies the action

### Requirement: Deduplication detection
The system SHALL detect potential duplicate incidents by matching on URL (exact match) and flag them for coordinator review. When a duplicate is detected, the system SHALL link the new incident to the existing one.

#### Scenario: Same URL submitted twice
- **WHEN** volunteer A submits an incident with URL "https://facebook.com/post/123" and volunteer B submits another incident with the same URL
- **THEN** the system flags the second incident as a potential duplicate and links it to the first

### Requirement: Incident data export
The system SHALL allow coordinators to export incidents as CSV. The export SHALL include all core fields and extra_fields (flattened as columns).

#### Scenario: Export filtered incidents
- **WHEN** a coordinator applies filters (platform: Facebook, date range: last month) and clicks "Export CSV"
- **THEN** the system downloads a CSV file containing only the filtered incidents with all fields
