"""MCP Tool Layer - bridges to existing mcp_server tools until DB refactor."""
# Bridge to existing tools during migration
from mcp_server.tools import call_tool as _old_call
from mcp_server.tools import TOOL_REGISTRY as _old_registry
from commerceos.mcp.registry import register_tool, get_tool, TOOL_REGISTRY

# Copy existing tools into the new registry
for name, func in _old_registry.items():
    register_tool(name, func)


def call_tool(tool_name: str, **kwargs):
    """Bridge that first checks new registry, then falls back to old."""
    func = get_tool(tool_name)
    if func:
        return func(**kwargs)
    return _old_call(tool_name, **kwargs)
