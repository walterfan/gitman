from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner
from fastapi.testclient import TestClient

from gitman.cli import main
from gitman.models import GitCommand, Plan
from gitman.planner import FakePlanner
from gitman.server import create_app
from tests.gitutil import run_git


def test_serve_help_mentions_host_and_port() -> None:
    result = CliRunner().invoke(main, ["serve", "--help"])
    assert result.exit_code == 0
    assert "--host" in result.output
    assert "--port" in result.output


def test_serve_explicit_port_unavailable(git_repo, monkeypatch) -> None:
    monkeypatch.setattr(
        "gitman.cli.choose_port",
        lambda _host, _port: (_ for _ in ()).throw(OSError("Requested port 9999 is unavailable.")),
    )
    result = CliRunner().invoke(main, ["serve", "--repo", str(git_repo), "--port", "9999"])
    assert result.exit_code != 0
    assert "unavailable" in result.output


def test_plan_and_execute_round_trip(git_repo, monkeypatch) -> None:
    (git_repo / "note.txt").write_text("ui\n", encoding="utf-8")
    plan = Plan(
        summary="Commit note",
        commands=[
            GitCommand(args=["add", "note.txt"]),
            GitCommand(args=["commit", "-m", "chore: update note.txt"]),
        ],
        commit_message="chore: update note.txt",
    )
    monkeypatch.setattr("gitman.server.get_planner", lambda: FakePlanner(plan=plan))
    client = TestClient(create_app(git_repo))
    home = client.get("/")
    assert home.status_code == 200
    assert "gitman" in home.text
    planned = client.post("/api/plan", json={"prompt": "commit the note"})
    assert planned.status_code == 200
    body = planned.json()
    assert body["summary"]
    assert body["commands"]
    declined = client.post("/api/execute", json={"plan": body, "confirm": False})
    assert declined.status_code == 400
    executed = client.post("/api/execute", json={"plan": body, "confirm": True})
    assert executed.status_code == 200
    message = run_git(git_repo, "log", "-1", "--pretty=%s").stdout.strip()
    assert message == "chore: update note.txt"


def test_execute_rejects_other_repo(git_repo, tmp_path: Path, monkeypatch) -> None:
    other = tmp_path / "other"
    other.mkdir()
    run_git(other, "init", "-b", "main")
    run_git(other, "config", "user.email", "dev@example.com")
    run_git(other, "config", "user.name", "Dev")
    (other / "README.md").write_text("o\n", encoding="utf-8")
    run_git(other, "add", "README.md")
    run_git(other, "commit", "-m", "init")
    plan = Plan(summary="status", commands=[GitCommand(args=["status", "--short"])])
    monkeypatch.setattr("gitman.server.get_planner", lambda: FakePlanner(plan=plan))
    client = TestClient(create_app(git_repo))
    response = client.post(
        "/api/execute",
        json={"plan": plan.model_dump(), "confirm": True, "repo": str(other)},
    )
    assert response.status_code == 403


def test_destructive_requires_extra_confirm(git_repo) -> None:
    client = TestClient(create_app(git_repo))
    plan = Plan(summary="reset", commands=[GitCommand(args=["reset", "--hard"])])
    response = client.post(
        "/api/execute",
        json={"plan": plan.model_dump(), "confirm": True, "destructive_confirm": False},
    )
    assert response.status_code == 400
    assert "Destructive" in response.json()["detail"]
