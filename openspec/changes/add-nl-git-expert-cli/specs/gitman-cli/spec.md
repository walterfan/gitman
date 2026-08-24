## ADDED Requirements

### Requirement: CLI entry point named gitman
The system SHALL provide a `gitman` CLI that prints usage when asked for help and exits zero on help.

#### Scenario: Help from uv entry
- **WHEN** the user runs `gitman --help` or `uv run gitman --help`
- **THEN** the CLI prints usage that mentions `ask` and `serve` and exits 0

### Requirement: Ask command accepts natural language
The system SHALL provide `gitman ask <prompt>` that plans git work for a target repository.

#### Scenario: Ask with prompt
- **WHEN** the user runs `gitman ask "commit the staged changes"` in a git work tree with a planner backend configured or injected
- **THEN** the CLI prints a plan that includes a summary and one or more git commands

### Requirement: Ask is the default command
The system SHALL treat a bare prompt as `ask` when the first token is not a subcommand such as `serve` or `ask`.

#### Scenario: Prompt without ask
- **WHEN** the user runs `gitman "commit the staged changes"`
- **THEN** the CLI behaves the same as `gitman ask "commit the staged changes"`

#### Scenario: Explicit subcommands still work
- **WHEN** the user runs `gitman serve --help` or `gitman ask "show status"`
- **THEN** the CLI invokes `serve` or `ask` respectively


### Requirement: Target repository is the start path
The system SHALL use the current working directory as the default repo and SHALL accept `--repo PATH` as an override. If the start path is not inside a git work tree, the CLI SHALL fail without mutating anything.

#### Scenario: Default cwd is a work tree
- **WHEN** the user runs `gitman ask "show status"` from inside a git work tree
- **THEN** the CLI uses that work tree's toplevel as the target repo

#### Scenario: Explicit repo path
- **WHEN** the user runs `gitman ask "show status" --repo /path/to/repo`
- **THEN** the CLI uses that path's git toplevel as the target repo

#### Scenario: Not a git work tree
- **WHEN** the user runs `gitman ask "show status"` from a directory that is not inside a git work tree
- **THEN** the CLI exits non-zero, prints that no git repository was found, and does not run git mutating commands

### Requirement: Dry-run does not mutate
The system SHALL support `--dry-run` on `ask` so the plan is printed and no mutating git command is executed.

#### Scenario: Dry-run ask
- **WHEN** the user runs `gitman ask "commit everything" --dry-run`
- **THEN** the CLI prints the plan and does not create a commit or otherwise mutate the repo
