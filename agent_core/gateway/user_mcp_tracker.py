"""
User MCP Tracker — Determines which MCPs are installed by the current user.

Data sources:
1. MCPManager._states keyed by server name (primary)
2. ~/_agent-corex/config.json under "installed_mcps" key (secondary, cache)
3. Backend /user/servers endpoint (optional, background sync)
"""

from __future__ import annotations

import json
import logging
import threading
import urllib.request
from typing import Optional

logger = logging.getLogger(__name__)


def get_installed_mcps(mcp_registry: dict) -> set[str]:
    """
    Extract the set of installed MCP server names from the tool registry.

    The registry is a dict of {tool_name: {meta_dict}}.
    Each meta_dict has a "_server" field indicating which MCP server it comes from.

    Args:
        mcp_registry: Dict from ToolRouter._mcp_registry

    Returns:
        Set of unique server names (e.g., {"github", "railway", "database"})
    """
    installed = set()
    try:
        for meta in mcp_registry.values():
            server = meta.get("_server")
            if server and isinstance(server, str):
                installed.add(server)
    except Exception as e:
        logger.warning(f"[MCP] Error extracting server names from registry: {e}")

    return installed


def get_cached_mcps() -> list[str]:
    """
    Read cached list of installed MCPs from local config.

    Reads from ~/.agent-corex/config.json under the "installed_mcps" key.
    Returns empty list if not found or error.
    """
    try:
        from agent_core import local_config

        cached = local_config.get("installed_mcps", [])
        if isinstance(cached, list):
            return cached
    except Exception as e:
        logger.warning(f"[MCP] Error reading cached MCPs: {e}")

    return []


def cache_installed_mcps(mcps: list[str]) -> None:
    """
    Cache the list of installed MCPs to local config.

    Stores in ~/.agent-corex/config.json under the "installed_mcps" key.
    Non-blocking — errors are logged but never raised.
    """
    try:
        from agent_core import local_config

        local_config.set_key("installed_mcps", mcps)
        logger.info(f"[MCP] Cached {len(mcps)} installed MCPs locally")
    except Exception as e:
        logger.warning(f"[MCP] Error caching MCPs: {e}")


def sync_from_backend_async(base_url: str, auth_header: str) -> None:
    """
    Background thread: sync user's installed MCPs from the backend.

    Calls GET /user/servers endpoint to fetch the user's enabled servers,
    then caches them locally.

    This is fire-and-forget — errors are logged, never raised.
    Uses daemon=False so the thread completes even if main is blocked on stdin.

    Args:
        base_url: Backend base URL (e.g., https://www.agent-corex.com)
        auth_header: Authorization header value (Bearer <token>)
    """

    def _do() -> None:
        try:
            import ssl

            if not base_url or not auth_header:
                return

            base_url_clean = base_url.rstrip("/")
            url = f"{base_url_clean}/user/servers"

            req = urllib.request.Request(
                url,
                headers={"Authorization": auth_header},
            )

            # SSL context
            try:
                import certifi

                ctx = ssl.create_default_context(cafile=certifi.where())
            except Exception:
                ctx = ssl.create_default_context()

            with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                data = json.loads(resp.read())

            # Extract enabled_servers from response
            enabled_servers = data.get("enabled_servers", [])
            if isinstance(enabled_servers, list) and enabled_servers:
                cache_installed_mcps(enabled_servers)
                logger.info(f"[MCP] Synced {len(enabled_servers)} enabled MCPs from backend")

        except Exception as e:
            logger.warning(f"[MCP] Background sync failed: {e}")

    # Fire-and-forget thread, NOT daemon (per CLAUDE.md constraint)
    threading.Thread(target=_do, daemon=False).start()
