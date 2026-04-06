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
# Public tool registry — the ONLY 2 tools exposed to Claude
# ---------------------------------------------------------------------------

TOOL_REGISTRY: dict[str, dict] = {
    "retrieve_tools": {
        "type": "free",
        "description": (
            "Search for the right tool by describing what you want to do. "
            "Available capability domains: {capabilities}. "
            "Returns tool names, what they do, and required inputs. "
            "Always call this before execute_tool."
        ),
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
    "execute_tool": {
        "type": "free",
        "description": "Execute a tool returned by retrieve_tools. Pass the exact tool_name and required arguments.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "description": "Exact tool name from retrieve_tools result",
                },
                "arguments": {
                    "type": "object",
                    "description": "Arguments required by the tool",
                },
            },
            "required": ["tool_name"],
        },
    },
}

# ---------------------------------------------------------------------------
# Internal routing table for enterprise tools
# NOT exposed via tools/list — routed internally by _run_execute_tool()
# ---------------------------------------------------------------------------

_ENTERPRISE_TOOLS: dict[str, dict] = {
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
        # Public tools — the only 2 tools Claude ever sees
        self._registry: dict[str, dict] = dict(TOOL_REGISTRY)
        self._registry_lock = threading.Lock()

        # Internal MCP tool registry — never sent to Claude via tools/list
        self._mcp_registry: dict[str, dict] = {}

        # MCPManager for lazy-starting servers on tool call
        self._mcp_manager = mcp_manager

        # Optionally merge in dynamically discovered MCP tools (all free)
        if extra_tools:
            self.add_mcp_tools(extra_tools)

    def add_mcp_tools(self, tools: list[dict]) -> None:
        """
        Thread-safe: store dynamically discovered MCP tools in the internal registry.
        These tools are NEVER exposed to Claude via tools/list.
        Called from the background discovery thread in MCPLoader.
        """
        added = 0
        with self._registry_lock:
            for tool in tools:
                name = tool.get("name")
                if name and name not in self._mcp_registry:
                    self._mcp_registry[name] = {
                        "type": "free",
                        "description": tool.get("description", ""),
                        "inputSchema": tool.get("input_schema") or tool.get("inputSchema") or {},
                        "_server": tool.get("server"),
                    }
                    added += 1
        if added:
            import logging

            logging.getLogger(__name__).info(
                f"[MCP] router: added {added} tools to internal registry"
            )

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
        Return ONLY the 2 public tools for MCP tools/list response.

        The retrieve_tools description is dynamically stamped with the
        current capability domains derived from _mcp_registry server names.
        This lets Claude know what is available before its first retrieve_tools call.

        max_mcp_tools and query parameters are kept for API compatibility
        but are no longer used — tool filtering is now done inside retrieve_tools.
        """
        capabilities = self.get_capabilities()
        cap_str = ", ".join(capabilities) if capabilities else "general tools"

        result = []
        for name, meta in TOOL_REGISTRY.items():
            formatted = self._format_tool(name, meta)
            if name == "retrieve_tools":
                # Stamp capabilities into description at call time
                formatted["description"] = meta["description"].replace("{capabilities}", cap_str)
            result.append(formatted)
        return result

    def get_capabilities(self) -> list[str]:
        """
        Derive human-readable capability labels from the internal MCP registry.
        Uses the server names stamped onto each tool by the discovery callback.
        """
        from agent_core.gateway.capability_provider import get_capabilities as _get_caps

        with self._registry_lock:
            server_names = {
                meta.get("_server", "")
                for meta in self._mcp_registry.values()
                if meta.get("_server")
            }
        return _get_caps(list(server_names))

    def is_enterprise(self, tool_name: str) -> bool:
        return tool_name in _ENTERPRISE_TOOLS

    def get_meta(self, tool_name: str) -> dict | None:
        with self._registry_lock:
            # Check public tools first (retrieve_tools, execute_tool)
            if tool_name in self._registry:
                return self._registry[tool_name]
            # Check internal MCP registry
            if tool_name in self._mcp_registry:
                return self._mcp_registry[tool_name]
        # Check enterprise tools (immutable, no lock needed)
        return _ENTERPRISE_TOOLS.get(tool_name)

    def get_server(self, tool_name: str) -> str | None:
        """Return the backing MCP server name for a tool in the internal MCP registry."""
        with self._registry_lock:
            meta = self._mcp_registry.get(tool_name, {})
        return meta.get("_server")

    def execute_free_tool(self, tool_name: str, arguments: dict) -> Any:
        """
        Execute a public tool — retrieve_tools or execute_tool.
        Both are free-tier (no auth check here).
        Enterprise auth is checked inside _run_execute_tool() when the target
        tool_name resolves to an enterprise tool.
        """
        if tool_name == "retrieve_tools":
            return self._run_retrieve_tools(arguments)
        if tool_name == "execute_tool":
            return self._run_execute_tool(arguments)
        raise ValueError(f"No executor for public tool: {tool_name!r}")

    def _run_execute_tool(self, args: dict) -> Any:
        """
        Route execute_tool calls to the correct backend.

        Routing priority:
          1. MCP tool (in _mcp_registry)  → _run_mcp_tool()
          2. Enterprise tool (in _ENTERPRISE_TOOLS) → auth gate → enterprise backend stub
          3. Unknown → helpful error with list of known tools

        Args:
            args: {"tool_name": str, "arguments": dict}
        """
        tool_name = args.get("tool_name", "").strip()
        arguments = args.get("arguments") or {}

        if not tool_name:
            return "Error: tool_name is required. Call retrieve_tools first to find the right tool."

        # ── Route 1: MCP tool ─────────────────────────────────────────────────
        server_name = self.get_server(tool_name)
        if server_name is not None:
            return self._run_mcp_tool(tool_name, server_name, arguments)

        # ── Route 2: Enterprise tool ──────────────────────────────────────────
        if tool_name in _ENTERPRISE_TOOLS:
            from agent_core.gateway.auth_middleware import check_auth

            auth_err = check_auth()
            if auth_err is not None:
                return json.dumps(auth_err, indent=2)

            # Auth passed — enterprise execution stub
            return (
                f"[Enterprise tool: {tool_name}]\n"
                f"Arguments: {json.dumps(arguments, indent=2)}\n\n"
                "This tool requires a running enterprise backend.\n"
                "See: https://agent-corex.ai/docs/enterprise"
            )

        # ── Route 3: Unknown tool ─────────────────────────────────────────────
        with self._registry_lock:
            known_mcp = list(self._mcp_registry.keys())
        known_enterprise = list(_ENTERPRISE_TOOLS.keys())
        all_known = known_mcp + known_enterprise
        hint = f" Known tools: {', '.join(all_known[:10])}" if all_known else ""
        return f"Unknown tool: {tool_name!r}. " "Use retrieve_tools to find available tools." + (
            f"\n{hint}" if hint else ""
        )

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

            # Build capability header
            capabilities = self.get_capabilities()
            cap_header = (
                f"Available capabilities: {', '.join(capabilities)}" if capabilities else ""
            )

            lines = []
            if cap_header:
                lines.append(cap_header)
                lines.append("")

            lines.append(f"Top {len(tools)} matching tools for {query!r}:")
            for i, t in enumerate(tools, 1):
                name = t.get("name", "")
                desc = t.get("description", "")

                # Get required inputs from the internal registry
                with self._registry_lock:
                    meta = self._mcp_registry.get(name, {})
                schema = meta.get("inputSchema") or {}
                required = schema.get("required") or []
                inputs_str = f"inputs: {', '.join(required)}" if required else "no required inputs"

                lines.append(f"{i}. {name} — {desc} ({inputs_str})")

            lines.append("")
            lines.append("Use execute_tool with the exact tool_name and required arguments.")
            return "\n".join(lines)

        except Exception as backend_exc:
            # ── Fallback: local keyword search (offline / backend down) ─────────
            try:
                from agent_core.retrieval.ranker import rank_tools
                from agent_core.tools.registry import ToolRegistry

                registry = ToolRegistry()
                all_tools = registry.get_all_tools()
                with self._registry_lock:
                    gateway_tools = [
                        {"name": n, "description": m["description"]}
                        for n, m in self._mcp_registry.items()
                    ]
                all_tools += [
                    t for t in gateway_tools if t["name"] not in {t2["name"] for t2 in all_tools}
                ]
                results = rank_tools(query, all_tools, top_k=top_k, method="keyword")
                selected_names = [t["name"] for t in results]
                _fire_and_forget_log(query, selected_names, {})

                if not results:
                    return f"No tools matched query: {query!r} (backend offline)"

                capabilities = self.get_capabilities()
                cap_header = (
                    f"Available capabilities: {', '.join(capabilities)}" if capabilities else ""
                )

                lines = []
                if cap_header:
                    lines.append(cap_header)
                    lines.append("")

                lines.append(f"Top {len(results)} matching tools for {query!r} (local fallback):")
                for i, t in enumerate(results, 1):
                    name = t.get("name", "")
                    desc = t.get("description", "")
                    with self._registry_lock:
                        meta = self._mcp_registry.get(name, {})
                    schema = meta.get("inputSchema") or {}
                    required = schema.get("required") or []
                    inputs_str = (
                        f"inputs: {', '.join(required)}" if required else "no required inputs"
                    )
                    lines.append(f"{i}. {name} — {desc} ({inputs_str})")

                lines.append("")
                lines.append("Use execute_tool with the exact tool_name and required arguments.")
                return "\n".join(lines)
            except Exception:
                return f"Error during retrieval: {backend_exc}"
