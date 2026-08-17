from __future__ import annotations

import re

FORBIDDEN_BINARIES = {
    "rm",
    "bash",
    "sh",
    "zsh",
    "python",
    "python3",
    "curl",
    "wget",
    "sudo",
    "chmod",
    "chown",
    "kill",
    "dd",
}

READ_ONLY_SUBCOMMANDS = {
    "status",
    "log",
    "diff",
    "show",
    "rev-parse",
    "describe",
    "ls-files",
    "cat-file",
    "blame",
    "version",
    "help",
    "grep",
    "shortlog",
    "ls-tree",
    "rev-list",
    "name-rev",
    "check-ignore",
}

SHELL_META = re.compile(r"[;|&`$]")


class UnsafeCommandError(ValueError):
    pass


def validate_git_args(args: list[str]) -> None:
    if not args:
        raise UnsafeCommandError("Empty git command.")
    first = args[0]
    if first in FORBIDDEN_BINARIES or first == "git" or "/" in first or "\\" in first:
        raise UnsafeCommandError(f"Rejected non-git command: {first}")
    if first.endswith(".sh") or first.endswith(".exe"):
        raise UnsafeCommandError(f"Rejected non-git command: {first}")
    message_indexes: set[int] = set()
    index = 0
    while index < len(args):
        if args[index] == "-m" and index + 1 < len(args):
            message_indexes.add(index + 1)
            index += 2
            continue
        index += 1
    for index, arg in enumerate(args):
        if index in message_indexes:
            continue
        if SHELL_META.search(arg):
            raise UnsafeCommandError("Rejected shell metacharacters in git args.")


def is_destructive(args: list[str]) -> bool:
    sub, rest = args[0], args[1:]
    if sub == "reset" and "--hard" in rest:
        return True
    if sub == "clean" and any(item.startswith("-") and "f" in item.lstrip("-") for item in rest):
        return True
    if sub == "push" and (
        "-f" in rest or "--force" in rest or any(item.startswith("--force") for item in rest)
    ):
        return True
    if sub in {"checkout", "restore"} and (
        "--" in rest or "-f" in rest or "--force" in rest or "--worktree" in rest
    ):
        return True
    if sub == "branch" and "-D" in rest:
        return True
    if sub == "rebase":
        return True
    if sub == "commit" and "--amend" in rest:
        return True
    if sub in {"filter-branch", "filter-repo"}:
        return True
    return sub == "update-ref" and "-d" in rest


def classify(args: list[str]) -> str:
    validate_git_args(args)
    if is_destructive(args):
        return "destructive"
    sub, rest = args[0], args[1:]
    if sub == "branch" and any(item in rest for item in ("-d", "--delete")):
        return "mutating"
    if sub in READ_ONLY_SUBCOMMANDS:
        return "read-only"
    if sub == "remote" and not rest:
        return "read-only"
    if sub == "branch" and not any(
        item.startswith("-") and item not in {"-a", "-v", "-vv", "-r"} for item in rest
    ):
        return "read-only"
    return "mutating"
