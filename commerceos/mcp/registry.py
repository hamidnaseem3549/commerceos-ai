"""MCP Tool Registry — module-level registry for tool lookup.

Tools register themselves via ``register_tool()`` at import time,
then are discovered by name through ``get_tool()``.
"""
TOOL_REGISTRY = {}


def register_tool(name: str, func):
    """Register a callable as an MCP tool.

    Args:
        name: Unique tool identifier (e.g. ``"get_all_products"``).
        func: Callable that implements the tool logic.
    """
    TOOL_REGISTRY[name] = func


def get_tool(name: str):
    """Look up a registered tool by name.

    Args:
        name: Tool identifier previously passed to ``register_tool``.

    Returns:
        The registered callable, or ``None`` if no tool with that
        name exists.
    """
    return TOOL_REGISTRY.get(name)


def list_tools():
    """Return names of all registered tools."""
    return list(TOOL_REGISTRY.keys())
