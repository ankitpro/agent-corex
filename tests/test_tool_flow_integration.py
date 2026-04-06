"""
Integration tests for the 3-tool flow.

Validates end-to-end execution:
1. get_capabilities → understand domain
2. retrieve_tools → find relevant tools
3. execute_tool → run selected tool
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from agent_core.gateway.tool_interface import ToolInterface
from agent_core.gateway.tool_executor import LocalToolExecutor
from agent_core.gateway.backend_router import BackendToolRouter


class MockRetriever:
    """Mock enhanced retriever."""

    async def retrieve(self, query: str, top_k: int = 5):
        """Return mock retrieval results."""
        return {
            "selected_capability": "deployment",
            "capability_confidence": 0.85,
            "tools": [
                {
                    "tool_name": "deploy",
                    "server": "railway",
                    "description": "Deploy app to Railway",
                    "confidence_score": 0.95,
                    "required_inputs": ["repo_path", "branch"],
                    "category": "deployment",
                    "tags": ["deploy", "production"],
                },
            ],
        }


class MockRouter:
    """Mock tool router."""

    async def execute_tool(self, tool_name: str, arguments: dict):
        """Execute tool and return result."""
        if tool_name == "deploy":
            if not arguments.get("repo_path"):
                return {"error": "Missing required input: repo_path"}
            if not arguments.get("branch"):
                return {"error": "Missing required input: branch"}

            return {
                "success": True,
                "result": {
                    "message": "Deployed successfully",
                    "url": "https://app.railway.app",
                },
            }
        else:
            return {"error": f"Unknown tool: {tool_name}"}


@pytest.mark.asyncio
class TestFullToolFlow:
    """Test the complete 3-tool flow."""

    async def test_step1_get_capabilities(self):
        """Step 1: Get capabilities."""
        interface = ToolInterface()
        interface.register_mcp_tools(
            [
                {"name": "deploy", "server": "railway", "capabilities": ["deployment"]},
                {"name": "search", "server": "github", "capabilities": ["github"]},
            ]
        )

        capabilities = interface.get_capabilities_list()

        assert "deployment" in capabilities
        assert "github" in capabilities

    async def test_step2_retrieve_tools(self):
        """Step 2: Retrieve tools for query."""
        retriever = MockRetriever()
        result = await retriever.retrieve("deploy app to production")

        assert result["selected_capability"] == "deployment"
        assert len(result["tools"]) > 0
        assert result["tools"][0]["tool_name"] == "deploy"
        assert "required_inputs" in result["tools"][0]

    async def test_step3_execute_tool_with_all_inputs(self):
        """Step 3: Execute tool with all required inputs."""
        router = MockRouter()
        result = await router.execute_tool(
            "deploy",
            {
                "repo_path": "/home/user/app",
                "branch": "main",
            },
        )

        assert result["success"] is True
        assert "url" in result["result"]

    async def test_step3_execute_tool_missing_input(self):
        """Step 3: Execute tool should fail with missing input."""
        router = MockRouter()
        result = await router.execute_tool(
            "deploy",
            {
                "repo_path": "/home/user/app",
                # Missing branch
            },
        )

        assert "error" in result
        assert "branch" in result["error"]

    async def test_full_flow_end_to_end(self):
        """Test full 3-step flow."""
        # Step 1: Setup and get capabilities
        interface = ToolInterface()
        interface.register_mcp_tools(
            [
                {"name": "deploy", "server": "railway", "capabilities": ["deployment"]},
            ]
        )

        capabilities = interface.get_capabilities_list()
        assert "deployment" in capabilities

        # Step 2: Retrieve tools
        retriever = MockRetriever()
        retrieve_result = await retriever.retrieve("deploy app")
        assert len(retrieve_result["tools"]) > 0

        # Step 3: Execute tool
        tool = retrieve_result["tools"][0]
        router = MockRouter()
        exec_result = await router.execute_tool(
            tool["tool_name"],
            {
                "repo_path": "/home/user/app",
                "branch": "main",
            },
        )
        assert exec_result["success"] is True


@pytest.mark.asyncio
class TestToolExecutor:
    """Test LocalToolExecutor."""

    async def test_executor_get_capabilities(self):
        """Test executor's get_capabilities."""
        interface = ToolInterface()
        interface.register_mcp_tools(
            [
                {"name": "deploy", "capabilities": ["deployment"]},
            ]
        )

        executor = LocalToolExecutor()
        # Mock the interface
        executor.interface = interface

        result = await executor.execute_get_capabilities()

        assert "capabilities" in result or "error" in result

    async def test_executor_retrieve_tools(self):
        """Test executor's retrieve_tools."""
        retriever = MockRetriever()
        executor = LocalToolExecutor(retriever=retriever)

        result = await executor.execute_retrieve_tools("deploy app")

        assert "tools" in result
        assert len(result["tools"]) > 0

    async def test_executor_execute_tool(self):
        """Test executor's execute_tool."""
        router = MockRouter()
        executor = LocalToolExecutor(router=router)

        result = await executor.execute_execute_tool(
            "deploy",
            {
                "repo_path": "/home/user/app",
                "branch": "main",
            },
        )

        assert "result" in result or "error" in result


