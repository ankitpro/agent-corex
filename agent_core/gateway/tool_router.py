"""
Tool Router — central registry for all agent-corex tools.

Classifies tools as:
  - free        available to all users, no auth required
  - enterprise  requires a valid API key at execution time

tools/list  → returns ALL tools (free + enterprise) — never hide tools
tools/call  → checks auth for enterprise tools before execution
"""

from __future__ import annotations

import json
import pathlib
import threading
import urllib.request
from typing import Any


def _fire_and_forget_log(query: str, selected: list[str], scores: dict) -> None:
    """Non-blocking POST to /query/log — never blocks tool execution."""

    def _do():
        try:
            import os
            import ssl

            from agent_core import local_config

            base_url = local_config.get_base_url().rstrip("/")
            api_key = local_config.get_api_key() or ""
            payload = json.dumps(
                {"query": query, "source": "mcp", "selected_tools": selected, "scores": scores}
            ).encode("utf-8")
            req = urllib.request.Request(
                f"{base_url}/query/log",
                data=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )

            # Build SSL context — try certifi bundle first (works in PyInstaller binary),
            # fall back to default context (works in normal Python).
            try:
                import certifi

                ctx = ssl.create_default_context(cafile=certifi.where())
            except Exception:
                ctx = ssl.create_default_context()

            with urllib.request.urlopen(req, timeout=5, context=ctx):
                pass
        except Exception as exc:
            # Write errors to ~/.agent-corex/query_log_debug.txt for diagnosing binary issues.
            try:
                import os

                log = os.path.join(os.path.expanduser("~"), ".agent-corex", "query_log_debug.txt")
                with open(log, "a") as fh:
                    fh.write(f"{exc}\n")
            except Exception:
                pass

    threading.Thread(target=_do, daemon=False).start()


# ---------------------------------------------------------------------------
# Static tool registry
# Extend this dict as new tools are added.  Enterprise tools get exposed in
# tools/list but are gated at tools/call time.
# ---------------------------------------------------------------------------

TOOL_REGISTRY: dict[str, dict] = {
    # ── Free tools ─────────────────────────────────────────────────────────
    "retrieve_tools": {
        "type": "free",
        "description": "Search for relevant MCP tools by natural-language query. Uses Qdrant-backed semantic search on the Agent-Corex backend.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural-language description of what you want to do",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Max results to return (1-20, default 5)",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
    "list_mcp_servers": {
        "type": "free",
        "description": "List all MCP servers configured in agent-corex.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    # ── Enterprise tools ────────────────────────────────────────────────────
    "github_search": {
        "type": "enterprise",
        "description": "Search GitHub repositories, issues, and pull requests.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "type": {
                    "type": "string",
                    "enum": ["repositories", "issues", "prs", "code"],
                    "description": "What to search for",
                },
            },
            "required": ["query"],
        },
    },
    "web_search": {
        "type": "enterprise",
        "description": "Search the web and return structured results.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        },
    },
    "database_query": {
        "type": "enterprise",
        "description": "Execute read-only SQL queries against managed databases.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "SQL SELECT statement"},
                "database": {"type": "string", "description": "Target database name"},
            },
            "required": ["sql", "database"],
        },
    },
}


