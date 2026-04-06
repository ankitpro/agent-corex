"""
Tool Executor — Backend tool routing and execution.

Handles:
- Validating required inputs
- Routing to appropriate backend (MCP, internal, external)
- Executing tools
- Tracking usage
- Error handling

LLM is completely abstracted from:
- Tool schemas (fetched on demand)
- Routing logic (backend decides how to execute)
- MCP manager details
- Validation rules
"""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ToolExecutor:
    """
    Backend tool execution — handles all 3 tools transparently.

    Methods correspond to the 3 LLM tools:
    - execute_get_capabilities()
    - execute_retrieve_tools()
    - execute_execute_tool()
    """

    def __init__(self, backend_client=None):
        """
        Initialize executor.

        Args:
            backend_client: HTTP client for backend API (optional)
        """
        self.backend_client = backend_client

    async def execute_get_capabilities(self) -> dict[str, Any]:
        """
        Execute get_capabilities tool.

        Fetches list of available MCP servers and their descriptions.
        Returns minimal metadata (no tool names, no schemas).

        Returns:
        {
            "capabilities": [
                {
                    "name": "github",
                    "description": "...",
                    "example_tasks": ["push code", "create PR"]
                }
            ]
        }
        """
        try:
            # Call backend /v2/capabilities endpoint
            result = await self._call_backend(
                method="GET",
                path="/v2/capabilities",
            )
            return result
        except Exception as e:
            logger.error("get_capabilities failed: %s", e)
            return {
                "error": f"Failed to fetch capabilities: {str(e)}",
                "capabilities": [],
            }

    async def execute_retrieve_tools(
        self,
        query: str,
        top_k: int = 5,
    ) -> dict[str, Any]:
        """
        Execute retrieve_tools tool.

        Finds top relevant tools for a user query using hybrid ranking.

        Args:
            query: Natural-language description of task
            top_k: Max results to return (1-10)

        Returns:
        {
            "selected_capability": "github",
            "tools": [
                {
                    "name": "search-repos",
                    "description": "Search GitHub repositories",
                    "required_inputs": ["query", "type"],
                    "confidence_score": 0.91
                }
            ]
        }
        """
        if not query or not query.strip():
            return {"error": "query cannot be empty"}

        if not (1 <= top_k <= 10):
            return {"error": "top_k must be between 1 and 10"}

        try:
            # Call backend /v2/retrieve_tools endpoint
            result = await self._call_backend(
                method="GET",
                path="/v2/retrieve_tools",
                params={
                    "query": query,
                    "top_k": top_k,
                    "use_hybrid_v3": True,  # Use enhanced retriever
                },
            )
            return result
        except Exception as e:
            logger.error("retrieve_tools failed: %s", e)
            return {
                "error": f"Failed to retrieve tools: {str(e)}",
                "selected_capability": None,
                "tools": [],
            }

    async def execute_execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute execute_tool tool.

        Validates inputs and executes the selected tool via backend.
        Backend fetches full schema, validates, and routes to MCP/external.

        Args:
            tool_name: Name of tool from retrieve_tools
            arguments: Arguments for the tool

        Returns:
        {
            "success": true,
            "result": {...}
        }
        OR
        {
            "error": "Missing required input: <field>"
        }
        """
        if not tool_name or not tool_name.strip():
            return {"error": "tool_name is required"}

        if not isinstance(arguments, dict):
            return {"error": "arguments must be a dictionary"}

        try:
            # Call backend /v2/execute_tool endpoint
            result = await self._call_backend(
                method="POST",
                path="/v2/execute_tool",
                json={
                    "tool_name": tool_name,
                    "arguments": arguments,
                },
            )
            return result
        except Exception as e:
            logger.error("execute_tool failed: %s", e)
            return {
                "error": f"Tool execution failed: {str(e)}",
            }

    async def _call_backend(
        self,
        method: str,
        path: str,
        params: Optional[dict[str, Any]] = None,
        json: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Call backend API.

        Subclasses should override this to implement actual HTTP calls.
        For testing, this can use mock responses.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path (e.g., /v2/retrieve_tools)
            params: Query parameters
            json: JSON body

        Returns:
            Response from backend
        """
        if self.backend_client is None:
            raise RuntimeError("Backend client not configured")

        if method == "GET":
            return await self.backend_client.get(path, params=params)
        elif method == "POST":
            return await self.backend_client.post(path, json=json)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")


class LocalToolExecutor(ToolExecutor):
    """
    Local tool executor — calls backend APIs synchronously.

    For use in the agent-corex gateway when backend is local.
    """

    def __init__(self, retriever=None, router=None):
        """
        Initialize with local components.

        Args:
            retriever: Enhanced retriever instance
            router: Backend tool router instance
        """
        super().__init__()
        self.retriever = retriever
        self.router = router

    async def execute_get_capabilities(self) -> dict[str, Any]:
        """
        Local implementation: fetch from tool interface.

        Returns capabilities directly without HTTP call.
        """
        try:
            from agent_core.gateway.tool_interface import get_tool_interface

            interface = get_tool_interface()
            capabilities = interface.get_capabilities_list()

            # Format as capability objects
            return {
                "capabilities": [
                    {
                        "name": cap,
                        "description": f"Tools in {cap} capability domain",
                        "example_tasks": [],  # Could be enhanced
                    }
                    for cap in capabilities
                ]
            }
        except Exception as e:
            logger.error("Local get_capabilities failed: %s", e)
            return {
                "error": str(e),
                "capabilities": [],
            }

    async def execute_retrieve_tools(
        self,
        query: str,
        top_k: int = 5,
    ) -> dict[str, Any]:
        """
        Local implementation: use enhanced retriever directly.
        """
        if not query or not query.strip():
            return {"error": "query cannot be empty"}

        if not (1 <= top_k <= 10):
            return {"error": "top_k must be between 1 and 10"}

        try:
            if self.retriever is None:
                raise RuntimeError("Retriever not configured")

            result = await self.retriever.retrieve(
                query=query,
                top_k=top_k,
            )

            # Transform to simplified format for LLM
            simplified = {
                "selected_capability": result.get("selected_capability"),
                "capability_confidence": result.get("capability_confidence", 0),
                "tools": [
                    {
                        "name": tool.get("tool_name", ""),
                        "description": tool.get("description", ""),
                        "required_inputs": tool.get(
                            "required_inputs", []
                        ),  # To be enhanced
                        "confidence_score": tool.get("confidence_score", 0),
                    }
                    for tool in result.get("tools", [])
                ],
            }
            return simplified
        except Exception as e:
            logger.error("Local retrieve_tools failed: %s", e)
            return {
                "error": str(e),
                "selected_capability": None,
                "tools": [],
            }

    async def execute_execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Local implementation: use router to execute tool.

        Validates inputs and executes via MCP or internal routing.
        """
        if not tool_name or not tool_name.strip():
            return {"error": "tool_name is required"}

        if not isinstance(arguments, dict):
            return {"error": "arguments must be a dictionary"}

        try:
            if self.router is None:
                raise RuntimeError("Router not configured")

            # Router handles execution, validation, tracking
            result = await self.router.execute_tool(
                tool_name=tool_name,
                arguments=arguments,
            )
            return result
        except Exception as e:
            logger.error("Local execute_tool failed: %s", e)
            return {
                "error": str(e),
            }
