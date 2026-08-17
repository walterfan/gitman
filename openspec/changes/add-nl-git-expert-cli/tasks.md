## 1. Project Scaffold

- [x] 1.1 Create `pyproject.toml`, `uv.lock`, pytest/ruff config, and `src/gitman/` layout for CLI, planner, gitops, safety, server, and models.
- [x] 1.2 Add the `gitman` console script and uv dev dependencies for pytest and ruff.
- [x] 1.3 Add a minimal `README.md` with install, `ask`, `serve`, and LLM env-var examples.
- [x] 1.4 Update `AGENTS.md` commands after `uv sync` works, removing `# TODO verify` once they actually run.

## 2. CLI And Repo Targeting

- [x] 2.1 Implement Click CLI with `gitman --help`, `ask`, and `serve`.
- [x] 2.2 Resolve the target repo from cwd or `--repo` via `git rev-parse --show-toplevel` and fail if the start path is not a work tree.
- [x] 2.3 Implement `--dry-run` so `ask` prints a plan without mutating git.
- [x] 2.4 Return clear non-zero errors for missing prompts and missing git repos.
- [x] 2.5 Add tests for help, missing prompt, missing repo, and `--repo` override.

## 3. Git Snapshot And Safety

- [x] 3.1 Collect branch, `git status --short`, and size-capped staged/unstaged diffs with `git -C`.
- [x] 3.2 Redact secret-like lines before they are sent to a planner or logged.
- [x] 3.3 Classify commands as read-only, mutating, or destructive per the execution spec.
- [x] 3.4 Reject non-git binaries and `shell=True` execution paths.
- [x] 3.5 Add tests for snapshot truncation, redaction, and destructive classification.

## 4. Planner And Commit Messages

- [x] 4.1 Define a pydantic plan model: summary, command args, commit_message, warnings.
- [x] 4.2 Implement a `Planner` protocol with an injectable fake for tests.
- [x] 4.3 Fail clearly when no LLM backend is configured and no planner is injected; do not mutate git.
- [x] 4.4 Implement an OpenAI-compatible HTTP planner using `GITMAN_LLM_BASE_URL`, `GITMAN_LLM_API_KEY`, and `GITMAN_LLM_MODEL`.
- [x] 4.5 Generate conventional-commit messages from the git snapshot, not from the prompt alone; skip empty commits.
- [x] 4.6 Add tests for valid plans, invalid JSON, no-backend, commit-message-from-diff, and empty-tree behavior.

## 5. Execution Loop

- [x] 5.1 Print the plan and prompt for confirmation before mutating git.
- [x] 5.2 Honor `--yes` for non-destructive mutating commands only.
- [x] 5.3 Require extra confirmation or an extra flag for destructive commands.
- [x] 5.4 Execute confirmed commands as `git -C <toplevel> <args...>` with `shell=False`, stop on first non-zero, and report stdout/stderr/exit.
- [x] 5.5 Pass generated commit messages with `-m` (and a second `-m` for the body).
- [x] 5.6 Add tests for decline, `--yes`, destructive block, mid-plan failure, and dry-run commit.

## 6. Web UI

- [x] 6.1 Implement `gitman serve` on `127.0.0.1`, default port `9626`, with `9626 + n` fallback.
- [x] 6.2 Print the actual URL; error if an explicit `--port` is unavailable.
- [x] 6.3 Add a static UI to submit a prompt, show the plan, confirm, and display command results.
- [x] 6.4 Reuse CLI planner/executor; reject execute requests that change the repo path; extra-confirm destructive plans.
- [x] 6.5 Add tests for default host/port, port fallback, explicit port failure, and execute rejection outside the serve-time repo.

## 7. Installation

- [x] 7.1 Implement `install.sh` requiring `uv` and Python 3.11+, running `uv sync` / package install, and linking `~/.local/bin/gitman`.
- [x] 7.2 Preserve invocation cwd as the default repo in the installed wrapper.
- [x] 7.3 Support `./install.sh uninstall` and print `gitman --help` as the smoke test on success.
- [x] 7.4 Fail with missing-Python and missing-uv messages; preserve build-failure output.

## 8. Verification

- [x] 8.1 Run `uv run ruff check .` and `uv run ruff format .` and fix issues.
- [x] 8.2 Run `uv run pytest` for CLI, planner, execution, commit-message, and UI tests.
- [x] 8.3 Run `uv run gitman --help` and a `--dry-run` ask against a sample git repo with the fake or configured planner.
- [x] 8.4 Run `./install.sh` and invoke installed `gitman --help` from another directory.
