from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict

class RunStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"

class AgentSpec(BaseModel):
    """Which agent to run + its configuration."""
    type: str = Field(..., description="Agent type name registered in AgentRegistry")
    config: Dict[str, Any] = Field(default_factory=dict)
    timeout_sec: Optional[float] = Field(default=30.0)
    retries: int = Field(default=1)

class NodeSpec(BaseModel):
    """A node in the execution graph."""
    id: str
    agent: AgentSpec
    params: Dict[str, Any] = Field(default_factory=dict)

class EdgeSpec(BaseModel):
    """Directed edge: output of 'source' is input dependency of 'target'."""
    source: str
    target: str

class WorkflowSpec(BaseModel):
    """Full graph specification."""
    model_config = ConfigDict(extra="forbid")
    nodes: List[NodeSpec]
    edges: List[EdgeSpec] = Field(default_factory=list)

class NodeResult(BaseModel):
    status: RunStatus
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    attempts: int = 0
    logs: List[str] = Field(default_factory=list)

class RunState(BaseModel):
    run_id: str
    status: RunStatus
    nodes: Dict[str, NodeResult]
    created_at: float
    updated_at: float
