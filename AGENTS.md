# AGENTS.md - gitman

<!-- Follows https://agents.md. Keep root files 70-90 lines when possible. -->

`gitman` is a local git expert: the user types natural language, an LLM
plans the work, then the tool proposes git commands, writes a commit
message from the real diff, and can execute after confirmation. It
ships as a CLI with an optional loopback Web UI.

## Context Map

- README: [`README.md`](README.md) — install, `ask`, `serve`, LLM env vars.
- Sibling pattern: [`../markpad`](../markpad) — Python CLI plus local
  FastAPI UI. Copy the product shape, not Poetry; this repo uses `uv`.

- `src/gitman/` — CLI, planner, gitops, safety, FastAPI UI
- `tests/` — CLI, planner, execution, commit messages, UI, install script
- `pyproject.toml` / `uv.lock` — uv, Python 3.11+, `gitman` console script
- `install.sh` — user-local install into `~/.local/bin/gitman`

## Commands

Use `uv` so local commands match `uv.lock`.

```bash
uv sync                     # lockfile-aligned local env
uv run gitman --help        # CLI entry smoke test
uv run gitman ask "..." --dry-run  # plan without mutating git
uv run pytest               # PR confidence suite
uv run ruff check .         # static checks before review
uv run ruff format .        # keeps diffs reviewable
./install.sh                # link ~/.local/bin/gitman
```

## Harness Rules

- Never fabricate paths, APIs, commands, tests, or results; inspect the
  repo or run the command first.
- Ask when ambiguity changes the output; otherwise resolve uncertainty
  by reading files and existing patterns.
- Think before coding: state assumptions, tradeoffs, and success
  criteria before non-trivial edits.
- Keep it simple; make surgical changes; every changed line should
  trace to the request.
- Verify before reporting done; a plausible diff is not proof.

## Project Rules

- Default stack is uv + Python 3.11+ + Click CLI + optional local
  FastAPI UI — do not add Poetry or switch package managers.
- Show the planned git commands and commit message before mutating the
  repo — silent execution is the main user-trust failure.
- Confirm before `push --force`, `reset --hard`, `clean -fd`, rebase of
  published commits, or history rewrite — these are hard to undo.
- Derive commit messages from `git status` and `git diff` in the target
  repo — NL-only messages drift from the actual change.
- Operate only on the user-specified working tree — walking parent
  directories can mutate the wrong repository.
- Bind the Web UI to loopback by default — a LAN bind can expose local
  git metadata and diffs.
- Do not send repo contents, diffs, or credentials to an LLM provider
  without an explicit user-configured backend.
- Load `GITMAN_*` from `.env` in cwd and the target repo; process env
  wins. Never log `.env` contents or commit that file.
- For corporate TLS interception, set `GITMAN_LLM_CA_BUNDLE` (or
  `GITMAN_LLM_VERIFY_SSL=false`) instead of leaving SSL tracebacks.

## AI Tooling

Primary tools: Cursor. OpenSpec skills live under `.cursor/`, `.claude/`,
`.codex/`, and `.opencode/`. Do not create `CLAUDE.md` / `GEMINI.md`
symlinks unless asked.

## Keeping Current

Update this file when commands, layout, guardrails, or LLM/git safety
rules change. When the user corrects a project-specific agent mistake,
add or tighten one concrete rule here, then prune later.

<!-- last_updated: 2026-08-17 -->
