# gitman

`gitman` is a local git expert. Type natural language, review a git command
plan, get a commit message from the real diff, and execute only after
confirmation. It is a CLI with an optional loopback Web UI.

## Install

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
./install.sh
gitman --help
```

Remove the installed command with:

```bash
./install.sh uninstall
```

For development in this repo:

```bash
uv sync
uv run gitman --help
```

## Ask

From any git working tree:

```bash
gitman ask "commit the staged changes" --dry-run
gitman ask "show status"
gitman ask "commit the refactor" --repo /path/to/repo
```

`--dry-run` prints the plan and does not mutate git. `--yes` confirms
non-destructive mutating commands. Destructive operations (`reset --hard`,
force-push, rebase, …) still need `--force-destructive` or an extra prompt.

## Web UI

```bash
gitman serve
```

Listens on `127.0.0.1:9626` by default (then `9627`, `9628`, … if busy).

## LLM backend

Planning calls an OpenAI-compatible chat API only when configured.
Put these in the environment or a `.env` file in the current directory
or the target git repo (already-set env vars win; `.env` is gitignored):

```bash
GITMAN_LLM_BASE_URL="https://api.openai.com"
GITMAN_LLM_MODEL="gpt-4.1-mini"
GITMAN_LLM_API_KEY="..."
```

A local server such as Ollama works by pointing `GITMAN_LLM_BASE_URL` at it.
Without these variables, `ask` and the UI plan endpoint fail without mutating git.

Company HTTP proxies often intercept HTTPS with a private CA. Point
gitman at that CA, or disable verification if you accept the risk.
`GITMAN_LLM_VERIFY_SSL=false` wins over CA-bundle env vars:

```bash
GITMAN_LLM_CA_BUNDLE="/path/to/corporate-root-ca.pem"
# or, less safe:
GITMAN_LLM_VERIFY_SSL=false
```

For local smoke tests without a model:

```bash
GITMAN_PLANNER=fake gitman ask "show status" --dry-run
```

## Development

```bash
uv run pytest
uv run ruff check .
uv run ruff format .
```
