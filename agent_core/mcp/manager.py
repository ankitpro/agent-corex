"""
MCPManager — registry of MCPClient instances with tool routing.

Usage:
    mgr = MCPManager.from_local_store()   # load from ~/.agent-corex/mcp.json
    result = mgr.call_tool("railway", "list_projects", {})
    mgr.shutdown_all()
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from .client import MCPClient
from .local_store import LocalStore

logger = logging.getLogger(__name__)


class MCPManager:
    """Registry that maps server names → MCPClient and tool names → server names."""

    def __init__(self) -> None:
        self.servers: Dict[str, MCPClient] = {}
        self._tool_map: Dict[str, str] = {}  # tool_name → server_name

    # ---- Construction ----

    @classmethod
    def from_local_store(cls) -> "MCPManager":
        """Build an MCPManager from ~/.agent-corex/mcp.json without starting servers.

        Servers are started lazily on first call_tool() call.
        """
        mgr = cls()
        store = LocalStore()
        config = store.load_mcp_config()
        for server_name, server_cfg in config.items():
            command = server_cfg.get("command", "npx")
            args = server_cfg.get("args", [])
            env = server_cfg.get("env") or None
            client = MCPClient(name=server_name, command=command, args=args, env=env)
            mgr.servers[server_name] = client
        return mgr

    def register(self, name: str, client: MCPClient) -> None:
        """Manually register a client (useful for tests)."""
        self.servers[name] = client

    # ---- Tool metadata ----

    def get_tools_for_server(self, server_name: str) -> List[Dict[str, Any]]:
        """Start the server if needed and return its tool list."""
        client = self._get_or_start(server_name)
        tools = client.list_tools()
        for t in tools:
            self._tool_map[t["name"]] = server_name
        return tools

    # ---- Execution ----

    def call_tool(
        self,
        server_name: str,
        tool_name: str,
        params: Dict[str, Any],
    ) -> Any:
        """Execute *tool_name* on *server_name* synchronously."""
        client = self._get_or_start(server_name)
        start = time.monotonic()
        try:
            result = client.call_tool(tool_name, params)
            logger.info(
                "call_tool success | server=%s tool=%s latency_ms=%d",
                server_name,
                tool_name,
                int((time.monotonic() - start) * 1000),
            )
            return result
        except Exception as exc:
            logger.warning(
                "call_tool failed | server=%s tool=%s error=%s",
                server_name,
                tool_name,
                exc,
            )
            raise

    async def call_tool_async(
        self,
        server_name: str,
        tool_name: str,
        params: Dict[str, Any],
    ) -> Any:
        """Async wrapper — offloads the blocking subprocess call to a thread."""
        return await asyncio.to_thread(self.call_tool, server_name, tool_name, params)

    # ---- Lifecycle ----

    def shutdown_all(self) -> None:
        """Stop all running MCP server subprocesses."""
        for name, client in self.servers.items():
            try:
                client.stop()
            except Exception as exc:
                logger.warning("Error stopping server '%s': %s", name, exc)

    # ---- Private ----

    def _get_or_start(self, server_name: str) -> MCPClient:
        if server_name not in self.servers:
            raise ValueError(
                f"Server '{server_name}' not in MCPManager. "
                f"Run: agent-corex mcp add {server_name}"
            )
        client = self.servers[server_name]
        if not client._initialized:
            client.start()
        return client
