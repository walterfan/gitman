from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from gitman.cli import main
from gitman.models import GitCommand, Plan
from gitman.planner import FakePlanner, PlannerNotConfigured


def test_help_lists_ask_and_serve() -> None:
    result = CliRunner().invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "ask" in result.output
    assert "serve" in result.output


def test_ask_requires_prompt() -> None:
    result = CliRunner().invoke(main, ["ask"])
    assert result.exit_code != 0
    assert "prompt is required" in result.output


def test_ask_fails_outside_git_repo(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("gitman.cli.get_planner", lambda: FakePlanner())
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(main, ["ask", "show status"])
    assert result.exit_code != 0
    assert "No git repository found" in result.output


def test_ask_uses_repo_option(git_repo: Path, monkeypatch) -> None:
    monkeypatch.setattr("gitman.cli.get_planner", lambda: FakePlanner())
    result = CliRunner().invoke(main, ["ask", "show status", "--repo", str(git_repo), "--dry-run"])
    assert result.exit_code == 0
    assert "git status --short" in result.output


def test_ask_uses_cwd_work_tree(git_repo: Path, monkeypatch) -> None:
    monkeypatch.setattr("gitman.cli.get_planner", lambda: FakePlanner())
    monkeypatch.chdir(git_repo)
    result = CliRunner().invoke(main, ["ask", "show status", "--dry-run"])
    assert result.exit_code == 0
    assert "git status --short" in result.output


def test_ask_without_backend_does_not_mutate(git_repo: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "gitman.cli.get_planner",
        lambda: (_ for _ in ()).throw(PlannerNotConfigured("No LLM backend configured.")),
    )
    result = CliRunner().invoke(main, ["ask", "commit", "--repo", str(git_repo)])
    assert result.exit_code != 0
    assert "No LLM backend configured" in result.output


def test_ask_loads_planner_from_repo_dotenv(git_repo: Path, monkeypatch) -> None:
    monkeypatch.delenv("GITMAN_PLANNER", raising=False)
    monkeypatch.delenv("GITMAN_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("GITMAN_LLM_MODEL", raising=False)
    monkeypatch.delenv("GITMAN_LLM_API_KEY", raising=False)
    (git_repo / ".env").write_text("GITMAN_PLANNER=fake\n", encoding="utf-8")
    result = CliRunner().invoke(main, ["ask", "show status", "--repo", str(git_repo), "--dry-run"])
    assert result.exit_code == 0, result.output
    assert "git status --short" in result.output


def test_dry_run_does_not_commit(git_repo: Path, monkeypatch) -> None:
    (git_repo / "note.txt").write_text("x\n", encoding="utf-8")
    from tests.gitutil import run_git

    head_before = run_git(git_repo, "rev-parse", "HEAD").stdout.strip()
    plan = Plan(
        summary="Commit note",
        commands=[
            GitCommand(args=["add", "note.txt"]),
            GitCommand(args=["commit", "-m", "chore: update note.txt"]),
        ],
        commit_message="chore: update note.txt",
    )
    monkeypatch.setattr("gitman.cli.get_planner", lambda: FakePlanner(plan=plan))
    result = CliRunner().invoke(
        main, ["ask", "commit everything", "--repo", str(git_repo), "--dry-run"]
    )
    assert result.exit_code == 0
    assert "Dry-run" in result.output
    head_after = run_git(git_repo, "rev-parse", "HEAD").stdout.strip()
    assert head_after == head_before


def test_decline_does_not_mutate(git_repo: Path, monkeypatch) -> None:
    from tests.gitutil import run_git

    (git_repo / "note.txt").write_text("x\n", encoding="utf-8")
    head_before = run_git(git_repo, "rev-parse", "HEAD").stdout.strip()
    plan = Plan(
        summary="Commit note",
        commands=[GitCommand(args=["add", "note.txt"]), GitCommand(args=["commit", "-m", "x"])],
        commit_message="chore: update note.txt",
    )
    monkeypatch.setattr("gitman.cli.get_planner", lambda: FakePlanner(plan=plan))
    result = CliRunner().invoke(main, ["ask", "commit", "--repo", str(git_repo)], input="n\n")
    assert "Cancelled" in result.output
    assert run_git(git_repo, "rev-parse", "HEAD").stdout.strip() == head_before


def test_yes_runs_non_destructive(git_repo: Path, monkeypatch) -> None:
    from tests.gitutil import run_git

    (git_repo / "note.txt").write_text("x\n", encoding="utf-8")
    plan = Plan(
        summary="Commit note",
        commands=[
            GitCommand(args=["add", "note.txt"]),
            GitCommand(args=["commit", "-m", "chore: update note.txt"]),
        ],
        commit_message="chore: update note.txt",
    )
    monkeypatch.setattr("gitman.cli.get_planner", lambda: FakePlanner(plan=plan))
    result = CliRunner().invoke(main, ["ask", "commit", "--repo", str(git_repo), "--yes"])
    assert result.exit_code == 0
    message = run_git(git_repo, "log", "-1", "--pretty=%B").stdout.strip()
    assert message == "chore: update note.txt"


def test_yes_does_not_authorize_destructive(git_repo: Path, monkeypatch) -> None:
    from tests.gitutil import run_git

    head_before = run_git(git_repo, "rev-parse", "HEAD").stdout.strip()
    plan = Plan(summary="Hard reset", commands=[GitCommand(args=["reset", "--hard"])])
    monkeypatch.setattr("gitman.cli.get_planner", lambda: FakePlanner(plan=plan))
    result = CliRunner().invoke(
        main, ["ask", "reset hard", "--repo", str(git_repo), "--yes"], input="n\n"
    )
    assert "Cancelled" in result.output
    assert run_git(git_repo, "rev-parse", "HEAD").stdout.strip() == head_before


def test_rejects_non_git_binary(git_repo: Path, monkeypatch) -> None:
    plan = Plan(summary="bad", commands=[GitCommand(args=["rm", "-rf", "/"])])
    monkeypatch.setattr("gitman.cli.get_planner", lambda: FakePlanner(plan=plan))
    result = CliRunner().invoke(main, ["ask", "clean", "--repo", str(git_repo), "--yes"])
    assert result.exit_code != 0
    assert "Rejected" in result.output


def test_mid_plan_failure_stops(git_repo: Path, monkeypatch) -> None:
    from tests.gitutil import run_git

    head_before = run_git(git_repo, "rev-parse", "HEAD").stdout.strip()
    plan = Plan(
        summary="fail then commit",
        commands=[
            GitCommand(args=["commit", "-m", "no changes"]),
            GitCommand(args=["status", "--short"]),
        ],
    )
    monkeypatch.setattr("gitman.cli.get_planner", lambda: FakePlanner(plan=plan))
    result = CliRunner().invoke(main, ["ask", "commit", "--repo", str(git_repo), "--yes"])
    assert result.exit_code != 0
    assert "failed" in result.output
    assert run_git(git_repo, "rev-parse", "HEAD").stdout.strip() == head_before
