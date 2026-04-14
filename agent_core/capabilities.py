"""
Thin capabilities client for the gateway and CLI.

All intelligence lives in the backend (see agent-corex-backend-2
`app/capabilities/` and `GET /capabilities`). This module only:

  1. Reads the list of installed servers from ~/.agent-corex/installed_servers.json
     (via LocalStore) so the backend call can be scoped.
  2. Fetches the structured capability payload from the backend.
  3. Caches the response on disk so the MCP gateway can render it into the
     system prompt without an extra round-trip per client start.
  4. Renders a compact markdown block for LLM system-prompt injection.

No retrieval, ranking, or template matching happens here — if you find
yourself adding any of that, it belongs in the backend.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent_core.mcp.local_store import LocalStore

logger = logging.getLogger(__name__)


def _cache_file() -> Path:
    return Path.home() / ".agent-corex" / ".cache" / "capabilities.json"


# ── Cache ─────────────────────────────────────────────────────────────────────


def load_cache() -> Optional[Dict[str, Any]]:
    path = _cache_file()
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("capabilities cache read failed: %s", exc)
        return None


def save_cache(payload: Dict[str, Any]) -> None:
    path = _cache_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)


def invalidate() -> None:
    """Drop the on-disk capability cache. Best-effort."""
    path = _cache_file()
    if path.exists():
        try:
            path.unlink()
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("capabilities cache unlink failed: %s", exc)


# ── Fetch ─────────────────────────────────────────────────────────────────────


def fetch(client: Any, use_cache: bool = True) -> Dict[str, Any]:
    """
    Fetch the capability payload for the locally-installed servers.

    *client* is an `AgentCoreXClient` (passed in so this module doesn't
    instantiate one itself — keeps credentials handling in one place).
    """
    if use_cache:
        cached = load_cache()
        if cached is not None:
            return cached

    installed: List[str] = sorted(LocalStore().load_installed().keys())
    if not installed:
        payload: Dict[str, Any] = {
            "servers": {},
            "skills": [],
            "templates": [],
            "installed_servers": [],
        }
        save_cache(payload)
        return payload

    try:
        payload = client.get_capabilities(servers=installed)
    except Exception as exc:
        logger.warning("capabilities fetch failed, using empty payload: %s", exc)
        payload = {
            "servers": {},
            "skills": [],
            "templates": [],
            "installed_servers": installed,
        }

    save_cache(payload)
    return payload


# ── Prompt rendering ──────────────────────────────────────────────────────────


def build_system_block(payload: Dict[str, Any], max_tools_per_server: int = 8) -> str:
    """
    Render a token-tight markdown block for LLM system-prompt injection.

    Shape:
        ## Available MCP capabilities
        ### railway
        - list_projects — List Railway projects
          e.g. "list railway projects"
        - deploy_service — ...
        ### github
        - list_repositories — ...

        Templates (instant execution):
        - "list railway projects" → railway.list_projects
    """
    servers: Dict[str, Any] = payload.get("servers") or {}
    templates: List[Dict[str, Any]] = payload.get("templates") or []

    if not servers and not templates:
        return ""

    lines: List[str] = ["## Available MCP capabilities"]

    for server, block in servers.items():
        caps = (block or {}).get("capabilities") or []
        if not caps:
            continue
        lines.append(f"### {server}")
        for cap in caps[:max_tools_per_server]:
            name = cap.get("name", "")
            desc = (cap.get("description") or "").split(".")[0].strip()
            if desc:
                lines.append(f"- {name} — {desc}")
            else:
                lines.append(f"- {name}")
            examples = cap.get("examples") or []
            if examples:
                lines.append(f'  e.g. "{examples[0]}"')

    if templates:
        lines.append("")
        lines.append("Templates (instant execution):")
        for tmpl in templates[:10]:
            pattern = tmpl.get("pattern", "")
            server = tmpl.get("server", "")
            tool = tmpl.get("tool", "")
            if pattern and server and tool:
                lines.append(f'- "{pattern}" → {server}.{tool}')

    return "\n".join(lines)
