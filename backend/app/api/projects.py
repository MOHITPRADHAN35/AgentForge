import os
import uuid
import json
import asyncio
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from sqlmodel import Session, select

from app.config import settings
from app.database.session import engine
from app.database.models import Project, TraceEvent, TestRun
from app.repository.loader import RepositoryLoader
from app.repository.analyzer import RepositoryAnalyzer
from app.agent.orchestrator import AgentOrchestrator
from app.agent.tools.patching import PatchingTools
from app.api.ws import ws_manager

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("")
def list_projects():
    with Session(engine) as session:
        projects = session.exec(select(Project).order_by(Project.created_at.desc())).all()
        return projects


@router.post("")
async def create_project(
    name: str = Form(...),
    repo_type: str = Form(...),  # "git", "zip", or "demo"
    git_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    project_id = str(uuid.uuid4())[:8]
    project_dir = settings.WORKSPACE_DIR / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    if repo_type == "git":
        if not git_url:
            raise HTTPException(status_code=400, detail="git_url is required for git repo_type")
        source_val = git_url
        try:
            RepositoryLoader.from_git(git_url, project_dir)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to clone repository: {str(e)}")

    elif repo_type == "zip":
        if not file:
            raise HTTPException(status_code=400, detail="Zip file is required for zip repo_type")
        source_val = file.filename or "uploaded.zip"
        content = await file.read()
        try:
            RepositoryLoader.from_zip(content, project_dir)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to extract zip file: {str(e)}")

    elif repo_type == "demo":
        source_val = "demo-repository"
        demo_path = Path("./demo-repository").resolve()
        if not demo_path.exists():
            raise HTTPException(status_code=500, detail="Demo repository template not found on server")
        RepositoryLoader.from_local_dir(demo_path, project_dir)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported repo_type: {repo_type}")

    # Analyze immediately
    source_dir = project_dir / "source"
    manifest = RepositoryAnalyzer.analyze(source_dir)

    project = Project(
        id=project_id,
        name=name,
        repo_type=repo_type,
        source=source_val,
        local_path=str(source_dir),
        sandbox_path=str(project_dir / "sandbox_workspace"),
        status="idle",
        manifest_json=manifest.model_dump_json()
    )

    with Session(engine) as session:
        session.add(project)
        session.commit()
        session.refresh(project)

    return {
        "id": project.id,
        "name": project.name,
        "repo_type": project.repo_type,
        "source": project.source,
        "status": project.status,
        "manifest": manifest.model_dump()
    }


@router.get("/{project_id}")
def get_project(project_id: str):
    with Session(engine) as session:
        project = session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        manifest = json.loads(project.manifest_json) if project.manifest_json else {}
        return {
            "id": project.id,
            "name": project.name,
            "repo_type": project.repo_type,
            "source": project.source,
            "status": project.status,
            "manifest": manifest,
            "created_at": project.created_at
        }


@router.post("/{project_id}/analyze")
def analyze_project(project_id: str):
    with Session(engine) as session:
        project = session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        source_dir = Path(project.local_path)
        manifest = RepositoryAnalyzer.analyze(source_dir)
        project.manifest_json = manifest.model_dump_json()
        session.add(project)
        session.commit()

        return manifest.model_dump()


async def run_agent_task(project_id: str, project_dir: Path, manifest: dict):
    # Callback to stream events to WebSocket
    async def on_event(event_dict):
        await ws_manager.broadcast_to_project(project_id, event_dict)

    orchestrator = AgentOrchestrator(
        project_id=project_id,
        project_dir=project_dir,
        event_callback=on_event
    )

    with Session(engine) as session:
        project = session.get(Project, project_id)
        if project:
            project.status = "running"
            session.add(project)
            session.commit()

    result = await orchestrator.run(manifest)

    with Session(engine) as session:
        project = session.get(Project, project_id)
        if project:
            project.status = result.get("status", "completed")
            session.add(project)
            session.commit()


@router.post("/{project_id}/agent/run")
async def trigger_agent(project_id: str, background_tasks: BackgroundTasks):
    with Session(engine) as session:
        project = session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        manifest = json.loads(project.manifest_json) if project.manifest_json else {}
        project_dir = settings.WORKSPACE_DIR / project_id

        background_tasks.add_task(run_agent_task, project_id, project_dir, manifest)

        return {"status": "started", "project_id": project_id}


@router.get("/{project_id}/status")
def get_project_status(project_id: str):
    with Session(engine) as session:
        project = session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"project_id": project_id, "status": project.status}


@router.get("/{project_id}/diff")
def get_project_diff(project_id: str):
    with Session(engine) as session:
        project = session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    project_dir = settings.WORKSPACE_DIR / project_id
    source_dir = project_dir / "source"
    sandbox_dir = project_dir / "sandbox_workspace"

    if not sandbox_dir.exists():
        return {"diff": "", "has_changes": False}

    diff = PatchingTools.compute_diff(source_dir, sandbox_dir)
    return {"diff": diff, "has_changes": bool(diff.strip())}


@router.get("/{project_id}/tests")
def get_project_tests(project_id: str):
    with Session(engine) as session:
        project = session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        tests = session.exec(select(TestRun).where(TestRun.project_id == project_id).order_by(TestRun.timestamp.asc())).all()
        return tests


@router.get("/{project_id}/trace")
def get_project_trace(project_id: str):
    with Session(engine) as session:
        project = session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        traces = session.exec(select(TraceEvent).where(TraceEvent.project_id == project_id).order_by(TraceEvent.timestamp.asc())).all()
        return [
            {
                "id": t.id,
                "timestamp": t.timestamp.isoformat(),
                "event_type": t.event_type,
                "tool_name": t.tool_name,
                "message": t.message,
                "payload": json.loads(t.payload_json) if t.payload_json else None
            }
            for t in traces
        ]

