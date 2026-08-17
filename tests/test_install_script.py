from __future__ import annotations

from pathlib import Path


def test_install_script_documents_prerequisites() -> None:
    script = Path("install.sh").read_text(encoding="utf-8")
    assert "python3.13 python3.12 python3.11 python3" in script
    assert "command -v uv" in script
    assert "uv sync" in script
    assert "uv build" in script
    assert "uv pip install" in script
    assert "GITMAN_DEFAULT_REPO" in script
    assert "uninstall" in script
    assert "${APP_NAME} --help" in script
    assert "Missing prerequisite: uv" in script
    assert "Missing prerequisite: Python" in script
