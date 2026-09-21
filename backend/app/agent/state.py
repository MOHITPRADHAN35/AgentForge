from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class AgentState(str, Enum):
    IDLE = "IDLE"
    INGESTING = "INGESTING"
    ANALYZING = "ANALYZING"
    PLANNING = "PLANNING"
    RUNNING_TESTS = "RUNNING_TESTS"
    ANALYZING_FAILURE = "ANALYZING_FAILURE"
    GENERATING_PATCH = "GENERATING_PATCH"
    APPLYING_PATCH = "APPLYING_PATCH"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AgentEvent(BaseModel):
    event_type: str
    message: str
    tool_name: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
