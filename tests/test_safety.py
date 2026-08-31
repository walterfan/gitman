from __future__ import annotations

import pytest

from gitman.safety import UnsafeCommandError, classify


def test_status_is_read_only() -> None:
    assert classify(["status", "--short"]) == "read-only"


def test_commit_is_mutating() -> None:
    assert classify(["commit", "-m", "msg"]) == "mutating"


def test_reset_hard_is_destructive() -> None:
    assert classify(["reset", "--hard"]) == "destructive"


def test_force_push_is_destructive() -> None:
    assert classify(["push", "--force"]) == "destructive"
    assert classify(["push", "--force-with-lease"]) == "destructive"


def test_clean_force_is_destructive() -> None:
    assert classify(["clean", "-fd"]) == "destructive"


def test_rebase_is_destructive() -> None:
    assert classify(["rebase", "main"]) == "destructive"


def test_rejects_rm() -> None:
    with pytest.raises(UnsafeCommandError):
        classify(["rm", "-rf", "."])


def test_rm_cached_is_allowed() -> None:
    assert classify(["rm", "--cached", "secret.txt"]) == "mutating"


def test_rejects_bash() -> None:
    with pytest.raises(UnsafeCommandError):
        classify(["bash", "-c", "git status"])


def test_rejects_shell_metacharacters() -> None:
    with pytest.raises(UnsafeCommandError):
        classify(["status", "--short;rm -rf /"])
