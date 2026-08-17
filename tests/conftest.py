from __future__ import annotations

from pathlib import Path

import pytest

from tests.gitutil import run_git


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    run_git(repo, "init", "-b", "main")
    run_git(repo, "config", "user.email", "dev@example.com")
    run_git(repo, "config", "user.name", "Dev")
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    run_git(repo, "add", "README.md")
    run_git(repo, "commit", "-m", "chore: initial")
    return repo
