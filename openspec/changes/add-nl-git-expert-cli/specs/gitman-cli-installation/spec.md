## ADDED Requirements

### Requirement: Shell script installs the CLI
The system SHALL provide `install.sh` that installs or links the `gitman` CLI for local use.

#### Scenario: Install from repository root
- **WHEN** the user runs `./install.sh` from the repository root
- **THEN** the script runs `uv sync`, installs the package, and makes the `gitman` command available

#### Scenario: Install reports command name
- **WHEN** the install script completes successfully
- **THEN** it prints the installed command name `gitman` and a smoke-test command such as `gitman --help`

### Requirement: Installed CLI uses invocation cwd as repo
The installed CLI SHALL treat the directory where the user invoked it as the default git start path.

#### Scenario: Run installed CLI in another clone
- **WHEN** the user runs the installed `gitman ask "show status" --dry-run` from a different git work tree
- **THEN** the CLI targets that work tree, not the gitman source checkout

### Requirement: Uninstall removes the command
The install script SHALL support `./install.sh uninstall`.

#### Scenario: Uninstall
- **WHEN** the user runs `./install.sh uninstall`
- **THEN** the script removes the `gitman` command link and the install directory

### Requirement: Install script fails clearly
The install script SHALL fail with clear guidance when required tools are missing.

#### Scenario: Missing Python runtime
- **WHEN** the install script runs without Python 3.11+ available
- **THEN** it exits non-zero and prints the missing prerequisite

#### Scenario: Missing uv
- **WHEN** the install script runs without `uv` available
- **THEN** it exits non-zero and prints the missing prerequisite

#### Scenario: Build failure
- **WHEN** `uv sync` or package install fails
- **THEN** the script exits non-zero and preserves the failing command output
