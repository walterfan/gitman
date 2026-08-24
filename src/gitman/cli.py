from __future__ import annotations

import os
from pathlib import Path

import click
import uvicorn

from gitman import __version__
from gitman.envfile import load_env_files
from gitman.gitops import (
    NotAGitRepoError,
    annotate_commands,
    collect_snapshot,
    execute_plan,
    resolve_repo,
)
from gitman.planner import PlannerError, PlannerNotConfigured, get_planner
from gitman.ports import choose_port
from gitman.safety import UnsafeCommandError


def _display_url(host: str, port: int) -> str:
    display_host = "localhost" if host in {"0.0.0.0", "127.0.0.1", "::1"} else host
    return f"http://{display_host}:{port}"


def _resolve_start(repo: Path | None) -> Path:
    if repo is not None:
        return repo
    env_default = os.environ.get("GITMAN_DEFAULT_REPO")
    if env_default:
        return Path(env_default)
    return Path.cwd()


def _print_plan(plan) -> None:
    click.echo(f"Summary: {plan.summary}")
    if plan.warnings:
        for warning in plan.warnings:
            click.echo(f"Warning: {warning}")
    if plan.commit_message:
        click.echo("Commit message:")
        click.echo(plan.commit_message)
    click.echo("Commands:")
    if not plan.commands:
        click.echo("  (none)")
        return
    for index, command in enumerate(plan.commands, start=1):
        rendered = " ".join(["git", *command.args])
        flags = []
        if command.destructive:
            flags.append("destructive")
        elif command.mutating:
            flags.append("mutating")
        suffix = f" [{', '.join(flags)}]" if flags else ""
        click.echo(f"  {index}. {rendered}{suffix}")


class DefaultAskGroup(click.Group):
    """Treat a bare prompt as `ask`; keep `serve` and `ask` as explicit commands."""

    _group_flags = {"--help", "-h", "--version"}

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        args = list(args)
        if self._should_default_ask(args):
            args.insert(0, "ask")
        return super().parse_args(ctx, args)

    def _should_default_ask(self, args: list[str]) -> bool:
        if not args:
            return True
        first_token = next((item for item in args if not item.startswith("-")), None)
        if first_token is None:
            flags = {item.split("=", 1)[0] for item in args if item.startswith("-")}
            return bool(flags - self._group_flags)
        return first_token not in self.commands


@click.group(cls=DefaultAskGroup)
@click.version_option(__version__)
def main() -> None:
    """Natural-language git expert (plan, then confirm)."""
    load_env_files(Path.cwd())


@main.command()
@click.argument("prompt", nargs=-1, required=False)
@click.option("--repo", "repo_option", type=click.Path(path_type=Path), default=None)
@click.option("--dry-run", is_flag=True, help="Print the plan without executing mutating git.")
@click.option("--yes", is_flag=True, help="Confirm non-destructive mutating commands.")
@click.option(
    "--force-destructive",
    is_flag=True,
    help="Allow destructive git commands without an extra prompt.",
)
def ask(
    prompt: tuple[str, ...],
    repo_option: Path | None,
    dry_run: bool,
    yes: bool,
    force_destructive: bool,
) -> None:
    """Plan git commands from a natural-language PROMPT."""
    prompt_text = " ".join(prompt).strip()
    if not prompt_text:
        raise click.UsageError("a prompt is required")
    try:
        repo = resolve_repo(_resolve_start(repo_option))
    except NotAGitRepoError as exc:
        raise click.ClickException(str(exc)) from exc
    load_env_files(Path.cwd(), repo)
    try:
        planner = get_planner()
    except PlannerNotConfigured as exc:
        raise click.ClickException(str(exc)) from exc
    snapshot = collect_snapshot(repo)
    try:
        plan = annotate_commands(planner.plan(prompt_text, snapshot))
    except PlannerError as exc:
        raise click.ClickException(str(exc)) from exc
    except UnsafeCommandError as exc:
        raise click.ClickException(str(exc)) from exc
    _print_plan(plan)
    if dry_run:
        click.echo("Dry-run: no git commands executed.")
        return
    mutating = any(cmd.mutating for cmd in plan.commands)
    destructive = any(cmd.destructive for cmd in plan.commands)
    if mutating and not yes and not click.confirm("Execute this plan?", default=False):
        click.echo("Cancelled.")
        return
    destructive_confirmed = force_destructive
    if destructive and not force_destructive:
        destructive_confirmed = click.confirm(
            "This plan includes destructive git commands. Continue?", default=False
        )
        if not destructive_confirmed:
            click.echo("Cancelled.")
            return
    try:
        results = execute_plan(
            repo,
            plan,
            dry_run=False,
            yes=yes,
            force_destructive=force_destructive,
            confirmed=True,
            destructive_confirmed=destructive_confirmed,
        )
    except (UnsafeCommandError, PermissionError) as exc:
        raise click.ClickException(str(exc)) from exc
    for result in results:
        click.echo(f"$ git {' '.join(result.args)}  (exit {result.exit_code})")
        if result.stdout:
            click.echo(result.stdout, nl=not result.stdout.endswith("\n"))
        if result.stderr:
            click.echo(result.stderr, err=True, nl=not result.stderr.endswith("\n"))
        if result.exit_code != 0:
            raise click.ClickException(
                f"git {' '.join(result.args)} failed with exit {result.exit_code}"
            )


@main.command()
@click.option("--repo", "repo_option", type=click.Path(path_type=Path), default=None)
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", type=int, default=None)
def serve(repo_option: Path | None, host: str, port: int | None) -> None:
    """Start the loopback Web UI for ask/plan/confirm/execute."""
    try:
        repo = resolve_repo(_resolve_start(repo_option))
    except NotAGitRepoError as exc:
        raise click.ClickException(str(exc)) from exc
    load_env_files(Path.cwd(), repo)
    try:
        chosen = choose_port(host, port)
    except OSError as exc:
        raise click.ClickException(str(exc)) from exc
    from gitman.server import create_app

    app = create_app(repo)
    click.echo(f"Serving {repo} at {_display_url(host, chosen)}")
    uvicorn.run(app, host=host, port=chosen, log_level="info")
