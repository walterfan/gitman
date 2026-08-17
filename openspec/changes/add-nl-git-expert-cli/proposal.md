## Why

Developers often know the git outcome they want ("commit this refactor", "undo the last commit but keep files") but not the exact, safe command sequence. A local CLI plus optional Web UI that turns natural language into a reviewed git plan, a diff-based commit message, and confirmed execution reduces that gap without sending the working tree to a hosted product by default.

## What Changes

- Add a uv-managed Python CLI named `gitman` that can run from any git working tree, matching the markpad local-tool shape (CLI first, optional loopback Web UI).
- Accept natural-language requests, have an LLM interpret them as a git expert, and produce a structured plan of git commands with a short rationale.
- Generate commit messages from `git status` and `git diff` in the target repo, not from the prompt alone.
- Show the plan before mutating the repo; execute only after confirmation, with extra confirmation for destructive operations.
- Add an optional local Web UI for the same ask/plan/confirm/execute loop.
- Add an install shell script so `gitman` can be invoked from arbitrary repositories.
- Add tests for CLI startup, planner output shape, execution safety, and commit-message generation.

## Capabilities

### New Capabilities

- `gitman-cli`: CLI entry point, repo targeting, ask/serve/help, and local-only defaults.
- `gitman-cli-installation`: shell-script install flow and post-install command availability.
- `nl-git-planner`: natural-language interpretation into a structured git command plan and rationale.
- `git-command-execution`: preview, confirmation, safety rails, and execution reporting.
- `commit-message-generation`: commit messages derived from real `git status` and `git diff`.
- `gitman-web-ui`: loopback Web UI for the same ask/plan/confirm/execute loop.

### Modified Capabilities

None. This repo has no accepted specs yet.

## Impact

- Adds Python application source under `src/gitman/`, uv/`pyproject.toml` metadata, an install script, tests, and developer commands.
- Introduces an LLM backend boundary: opt-in provider configuration; repo contents and credentials are not sent off-box unless the user configures a backend.
- Introduces subprocess git execution against a user-specified working tree, so path and destructive-command guards are required.
- Introduces optional HTTP routes for the Web UI, bound to `127.0.0.1` by default.
- Requires the system `git` binary; the tool plans and runs git, it does not reimplement git.
