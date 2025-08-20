from .base import ToolRegistry
from .http import HttpGet
from .jsonjq import JsonPick

def default_tool_registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(HttpGet)
    reg.register(JsonPick)
    return reg