import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.repository.analyzer import RepositoryAnalyzer
from app.agent.tools.filesystem import FilesystemTools
from app.agent.tools.patching import PatchingTools

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "docker_available" in data
    assert "nebius_configured" in data


def test_repository_analyzer():
    demo_dir = Path(__file__).parent.parent.parent / "demo-repository"
    assert demo_dir.exists()
    manifest = RepositoryAnalyzer.analyze(demo_dir)
    assert manifest.language == "python"
    assert manifest.test_framework == "pytest"
    assert len(manifest.test_files) >= 3
    assert len(manifest.source_files) >= 3


def test_filesystem_and_patching_tools(tmp_path):
    # Test write_file
    res = FilesystemTools.write_file(tmp_path, "sample.py", "def foo():\n    return 1\n")
    assert res["success"] is True

    # Test read_file
    read_res = FilesystemTools.read_file(tmp_path, "sample.py")
    assert "def foo():" in read_res["content"]

    # Test search_code
    search_res = FilesystemTools.search_code(tmp_path, "foo")
    assert len(search_res["matches"]) == 1

    # Test patch
    patch_res = PatchingTools.apply_patch(tmp_path, "sample.py", "return 1", "return 2")
    assert patch_res["success"] is True

    # Test diff
    orig_dir = tmp_path / "orig"
    orig_dir.mkdir()
    (orig_dir / "sample.py").write_text("def foo():\n    return 1\n")
    diff = PatchingTools.compute_diff(orig_dir, tmp_path)
    assert "-    return 1" in diff
    assert "+    return 2" in diff


def test_create_and_run_demo_project():
    # 1. Create project with demo repo
    response = client.post(
        "/api/projects",
        data={"name": "Demo Buggy Repo", "repo_type": "demo"}
    )
    assert response.status_code == 200
    project = response.json()
    project_id = project["id"]
    assert project["name"] == "Demo Buggy Repo"
    assert project["manifest"]["language"] == "python"

    # 2. Get status
    status_resp = client.get(f"/api/projects/{project_id}/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "idle"

    # 3. Trigger agent run synchronously by running orchestrator directly
    from app.agent.orchestrator import AgentOrchestrator
    from app.config import settings
    import asyncio

    project_dir = settings.WORKSPACE_DIR / project_id
    orchestrator = AgentOrchestrator(project_id=project_id, project_dir=project_dir)
    result = asyncio.run(orchestrator.run(project["manifest"]))
    assert result["status"] == "completed"
    assert result["verified"] is True
    assert len(result["diff"]) > 0

    # 4. Check diff endpoint
    diff_resp = client.get(f"/api/projects/{project_id}/diff")
    assert diff_resp.status_code == 200
    diff_data = diff_resp.json()
    assert diff_data["has_changes"] is True
    assert "quantity == 0" in diff_data["diff"] or "def" in diff_data["diff"]

    # 5. Check trace events
    trace_resp = client.get(f"/api/projects/{project_id}/trace")
    assert trace_resp.status_code == 200
    events = trace_resp.json()
    assert len(events) >= 5
