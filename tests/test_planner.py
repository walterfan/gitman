from __future__ import annotations

import json

import pytest

from gitman.gitops import collect_snapshot
from gitman.messages import commit_message_from_snapshot
from gitman.models import GitCommand, Plan
from gitman.planner import FakePlanner, PlanParseError, heuristic_plan, parse_plan_json
from tests.gitutil import run_git


def test_parse_plan_json_success() -> None:
    plan = parse_plan_json(
        json.dumps(
            {
                "summary": "Stage src and commit",
                "commands": [{"args": ["add", "src"]}, {"args": ["commit", "-m", "feat: x"]}],
                "commit_message": "feat: x",
                "warnings": [],
            }
        )
    )
    assert plan.summary
    assert plan.commands[0].args == ["add", "src"]


def test_parse_plan_json_invalid() -> None:
    with pytest.raises(PlanParseError):
        parse_plan_json("not json at all")


def test_fake_planner_invalid_raw(git_repo) -> None:
    snapshot = collect_snapshot(git_repo)
    planner = FakePlanner(raw="nope")
    with pytest.raises(PlanParseError):
        planner.plan("commit", snapshot)


def test_heuristic_status_plan(git_repo) -> None:
    snapshot = collect_snapshot(git_repo)
    plan = heuristic_plan("show status", snapshot)
    assert plan.commands[0].args[0] == "status"


def test_ambiguous_undo_is_read_only(git_repo) -> None:
    (git_repo / "note.txt").write_text("x\n", encoding="utf-8")
    snapshot = collect_snapshot(git_repo)
    plan = heuristic_plan("undo", snapshot)
    assert plan.warnings
    assert all(cmd.args[0] == "status" for cmd in plan.commands)


def test_commit_message_from_staged_cli(git_repo) -> None:
    path = git_repo / "src" / "gitman"
    path.mkdir(parents=True)
    (path / "cli.py").write_text("def main():\n    print('ask and serve')\n", encoding="utf-8")
    run_git(git_repo, "add", "src/gitman/cli.py")
    snapshot = collect_snapshot(git_repo)
    message = commit_message_from_snapshot(snapshot)
    assert message is not None
    assert message.startswith("feat:")
    assert "cli.py" in message
    assert "secret.txt" not in message


def test_empty_tree_has_no_commit_message(git_repo) -> None:
    snapshot = collect_snapshot(git_repo)
    assert commit_message_from_snapshot(snapshot) is None
    plan = heuristic_plan("commit the staged changes", snapshot)
    assert plan.commit_message is None
    assert all(cmd.args[0] != "commit" for cmd in plan.commands)


def test_commit_uses_generated_message(git_repo, monkeypatch) -> None:
    from click.testing import CliRunner

    from gitman.cli import main

    path = git_repo / "src" / "gitman"
    path.mkdir(parents=True)
    (path / "cli.py").write_text("def extra():\n    pass\n", encoding="utf-8")
    run_git(git_repo, "add", "src/gitman/cli.py")
    snapshot = collect_snapshot(git_repo)
    message = commit_message_from_snapshot(snapshot)
    assert message is not None
    plan = Plan(
        summary="Commit CLI",
        commands=[GitCommand(args=["commit", "-m", "<generated message>"])],
        commit_message=message,
    )
    monkeypatch.setattr("gitman.cli.get_planner", lambda: FakePlanner(plan=plan))
    result = CliRunner().invoke(main, ["ask", "commit", "--repo", str(git_repo), "--yes"])
    assert result.exit_code == 0, result.output
    logged = run_git(git_repo, "log", "-1", "--pretty=%B").stdout.strip()
    assert logged == message


def test_llm_tls_verify_defaults_to_true(monkeypatch) -> None:
    monkeypatch.delenv("GITMAN_LLM_VERIFY_SSL", raising=False)
    monkeypatch.delenv("GITMAN_LLM_CA_BUNDLE", raising=False)
    monkeypatch.delenv("SSL_CERT_FILE", raising=False)
    monkeypatch.delenv("REQUESTS_CA_BUNDLE", raising=False)
    monkeypatch.delenv("CURL_CA_BUNDLE", raising=False)
    from gitman.planner import llm_tls_verify

    assert llm_tls_verify() is True


def test_llm_tls_verify_ca_bundle(monkeypatch, tmp_path) -> None:
    bundle = tmp_path / "corp-ca.pem"
    monkeypatch.setenv("GITMAN_LLM_VERIFY_SSL", "true")
    monkeypatch.setenv("GITMAN_LLM_CA_BUNDLE", str(bundle))
    from gitman.planner import llm_tls_verify

    assert llm_tls_verify() == str(bundle)


def test_llm_tls_verify_can_be_disabled(monkeypatch) -> None:
    monkeypatch.setenv("SSL_CERT_FILE", "/etc/ssl/corp.pem")
    monkeypatch.setenv("GITMAN_LLM_CA_BUNDLE", "/tmp/corp.pem")
    monkeypatch.setenv("GITMAN_LLM_VERIFY_SSL", "false")
    from gitman.planner import llm_tls_verify

    assert llm_tls_verify() is False


def test_ssl_connect_error_becomes_planner_error(git_repo, monkeypatch) -> None:
    import httpx

    from gitman.planner import OpenAICompatiblePlanner, PlannerError

    class BoomClient:
        def __init__(self, *args, **kwargs):
            raise httpx.ConnectError(
                "[SSL: CERTIFICATE_VERIFY_FAILED] self-signed certificate"
            )

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(httpx, "Client", BoomClient)
    snapshot = collect_snapshot(git_repo)
    planner = OpenAICompatiblePlanner("https://api.example.com", "demo", None)
    with pytest.raises(PlannerError, match="GITMAN_LLM_CA_BUNDLE"):
        planner.plan("show status", snapshot)
