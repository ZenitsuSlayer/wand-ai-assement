from __future__ import annotations
from typing import Any, Dict, Protocol
from app.tools.base import ToolRegistry

class Agent(Protocol):
    type: str
    async def run(self, *, params: Dict[str, Any], inputs: Dict[str, Any], tools: ToolRegistry) -> Dict[str, Any]:
        ...

class AgentRegistry:
    def __init__(self) -> None:
        self._agents: Dict[str, type] = {}

    def register(self, cls: type) -> None:
        t = getattr(cls, "type", None)
        if not t:
            raise ValueError("Agent must define 'type'")
        self._agents[t] = cls

    def create(self, type_: str, **kwargs: Any) -> Agent:
        if type_ not in self._agents:
            raise KeyError(f"Unknown agent type: {type_}")
        return self._agents[type_](**kwargs)  # type: ignore

    def list(self) -> Dict[str, Any]:
        return {k: {"class": v.__name__} for k, v in self._agents.items()}

class ToolAgent:
    """
    Runs a single tool with provided params.
    params:
      tool: str (required)
      args: dict passed to tool.run(...)
      input_from: optional node id to pull data from inputs
    """
    type = "tool.agent"

    def __init__(self) -> None:
        ...

    async def run(self, *, params: Dict[str, Any], inputs: Dict[str, Any], tools: ToolRegistry) -> Dict[str, Any]:
        tool_name = params.get("tool")
        if not tool_name:
            raise ValueError("params.tool is required")
        tool = tools.create(tool_name)
        args = dict(params.get("args") or {})
        # Allow passing previous node output directly
        source = params.get("input_from")
        if source:
            args["data"] = inputs.get(source)
        return await tool.run(**args)
