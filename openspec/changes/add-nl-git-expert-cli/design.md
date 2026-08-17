## Context

The repo is a scaffold: OpenSpec wiring, `AGENTS.md`, and no application code. The product is a local git expert like markpad: a uv-managed Python CLI, optional loopback Web UI, and an install script so it can run from any git working tree. The user types natural language; an LLM produces a git command plan and a commit message; the tool executes only after confirmation.

Constraints from `AGENTS.md`: Python 3.11+ and uv; plan before mutate; extra confirmation for destructive git; commit messages from real `git status`/`git diff`; operate only on the user-specified working tree; Web UI on loopback; LLM backend opt-in; never log credentials.

## Goals / Non-Goals

**Goals:**

- Ship a `gitman` CLI that asks, plans, and optionally executes git in a target repo.
- Ship `gitman serve` with a loopback Web UI for the same loop.
- Produce structured plans (argv commands + rationale), not shell strings.
- Generate commit messages from the actual working-tree status and diff.
- Install via `install.sh` so the command works outside this repo.
- Keep the first implementation small, testable, and uv-managed.

**Non-Goals:**

- Do not reimplement git; require a system `git` binary.
- Do not build a hosted multi-user git service or CI replacement.
- Do not auto-send repo contents to an LLM without a configured backend.
- Do not support arbitrary shell execution, hooks editing, or credential helpers.
- Do not add GitHub/GitLab API features in this change (clone/push via git only).

## Decisions

### Use uv, Click, FastAPI, and a static Web UI (markpad product shape)

Layout:

- `pyproject.toml` / `uv.lock` — Python 3.11+, console script `gitman`.
- `src/gitman/cli.py` — Click entry: `ask`, `serve`, `--repo`, `--help`.
- `src/gitman/planner.py` — LLM call + plan parsing.
- `src/gitman/gitops.py` — `git -C <repo>` status/diff/execute.
- `src/gitman/safety.py` — mutating vs destructive classification.
- `src/gitman/server.py` — FastAPI + static HTML/JS UI.
- `tests/` — fake planner, temp git repos, no live LLM in CI.

Local commands are `uv sync` and `uv run <cmd>`. Do not add Poetry.

Rationale: uv gives a PEP 621 project, a single lockfile, and fast reproducible installs. The CLI/UI shape still follows markpad; only the package manager differs because the user chose uv.

Alternatives considered:

- Poetry (markpad): rejected for this repo after an explicit uv choice.
- Go CLI: fast binary, but diverges from the requested Python CLI + Web UI.
- Python + LangChain agents with tools: too much framework for a first local tool.
- Shell-out of LLM-authored scripts: unsafe; argv-only git is the contract.

### CLI is the primary surface; Web UI is `gitman serve`

- `gitman ask "commit the refactor"` — gather git context, plan, print, prompt to execute.
- `gitman serve` — bind `127.0.0.1`, default port `9626`, fallback `9626 + n`.
- Default repo is the current working directory if it is a git work tree; `--repo PATH` overrides.
- `--dry-run` prints the plan and does not execute.
- `--yes` auto-confirms non-destructive mutating commands only.

Rationale: CLI-first matches markpad and scripts; the UI is the same loop in a browser.

### Resolve the repo from the start path only

Call `git rev-parse --show-toplevel` from cwd or `--repo`. If that start path is not inside a work tree, exit non-zero. Do not search sibling directories or a configured global projects root.

Rationale: silently using a parent or unrelated repo is the failure mode `AGENTS.md` calls out.

### Plans are argv lists executed with `git -C`, never a shell

The planner MUST emit JSON matching a pydantic model, for example:

```json
{
  "summary": "Stage Python files and commit",
  "commands": [
    {"args": ["add", "src/gitman"], "mutating": true, "destructive": false},
    {"args": ["commit", "-m", "<generated message>"], "mutating": true, "destructive": false}
  ],
  "commit_message": "feat: add gitman CLI planner",
  "warnings": []
}
```

The executor prepends `git -C <repo>` and runs `subprocess.run(..., shell=False)`. Reject plans whose args include shell metacharacters, `git` as arg0 (already implied), or non-git binaries.

Rationale: LLM-generated shell strings are the highest-severity injection path.

### Destructive commands need a second confirmation

Treat as destructive (not covered by `--yes`): `reset --hard`, `checkout`/`restore` that discards uncommitted work, `clean -f`, `push --force` / `--force-with-lease`, `branch -D`, `rebase`, `commit --amend` of a published commit, `filter-branch`, `filter-repo`, `update-ref -d`.

Rationale: these are hard to undo; a git expert still must not surprise the user.

### LLM backend is opt-in and injectable

Config via env: `GITMAN_LLM_BASE_URL`, `GITMAN_LLM_API_KEY`, `GITMAN_LLM_MODEL` (OpenAI-compatible chat completions). Tests inject a `Planner` protocol fake. If no backend is configured, `ask` and the UI plan endpoint fail with a setup message and MUST NOT mutate git.

Prompt context is bounded: branch name, `git status --short`, and a size-capped `git diff` / `git diff --staged`. Redact lines that look like tokens or `.env` values before sending.

Rationale: default-off network plus a fake planner keeps CI deterministic and private repos local until the user opts in.

### Commit messages come from git, then the LLM

Always collect `git status` and diffs in the target repo first. Pass that snapshot to the planner when a commit is requested. The subject MUST describe files/hunks present in that snapshot; do not invent paths. Prefer conventional-commit style (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).

Rationale: NL-only messages drift from the actual change.

### Install script mirrors markpad

`install.sh` requires `uv` (and Python 3.11+ via uv or the system), runs `uv sync` / package install, and links `gitman` into `~/.local/bin`. The wrapper preserves the invocation cwd as the default repo. `install.sh uninstall` removes the link and install dir.

Rationale: users run `gitman` inside other clones, not only this repo.

## Risks / Trade-offs

- LLM invents unsafe git → argv allowlist (git only), destructive classifier, confirm-before-run.
- Prompt injection via commit messages or file names in the diff → treat LLM output as data; never `shell=True`; validate JSON schema.
- Secrets in diffs sent to a provider → cap + redact; require explicit backend config.
- Wrong repo mutated → start-path work-tree check; always `git -C <resolved-toplevel>`.
- `--yes` in scripts → still block destructive commands without an explicit extra flag.
- Port fallback hiding another instance → print the actual URL like markpad.
- No LLM in CI → fake planner covers plan/execute/commit-message tests.

## Migration Plan

1. Scaffold the uv Python package, CLI `--help`, tests, README, verified `AGENTS.md` commands.
2. Implement repo resolution, status/diff collection, and dry-run plan printing with a fake planner.
3. Add confirmation, execution, and destructive guards.
4. Add commit-message generation from real diffs.
5. Add OpenAI-compatible planner behind env config.
6. Add FastAPI loopback UI and `install.sh`.

Rollback during initial development: remove the package scaffold; no production data store.

## Open Questions

- Should the first LLM provider also support a local `ollama` base URL out of the box? (Env `GITMAN_LLM_BASE_URL` already allows this without extra code.)
- Should `gitman ask` default to dry-run with an explicit `--execute`, or prompt interactively? Default: interactive confirm; `--dry-run` and `--yes` as overrides.
