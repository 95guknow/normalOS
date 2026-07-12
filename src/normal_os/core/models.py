from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(BaseModel):
    id: str
    type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    priority: int = 5


class QUBOProblem(BaseModel):
    id: str | None = None
    Q: dict[tuple[int, int], float]
    bias: dict[int, float]
    metadata: dict[str, Any] = Field(default_factory=dict)


class QUBOSolution(BaseModel):
    problem_id: str | None = None
    solution: dict[int, int]
    energy: float
    num_reads: int
    solver: str
    cached: bool = False


class AgentInfo(BaseModel):
    name: str
    type: str
    status: Literal["idle", "busy", "error"] = "idle"
    capabilities: list[str] = Field(default_factory=list)
    last_used: datetime | None = None