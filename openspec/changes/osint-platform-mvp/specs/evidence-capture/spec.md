## ADDED Requirements

### Requirement: Browser extension captures evidence
The system SHALL provide a browser extension (Chrome and Firefox) that captures evidence from the current page with one click: full-page screenshot, URL, page title, timestamp, and auto-detected platform name.

#### Scenario: One-click capture on Facebook
- **WHEN** a volunteer clicks the extension button while viewing a Facebook post
- **THEN** the extension captures a full-page screenshot, the post URL, the page title, the current timestamp, and detects the platform as "Facebook"

#### Scenario: Platform auto-detection
- **WHEN** the extension captures from a URL containing "telegram.org"
- **THEN** the platform field is auto-filled as "Telegram"

### Requirement: Extension authenticates with the platform
The extension SHALL authenticate with the web platform using a personal API token generated from the user's account settings. The token is stored in extension local storage.

#### Scenario: Token setup
- **WHEN** a volunteer installs the extension and enters their API token from the platform settings page
- **THEN** the extension stores the token and uses it for all subsequent captures

#### Scenario: Invalid token
- **WHEN** the extension sends a capture with an expired or invalid token
- **THEN** the extension shows an error message asking the user to re-enter their token

### Requirement: Extension submits to platform API
The extension SHALL POST captured evidence to the platform's `/api/v1/incidents/capture` endpoint. The response SHALL return the created incident ID and a link to the annotation form.

#### Scenario: Successful capture submission
- **WHEN** the extension submits a capture with screenshot, URL, and metadata
- **THEN** the API creates an incident in "draft" status and returns the incident ID

#### Scenario: Extension opens annotation form
- **WHEN** a capture is successfully submitted
- **THEN** the extension opens the annotation form for the new incident in a new tab

### Requirement: Manual evidence upload as fallback
The system SHALL allow volunteers to manually upload a screenshot and enter the URL through the web form, for cases when the extension is not available (mobile, unsupported browser).

#### Scenario: Manual upload from phone
- **WHEN** a volunteer on their phone navigates to "New Incident" and uploads a screenshot from their gallery and pastes a URL
- **THEN** the system creates a draft incident with the uploaded screenshot and URL
