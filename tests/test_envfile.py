from __future__ import annotations

import os
from pathlib import Path

from gitman.envfile import load_env_files


def test_load_env_files_sets_missing_vars(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("GITMAN_PLANNER", raising=False)
    (tmp_path / ".env").write_text("GITMAN_PLANNER=fake\n", encoding="utf-8")
    loaded = load_env_files(tmp_path)
    assert loaded == [(tmp_path / ".env").resolve()]
    assert os.environ.get("GITMAN_PLANNER") == "fake"


def test_load_env_files_does_not_override(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("GITMAN_PLANNER", "fake")
    (tmp_path / ".env").write_text("GITMAN_PLANNER=from-file\n", encoding="utf-8")
    load_env_files(tmp_path)
    assert os.environ["GITMAN_PLANNER"] == "fake"


def test_load_env_files_skips_missing(tmp_path: Path) -> None:
    assert load_env_files(tmp_path) == []
