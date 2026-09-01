# gitman

`gitman` is a local git expert. Type natural language, review a git command
plan, get a commit message from the real diff, and execute only after
confirmation. It is a CLI with an optional loopback Web UI.

## Install

Prerequisites: **Python 3.11+** and [uv](https://docs.astral.sh/uv/getting-started/installation/).

### One-line install

Download and run the bootstrap installer (fetches the latest `main` source, then runs `install.sh`):

```bash
curl -fsSL https://raw.githubusercontent.com/walterfan/gitman/main/bootstrap.sh | bash
```

To install from another branch, set `GITMAN_BRANCH` before piping:

```bash
curl -fsSL https://raw.githubusercontent.com/walterfan/gitman/main/bootstrap.sh | GITMAN_BRANCH=develop bash
```

### Install from a local clone

```bash
git clone https://github.com/walterfan/gitman.git
cd gitman
./install.sh
```

The installer builds the package, installs it into `~/.local/share/gitman/venv`,
and links the `gitman` command into `~/.local/bin`. Verify installation with:

```bash
gitman --help
```

To remove the installed venv and command link:

```bash
./install.sh uninstall
```

If you used the one-line installer and no longer have a local clone, download
`install.sh` again or clone the repo and run `./install.sh uninstall`.

For development in this repo:

```bash
uv sync
uv run gitman --help
```

## Ask

From any git working tree:

```bash
gitman "commit the staged changes" --dry-run
gitman "show status"
gitman ask "commit the refactor" --repo /path/to/repo
```

`ask` is the default command, so `gitman "show status"` is the same as
`gitman ask "show status"`. Use `gitman serve` for the Web UI.

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
GITMAN_PLANNER=fake gitman "show status" --dry-run
```

## Development

```bash
uv run pytest
uv run ruff check .
uv run ruff format .
```

## License

Licensed under the [Apache License, Version 2.0](LICENSE).
