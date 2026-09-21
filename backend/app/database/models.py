from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field


class Project(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    repo_type: str  # "git" or "zip"
    source: str  # URL or filename
    local_path: str  # Path to local workspace
    sandbox_path: Optional[str] = None  # Working copy inside sandbox
    status: str = "idle"  # idle, analyzing, planning, running_tests, fixing, completed, failed
    manifest_json: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TraceEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: str = Field(index=True)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str  # tool_call, tool_result, test_started, patch_applied, etc.
    tool_name: Optional[str] = None
    message: str
    payload_json: Optional[str] = None


class TestRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: str = Field(index=True)
    stage: str  # "baseline", "regression", "verification"
    passed: int = 0
    failed: int = 0
    errors: int = 0
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PatchRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: str = Field(index=True)
    attempt_number: int = 1
    file_path: str
    diff: str
    verified: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
