from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from gitman.models import CommandResult, GitCommand, Plan
from gitman.redact import redact
from gitman.safety import classify, validate_git_args

DIFF_CAP = 8_000


class GitError(RuntimeError):
    pass


class NotAGitRepoError(GitError):
    pass


@dataclass
class GitSnapshot:
    toplevel: Path
    branch: str
    status: str
    staged_diff: str
    unstaged_diff: str
    truncated: bool = False
    warnings: list[str] = field(default_factory=list)
    has_head: bool = False

    @property
    def has_changes(self) -> bool:
        return bool(self.status.strip())

    def changed_paths(self) -> list[str]:
        paths: list[str] = []
        for line in self.status.splitlines():
            if len(line) < 4:
                continue
            path = line[3:].strip()
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            if path and path not in paths:
                paths.append(path)
        return paths

    def planner_context(self) -> dict[str, object]:
        return {
            "branch": self.branch,
            "status": redact(self.status),
            "staged_diff": redact(self.staged_diff),
            "unstaged_diff": redact(self.unstaged_diff),
            "truncated": self.truncated,
            "warnings": list(self.warnings),
        }


def _run_git(repo: Path, args: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=check,
        shell=False,
    )


def resolve_repo(start: Path) -> Path:
    start = start.resolve()
    if not start.exists():
        raise NotAGitRepoError(f"Path does not exist: {start}")
    probe = start if start.is_dir() else start.parent
    result = _run_git(probe, ["rev-parse", "--is-inside-work-tree"])
    if result.returncode != 0 or result.stdout.strip() != "true":
        raise NotAGitRepoError(f"No git repository found at {probe}")
    toplevel = _run_git(probe, ["rev-parse", "--show-toplevel"], check=True)
    return Path(toplevel.stdout.strip())


def collect_snapshot(repo: Path, diff_cap: int = DIFF_CAP) -> GitSnapshot:
    branch_proc = _run_git(repo, ["rev-parse", "--abbrev-ref", "HEAD"])
    branch = branch_proc.stdout.strip() or "HEAD"
    has_head = _run_git(repo, ["rev-parse", "--verify", "HEAD"]).returncode == 0
    status = _run_git(repo, ["status", "--short"]).stdout
    staged = _run_git(repo, ["diff", "--staged"]).stdout
    unstaged = _run_git(repo, ["diff"]).stdout
    warnings: list[str] = []
    truncated = False
    if len(unstaged) > diff_cap:
        unstaged = unstaged[:diff_cap]
        truncated = True
        warnings.append("Unstaged diff was truncated.")
    if len(staged) > diff_cap:
        staged = staged[:diff_cap]
        truncated = True
        warnings.append("Staged diff was truncated.")
    return GitSnapshot(
        toplevel=repo,
        branch=branch,
        status=status,
        staged_diff=staged,
        unstaged_diff=unstaged,
        truncated=truncated,
        warnings=warnings,
        has_head=has_head,
    )


def apply_commit_message(args: list[str], message: str | None) -> list[str]:
    if not args or args[0] != "commit" or not message:
        return args
    if "--allow-empty" in args:
        pass
    subject, _, body = message.partition("\n\n")
    subject = subject.strip()
    body = body.strip()
    if "-m" in args:
        out: list[str] = []
        i = 0
        replaced = False
        while i < len(args):
            if args[i] == "-m" and i + 1 < len(args) and not replaced:
                out.extend(["-m", subject])
                if body:
                    out.extend(["-m", body])
                replaced = True
                i += 2
                continue
            if args[i] == "-m" and replaced:
                i += 2
                continue
            out.append(args[i])
            i += 1
        return out
    extra = ["-m", subject]
    if body:
        extra.extend(["-m", body])
    return [*args, *extra]


def execute_command(repo: Path, args: list[str]) -> CommandResult:
    validate_git_args(args)
    proc = _run_git(repo, args)
    return CommandResult(
        args=args,
        exit_code=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )


def execute_plan(
    repo: Path,
    plan: Plan,
    *,
    dry_run: bool = False,
    yes: bool = False,
    force_destructive: bool = False,
    confirmed: bool = False,
    destructive_confirmed: bool = False,
) -> list[CommandResult]:
    results: list[CommandResult] = []
    if dry_run:
        return [
            CommandResult(args=cmd.args, exit_code=0, skipped=True, skipped_reason="dry-run")
            for cmd in plan.commands
        ]
    for cmd in plan.commands:
        kind = classify(cmd.args)
        args = apply_commit_message(cmd.args, plan.commit_message)
        if kind != "read-only" and not yes and not confirmed:
            raise PermissionError("Plan was not confirmed.")
        if kind == "destructive" and not force_destructive and not destructive_confirmed:
            raise PermissionError("Destructive command requires extra confirmation.")
        result = execute_command(repo, args)
        results.append(result)
        if result.exit_code != 0:
            break
    return results


def annotate_commands(plan: Plan) -> Plan:
    commands: list[GitCommand] = []
    for cmd in plan.commands:
        kind = classify(cmd.args)
        commands.append(
            cmd.model_copy(
                update={"mutating": kind != "read-only", "destructive": kind == "destructive"}
            )
        )
    return plan.model_copy(update={"commands": commands})
