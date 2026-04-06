"""
Backend Tool Router — Handles routing and execution of the 3 tools.

Responsibilities:
- Route execute_tool calls to appropriate backend (MCP, internal, external)
- Fetch full tool schemas (internal, not exposed to LLM)
- Validate required inputs
- Execute tools and track usage
- Handle errors gracefully

LLM never sees this — it's pure backend routing.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class BackendToolRouter:
    """
    Routes tool execution to backend systems.

    Handles the 3-tool flow:
    1. get_capabilities: Fetch available capability domains
    2. retrieve_tools: Find relevant tools via hybrid search
    3. execute_tool: Route to appropriate backend and execute
    """

    def __init__(self, mcp_manager=None, retriever=None, usage_tracker=None):
        """
        Initialize router.

        Args:
            mcp_manager: MCPManager for executing MCP tools
            retriever: Enhanced retriever for retrieve_tools
            usage_tracker: UsageTracker for recording executions
        """
        self.mcp_manager = mcp_manager
        self.retriever = retriever
        self.usage_tracker = usage_tracker

    async def route_execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        user_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Route tool execution to appropriate backend.

        Fetches full schema, validates, executes, tracks usage.

        Args:
            tool_name: Name of tool (from retrieve_tools)
            arguments: Arguments provided by LLM
            user_id: User context for tracking

        Returns:
        {
            "success": true,
            "result": {...}
        }
        OR
        {
            "error": "Error message"
        }
        """
        if not tool_name or not tool_name.strip():
            return {"error": "tool_name is required"}

        if not isinstance(arguments, dict):
            return {"error": "arguments must be a dictionary"}

        try:
            # Step 1: Get full tool schema (internal, not exposed to LLM)
            tool_schema = await self._fetch_tool_schema(tool_name)
            if not tool_schema:
                logger.warning("Tool schema not found: %s", tool_name)
                return {"error": f"Tool not found: {tool_name}"}

            # Step 2: Validate required inputs
            validation_error = self._validate_inputs(tool_schema, arguments)
            if validation_error:
                return {"error": validation_error}

            # Step 3: Route to appropriate backend
            server = tool_schema.get("server", "")
            if not server:
                return {"error": f"Tool has no server: {tool_name}"}

            # Step 4: Execute tool
            result = await self._execute_in_backend(
                tool_name=tool_name,
                server=server,
                arguments=arguments,
            )

            # Step 5: Track usage
            if self.usage_tracker and user_id:
                await self.usage_tracker.record_execution(
                    tool_name=tool_name,
                    server=server,
                    user_id=user_id,
                    success=result.get("success", False),
                    execution_time_ms=result.get("execution_time_ms"),
                )

            return result

        except Exception as e:
            logger.error("Tool execution failed: %s", e)
            return {"error": f"Tool execution failed: {str(e)}"}

    async def _fetch_tool_schema(self, tool_name: str) -> Optional[dict[str, Any]]:
        """
        Fetch full tool schema from internal registry.

        This is NOT exposed to LLM, only used internally for routing.

        Schema includes:
        - name: tool name
        - description: what tool does
        - server: which MCP server provides this tool
        - schema: full input/output schema
        - required_inputs: list of required parameters
        """
        try:
            # Try to get from MCP manager
            if self.mcp_manager:
                tool = self.mcp_manager.get_tool(tool_name)
                if tool:
                    return tool

            # Could also check retriever's internal cache
            # Or database of tool schemas
            logger.warning("Tool schema not found in any registry: %s", tool_name)
            return None

        except Exception as e:
            logger.error("Failed to fetch tool schema: %s", e)
            return None

    def _validate_inputs(
        self,
        tool_schema: dict[str, Any],
        arguments: dict[str, Any],
    ) -> Optional[str]:
        """
        Validate required inputs against tool schema.

        Returns error message if validation fails, None if valid.
        """
        required_inputs = tool_schema.get("required_inputs", [])

        for required in required_inputs:
            if required not in arguments:
                return f"Missing required input: {required}"

            value = arguments[required]
            if value is None or (isinstance(value, str) and not value.strip()):
                return f"Required input '{required}' cannot be empty"

        return None

    async def _execute_in_backend(
        self,
        tool_name: str,
        server: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute tool in appropriate backend system.

        Routes based on server type:
        - MCP server: use mcp_manager
        - Internal: use internal router
        - External: use HTTP client

        Args:
            tool_name: Name of tool
            server: Which server provides the tool
            arguments: Tool arguments

        Returns:
        {
            "success": true,
            "result": {...},
            "execution_time_ms": 250
        }
        """
        import time

        start_time = time.time()

        try:
            # Determine how to execute based on server type
            if server in ["github", "railway", "aws", "database", "filesystem"]:
                # MCP servers
                if self.mcp_manager:
                    result = await self.mcp_manager.execute(
                        server=server,
                        tool_name=tool_name,
                        arguments=arguments,
                    )
                else:
                    return {"error": f"MCP manager not configured for {server}"}

            elif server in ["github_search", "web_search", "database_query"]:
                # Internal backend tools
                result = await self._execute_internal(
                    server=server,
                    arguments=arguments,
                )

            else:
                return {"error": f"Unknown server type: {server}"}

            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000

            return {
                "success": True,
                "result": result,
                "execution_time_ms": execution_time_ms,
            }

        except Exception as e:
            logger.error("Backend execution failed: %s", e)
            execution_time_ms = (time.time() - start_time) * 1000

            return {
                "success": False,
                "error": str(e),
                "execution_time_ms": execution_time_ms,
            }

    async def _execute_internal(
        self,
        server: str,
        arguments: dict[str, Any],
    ) -> Any:
        """
        Execute internal backend tool (github_search, web_search, etc).

        These are enterprise tools NOT exposed via tools_list.
        """
        if server == "github_search":
            return await self._execute_github_search(arguments)
        elif server == "web_search":
            return await self._execute_web_search(arguments)
        elif server == "database_query":
            return await self._execute_database_query(arguments)
        else:
            raise ValueError(f"Unknown internal server: {server}")

    async def _execute_github_search(self, arguments: dict[str, Any]) -> Any:
        """Execute GitHub search (internal)."""
        # Implementation would call GitHub API
        # For now, return placeholder
        return {
            "results": [],
            "message": "GitHub search not yet fully implemented",
        }

    async def _execute_web_search(self, arguments: dict[str, Any]) -> Any:
        """Execute web search (internal)."""
        # Implementation would call web search API
        query = arguments.get("query", "")
        max_results = arguments.get("max_results", 10)

        return {
            "results": [],
            "query": query,
            "message": "Web search not yet fully implemented",
        }

    async def _execute_database_query(self, arguments: dict[str, Any]) -> Any:
        """Execute database query (internal)."""
        # Implementation would execute SQL safely
        sql = arguments.get("sql", "")
        database = arguments.get("database", "")

        return {
            "rows": [],
            "message": "Database query not yet fully implemented",
        }

    async def get_tool_schema_for_execution(
        self,
        tool_name: str,
    ) -> Optional[dict[str, Any]]:
        """
        Get tool schema for validation/execution.

        This is INTERNAL ONLY — not exposed to LLM.
        Returns full schema with all details.
        """
        return await self._fetch_tool_schema(tool_name)


class ToolSchemaCache:
    """
    Cache for tool schemas to avoid repeated lookups.

    Schemas are fetched once and cached in memory with TTL.
    """

    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize schema cache.

        Args:
            ttl_seconds: Cache time-to-live (default 1 hour)
        """
        self._cache: dict[str, tuple[float, dict[str, Any]]] = {}
        self._ttl = ttl_seconds

    def get(self, tool_name: str) -> Optional[dict[str, Any]]:
        """Get cached schema if not expired."""
        if tool_name not in self._cache:
            return None

        timestamp, schema = self._cache[tool_name]
        import time

        if time.time() - timestamp > self._ttl:
            del self._cache[tool_name]
            return None

        return schema

    def set(self, tool_name: str, schema: dict[str, Any]) -> None:
        """Cache a tool schema."""
        import time

        self._cache[tool_name] = (time.time(), schema)

    def clear(self) -> None:
        """Clear entire cache."""
        self._cache.clear()
