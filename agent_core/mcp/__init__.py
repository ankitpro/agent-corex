"""
agent_core.mcp — Local MCP server management for Agent-CoreX.

Provides:
    MCPClient     — JSON-RPC 2.0 stdio client for a single MCP server process
    MCPManager    — Registry of multiple MCPClient instances with tool routing
    MCPRegistry   — Bundled catalog of known MCP servers (command, args, env vars)
    LocalStore    — Read/write ~/.agent-corex/mcp.json and installed_servers.json
"""
from .client import MCPClient
from .manager import MCPManager
from .registry import MCPRegistry
from .local_store import LocalStore

__all__ = ["MCPClient", "MCPManager", "MCPRegistry", "LocalStore"]
