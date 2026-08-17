from __future__ import annotations

from gitman.gitops import DIFF_CAP, collect_snapshot
from gitman.redact import redact


def test_snapshot_includes_branch_status_and_diff(git_repo) -> None:
    (git_repo / "note.txt").write_text("hello\n", encoding="utf-8")
    snapshot = collect_snapshot(git_repo)
    assert snapshot.branch == "main"
    assert "note.txt" in snapshot.status
    assert snapshot.has_head


def test_snapshot_truncates_large_diff(git_repo) -> None:
    (git_repo / "big.txt").write_text("x" * (DIFF_CAP + 50) + "\n", encoding="utf-8")
    from tests.gitutil import run_git

    run_git(git_repo, "add", "big.txt")
    snapshot = collect_snapshot(git_repo, diff_cap=100)
    assert snapshot.truncated
    assert any("truncated" in warning.lower() for warning in snapshot.warnings)
    assert len(snapshot.staged_diff) <= 100


def test_planner_context_redacts_secrets(git_repo) -> None:
    (git_repo / ".env").write_text("API_KEY=supersecretvalue\n", encoding="utf-8")
    from tests.gitutil import run_git

    run_git(git_repo, "add", ".env")
    snapshot = collect_snapshot(git_repo)
    context = snapshot.planner_context()
    blob = f"{context['status']}\n{context['staged_diff']}"
    assert "supersecretvalue" not in blob
    assert "<redacted>" in redact("token=ghp_abcdefghijklmnopqrstuvwxyz123456")
