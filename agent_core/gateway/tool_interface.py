"""
Tool Interface Layer — Refactored for retrieval-first architecture.

CRITICAL: LLM sees ONLY 3 tools:
  1. get_capabilities
  2. retrieve_tools
  3. execute_tool

All MCP tools are hidden behind backend routing.
All tool schemas are managed by backend.

This enforces the 3-tool flow:
  get_capabilities → understand what's available
  retrieve_tools  → find relevant tools
  execute_tool    → run selected tool
"""

from __future__ import annotations

import json
import logging
import threading
from typing import Any, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# TOOL CONTRACTS — The ONLY 3 tools LLM sees
# =============================================================================

TOOL_REGISTRY: dict[str, dict[str, Any]] = {
    "get_capabilities": {
        "type": "free",
        "description": (
            "Discover available MCP server capabilities. "
            "Returns a list of installed MCP servers (e.g., github, railway, aws) "
            "with their descriptions. "
            "Use this first to understand what capabilities are available, "
            "then call retrieve_tools to find specific tools."
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
            "Find the best tools for a given task. "
            "Provide a natural-language description of what you want to do, "
            "and this returns the top 3-5 most relevant tools with required inputs. "
            "Use this AFTER get_capabilities to understand context, "
            "and BEFORE execute_tool."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Natural-language description of what you want to accomplish. "
                        "Example: 'deploy my backend to production', 'search github for react hooks'"
                    ),
                },
                "top_k": {
                    "type": "integer",
                    "description": "Max results to return (1-10, default 5)",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 10,
                },
            },
            "required": ["query"],
        },
    },
    "execute_tool": {
        "type": "free",
        "description": (
            "Execute a tool that you selected from retrieve_tools. "
            "Provide the exact tool_name and all required inputs. "
            "The backend will validate inputs, fetch the full schema, "
            "execute via MCP, and return results."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "description": (
                        "Exact tool name from retrieve_tools response. "
                        "Example: 'deploy', 'search-repos', 'list-files'"
                    ),
                },
                "arguments": {
                    "type": "object",
                    "description": (
                        "Arguments required by the tool. "
                        "Must include all 'required_inputs' from retrieve_tools response."
                    ),
                },
            },
            "required": ["tool_name", "arguments"],
        },
    },
}


# =============================================================================
# INTERNAL ROUTING — Hidden from LLM
# =============================================================================

_INTERNAL_TOOLS: dict[str, dict[str, Any]] = {
    "github_search": {
        "type": "internal",
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
        "type": "internal",
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
        "type": "internal",
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


class ToolInterface:
    """
    Tool Interface Layer — enforces retrieval-first architecture.

    LLM sees:  ONLY 3 tools (get_capabilities, retrieve_tools, execute_tool)
    Backend:   Manages schemas, routing, validation, MCP execution

    Invariant: tools_list() returns EXACTLY 3 tools, never more.
    """

    def __init__(self):
        self._registry: dict[str, dict[str, Any]] = dict(TOOL_REGISTRY)
        self._registry_lock = threading.Lock()

        # MCP tools are stored internally, never exposed to LLM
        self._mcp_tools: dict[str, dict[str, Any]] = {}

        # Internal tools for backend routing
        self._internal_tools = dict(_INTERNAL_TOOLS)

    def tools_list(self) -> list[dict[str, Any]]:
        """
        Return the EXACT 3 tools LLM is allowed to see.

        CRITICAL: This MUST always return exactly 3 tools.
        If you're tempted to add more, use backend routing instead.
        """
        with self._registry_lock:
            return [
                {
                    "name": "get_capabilities",
                    "description": self._registry["get_capabilities"]["description"],
                    "inputSchema": self._registry["get_capabilities"]["inputSchema"],
                },
                {
                    "name": "retrieve_tools",
                    "description": self._registry["retrieve_tools"]["description"],
                    "inputSchema": self._registry["retrieve_tools"]["inputSchema"],
                },
                {
                    "name": "execute_tool",
                    "description": self._registry["execute_tool"]["description"],
                    "inputSchema": self._registry["execute_tool"]["inputSchema"],
                },
            ]

    def get_tool_schema(self, tool_name: str) -> Optional[dict[str, Any]]:
        """Get schema for a known tool."""
        if tool_name in self._registry:
            return self._registry[tool_name]
        if tool_name in self._internal_tools:
            return self._internal_tools[tool_name]
        if tool_name in self._mcp_tools:
            return self._mcp_tools[tool_name]
        return None

    def is_public_tool(self, tool_name: str) -> bool:
        """Check if tool is exposed to LLM (the 3 allowed tools)."""
        return tool_name in TOOL_REGISTRY

    def is_internal_tool(self, tool_name: str) -> bool:
        """Check if tool is internal (github_search, web_search, database_query)."""
        return tool_name in self._internal_tools

    def is_mcp_tool(self, tool_name: str) -> bool:
        """Check if tool is an MCP tool (hidden from LLM)."""
        return tool_name in self._mcp_tools

    def register_mcp_tools(self, tools: list[dict[str, Any]]) -> int:
        """
        Register MCP tools discovered from config.

        These tools are NEVER exposed to LLM via tools_list().
        They are executed internally via execute_tool routing.

        Returns: number of tools registered
        """
        with self._registry_lock:
            count = 0
            for tool in tools:
                name = tool.get("name")
                if name:
                    self._mcp_tools[name] = tool
                    count += 1
            logger.info(
                "Registered %d MCP tools (hidden from LLM)",
                count,
            )
            return count

    def get_mcp_tool(self, tool_name: str) -> Optional[dict[str, Any]]:
        """Get full schema for an MCP tool (internal use only)."""
        return self._mcp_tools.get(tool_name)

    def list_mcp_tools(self) -> list[str]:
        """List all registered MCP tools (for internal reference only)."""
        with self._registry_lock:
            return list(self._mcp_tools.keys())

    def get_capabilities_list(self) -> list[str]:
        """Extract unique capability names from all MCP tools."""
        capabilities = set()
        with self._registry_lock:
            for tool in self._mcp_tools.values():
                caps = tool.get("capabilities", [])
                if isinstance(caps, list):
                    capabilities.update(caps)
        return sorted(capabilities)


def get_tool_interface() -> ToolInterface:
    """Get or create the global tool interface from the DI container."""
    from infrastructure.container import get_container

    return get_container().get_tool_interface()
