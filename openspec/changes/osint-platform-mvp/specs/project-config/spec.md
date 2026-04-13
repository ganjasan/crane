## ADDED Requirements

### Requirement: Configure project-specific fields
The system SHALL allow coordinators to define custom fields for their project's incident records. Each field has: name (kebab-case identifier), label (display name), type (choice/text/number/boolean), required (true/false), choices (list, for choice type), and display order.

#### Scenario: Add species dropdown field
- **WHEN** a coordinator creates a field with name "species-name", label "Species Name", type "choice", required true, choices ["Demoiselle Crane", "Siberian Crane", "Eurasian Crane", "Black-necked Crane", "Sarus Crane"]
- **THEN** the annotation form for this project includes a required "Species Name" dropdown with those choices

#### Scenario: Add optional text field
- **WHEN** a coordinator creates a field with name "price", label "Price", type "text", required false
- **THEN** the annotation form includes an optional text input for price

#### Scenario: Reorder fields
- **WHEN** a coordinator changes the display order of fields
- **THEN** the annotation form renders fields in the new order

### Requirement: Configure platforms list
The system SHALL allow coordinators to define which platforms are monitored in their project. The platform list populates dropdowns in the incident form and defines rows in the coverage matrix.

#### Scenario: Add platforms to project
- **WHEN** a coordinator adds platforms ["Facebook", "Telegram", "OLX", "VK", "Lalafo"] to the project
- **THEN** these platforms appear in incident form dropdowns and coverage matrix rows

### Requirement: Configure languages list
The system SHALL allow coordinators to define which languages are relevant to their project. The language list populates dropdowns and defines coverage matrix dimensions.

#### Scenario: Set project languages
- **WHEN** a coordinator sets languages to ["Kyrgyz", "Russian", "Uzbek", "English"]
- **THEN** these languages appear in incident form dropdowns and coverage matrix columns

### Requirement: Configure keyword categories
The system SHALL allow coordinators to define keyword categories for their project (e.g., "sale", "purchase", "hunting", "transport", "slang"). These categories organize the keyword bank and define coverage matrix dimensions.

#### Scenario: Define keyword categories
- **WHEN** a coordinator sets categories to ["sale", "purchase", "hunting", "transport", "slang", "species-specific"]
- **THEN** keyword creation and coverage matrix use these categories

### Requirement: Record ID prefix configuration
The system SHALL allow coordinators to set a prefix for auto-generated incident record IDs (e.g., "BTCA" for Bird Trade Central Asia). Record IDs follow the pattern `{prefix}-{sequential_number}`.

#### Scenario: Set record ID prefix
- **WHEN** a coordinator sets the record ID prefix to "BTCA"
- **THEN** new incidents get record IDs like "BTCA-001", "BTCA-002", etc.

### Requirement: Seed data import
The system SHALL allow coordinators to import initial project configuration (species list, keyword bank, platforms, languages) from a structured file (CSV or JSON). This enables quick project setup from prepared data.

#### Scenario: Import species list from CSV
- **WHEN** a coordinator uploads a CSV with columns [common_name, scientific_name] containing 50 species
- **THEN** the system creates a choice field "species-name" with 50 options, and a linked "scientific-name" auto-fill mapping
