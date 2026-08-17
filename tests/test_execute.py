from __future__ import annotations

import pytest

from gitman.gitops import execute_plan
from gitman.models import GitCommand, Plan
from gitman.safety import UnsafeCommandError


def test_dry_run_skips_mutating_git(git_repo) -> None:
    from tests.gitutil import run_git

    head = run_git(git_repo, "rev-parse", "HEAD").stdout.strip()
    plan = Plan(
        summary="commit",
        commands=[GitCommand(args=["commit", "--allow-empty", "-m", "nope"])],
        commit_message="nope",
    )
    results = execute_plan(git_repo, plan, dry_run=True)
    assert all(item.skipped for item in results)
    assert run_git(git_repo, "rev-parse", "HEAD").stdout.strip() == head


def test_unconfirmed_mutating_plan_raises(git_repo) -> None:
    plan = Plan(summary="add", commands=[GitCommand(args=["add", "-A"])])
    with pytest.raises(PermissionError):
        execute_plan(git_repo, plan, confirmed=False)


def test_non_git_binary_rejected(git_repo) -> None:
    plan = Plan(summary="bad", commands=[GitCommand(args=["rm", "-rf", "."])])
    with pytest.raises(UnsafeCommandError):
        execute_plan(git_repo, plan, confirmed=True, yes=True)


def test_mid_plan_stops_after_failure(git_repo) -> None:
    plan = Plan(
        summary="fail",
        commands=[
            GitCommand(args=["commit", "-m", "empty"]),
            GitCommand(args=["status", "--short"]),
        ],
    )
    results = execute_plan(git_repo, plan, yes=True)
    assert results[0].exit_code != 0
    assert len(results) == 1


def test_commit_message_body_uses_two_dash_m(git_repo) -> None:
    from tests.gitutil import run_git

    (git_repo / "note.txt").write_text("body\n", encoding="utf-8")
    run_git(git_repo, "add", "note.txt")
    plan = Plan(
        summary="commit",
        commands=[GitCommand(args=["commit"])],
        commit_message="chore: update note.txt\n\nInclude the new note file.",
    )
    results = execute_plan(git_repo, plan, yes=True)
    assert results[0].exit_code == 0, results[0].stderr
    message = run_git(git_repo, "log", "-1", "--pretty=%B").stdout
    assert message.startswith("chore: update note.txt")
    assert "Include the new note file." in message
