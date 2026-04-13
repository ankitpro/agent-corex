"""
MCPClient — JSON-RPC 2.0 client for a single local MCP stdio server.

Handles:
  - Windows command resolution (npx → npx.cmd)
  - MCP initialize handshake (protocol version 2024-11-05)
  - tools/list and tools/call
  - Subprocess lifecycle (start / stop)
"""

from __future__ import annotations

import json
import logging
import shutil
import sys
import time
import uuid
from typing import Any, Dict, List

from agent_core import __version__ as _VERSION
from .transport import MCPStdioTransport

logger = logging.getLogger(__name__)


def _resolve_command(command: str) -> str:
    """Resolve platform-specific command name."""
    if command == "npx":
        # On Windows the shim is npx.cmd
        if sys.platform.startswith("win"):
            return "npx.cmd"
        return "npx"
    if command == "uvx":
        if shutil.which("uvx"):
            return "uvx"
        raise RuntimeError("uvx not found. Install with: pip install uv (or pipx install uv)")
    return command


class MCPClient:
    """Manages a single local MCP server subprocess and communicates via JSON-RPC 2.0."""

    def __init__(
        self,
        name: str,
        command: str,
        args: list,
        env: dict | None = None,
    ):
        self.name = name
        self._command = command
        self._args = args
        self._env = env
        self._transport: MCPStdioTransport | None = None
        self._initialized = False

    def start(self) -> None:
        """Start the server subprocess and run the MCP initialize handshake."""
        resolved = _resolve_command(self._command)
        self._transport = MCPStdioTransport(resolved, self._args, env=self._env)
        self._transport.start()

        # Give the server a moment to boot (especially on Windows)
        if sys.platform.startswith("win"):
            time.sleep(1)

        if self._transport.process and self._transport.process.poll() is not None:
            stderr = ""
            try:
                stderr = self._transport.process.stderr.read()
            except Exception:
                pass
            raise RuntimeError(f"MCP server '{self.name}' failed to start: {stderr}")

        self._initialize()
        logger.info("MCPClient started: %s", self.name)

    def _initialize(self) -> None:
        """Send the MCP initialize handshake."""
        req_id = str(uuid.uuid4())
        # Write directly (don't use transport.send — it also reads stdout)
        self._transport.process.stdin.write(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "agent-corex", "version": _VERSION},
                    },
                }
            )
            + "\n"
        )
        self._transport.process.stdin.flush()

        # Drain until we see our response id
        while True:
            line = self._transport.process.stdout.readline()
            if not line:
                raise RuntimeError(f"MCP server '{self.name}' closed during initialize")
            resp = json.loads(line)
            if resp.get("id") == req_id:
                break

        # Send initialized notification
        self._transport.process.stdin.write(
            json.dumps({"jsonrpc": "2.0", "method": "initialized", "params": {}}) + "\n"
        )
        self._transport.process.stdin.flush()
        self._initialized = True

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return the list of tools exposed by this server."""
        result = self._send("tools/list")
        return result.get("tools", [])

    def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Call a tool and return the raw result."""
        return self._send(
            "tools/call",
            {"name": tool_name, "arguments": params},
        )

    def _send(self, method: str, params: dict | None = None) -> Any:
        if self._transport is None or not self._initialized:
            raise RuntimeError(f"MCPClient '{self.name}' not started")
        req_id = str(uuid.uuid4())
        self._transport.process.stdin.write(
            json.dumps({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params or {}})
            + "\n"
        )
        self._transport.process.stdin.flush()
        while True:
            line = self._transport.process.stdout.readline()
            if not line:
                stderr = ""
                try:
                    stderr = self._transport.process.stderr.read()
                except Exception:
                    pass
                raise RuntimeError(f"MCP server '{self.name}' closed. stderr: {stderr}")
            resp = json.loads(line)
            if resp.get("id") == req_id:
                if "error" in resp:
                    raise RuntimeError(f"MCP error from '{self.name}': {resp['error']}")
                return resp.get("result", {})

    def stop(self) -> None:
        """Terminate the server subprocess."""
        if self._transport:
            self._transport.stop()
        self._initialized = False
        logger.info("MCPClient stopped: %s", self.name)
