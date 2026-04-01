"""
MCP Manager — API-backed MCP server installation and management.

Fetches MCP server configs from the Agent-CoreX registry API and persists
them in ~/.agent-corex/registry.json.

API response for GET /mcp_servers/<name>:
{
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem"],
  "env": {},
  "description": "Read and write files in the workspace",
  "env_required": [],
  "env_optional": ["ALLOWED_DIRS"]
}
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx

from agent_core import local_config
from agent_core.uvx import registry


class MCPManager:
    """Add, remove, and list MCP servers in the local registry."""

    def __init__(self, base_url: Optional[str] = None) -> None:
        """
        Args:
            base_url: Override the API base URL (default: from local_config).
        """
        self._base_url = (base_url or local_config.get_base_url()).rstrip("/")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _auth_headers(self) -> Dict[str, str]:
        """Return Authorization headers, honouring AGENT_COREX_API_KEY env var."""
        key = os.getenv("AGENT_COREX_API_KEY") or local_config.get_api_key()
        if key:
            return {"Authorization": f"Bearer {key}"}
        token = local_config.get_access_token()
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    def _fetch_server_config(self, name: str) -> Dict[str, Any]:
        """
        Fetch a server definition from the API.

        GET /mcp_servers/<name>

        Returns:
            Server config dict with at least ``command`` and ``args``.

        Raises:
            ValueError:   Server not found (HTTP 404).
            RuntimeError: Network or unexpected API error.
        """
        url = f"{self._base_url}/mcp_servers/{name}"
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(url, headers=self._auth_headers())
        except httpx.ConnectError as exc:
            raise RuntimeError(
                f"Cannot reach Agent-CoreX backend at {self._base_url}. "
                "Check your internet connection."
            ) from exc
        except httpx.TimeoutException as exc:
            raise RuntimeError(f"Request timed out fetching MCP server '{name}'.") from exc

        if resp.status_code == 404:
            raise ValueError(
                f"MCP server '{name}' not found in the Agent-CoreX registry.\n"
                "Run  uvx agent-corex mcp list  to see installed servers."
            )
        if resp.status_code == 401:
            raise PermissionError(
                "Authentication required.\n"
                "  Get your API key : https://www.agent-corex.com/dashboard/keys\n"
                "  Then run         : uvx agent-corex login --key <key>"
            )
        if resp.status_code != 200:
            raise RuntimeError(
                f"API error {resp.status_code} fetching MCP server '{name}': {resp.text}"
            )

        return resp.json()

    # ── Public API ────────────────────────────────────────────────────────────

    def add_server(self, name: str, source: str = "manual") -> Dict[str, Any]:
        """
        Fetch an MCP server config from the API and store it in the registry.

        Steps:
          1. GET /mcp_servers/<name>
          2. Persist config in ~/.agent-corex/registry.json

        Args:
            name:   Server slug (e.g. ``"filesystem"``).
            source: Installation origin — ``"manual"`` or ``"pack:<name>"``.

        Returns:
            The stored server config dict.

        Raises:
            ValueError:       Server not found in registry.
            PermissionError:  Not authenticated.
            RuntimeError:     Network / API error.
        """
        config = self._fetch_server_config(name)

        command: str = config.get("command", "")
        args: List[str] = config.get("args", [])
        env: Dict[str, str] = config.get("env", {})

        if not command:
            raise RuntimeError(f"Invalid server config for '{name}': missing 'command' field.")

        registry.add_server(
            name=name,
            command=command,
            args=args,
            env=env,
            source=source,
            extra={
                "description": config.get("description", ""),
                "env_required": config.get("env_required", []),
                "env_optional": config.get("env_optional", []),
            },
        )

        return {
            "name": name,
            "command": command,
            "args": args,
            "env": env,
            "description": config.get("description", ""),
            "env_required": config.get("env_required", []),
            "source": source,
        }

    def remove_server(self, name: str) -> bool:
        """
        Remove an MCP server from the local registry.

        Args:
            name: Server slug.

        Returns:
            ``True`` if found and removed, ``False`` if it was not installed.
        """
        return registry.remove_server(name)

    def list_servers(self) -> Dict[str, Any]:
        """
        Return all MCP servers currently in the local registry.

        Returns:
            ``{server_name: config_dict, ...}``
        """
        return registry.get_servers()

    def get_server(self, name: str) -> Optional[Dict[str, Any]]:
        """Return a single server's registry entry, or ``None`` if not installed."""
        return registry.get_server(name)

    def is_installed(self, name: str) -> bool:
        """Return ``True`` if the named server is in the local registry."""
        return registry.server_is_installed(name)
