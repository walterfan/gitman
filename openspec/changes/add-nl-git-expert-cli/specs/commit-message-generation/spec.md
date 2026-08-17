## ADDED Requirements

### Requirement: Commit messages come from real git state
The system SHALL generate commit messages from `git status` and `git diff` / `git diff --staged` in the target repository, not from the user prompt alone.

#### Scenario: Message matches staged files
- **WHEN** the user asks to commit and `src/gitman/cli.py` is staged with a CLI help-text change
- **THEN** the generated subject refers to that change and does not name files absent from status and diff

#### Scenario: No changes to commit
- **WHEN** the work tree has no staged or unstaged changes
- **THEN** the system does not invent a commit message that claims files were changed and does not create an empty commit

### Requirement: Conventional commit subject
The system SHALL produce a single-line subject in conventional-commit style (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`) and MAY include a body separated by a blank line.

#### Scenario: Feature change
- **WHEN** the diff adds a new CLI command
- **THEN** the subject starts with `feat:` and summarizes the addition

### Requirement: Message is used by commit commands in the plan
When the plan includes `git commit`, the system SHALL pass the generated message with `-m` (and additional `-m` for the body if present) rather than opening an editor.

#### Scenario: Commit uses generated message
- **WHEN** the user confirms a commit plan
- **THEN** the created commit's message equals the generated subject and optional body
