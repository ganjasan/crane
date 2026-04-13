## ADDED Requirements

### Requirement: Project overview dashboard
The system SHALL provide a project-level dashboard accessible to coordinators showing: total incidents, incidents this week/month, active volunteers, coverage score (% of matrix cells searched in last 30 days).

#### Scenario: Coordinator opens dashboard
- **WHEN** a coordinator navigates to the project dashboard
- **THEN** they see summary cards with total incidents (142), this week (7), active volunteers (5), coverage score (68%)

### Requirement: Recent incidents feed
The dashboard SHALL show the most recent incidents (last 20) with status, platform, volunteer name, and date. Each entry links to the full incident view.

#### Scenario: New incident appears in feed
- **WHEN** a volunteer submits a new incident
- **THEN** it appears at the top of the dashboard's recent incidents feed

### Requirement: Review queue
The dashboard SHALL show a queue of incidents with status "submitted" that need coordinator review. The queue SHALL show count and allow quick navigation.

#### Scenario: Incidents awaiting review
- **WHEN** 5 incidents are in "submitted" status
- **THEN** the dashboard shows "5 incidents awaiting review" with a link to the review queue

### Requirement: Coverage heatmap widget
The dashboard SHALL include a compact coverage heatmap (from `search-coverage` capability) showing the top-level gaps at a glance.

#### Scenario: Heatmap on dashboard
- **WHEN** a coordinator views the dashboard
- **THEN** a compact heatmap shows the worst coverage gaps highlighted in red

### Requirement: Keyword candidates notification
The dashboard SHALL show the count of keywords with status "candidate" that need coordinator approval.

#### Scenario: Pending keyword proposals
- **WHEN** 3 keywords are in "candidate" status
- **THEN** the dashboard shows "3 keywords pending review" with a link to the keyword bank filtered by status=candidate

### Requirement: Data quality flags
The dashboard SHALL flag incidents with potential quality issues: missing required extra_fields, no screenshot, duplicate URL detected.

#### Scenario: Incidents with missing data
- **WHEN** 2 incidents are missing the species_name field
- **THEN** the dashboard shows "2 incidents with incomplete data" with links to edit them
