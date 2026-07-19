"""MCP Tool Registry."""
TOOL_REGISTRY = {}


def register_tool(name: str, func):
    TOOL_REGISTRY[name] = func


def get_tool(name: str):
    return TOOL_REGISTRY.get(name)


def list_tools():
    return list(TOOL_REGISTRY.keys())
