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

from agent_core.input_abstraction import (
    AbstractionRegistry,
    ContextResolver,
    ParamClassifier,
)


def _fire_and_forget_log(
    query: str, selected: list[str], scores: dict, retrieved_tools: list[dict] | None = None
) -> None:
    """Non-blocking POST to /query/log — never blocks tool execution."""

    def _do():
        try:
            import os
            import ssl

            from agent_core import local_config

            base_url = local_config.get_base_url().rstrip("/")
            api_key = local_config.get_api_key() or ""
            payload_dict = {
                "query": query,
                "source": "mcp",
                "selected_tools": selected,
                "scores": scores,
            }
            # Include retrieved_tools if provided (all tools returned from retrieve_tools endpoint)
            if retrieved_tools:
                payload_dict["retrieved_tools"] = retrieved_tools

            payload = json.dumps(payload_dict).encode("utf-8")
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
# Public tool registry — 5 tools exposed to Claude
# ---------------------------------------------------------------------------

TOOL_REGISTRY: dict[str, dict] = {
    "get_capabilities": {
        "type": "free",
        "description": (
            "Discover what MCP server capabilities are installed and what's available to install. "
            "Shows which MCPs you have configured and which others are available in the ecosystem. "
            "Use this to understand what's available before calling retrieve_tools."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    "retrieve_tools": {
        "type": "free",
        "description": (
            "Search for the right tool by describing what you want to do. "
            "Available capability domains: {capabilities}. "
            "Returns tool names, what they do, and required inputs. "
            "If no tools are found, suggests MCPs you can install. "
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
    "recommend_mcps": {
        "type": "free",
        "description": (
            "Recommend MCP servers to install for a specific task. "
            "Useful when retrieve_tools returns no results or when you want to know what MCPs support a capability. "
            "Returns suggestions with descriptions and example tasks."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Description of what you want to accomplish (e.g., 'deploy to AWS', 'search GitHub issues')",
                },
            },
            "required": ["query"],
        },
    },
    "recommend_mcps_from_stack": {
        "type": "free",
        "description": (
            "Recommend complementary MCP servers based on your current tech stack. "
            "Provide the technologies you're using and get suggestions for MCPs that integrate with them. "
            "Useful for discovering tools that work well with your existing setup."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "stack": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of technologies/MCPs you're using (e.g., ['github', 'docker', 'aws'])",
                },
            },
            "required": ["stack"],
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

        # Input abstraction layer — hides internal params from LLM
        self._abstraction_registry = AbstractionRegistry(ParamClassifier())
        self._context_resolver = ContextResolver()

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
        added_names = []
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
                    added_names.append(name)

        # Invalidate abstraction cache for newly added tools
        for name in added_names:
            self._abstraction_registry.invalidate(name)

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
        Execute a public tool — all 5 publicly exposed tools.
        All are free-tier (no auth check here).
        Enterprise auth is checked inside _run_execute_tool() when the target
        tool_name resolves to an enterprise tool.
        """
        if tool_name == "get_capabilities":
            return self._run_get_capabilities(arguments)
        if tool_name == "retrieve_tools":
            return self._run_retrieve_tools(arguments)
        if tool_name == "execute_tool":
            return self._run_execute_tool(arguments)
        if tool_name == "recommend_mcps":
            return self._run_recommend_mcps(arguments)
        if tool_name == "recommend_mcps_from_stack":
            return self._run_recommend_mcps_from_stack(arguments)
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
        """Execute a tool on its backing MCP server, starting it lazily if needed.

        Includes input validation and internal parameter injection via the
        input abstraction layer.
        """
        if self._mcp_manager is None:
            raise RuntimeError("MCP manager not available")

        # Lazy-start the server if not running
        if not self._mcp_manager.ensure_server_running(server_name):
            raise RuntimeError(
                f"MCP server {server_name!r} could not be started. Check logs for details."
            )

        client = self._mcp_manager.get_client(server_name)
        if client is None:
            raise RuntimeError(f"MCP server {server_name!r} has no active client")

        # ─────────────────────────────────────────────────────────────────
        # Input Abstraction Layer: validate user inputs + inject internal params
        # ─────────────────────────────────────────────────────────────────
        with self._registry_lock:
            meta = self._mcp_registry.get(tool_name, {})
        raw_schema = meta.get("inputSchema") or {}
        abstracted = self._abstraction_registry.get(tool_name, server_name, raw_schema)

        # Step 1: Validate required user inputs
        for field in abstracted.required_inputs:
            if field.name not in arguments:
                error_msg = f"Missing required input: '{field.name}'. {field.description}"
                return json.dumps({"error": error_msg})
            val = arguments[field.name]
            if val is None or (isinstance(val, str) and not val.strip()):
                error_msg = f"Required input '{field.name}' cannot be empty."
                return json.dumps({"error": error_msg})

        # Step 2: Resolve and inject internal parameters
        server_config = self._mcp_manager.server_configs.get(server_name, {})
        internal_resolved = self._context_resolver.resolve_all(
            abstracted.internal_params, server_config
        )

        # Build final arguments: user inputs + auto-resolved internal params
        final_arguments = {**arguments, **internal_resolved}

        # ─────────────────────────────────────────────────────────────────
        # End Input Abstraction Layer
        # ─────────────────────────────────────────────────────────────────

        result = client.call_tool(tool_name, final_arguments)
        return result

    # ── Built-in free tool implementations ────────────────────────────────

    def _run_get_capabilities(self, args: dict) -> str:
        """
        Return list of installed and available MCP server capabilities.

        Response format:
        {
            "installed": ["github", "railway", ...],
            "available_but_not_installed": ["aws", "database", ...],
        }
        """
        try:
            # Get installed servers from MCP registry
            installed_servers = {
                meta.get("_server") for meta in self._mcp_registry.values() if meta.get("_server")
            }
            installed_servers.discard(None)  # Remove None if present
            installed_list = sorted(installed_servers)

            # Get all known MCPs from the recommender catalog
            from agent_core.gateway.mcp_recommender import get_all_known_mcps

            all_known = set(get_all_known_mcps())
            available_list = sorted(all_known - installed_servers)

            result = {
                "installed": installed_list,
                "available_but_not_installed": available_list,
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps({"error": f"Failed to get capabilities: {e}"})

    def _run_recommend_mcps(self, args: dict) -> str:
        """
        Recommend MCP servers based on a query.

        Input: {query: "string"}
        Output: {recommendations: [{name, reason, example_tasks}, ...]}
        """
        try:
            query = args.get("query", "").strip()
            if not query:
                return json.dumps({"error": "query is required"})

            # Get installed MCPs
            installed = {
                meta.get("_server") for meta in self._mcp_registry.values() if meta.get("_server")
            }
            installed.discard(None)

            # Get recommendations from local recommender
            from agent_core.gateway.mcp_recommender import recommend_from_query

            recommendations = recommend_from_query(query, installed)

            if not recommendations:
                return json.dumps(
                    {
                        "recommendations": [],
                        "message": "No additional MCPs found for this query",
                    }
                )

            return json.dumps({"recommendations": recommendations}, indent=2)

        except Exception as e:
            return json.dumps({"error": f"Recommendation failed: {e}"})

    def _run_recommend_mcps_from_stack(self, args: dict) -> str:
        """
        Recommend MCP servers based on a tech stack.

        Input: {stack: ["github", "docker", "aws", ...]}
        Output: {recommendations: [{name, reason, example_tasks}, ...]}
        """
        try:
            stack = args.get("stack", [])
            if not isinstance(stack, list) or not stack:
                return json.dumps({"error": "stack must be a non-empty array"})

            # Get installed MCPs
            installed = {
                meta.get("_server") for meta in self._mcp_registry.values() if meta.get("_server")
            }
            installed.discard(None)

            # Get recommendations from local recommender
            from agent_core.gateway.mcp_recommender import recommend_from_stack

            recommendations = recommend_from_stack(stack, installed)

            if not recommendations:
                return json.dumps(
                    {
                        "recommendations": [],
                        "message": "No complementary MCPs found for this stack",
                    }
                )

            return json.dumps({"recommendations": recommendations}, indent=2)

        except Exception as e:
            return json.dumps({"error": f"Recommendation failed: {e}"})

    def _run_retrieve_tools(self, args: dict) -> str:
        """
        Retrieve tools via the enterprise backend (Qdrant-backed, user-aware).

        Pipeline:
        1. Call /v2/retrieve_tools with auth header (includes user_id)
        2. Backend filters results to user's installed MCPs
        3. If no tools found, recommendations are included in response
        4. Fallback to local keyword search if backend unreachable

        Returns formatted text with tool list or recommendations.
        """
        query = args.get("query", "")
        top_k = int(args.get("top_k", 5))
        top_k = max(1, min(top_k, 20))

        if not query.strip():
            return "Error: query is required"

        # ── Primary: call enterprise backend (v2 with user-aware filtering) ────
        try:
            import json as _json
            import ssl
            import urllib.parse
            import urllib.request

            from agent_core import local_config

            base_url = local_config.get_base_url().rstrip("/")
            auth_header = local_config.get_auth_header()

            # Call /v2/retrieve_tools with user_id from auth header
            params = urllib.parse.urlencode({"query": query, "top_k": top_k})
            url = f"{base_url}/v2/retrieve_tools?{params}"
            headers = {}
            if auth_header:
                headers["Authorization"] = auth_header

            req = urllib.request.Request(url, headers=headers)
            try:
                import certifi

                ctx = ssl.create_default_context(cafile=certifi.where())
            except Exception:
                ctx = ssl.create_default_context()

            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                response = _json.loads(resp.read())

            # Handle v2 response format: {tools: [...], recommended_mcps: [...], ...}
            tools = response.get("tools", []) if isinstance(response, dict) else response
            if not isinstance(tools, list):
                raise ValueError(f"unexpected backend response format: {type(response)}")

            # Build score map and retrieved_tools data for logging
            score_map: dict = {}
            retrieved_tools_data: list[dict] = []
            for t in tools:
                if not isinstance(t, dict) or not t.get("tool_name"):
                    continue
                tool_name = t.get("tool_name") or t.get("name", "")
                score = t.get("confidence_score", 0.0)
                score_map[tool_name] = {
                    "score": score,
                    "semantic_score": score,
                    "capability_score": 0.0,
                    "success_rate": t.get("success_rate", 0.5),
                }
                # Capture full tool metadata for dashboard display
                retrieved_tools_data.append(
                    {
                        "name": tool_name,
                        "server": t.get("server", tool_name),
                        "category": t.get("category", ""),
                        "capabilities": t.get("capabilities", []),
                        "score": score,
                        "semantic_score": score,
                        "capability_score": 0.0,
                        "success_rate": t.get("success_rate", 0.5),
                    }
                )

            selected_names = [
                t.get("tool_name") or t.get("name", "") for t in tools if isinstance(t, dict)
            ]
            _fire_and_forget_log(query, selected_names, score_map, retrieved_tools_data)

            # Format response with tools or recommendations
            return self._format_retrieve_tools_response(
                tools=tools,
                recommended_mcps=response.get("recommended_mcps", []),
                query=query,
            )

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
                # Build basic retrieved_tools data from fallback results
                fallback_retrieved_tools = [
                    {
                        "name": t.get("name", ""),
                        "server": t.get("server", t.get("name", "")),
                        "category": t.get("category", ""),
                        "capabilities": t.get("capabilities", []),
                        "score": 0.0,  # No score available in fallback
                        "semantic_score": 0.0,
                        "capability_score": 0.0,
                        "success_rate": 0.5,
                    }
                    for t in results
                ]
                _fire_and_forget_log(query, selected_names, {}, fallback_retrieved_tools)

                return self._format_retrieve_tools_response(
                    tools=results,
                    recommended_mcps=[],
                    query=query,
                    is_fallback=True,
                )
            except Exception:
                return f"Error during retrieval: {backend_exc}"

    def _format_retrieve_tools_response(
        self,
        tools: list,
        recommended_mcps: list,
        query: str,
        is_fallback: bool = False,
    ) -> str:
        """Format tools and recommendations into readable text response."""
        lines = []

        # Add capability header (get_capabilities() returns list of capability labels)
        capabilities = self.get_capabilities()
        cap_header = f"Available capabilities: {', '.join(capabilities)}" if capabilities else ""

        if cap_header:
            lines.append(cap_header)
            lines.append("")

        # Add tools if found
        if tools:
            fallback_suffix = " (local fallback)" if is_fallback else ""
            lines.append(f"Top {len(tools)} matching tools for {query!r}{fallback_suffix}:")
            for i, t in enumerate(tools, 1):
                # Handle both {"name": ...} and {"tool_name": ...} formats
                name = t.get("tool_name") or t.get("name", "")
                desc = t.get("description", "")

                # Get abstracted inputs from input abstraction layer
                with self._registry_lock:
                    meta = self._mcp_registry.get(name, {})
                raw_schema = meta.get("inputSchema") or {}
                server = meta.get("_server", "")
                abstracted = self._abstraction_registry.get(name, server, raw_schema)

                req_names = [f.name for f in abstracted.required_inputs]
                opt_names = [f.name for f in abstracted.optional_inputs]

                if req_names:
                    inputs_str = f"required: {', '.join(req_names)}"
                    if opt_names:
                        # Show first 3 optional inputs to keep output readable
                        inputs_str += f" | optional: {', '.join(opt_names[:3])}"
                else:
                    inputs_str = "no required inputs"

                lines.append(f"{i}. {name} — {desc} ({inputs_str})")

            lines.append("")
            lines.append("Use execute_tool with the exact tool_name and required arguments.")

        # Add recommendations if tools not found
        elif recommended_mcps:
            lines.append(f"No tools found for: {query!r}")
            lines.append("")
            lines.append("Recommended MCP servers to install:")
            for rec in recommended_mcps[:3]:
                name = rec.get("name", "")
                reason = rec.get("reason", "")
                examples = rec.get("example_tasks", [])[:2]
                example_str = ", ".join(examples) if examples else ""

                lines.append(f"• {name} — {reason}")
                if example_str:
                    lines.append(f"  Examples: {example_str}")

            lines.append("")
            lines.append(
                "Use recommend_mcps(query) or recommend_mcps_from_stack(stack) to get installation help."
            )

        else:
            lines.append(f"No tools found for query: {query!r}")

        return "\n".join(lines)
