## ADDED Requirements

### Requirement: Dynamic form from project configuration
The annotation form SHALL be dynamically generated based on the project's field configuration (see `project-config`). Core fields are always present. Project-specific fields appear based on the project's `ProjectFieldConfig` entries.

#### Scenario: Bird trade project form
- **WHEN** a volunteer opens the annotation form for a project configured with fields "species_name" (choice), "price" (text), "trade_type" (choice)
- **THEN** the form shows core fields plus dropdowns for species and trade type, and a text input for price

#### Scenario: Different project shows different fields
- **WHEN** a volunteer opens the annotation form for a timber trade project configured with "wood_species" and "volume"
- **THEN** the form shows core fields plus timber-specific fields, not bird-specific ones

### Requirement: Core fields always present
The annotation form SHALL always include: platform (auto-filled if from extension), URL (auto-filled if from extension), date_of_post, location_mentioned, probable_location, language (dropdown), confidence (high/medium/low), notes (free text).

#### Scenario: Extension pre-fills fields
- **WHEN** a volunteer opens the form after a browser extension capture
- **THEN** platform, URL, and screenshot are pre-filled and the volunteer only needs to complete remaining fields

### Requirement: Dropdown choices from project config
Choice-type fields SHALL render as dropdowns populated from the project's field configuration. The choices SHALL support display in the volunteer's language where translations are available.

#### Scenario: Species dropdown
- **WHEN** the project has a field "species_name" of type "choice" with options ["Demoiselle Crane", "Siberian Crane", "Sarus Crane", ...]
- **THEN** the form renders a searchable dropdown with these options

### Requirement: Mobile-friendly form
The annotation form SHALL be fully functional on mobile browsers. All inputs SHALL be touch-friendly with adequate tap targets. The form SHALL work on viewport widths from 320px.

#### Scenario: Form on small screen
- **WHEN** a volunteer opens the annotation form on a 360px-wide phone screen
- **THEN** all fields are visible, scrollable, and usable without horizontal scrolling

### Requirement: Save as draft
The form SHALL allow saving an incident as "draft" without requiring all mandatory fields. This enables partial completion and later finishing.

#### Scenario: Incomplete form saved
- **WHEN** a volunteer fills in platform and URL but not species, and clicks "Save Draft"
- **THEN** the incident is saved with status "draft" and can be edited later

### Requirement: Submit for review
The form SHALL validate all required fields before allowing submission. On submission, the incident status changes to "submitted" and it appears in the coordinator's review queue.

#### Scenario: Submit with all required fields
- **WHEN** a volunteer fills in all required fields and clicks "Submit"
- **THEN** the incident status becomes "submitted" and the volunteer sees a confirmation

#### Scenario: Submit with missing required fields
- **WHEN** a volunteer clicks "Submit" but a required field (e.g., platform) is empty
- **THEN** the form highlights the missing fields and does not submit
