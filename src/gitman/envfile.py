from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


def load_env_files(*roots: Path | None) -> list[Path]:
    """Load `.env` from each root. Existing process env vars win."""
    loaded: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        if root is None:
            continue
        candidate = root if root.name == ".env" and root.is_file() else root / ".env"
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved in seen or not resolved.is_file():
            continue
        load_dotenv(resolved, override=False)
        seen.add(resolved)
        loaded.append(resolved)
    return loaded