class ToolRouter:
    """
    Routes tool execution requests.

    tools_list()  — returns all tools (always, no auth required)
    is_enterprise(name) — True if the tool requires auth
    """

    def __init__(self, extra_tools: list[dict] | None = None, mcp_manager=None) -> None:
        # Start with the static registry
        self._registry: dict[str, dict] = dict(TOOL_REGISTRY)
        self._registry_lock = threading.Lock()

        # MCPManager for lazy-starting servers on tool call
        self._mcp_manager = mcp_manager

        # Optionally merge in dynamically discovered MCP tools (all free)
        if extra_tools:
            self.add_mcp_tools(extra_tools)

    def add_mcp_tools(self, tools: list[dict]) -> None:
        """
        Thread-safe: add dynamically discovered MCP tools to the registry.
        Called from the background discovery thread in MCPLoader.
        """
        added = 0
        with self._registry_lock:
            for tool in tools:
                name = tool.get("name")
                if name and name not in self._registry:
                    self._registry[name] = {
                        "type": "free",
                        "description": tool.get("description", ""),
                        "inputSchema": tool.get("input_schema") or tool.get("inputSchema") or {},
                        "_server": tool.get("server"),
                    }
                    added += 1
        if added:
            import logging

            logging.getLogger(__name__).info(f"[MCP] router: added {added} new tools")

    def _format_tool(self, name: str, meta: dict) -> dict[str, Any]:
        """Format a single tool for MCP tools/list response."""
        schema = dict(meta.get("inputSchema") or {})
        # Claude Code rejects tools whose inputSchema lacks "type": "object"
        if schema.get("type") != "object":
            schema["type"] = "object"
        tool_def: dict[str, Any] = {
            "name": name,
            "description": meta["description"],
            "inputSchema": schema,
        }
        # Surface tier information as an annotation so clients can display it
        if meta["type"] == "enterprise":
            tool_def["annotations"] = {
                "tier": "enterprise",
                "hint": "Requires Agent-Corex API key. Run: agent-corex login",
            }
        else:
            tool_def["annotations"] = {"tier": "free"}
        return tool_def

    def tools_list(self, max_mcp_tools: int = 10, query: str | None = None) -> list[dict]:
        """
        Return tools formatted for MCP tools/list response.

        Intelligently filters MCP tools:
        - Always includes all static built-in tools
        - If extra MCP tools > max_mcp_tools: uses ranking to select top tools
        - If query provided: ranks tools by relevance to query
        - Tracks filtering decisions for observability

        Args:
            max_mcp_tools: Maximum MCP tools to include (default 10)
            query: Optional context query for ranking (e.g., "deploy", "database")
        """
        result = []

        # 1. Always include all static built-in tools first
        for name, meta in TOOL_REGISTRY.items():
            result.append(self._format_tool(name, meta))

        # 2. Filter extra MCP tools if there are too many
        mcp_tools_to_add = [
            (name, meta) for name, meta in self._registry.items() if name not in TOOL_REGISTRY
        ]

        if len(mcp_tools_to_add) > max_mcp_tools:
            # Use lightweight keyword scoring — no ML models, no network calls.
            # Heavy semantic ranking happens in _run_retrieve_tools() via the backend.
            ranking_query = query or "general development file database web deploy build"
            tokens = set(ranking_query.lower().split())

            def _kw_score(name: str, desc: str) -> float:
                text = f"{name} {desc}".lower()
                return sum(1 for tok in tokens if tok in text) / max(len(tokens), 1)

            scored_mcp = sorted(
                mcp_tools_to_add,
                key=lambda item: _kw_score(item[0], item[1].get("description", "")),
                reverse=True,
            )
            selected_names = {item[0] for item in scored_mcp[:max_mcp_tools]}
            rejected_names = {name for name, _ in mcp_tools_to_add} - selected_names

            # Track the filtering decision
            try:
                from agent_core.tools.observability.tool_selection_tracker import get_tracker

                tracker = get_tracker()
                tracker.track(
                    f"tools/list ({ranking_query})" if query else "tools/list (default)",
                    list(selected_names),
                    list(rejected_names),
                    scores={
                        "reason": "max_tools_threshold",
                        "threshold": max_mcp_tools,
                        "query": query,
                    },
                )
            except Exception:
                pass  # Observability is optional

            mcp_tools_to_add = [
                (name, meta) for name, meta in mcp_tools_to_add if name in selected_names
            ]

        # 3. Add filtered MCP tools to result
        for name, meta in mcp_tools_to_add:
            result.append(self._format_tool(name, meta))

        return result

    def is_enterprise(self, tool_name: str) -> bool:
        meta = self._registry.get(tool_name)
        if meta is None:
            return False
        return meta.get("type") == "enterprise"

    def get_meta(self, tool_name: str) -> dict | None:
        with self._registry_lock:
            return self._registry.get(tool_name)

    def get_server(self, tool_name: str) -> str | None:
        """Return the backing MCP server name for dynamically loaded tools."""
        meta = self._registry.get(tool_name, {})
        return meta.get("_server")

    def execute_free_tool(self, tool_name: str, arguments: dict) -> Any:
        """
        Execute a free tool — built-in or MCP-backed.
        Returns the result payload (str or dict).
        """
        if tool_name == "retrieve_tools":
            return self._run_retrieve_tools(arguments)
        if tool_name == "list_mcp_servers":
            return self._run_list_mcp_servers()

        # Check if this is a dynamically loaded MCP tool
        server_name = self.get_server(tool_name)
        if server_name is not None:
            return self._run_mcp_tool(tool_name, server_name, arguments)

        raise ValueError(f"No executor for tool: {tool_name!r}")

    def _run_mcp_tool(self, tool_name: str, server_name: str, arguments: dict) -> Any:
        """Execute a tool on its backing MCP server, starting it lazily if needed."""
        if self._mcp_manager is None:
            raise RuntimeError("MCP manager not available")

        # Lazy-start the server if not running
        if not self._mcp_manager.ensure_server_running(server_name):
            raise RuntimeError(
                f"MCP server {server_name!r} could not be started. " "Check logs for details."
            )

        client = self._mcp_manager.get_client(server_name)
        if client is None:
            raise RuntimeError(f"MCP server {server_name!r} has no active client")

        result = client.call_tool(tool_name, arguments)
        return result

    # ── Built-in free tool implementations ────────────────────────────────

    def _run_retrieve_tools(self, args: dict) -> str:
        """
        Retrieve tools via the enterprise backend (Qdrant-backed).
        No local ML models — all ranking runs server-side.
        Falls back to local keyword search if the backend is unreachable.
        """
        query = args.get("query", "")
        top_k = int(args.get("top_k", 5))
        top_k = max(1, min(top_k, 20))

        if not query.strip():
            return "Error: query is required"

        # ── Primary: call enterprise backend ──────────────────────────────────
        try:
            import json as _json
            import ssl
            import urllib.parse
            import urllib.request

            from agent_core import local_config

            base_url = local_config.get_base_url().rstrip("/")
            api_key = local_config.get_api_key() or ""

            params = urllib.parse.urlencode({"query": query, "top_k": top_k})
            url = f"{base_url}/retrieve_tools?{params}"
            req = urllib.request.Request(
                url,
                headers={"Authorization": f"Bearer {api_key}"},
            )
            try:
                import certifi

                ctx = ssl.create_default_context(cafile=certifi.where())
            except Exception:
                ctx = ssl.create_default_context()

            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                tools = _json.loads(resp.read())

            if not isinstance(tools, list):
                raise ValueError(f"unexpected backend response: {tools}")

            # Build nested score map for the DB
            score_map: dict = {}
            for t in tools:
                if not isinstance(t, dict) or not t.get("name"):
                    continue
                score_map[t["name"]] = {
                    "score": t.get("score", 0.0),
                    "semantic_score": t.get("semantic_score", t.get("score", 0.0)),
                    "capability_score": t.get("capability_score", 0.0),
                    "success_rate": t.get("success_rate", 0.5),
                }

            selected_names = [t["name"] for t in tools if isinstance(t, dict) and t.get("name")]
            _fire_and_forget_log(query, selected_names, score_map)

            if not tools:
                return f"No tools found for query: {query!r}"

            lines = [f"Top {len(tools)} tool(s) for {query!r}:\n"]
            for i, t in enumerate(tools, 1):
                score_pct = int(t.get("score", 0) * 100)
                meta = self._registry.get(t["name"], {})
                server = meta.get("_server", "")
                tier = meta.get("type", "")
                label = " [enterprise]" if tier == "enterprise" else ""
                prefix = f"{server}.{t['name']}" if server else t["name"]
                lines.append(f"{i}. {prefix}{label}  {score_pct}%")
                if server:
                    lines.append(f"   Server: {server}")
                if t.get("description"):
                    lines.append(f"   {t['description']}")
            return "\n".join(lines)

        except Exception as backend_exc:
            # ── Fallback: local keyword search (offline / backend down) ─────────
            try:
                from agent_core.retrieval.ranker import rank_tools
                from agent_core.tools.registry import ToolRegistry

                registry = ToolRegistry()
                all_tools = registry.get_all_tools()
                gateway_tools = [
                    {"name": n, "description": m["description"]} for n, m in self._registry.items()
                ]
                all_tools += [
                    t for t in gateway_tools if t["name"] not in {t2["name"] for t2 in all_tools}
                ]
                results = rank_tools(query, all_tools, top_k=top_k, method="keyword")
                selected_names = [t["name"] for t in results]
                _fire_and_forget_log(query, selected_names, {})

                if not results:
                    return f"No tools matched query: {query!r} (backend offline)"

                def _inline_score(q: str, name: str, desc: str) -> int:
                    import re

                    tokens = set(re.findall(r"\w+", q.lower()))
                    text = f"{name} {desc}".lower()
                    return int(sum(1 for tok in tokens if tok in text) / max(len(tokens), 1) * 100)

                lines = [f"Top {len(results)} tool(s) for {query!r} (local fallback):\n"]
                for i, t in enumerate(results, 1):
                    score_pct = _inline_score(query, t.get("name", ""), t.get("description", ""))
                    meta = self._registry.get(t["name"], {})
                    server = meta.get("_server", t.get("server", ""))
                    prefix = f"{server}.{t['name']}" if server else t["name"]
                    lines.append(f"{i}. {prefix}  {score_pct}%")
                    if server:
                        lines.append(f"   Server: {server}")
                    if t.get("description"):
                        lines.append(f"   {t['description']}")
                return "\n".join(lines)
            except Exception:
                return f"Error during retrieval: {backend_exc}"

    def _run_list_mcp_servers(self) -> str:
        config_path = pathlib.Path.home() / ".agent-corex" / "config.json"
        mcp_config = pathlib.Path(__file__).parent.parent.parent / "config" / "mcp.json"

        lines = ["Configured MCP servers:\n"]
        if mcp_config.exists():
            import json

            try:
                data = json.loads(mcp_config.read_text())
                for name in data.get("mcpServers", {}):
                    lines.append(f"  • {name}")
            except Exception:
                lines.append("  (error reading mcp.json)")
        else:
            lines.append("  No mcp.json found.")
        return "\n".join(lines)
