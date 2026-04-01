"""
Pack Manager — API-backed pack installation and management.

A "pack" is a curated bundle of MCP servers and tools fetched from the
Agent-CoreX backend.  This module handles:

  - Fetching pack definitions from the API (GET /packs/<name>)
  - Installing the MCP servers a pack requires
  - Persisting state in ~/.agent-corex/registry.json

Pack definition returned by the API:
{
  "name": "youtube-productivity",
  "description": "Tools for YouTube research and productivity",
  "mcp_servers": ["filesystem", "youtube"],
  "tools": ["summarize_video", "download_transcript"]
}
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx

from agent_core import local_config
from agent_core.uvx import registry
from agent_core.uvx.mcp_manager import MCPManager


class PackManager:
    """Install, remove, and list Agent-CoreX packs."""

    def __init__(self, base_url: Optional[str] = None) -> None:
        """
        Args:
            base_url: Override the API base URL (default: from local_config).
        """
        self._base_url = (base_url or local_config.get_base_url()).rstrip("/")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _auth_headers(self) -> Dict[str, str]:
        """Return Authorization headers for API calls, checking ENV first."""
        key = os.getenv("AGENT_COREX_API_KEY") or local_config.get_api_key()
        if key:
            return {"Authorization": f"Bearer {key}"}
        token = local_config.get_access_token()
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    def _fetch_pack(self, name: str) -> Dict[str, Any]:
        """
        Fetch a pack definition from the API.

        GET /packs/<name>

        Returns:
            Pack definition dict.

        Raises:
            ValueError: If the pack is not found (HTTP 404).
            RuntimeError: On network or API errors.
        """
        url = f"{self._base_url}/packs/{name}"
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(url, headers=self._auth_headers())
        except httpx.ConnectError as exc:
            raise RuntimeError(
                f"Cannot reach Agent-CoreX backend at {self._base_url}. "
                "Check your internet connection."
            ) from exc
        except httpx.TimeoutException as exc:
            raise RuntimeError(f"Request timed out fetching pack '{name}'.") from exc

        if resp.status_code == 404:
            raise ValueError(
                f"Pack '{name}' not found in the Agent-CoreX registry.\n"
                "Run  uvx agent-corex pack list  to see available packs."
            )
        if resp.status_code == 401:
            raise PermissionError(
                "Authentication required.\n"
                "  Get your API key : https://www.agent-corex.com/dashboard/keys\n"
                "  Then run         : uvx agent-corex login --key <key>"
            )
        if resp.status_code != 200:
            raise RuntimeError(f"API error {resp.status_code} fetching pack '{name}': {resp.text}")

        return resp.json()

    # ── Public API ────────────────────────────────────────────────────────────

    def install_pack(self, name: str) -> Dict[str, Any]:
        """
        Install a pack by fetching its definition from the API.

        Steps:
          1. GET /packs/<name> → pack definition
          2. Install each required MCP server via MCPManager
          3. Register the pack in ~/.agent-corex/registry.json

        Args:
            name: Pack slug (e.g. ``"youtube-productivity"``).

        Returns:
            A summary dict:
            {
              "name": "youtube-productivity",
              "mcp_servers": ["filesystem", "youtube"],
              "tools": ["summarize_video"],
              "servers_added": ["youtube"],   # newly installed
              "servers_skipped": ["filesystem"]  # already installed
            }

        Raises:
            ValueError:       Pack not found in registry.
            PermissionError:  Not authenticated.
            RuntimeError:     Network / API error.
        """
        pack_def = self._fetch_pack(name)

        required_servers: List[str] = pack_def.get("mcp_servers", [])
        tools: List[str] = pack_def.get("tools", [])

        mcp_mgr = MCPManager(base_url=self._base_url)
        servers_added: List[str] = []
        servers_skipped: List[str] = []

        for server_name in required_servers:
            if registry.server_is_installed(server_name):
                servers_skipped.append(server_name)
                continue
            try:
                mcp_mgr.add_server(server_name, source=f"pack:{name}")
                servers_added.append(server_name)
            except Exception as exc:
                # Non-fatal: note the failure but continue with other servers
                servers_skipped.append(server_name)
                # Re-raise so the caller can surface this clearly
                raise RuntimeError(
                    f"Failed to install MCP server '{server_name}' "
                    f"required by pack '{name}': {exc}"
                ) from exc

        # Persist pack registration
        registry.add_pack(
            name=name,
            mcp_servers=required_servers,
            tools=tools,
            extra={
                "description": pack_def.get("description", ""),
                "display_name": pack_def.get("display_name", name),
            },
        )

        return {
            "name": name,
            "display_name": pack_def.get("display_name", name),
            "description": pack_def.get("description", ""),
            "mcp_servers": required_servers,
            "tools": tools,
            "servers_added": servers_added,
            "servers_skipped": servers_skipped,
        }

    def remove_pack(self, name: str) -> bool:
        """
        Remove a pack from the registry.

        Note: MCP servers installed by the pack are NOT automatically removed
        because they may be shared with other packs.  Use
        ``uvx agent-corex mcp remove <server>`` to remove individual servers.

        Args:
            name: Pack slug.

        Returns:
            ``True`` if the pack was found and removed, ``False`` if it was
            not installed.
        """
        return registry.remove_pack(name)

    def list_packs(self) -> Dict[str, Any]:
        """
        Return all installed packs from the local registry.

        Returns:
            ``{pack_name: metadata_dict, ...}``
        """
        return registry.get_packs()

    def get_pack(self, name: str) -> Optional[Dict[str, Any]]:
        """Return a single installed pack's metadata, or ``None``."""
        return registry.get_pack(name)
