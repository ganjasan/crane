## ADDED Requirements

### Requirement: Organization CRUD
The system SHALL allow authenticated users to create organizations. An organization has a name, slug (auto-generated from name, unique), and description. The creating user becomes the owner.

#### Scenario: Create organization
- **WHEN** an authenticated user submits an organization creation form with name "ICF"
- **THEN** the system creates an organization with slug "icf" and assigns the user the "owner" role

#### Scenario: Slug uniqueness
- **WHEN** a user tries to create an organization with a name that generates an already-taken slug
- **THEN** the system rejects the creation and shows an error

### Requirement: Organization membership with roles
The system SHALL support three organization-level roles: owner, admin, member. A user can belong to multiple organizations. Each membership has exactly one role.

#### Scenario: Owner invites admin
- **WHEN** an org owner submits an invitation for email "ella@example.com" with role "admin"
- **THEN** the system sends an invite email with a unique link, and upon acceptance the user is added as admin

#### Scenario: Member cannot manage other members
- **WHEN** a user with role "member" attempts to invite or remove another user
- **THEN** the system denies the action with a permission error

### Requirement: Project belongs to organization
The system SHALL allow org admins and owners to create projects within an organization. A project has a name (unique within org), slug, and description.

#### Scenario: Create project
- **WHEN** an org admin creates a project named "Bird Trade Central Asia" in org "ICF"
- **THEN** the system creates the project with slug "bird-trade-central-asia" under that organization

#### Scenario: Project name unique per org
- **WHEN** an admin tries to create a project with a name that already exists in the same org
- **THEN** the system rejects the creation with a uniqueness error

### Requirement: Project membership with roles
The system SHALL support two project-level roles: coordinator, volunteer. Org owners and admins can assign project roles. A coordinator has full project access. A volunteer can submit data and view their own submissions.

#### Scenario: Assign volunteer to project
- **WHEN** a coordinator adds user "intern1@example.com" to the project with role "volunteer"
- **THEN** the user can access the project and submit incidents

#### Scenario: Volunteer cannot access unassigned projects
- **WHEN** a user with org role "member" tries to access a project they are not assigned to
- **THEN** the system returns a 404 (project not found)

### Requirement: URL-based context resolution
The system SHALL resolve the current organization and project from the URL path: `/{org-slug}/{project-slug}/...`. A middleware attaches the resolved organization and project to the request.

#### Scenario: Valid org and project in URL
- **WHEN** a user navigates to `/icf/bird-trade-central-asia/incidents`
- **THEN** the system resolves org "ICF" and project "Bird Trade Central Asia" and attaches them to the request

#### Scenario: User not a member of org
- **WHEN** a user navigates to a URL for an org they don't belong to
- **THEN** the system returns a 404

### Requirement: Invitation flow
The system SHALL support email-based invitations. An invitation contains the target org, optional project, and role. The invite link is valid for 7 days. Accepting an invite creates an account (if needed) and adds the membership.

#### Scenario: New user accepts invite
- **WHEN** a person without an account clicks an invite link and completes registration
- **THEN** the system creates their account and adds them to the org/project with the specified role

#### Scenario: Expired invite
- **WHEN** a person clicks an invite link older than 7 days
- **THEN** the system shows "Invitation expired" and suggests contacting the org admin

### Requirement: Org-scoped data isolation
Every data model that belongs to a tenant SHALL have an `organization_id` foreign key. All queries SHALL filter by the current organization from the request context. No data from one organization SHALL be visible to members of another organization.

#### Scenario: Cross-org data isolation
- **WHEN** a user in org "ICF" queries incidents
- **THEN** only incidents belonging to org "ICF" are returned, never incidents from org "WWF"
