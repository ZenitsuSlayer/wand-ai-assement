from __future__ import annotations
from typing import Any, Dict, Protocol

class Tool(Protocol):
    name: str
    async def run(self, **kwargs: Any) -> Dict[str, Any]:
        ...

class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, type] = {}

    def register(self, cls: type) -> None:
        name = getattr(cls, "name", None)
        if not name:
            raise ValueError("Tool class must define a 'name'")
        self._tools[name] = cls

    def create(self, name: str, **init_kwargs: Any) -> Tool:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name](**init_kwargs)  # type: ignore

    def list(self) -> Dict[str, Any]:
        return {k: {"class": v.__name__} for k, v in self._tools.items()}