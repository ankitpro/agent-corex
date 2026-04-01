"""
agent_core.uvx — uvx-native modules for Agent-CoreX.

Provides the registry, pack manager, MCP manager, and executor that power:

    uvx agent-corex pack list/install/remove
    uvx agent-corex mcp  list/add/remove
    uvx agent-corex execute "<task>"
    uvx agent-corex plan "<task>"
    uvx agent-corex mcp           # starts MCP server

All modules share ~/.agent-corex/ as their home directory and reuse
agent_core.local_config for authentication.
"""
