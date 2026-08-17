from __future__ import annotations

from gitman.gitops import GitSnapshot


def commit_message_from_snapshot(snapshot: GitSnapshot) -> str | None:
    paths = snapshot.changed_paths()
    if not paths:
        return None
    blob = f"{snapshot.status}\n{snapshot.staged_diff}\n{snapshot.unstaged_diff}"
    prefix = _prefix_for(paths, blob)
    summary = ", ".join(paths[:3])
    return f"{prefix}: update {summary}"


def _prefix_for(paths: list[str], blob: str) -> str:
    lowered = blob.lower()
    if all(path.endswith(".md") for path in paths):
        return "docs"
    if all(
        path.startswith("tests/") or path.startswith("test_") or "/test_" in path for path in paths
    ):
        return "test"
    if any(
        line.startswith("A ") or line.startswith("A\t") or line[0] == "A"
        for line in blob.splitlines()
        if line
    ):
        if "cli" in lowered or "command" in lowered or any("cli" in path for path in paths):
            return "feat"
        return "feat"
    if "fix" in lowered:
        return "fix"
    if "refactor" in lowered:
        return "refactor"
    return "chore"
