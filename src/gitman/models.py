from __future__ import annotations

from pydantic import BaseModel, Field


class GitCommand(BaseModel):
    args: list[str]
    mutating: bool = False
    destructive: bool = False


class Plan(BaseModel):
    summary: str
    commands: list[GitCommand] = Field(default_factory=list)
    commit_message: str | None = None
    warnings: list[str] = Field(default_factory=list)


class CommandResult(BaseModel):
    args: list[str]
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    skipped: bool = False
    skipped_reason: str | None = None
