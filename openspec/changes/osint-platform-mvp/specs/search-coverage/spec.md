## ADDED Requirements

### Requirement: Log a search session
The system SHALL allow volunteers to log what they searched: platform, language, keyword categories covered, date, duration (optional), number of incidents found, and notes.

#### Scenario: Volunteer logs a search session
- **WHEN** a volunteer submits a search log with platform "Facebook", language "Kyrgyz", categories ["sale", "hunting"], date "2026-04-13", incidents_found "2"
- **THEN** the system records the search session linked to the volunteer and project

#### Scenario: Quick log after search
- **WHEN** a volunteer finishes searching and clicks "Log Search"
- **THEN** a compact form appears with platform, language, and category dropdowns, pre-filled with today's date

### Requirement: Coverage matrix view
The system SHALL display a matrix with rows = (platform x language) and columns = keyword categories. Each cell shows the date of the most recent search session covering that combination. Cells SHALL be color-coded: green (searched within 7 days), yellow (8-30 days), red (over 30 days or never).

#### Scenario: Coordinator views coverage matrix
- **WHEN** a coordinator opens the coverage matrix for project "Bird Trade Central Asia"
- **THEN** a heatmap grid shows all platform-language combinations with color-coded recency

#### Scenario: Identify coverage gap
- **WHEN** the matrix shows a red cell for "Telegram × Tajik × sale"
- **THEN** the coordinator knows that Telegram in Tajik language for sale keywords has not been searched in over 30 days

### Requirement: Coverage matrix is filterable
The system SHALL allow filtering the coverage matrix by platform, language, or keyword category to focus on specific areas.

#### Scenario: Filter matrix by platform
- **WHEN** a coordinator filters the matrix to show only "Facebook"
- **THEN** only Facebook rows are displayed across all languages

### Requirement: Coverage gap drives assignments
The system SHALL allow a coordinator to click a coverage gap cell and create a volunteer assignment from it, pre-filled with the platform, language, and keyword category.

#### Scenario: Create assignment from gap
- **WHEN** a coordinator clicks a red cell for "OLX × Uzbek × sale"
- **THEN** an assignment creation form opens with platform "OLX", language "Uzbek", category "sale" pre-filled

### Requirement: Volunteer search activity summary
The system SHALL show per-volunteer activity: number of search sessions, platforms covered, incidents found, and last active date.

#### Scenario: Coordinator reviews volunteer activity
- **WHEN** a coordinator opens the volunteer activity view
- **THEN** a table shows each volunteer with their total searches, incidents found, and days since last activity
