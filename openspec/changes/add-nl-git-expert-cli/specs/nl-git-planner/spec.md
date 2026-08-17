## ADDED Requirements

### Requirement: Natural language becomes a structured plan
The system SHALL convert a user prompt into a structured plan with a summary, git command argument lists, optional commit message, and optional warnings.

#### Scenario: Successful plan
- **WHEN** the planner receives "stage src and commit" plus a git status/diff snapshot
- **THEN** it returns JSON-compatible data with a non-empty summary and commands whose `args` are git subcommand argument lists without a shell wrapper

#### Scenario: Invalid planner output
- **WHEN** the LLM returns text that is not valid plan JSON
- **THEN** the system does not execute git and reports that the plan could not be parsed

### Requirement: Planner requires an explicit backend
The system SHALL NOT call a remote LLM unless a backend is configured. Tests MAY inject a fake planner.

#### Scenario: No backend configured
- **WHEN** the user runs `gitman ask "commit"` with no LLM backend configured and no injected planner
- **THEN** the CLI exits non-zero with setup guidance and does not mutate the repository

#### Scenario: Injected planner in tests
- **WHEN** tests supply a fake planner
- **THEN** ask/plan succeeds without network calls

### Requirement: Prompt context is bounded and redacted
The system SHALL send the planner a bounded snapshot: branch name, short status, and size-capped staged/unstaged diffs. It SHALL redact values that look like secrets before sending.

#### Scenario: Diff larger than cap
- **WHEN** the unstaged diff exceeds the configured size cap
- **THEN** the planner context includes a truncated diff plus a warning that the diff was truncated

#### Scenario: Secret-like line
- **WHEN** status or diff contains a line matching a token or `.env` secret pattern
- **THEN** that value is redacted in the planner context and is not logged

### Requirement: Ambiguous requests are not executed
The system SHALL return a plan with warnings and no mutating commands, or refuse the request, when the prompt is too ambiguous to choose a safe git action.

#### Scenario: Ambiguous undo
- **WHEN** the user says "undo" with both uncommitted changes and a recent commit present
- **THEN** the plan does not execute automatically and either asks for clarification or lists non-mutating inspection commands only
