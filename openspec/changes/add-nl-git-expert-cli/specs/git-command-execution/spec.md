## ADDED Requirements

### Requirement: Preview before mutation
The system SHALL print or display the planned git commands before running any mutating command, unless `--yes` is used for non-destructive commands.

#### Scenario: Interactive confirm
- **WHEN** the user runs `gitman ask "commit staged files"` without `--dry-run` or `--yes`
- **THEN** the CLI shows the plan and waits for confirmation before running mutating git

#### Scenario: User declines
- **WHEN** the user declines confirmation
- **THEN** no mutating git command is executed

### Requirement: Execute argv-only git in the target repo
The system SHALL run each approved command as `git -C <toplevel> <args...>` with `shell=False`. It SHALL reject plans that invoke any binary other than git.

#### Scenario: Approved non-destructive command
- **WHEN** the user confirms a plan whose command args are `["status", "--short"]`
- **THEN** the executor runs git status in the target repo and prints the command result

#### Scenario: Non-git binary rejected
- **WHEN** a plan command would run `rm`, `bash`, or another non-git binary
- **THEN** the executor refuses the command and does not start that process

### Requirement: Stop on first failure
The system SHALL stop executing remaining commands when a git command exits non-zero.

#### Scenario: Mid-plan failure
- **WHEN** the second command in a confirmed plan exits non-zero
- **THEN** later commands are not run and the CLI reports the failed command's exit code and stderr

### Requirement: Destructive commands need extra confirmation
The system SHALL treat force-push, hard reset, force clean, discarding checkouts/restores, deleting branches with `-D`, rebase, history rewrite, and amend of published commits as destructive. `--yes` SHALL NOT authorize destructive commands.

#### Scenario: Hard reset blocked by --yes
- **WHEN** the plan includes `reset --hard` and the user passed `--yes`
- **THEN** the executor still requires an extra explicit confirmation or an extra destructive flag before running it

#### Scenario: Destructive declined
- **WHEN** the user does not give extra confirmation for a destructive command
- **THEN** that command is not executed

### Requirement: Dry-run never executes mutating git
The system SHALL not run mutating git commands in `--dry-run` mode.

#### Scenario: Dry-run commit plan
- **WHEN** the plan includes `commit` and the user passed `--dry-run`
- **THEN** no commit object is created