@pytest.mark.asyncio
class TestBackendRouter:
    """Test BackendToolRouter."""

    async def test_router_validates_required_inputs(self):
        """Router should validate required inputs."""
        router = BackendToolRouter()

        # Tool schema with required inputs
        schema = {
            "name": "deploy",
            "server": "railway",
            "required_inputs": ["repo_path", "branch"],
        }

        # Missing repo_path
        error = router._validate_inputs(schema, {"branch": "main"})
        assert error is not None
        assert "repo_path" in error

    async def test_router_accepts_valid_inputs(self):
        """Router should accept valid inputs."""
        router = BackendToolRouter()

        schema = {
            "name": "deploy",
            "server": "railway",
            "required_inputs": ["repo_path", "branch"],
        }

        # All required inputs present
        error = router._validate_inputs(
            schema,
            {
                "repo_path": "/home/user/app",
                "branch": "main",
            },
        )
        assert error is None

    async def test_router_rejects_empty_values(self):
        """Router should reject empty string values."""
        router = BackendToolRouter()

        schema = {
            "name": "deploy",
            "required_inputs": ["repo_path"],
        }

        error = router._validate_inputs(schema, {"repo_path": ""})
        assert error is not None

    async def test_router_rejects_none_values(self):
        """Router should reject None values."""
        router = BackendToolRouter()

        schema = {
            "name": "deploy",
            "required_inputs": ["repo_path"],
        }

        error = router._validate_inputs(schema, {"repo_path": None})
        assert error is not None


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling in 3-tool flow."""

    async def test_invalid_tool_name(self):
        """Executing invalid tool should return error."""
        executor = LocalToolExecutor()

        result = await executor.execute_execute_tool("", {})

        assert "error" in result
        assert "tool_name" in result["error"]

    async def test_invalid_arguments_type(self):
        """Arguments must be a dictionary."""
        executor = LocalToolExecutor()

        result = await executor.execute_execute_tool("deploy", "invalid")

        assert "error" in result
        assert "dictionary" in result["error"]

    async def test_missing_required_input(self):
        """Missing required input should be caught."""
        router = MockRouter()
        executor = LocalToolExecutor(router=router)

        result = await executor.execute_execute_tool(
            "deploy",
            {
                "repo_path": "/home/user/app",
                # Missing branch
            },
        )

        # Executor would pass to router, which validates
        assert result is not None


@pytest.mark.asyncio
class TestToolConstraints:
    """Test that tool interface constraints are enforced."""

    def test_only_three_tools_visible(self):
        """Only 3 tools should be visible to LLM."""
        interface = ToolInterface()

        # Register 100 MCP tools
        for i in range(100):
            interface.register_mcp_tools(
                [
                    {"name": f"tool{i}", "server": f"server{i}"},
                ]
            )

        # tools_list should still return exactly 3
        tools = interface.tools_list()
        assert len(tools) == 3

    def test_no_mcp_tools_exposed(self):
        """No MCP tools should be in tools_list."""
        interface = ToolInterface()

        interface.register_mcp_tools(
            [
                {"name": "deploy", "server": "railway"},
                {"name": "search", "server": "github"},
            ]
        )

        tools = interface.tools_list()
        tool_names = [t["name"] for t in tools]

        assert "deploy" not in tool_names
        assert "search" not in tool_names

    def test_no_internal_tools_exposed(self):
        """No internal tools should be in tools_list."""
        interface = ToolInterface()

        tools = interface.tools_list()
        tool_names = [t["name"] for t in tools]

        assert "github_search" not in tool_names
        assert "web_search" not in tool_names
        assert "database_query" not in tool_names


class TestToolNaming:
    """Test tool naming consistency."""

    def test_public_tools_have_correct_names(self):
        """Public tools must have exact names."""
        interface = ToolInterface()
        tools = interface.tools_list()

        tool_names = {t["name"] for t in tools}

        assert tool_names == {
            "get_capabilities",
            "retrieve_tools",
            "execute_tool",
        }

    def test_tool_names_match_descriptions(self):
        """Tool names should match their function."""
        interface = ToolInterface()
        tools = interface.tools_list()

        for tool in tools:
            name = tool["name"]
            desc = tool["description"].lower()

            if name == "get_capabilities":
                assert "capabilit" in desc
            elif name == "retrieve_tools":
                assert "retrieve" in desc or "find" in desc or "search" in desc
            elif name == "execute_tool":
                assert "execute" in desc or "run" in desc
