"""
Tool Router — central registry for all agent-corex tools.

Classifies tools as:
  - free        available to all users, no auth required
  - enterprise  requires a valid API key at execution time

tools/list  → returns ALL tools (free + enterprise) — never hide tools
tools/call  → checks auth for enterprise tools before execution
"""

from __future__ import annotations

import pathlib
from typing import Any

# ---------------------------------------------------------------------------
# Static tool registry
# Extend this dict as new tools are added.  Enterprise tools get exposed in
# tools/list but are gated at tools/call time.
# ---------------------------------------------------------------------------

TOOL_REGISTRY: dict[str, dict] = {
    # ── Free tools ─────────────────────────────────────────────────────────
    "retrieve_tools": {
        "type": "free",
        "description": "Search for relevant MCP tools by natural-language query.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural-language description of what you want to do",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Max results to return (default 5)",
                    "default": 5,
                },
                "method": {
                    "type": "string",
                    "enum": ["keyword", "hybrid", "embedding"],
                    "description": "Ranking method (default hybrid)",
                    "default": "hybrid",
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

    def __init__(self, extra_tools: list[dict] | None = None) -> None:
        # Start with the static registry
        self._registry: dict[str, dict] = dict(TOOL_REGISTRY)

        # Optionally merge in dynamically discovered MCP tools (all free)
        if extra_tools:
            for tool in extra_tools:
                name = tool.get("name")
                if name and name not in self._registry:
                    self._registry[name] = {
                        "type": "free",
                        "description": tool.get("description", ""),
                        "inputSchema": tool.get("input_schema") or tool.get("inputSchema") or {},
                        "_server": tool.get("server"),  # which MCP server owns it
                    }

    def tools_list(self) -> list[dict]:
        """Return all tools formatted for MCP tools/list response."""
        result = []
        for name, meta in self._registry.items():
            tool_def: dict[str, Any] = {
                "name": name,
                "description": meta["description"],
                "inputSchema": meta.get("inputSchema", {}),
            }
            # Surface tier information as an annotation so clients can display it
            if meta["type"] == "enterprise":
                tool_def["annotations"] = {
                    "tier": "enterprise",
                    "hint": "Requires Agent-Corex API key. Run: agent-corex login",
                }
            else:
                tool_def["annotations"] = {"tier": "free"}
            result.append(tool_def)
        return result

    def is_enterprise(self, tool_name: str) -> bool:
        meta = self._registry.get(tool_name)
        if meta is None:
            return False
        return meta.get("type") == "enterprise"

    def get_meta(self, tool_name: str) -> dict | None:
        return self._registry.get(tool_name)

    def get_server(self, tool_name: str) -> str | None:
        """Return the backing MCP server name for dynamically loaded tools."""
        meta = self._registry.get(tool_name, {})
        return meta.get("_server")

    def execute_free_tool(self, tool_name: str, arguments: dict) -> Any:
        """
        Execute a free built-in tool.
        Returns the result payload (str or dict).
        """
        if tool_name == "retrieve_tools":
            return self._run_retrieve_tools(arguments)
        if tool_name == "list_mcp_servers":
            return self._run_list_mcp_servers()
        # Unknown built-in tool
        raise ValueError(f"No built-in executor for tool: {tool_name!r}")

    # ── Built-in free tool implementations ────────────────────────────────

    def _run_retrieve_tools(self, args: dict) -> str:
        query = args.get("query", "")
        top_k = int(args.get("top_k", 5))
        method = args.get("method", "hybrid")

        try:
            from agent_core.retrieval.ranker import rank_tools
            from agent_core.tools.registry import ToolRegistry

            registry = ToolRegistry()
            tools = registry.get_all_tools()

            # Also include tools from our gateway registry
            gateway_tools = [
                {"name": n, "description": m["description"]}
                for n, m in self._registry.items()
            ]
            all_tools = tools + [t for t in gateway_tools if t["name"] not in {t2["name"] for t2 in tools}]

            if not all_tools:
                return "No tools found."

            results = rank_tools(query, all_tools, top_k=top_k, method=method)
            if not results:
                return f"No tools matched query: {query!r}"

            lines = [f"Top {len(results)} tool(s) for {query!r}:\n"]
            for i, t in enumerate(results, 1):
                tier = self._registry.get(t["name"], {}).get("type", "free")
                label = " [enterprise]" if tier == "enterprise" else ""
                lines.append(f"{i}. {t['name']}{label}")
                lines.append(f"   {t.get('description', '')}")
            return "\n".join(lines)
        except Exception as exc:
            return f"Error during retrieval: {exc}"

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
