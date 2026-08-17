from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from gitman.envfile import load_env_files
from gitman.gitops import (
    NotAGitRepoError,
    annotate_commands,
    collect_snapshot,
    execute_plan,
    resolve_repo,
)
from gitman.models import Plan
from gitman.planner import PlannerError, PlannerNotConfigured, get_planner
from gitman.safety import UnsafeCommandError

STATIC_DIR = Path(__file__).parent / "static"


class PlanRequest(BaseModel):
    prompt: str


class ExecuteRequest(BaseModel):
    plan: Plan
    confirm: bool = False
    destructive_confirm: bool = False
    repo: str | None = None


def create_app(repo: Path) -> FastAPI:
    load_env_files(Path.cwd(), repo)
    app = FastAPI(title="gitman")
    app.state.repo = repo.resolve()

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.post("/api/plan")
    def api_plan(body: PlanRequest) -> Plan:
        if not body.prompt.strip():
            raise HTTPException(status_code=400, detail="a prompt is required")
        try:
            planner = get_planner()
        except PlannerNotConfigured as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        snapshot = collect_snapshot(app.state.repo)
        try:
            return annotate_commands(planner.plan(body.prompt, snapshot))
        except PlannerError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except UnsafeCommandError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/execute")
    def api_execute(body: ExecuteRequest) -> dict:
        if body.repo:
            try:
                requested = resolve_repo(Path(body.repo))
            except NotAGitRepoError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            if requested != app.state.repo:
                raise HTTPException(
                    status_code=403, detail="Repo path is outside the serve-time target."
                )
        try:
            plan = annotate_commands(body.plan)
        except UnsafeCommandError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if any(cmd.destructive for cmd in plan.commands) and not body.destructive_confirm:
            raise HTTPException(
                status_code=400,
                detail="Destructive command requires extra confirmation.",
            )
        try:
            results = execute_plan(
                app.state.repo,
                plan,
                confirmed=body.confirm,
                destructive_confirmed=body.destructive_confirm,
                yes=body.confirm,
            )
        except PermissionError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except UnsafeCommandError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"results": [item.model_dump() for item in results]}

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app
