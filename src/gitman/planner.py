from __future__ import annotations

import json
import os
import re
from typing import Protocol

import httpx
from pydantic import ValidationError

from gitman.gitops import GitSnapshot
from gitman.messages import commit_message_from_snapshot
from gitman.models import GitCommand, Plan

SYSTEM_PROMPT = """You are a local git expert. Return ONLY JSON with keys:
summary (string), commands (array of {args: string[]}),
commit_message (string or null), warnings (string[]).
Each commands[].args is a git subcommand and its arguments,
without the git binary and without a shell.
Never invent file paths that are not in the provided status/diff snapshot.
To stage a deleted file, use `add -A` or `add <path>` instead of `rm`.
`rm` is only allowed with `--cached` (unstage/untrack without touching the
working tree); plain `rm` is always rejected because it deletes files on disk.
If the request is ambiguous (for example "undo" when both uncommitted
changes and a HEAD commit exist), return only read-only inspection
commands and a warning; do not mutate.
If a commit is requested and the snapshot has no changes,
set commit_message to null and do not include commit.
Prefer conventional commit subjects (feat:, fix:, docs:, refactor:, test:, chore:).
"""


class PlannerError(RuntimeError):
    pass


class PlannerNotConfigured(PlannerError):
    pass


class PlanParseError(PlannerError):
    pass


def llm_tls_verify() -> bool | str:
    flag = os.environ.get("GITMAN_LLM_VERIFY_SSL", "true").strip().lower().strip("\"'")
    if flag in {"0", "false", "no", "off"}:
        return False
    for key in (
        "GITMAN_LLM_CA_BUNDLE",
        "SSL_CERT_FILE",
        "REQUESTS_CA_BUNDLE",
        "CURL_CA_BUNDLE",
    ):
        path = os.environ.get(key, "").strip().strip("\"'")
        if path:
            return path
    return True


def _explain_llm_request_error(exc: httpx.RequestError) -> str:
    detail = str(exc)
    if "CERTIFICATE" in detail.upper() or "SSL" in detail.upper():
        return (
            "Could not connect to the LLM API because TLS verification failed "
            "(often a company HTTP proxy with a private CA). "
            "Set GITMAN_LLM_CA_BUNDLE to your corporate root CA file, "
            "or set GITMAN_LLM_VERIFY_SSL=false if you accept the risk."
        )
    return f"Could not connect to the LLM API: {exc}"


class Planner(Protocol):
    def plan(self, prompt: str, snapshot: GitSnapshot) -> Plan: ...


class FakePlanner:
    def __init__(self, plan: Plan | None = None, raw: str | None = None) -> None:
        self._plan = plan
        self._raw = raw

    def plan(self, prompt: str, snapshot: GitSnapshot) -> Plan:
        if self._raw is not None:
            raise PlanParseError("Planner output was not valid plan JSON.")
        if self._plan is not None:
            return self._plan
        return heuristic_plan(prompt, snapshot)


def heuristic_plan(prompt: str, snapshot: GitSnapshot) -> Plan:
    text = prompt.strip().lower()
    if text in {"undo", "undo that"} and snapshot.has_changes and snapshot.has_head:
        return Plan(
            summary="Ambiguous undo: inspect first",
            commands=[GitCommand(args=["status", "--short"])],
            warnings=[
                "Both uncommitted changes and a HEAD commit exist. "
                "Say whether to discard working-tree changes or undo the last commit."
            ],
        )
    if "status" in text or text == "show status":
        return Plan(
            summary="Show short git status", commands=[GitCommand(args=["status", "--short"])]
        )
    if "commit" in text:
        message = commit_message_from_snapshot(snapshot)
        if message is None:
            return Plan(
                summary="Nothing to commit",
                commands=[GitCommand(args=["status", "--short"])],
                warnings=["Working tree has no staged or unstaged changes."],
            )
        commands = []
        if any(
            len(line) >= 2 and line[1] not in {" ", "?"} for line in snapshot.status.splitlines()
        ) or any(line.startswith("??") for line in snapshot.status.splitlines()):
            commands.append(GitCommand(args=["add", "-A"]))
        commands.append(GitCommand(args=["commit", "-m", message]))
        return Plan(summary=f"Commit changes: {message}", commands=commands, commit_message=message)
    return Plan(
        summary="Show repository status",
        commands=[GitCommand(args=["status", "--short"])],
        warnings=["Prompt was too vague for a mutating plan."],
    )


class OpenAICompatiblePlanner:
    def __init__(self, base_url: str, model: str, api_key: str | None) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key

    def plan(self, prompt: str, snapshot: GitSnapshot) -> Plan:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(
                        {"prompt": prompt, "snapshot": snapshot.planner_context()}
                    ),
                },
            ],
            "temperature": 0,
        }
        try:
            with httpx.Client(verify=llm_tls_verify(), timeout=60.0) as client:
                response = client.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise PlannerError(
                f"LLM API returned HTTP {exc.response.status_code}. "
                "Check GITMAN_LLM_BASE_URL and the model name."
            ) from exc
        except httpx.RequestError as exc:
            raise PlannerError(_explain_llm_request_error(exc)) from exc
        content = response.json()["choices"][0]["message"]["content"]
        return parse_plan_json(content)


_JSON_BLOCK = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def parse_plan_json(text: str) -> Plan:
    candidate = text.strip()
    match = _JSON_BLOCK.search(candidate)
    if match:
        candidate = match.group(1)
    try:
        return Plan.model_validate_json(candidate)
    except (ValidationError, ValueError) as exc:
        raise PlanParseError("Planner output was not valid plan JSON.") from exc


def configured_planner() -> Planner:
    if os.environ.get("GITMAN_PLANNER") == "fake":
        return FakePlanner()
    base = os.environ.get("GITMAN_LLM_BASE_URL")
    model = os.environ.get("GITMAN_LLM_MODEL")
    key = os.environ.get("GITMAN_LLM_API_KEY")
    if not base or not model:
        raise PlannerNotConfigured(
            "No LLM backend configured. Set GITMAN_LLM_BASE_URL and GITMAN_LLM_MODEL "
            "(optional GITMAN_LLM_API_KEY) in the environment or a `.env` file. "
            "Example: GITMAN_LLM_BASE_URL=http://127.0.0.1:11434/v1"
        )
    return OpenAICompatiblePlanner(base_url=base, model=model, api_key=key)


_override: Planner | None = None


def get_planner() -> Planner:
    if _override is not None:
        return _override
    return configured_planner()


def set_planner(planner: Planner | None) -> None:
    global _override
    _override = planner
