## ADDED Requirements

### Requirement: Serve starts a loopback Web UI
The system SHALL provide `gitman serve` that starts a local web server for the ask/plan/confirm/execute loop.

#### Scenario: Default host
- **WHEN** the user runs `gitman serve` without a host option
- **THEN** the server listens on `127.0.0.1`

#### Scenario: Default port with fallback
- **WHEN** the user runs `gitman serve` without a port option and port `9626` is available
- **THEN** the server listens on port `9626`

#### Scenario: Default port occupied
- **WHEN** the user runs `gitman serve` without a port option and port `9626` is occupied
- **THEN** the server tries `9627` (`9626 + n`) until it finds a free port in a bounded range

#### Scenario: Explicit port unavailable
- **WHEN** the user passes `--port` and that port is in use
- **THEN** the CLI exits non-zero and explains the port is unavailable

#### Scenario: URL printed
- **WHEN** the server is ready
- **THEN** the CLI prints a URL containing the active host and port

### Requirement: UI supports ask, plan, confirm, execute
The Web UI SHALL let the user enter natural language, view the plan, confirm, and see command results for the target repo.

#### Scenario: Submit prompt
- **WHEN** the user submits a prompt in the UI for a valid git work tree
- **THEN** the UI shows the plan summary and git commands before any mutating execute

#### Scenario: Confirm execute
- **WHEN** the user confirms a non-destructive plan in the UI
- **THEN** the server executes the approved commands in the target repo and the UI shows each command's result

#### Scenario: Decline execute
- **WHEN** the user does not confirm
- **THEN** the server does not run mutating git commands

### Requirement: UI uses the same repo and safety rules as the CLI
The Web UI SHALL target the serve-time repo (cwd or `--repo`) and SHALL apply the same destructive-command confirmation rules as the CLI.

#### Scenario: Path stays in target repo
- **WHEN** a UI execute request tries to set a repo path outside the serve-time target
- **THEN** the server rejects the request and does not run git there

#### Scenario: Destructive from UI
- **WHEN** the plan includes a destructive git command
- **THEN** the UI requires an extra confirmation distinct from ordinary execute
