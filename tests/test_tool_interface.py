"""
Unit tests for Tool Interface Layer.

Validates:
- Only 3 tools are exposed to LLM
- MCP tools are hidden
- Internal tools are hidden
- Tool registration works
- Tool validation works
"""

import pytest
from agent_core.gateway.tool_interface import ToolInterface, get_tool_interface


class TestToolInterfaceBasics:
    """Test basic tool interface functionality."""

    def test_tools_list_returns_exactly_three(self):
        """Tool interface must return exactly 3 tools."""
        interface = ToolInterface()
        tools = interface.tools_list()

        assert len(tools) == 3, f"Expected 3 tools, got {len(tools)}"

    def test_tools_list_contains_correct_names(self):
        """The 3 tools must have correct names."""
        interface = ToolInterface()
        tools = interface.tools_list()
        tool_names = [t["name"] for t in tools]

        assert "get_capabilities" in tool_names
        assert "retrieve_tools" in tool_names
        assert "execute_tool" in tool_names

    def test_all_tools_have_description(self):
        """All tools must have descriptions."""
        interface = ToolInterface()
        tools = interface.tools_list()

        for tool in tools:
            assert "description" in tool
            assert len(tool["description"]) > 10

    def test_all_tools_have_input_schema(self):
        """All tools must have input schemas."""
        interface = ToolInterface()
        tools = interface.tools_list()

        for tool in tools:
            assert "inputSchema" in tool
            assert tool["inputSchema"]["type"] == "object"

    def test_get_capabilities_has_empty_required_inputs(self):
        """get_capabilities should have no required inputs."""
        interface = ToolInterface()
        tools = interface.tools_list()
        get_caps = next(t for t in tools if t["name"] == "get_capabilities")

        assert get_caps["inputSchema"]["required"] == []

    def test_retrieve_tools_has_query_required(self):
        """retrieve_tools must require 'query' input."""
        interface = ToolInterface()
        tools = interface.tools_list()
        retrieve = next(t for t in tools if t["name"] == "retrieve_tools")

        assert "query" in retrieve["inputSchema"]["required"]

    def test_execute_tool_has_required_inputs(self):
        """execute_tool must require 'tool_name' and 'arguments'."""
        interface = ToolInterface()
        tools = interface.tools_list()
        execute = next(t for t in tools if t["name"] == "execute_tool")

        assert "tool_name" in execute["inputSchema"]["required"]
        assert "arguments" in execute["inputSchema"]["required"]


class TestMCPToolIsolation:
    """Test that MCP tools are properly isolated from LLM."""

    def test_mcp_tools_not_in_tools_list(self):
        """MCP tools must not appear in tools_list."""
        interface = ToolInterface()

        # Register some MCP tools
        interface.register_mcp_tools([
            {"name": "deploy", "description": "Deploy app", "server": "railway"},
            {"name": "search-repos", "description": "Search GitHub", "server": "github"},
        ])

        # tools_list should still return only 3
        tools = interface.tools_list()
        assert len(tools) == 3

        tool_names = [t["name"] for t in tools]
        assert "deploy" not in tool_names
        assert "search-repos" not in tool_names

    def test_mcp_tools_accessible_internally(self):
        """MCP tools should be accessible for internal routing."""
        interface = ToolInterface()

        interface.register_mcp_tools([
            {"name": "deploy", "description": "Deploy app", "server": "railway"},
        ])

        assert interface.is_mcp_tool("deploy")
        assert interface.get_mcp_tool("deploy") is not None

    def test_mcp_tools_not_public(self):
        """MCP tools must not be marked as public."""
        interface = ToolInterface()

        interface.register_mcp_tools([
            {"name": "deploy", "description": "Deploy app", "server": "railway"},
        ])

        assert not interface.is_public_tool("deploy")

    def test_list_mcp_tools_internal_only(self):
        """list_mcp_tools should return all registered MCP tools."""
        interface = ToolInterface()

        interface.register_mcp_tools([
            {"name": "deploy", "server": "railway"},
            {"name": "search-repos", "server": "github"},
        ])

        mcp_tools = interface.list_mcp_tools()
        assert "deploy" in mcp_tools
        assert "search-repos" in mcp_tools


class TestCapabilityExtraction:
    """Test capability extraction from MCP tools."""

    def test_get_capabilities_from_tools(self):
        """Should extract capabilities from registered tools."""
        interface = ToolInterface()

        interface.register_mcp_tools([
            {
                "name": "deploy",
                "server": "railway",
                "capabilities": ["deployment", "infrastructure"],
            },
            {
                "name": "search",
                "server": "github",
                "capabilities": ["github", "version_control"],
            },
        ])

        capabilities = interface.get_capabilities_list()
        assert "deployment" in capabilities
        assert "infrastructure" in capabilities
        assert "github" in capabilities
        assert "version_control" in capabilities

    def test_capabilities_are_unique(self):
        """Capabilities should not be duplicated."""
        interface = ToolInterface()

        interface.register_mcp_tools([
            {
                "name": "deploy1",
                "server": "railway",
                "capabilities": ["deployment"],
            },
            {
                "name": "deploy2",
                "server": "railway",
                "capabilities": ["deployment"],
            },
        ])

        capabilities = interface.get_capabilities_list()
        # Count occurrences of "deployment"
        count = sum(1 for c in capabilities if c == "deployment")
        assert count == 1, "deployment should appear only once"

    def test_capabilities_are_sorted(self):
        """Capabilities should be sorted alphabetically."""
        interface = ToolInterface()

        interface.register_mcp_tools([
            {"name": "z-tool", "capabilities": ["zebra"]},
            {"name": "a-tool", "capabilities": ["apple"]},
            {"name": "m-tool", "capabilities": ["middle"]},
        ])

        capabilities = interface.get_capabilities_list()
        assert capabilities == sorted(capabilities)


class TestInternalTools:
    """Test that internal tools are hidden but accessible."""

    def test_internal_tools_not_in_tools_list(self):
        """Internal tools must not appear in tools_list."""
        interface = ToolInterface()
        tools = interface.tools_list()
        tool_names = [t["name"] for t in tools]

        # Internal tools should not be in public list
        assert "github_search" not in tool_names
        assert "web_search" not in tool_names
        assert "database_query" not in tool_names

    def test_internal_tools_not_public(self):
        """Internal tools must not be marked as public."""
        interface = ToolInterface()

        assert not interface.is_public_tool("github_search")
        assert not interface.is_public_tool("web_search")
        assert not interface.is_public_tool("database_query")

    def test_internal_tools_marked_correctly(self):
        """Internal tools should be marked as internal."""
        interface = ToolInterface()

        assert interface.is_internal_tool("github_search")
        assert interface.is_internal_tool("web_search")
        assert interface.is_internal_tool("database_query")


class TestToolSchemaAccess:
    """Test tool schema access for internal routing."""

    def test_get_tool_schema_for_public_tool(self):
        """Should return schema for public tools."""
        interface = ToolInterface()
        schema = interface.get_tool_schema("retrieve_tools")

        assert schema is not None
        assert "description" in schema
        assert "inputSchema" in schema

    def test_get_tool_schema_for_internal_tool(self):
        """Should return schema for internal tools."""
        interface = ToolInterface()
        schema = interface.get_tool_schema("github_search")

        assert schema is not None
        assert "description" in schema
        assert "inputSchema" in schema

    def test_get_tool_schema_for_mcp_tool(self):
        """Should return schema for MCP tools."""
        interface = ToolInterface()

        interface.register_mcp_tools([
            {
                "name": "deploy",
                "description": "Deploy app",
                "server": "railway",
            },
        ])

        schema = interface.get_tool_schema("deploy")
        assert schema is not None
        assert schema["description"] == "Deploy app"

    def test_get_tool_schema_for_nonexistent_tool(self):
        """Should return None for nonexistent tool."""
        interface = ToolInterface()
        schema = interface.get_tool_schema("nonexistent_tool")

        assert schema is None


class TestToolRegistration:
    """Test MCP tool registration."""

    def test_register_multiple_tools(self):
        """Should register multiple tools."""
        interface = ToolInterface()

        count = interface.register_mcp_tools([
            {"name": "tool1", "server": "server1"},
            {"name": "tool2", "server": "server2"},
            {"name": "tool3", "server": "server3"},
        ])

        assert count == 3

    def test_register_tools_without_name_skipped(self):
        """Tools without name should be skipped."""
        interface = ToolInterface()

        count = interface.register_mcp_tools([
            {"name": "tool1", "server": "server1"},
            {"server": "server2"},  # Missing name
            {"name": "tool3", "server": "server3"},
        ])

        assert count == 2  # Only 2 valid tools

    def test_tools_list_still_three_after_registration(self):
        """tools_list should always return 3 regardless of registration."""
        interface = ToolInterface()

        interface.register_mcp_tools([
            {"name": f"tool{i}", "server": f"server{i}"} for i in range(100)
        ])

        tools = interface.tools_list()
        assert len(tools) == 3


class TestToolInterfaceSingleton:
    """Test singleton pattern for tool interface."""

    def test_get_tool_interface_returns_same_instance(self):
        """get_tool_interface should return same instance."""
        interface1 = get_tool_interface()
        interface2 = get_tool_interface()

        assert interface1 is interface2

    def test_singleton_maintains_registrations(self):
        """Registrations should persist across calls."""
        # Clear and reset
        import agent_core.gateway.tool_interface as mod
        mod._tool_interface = None

        interface1 = get_tool_interface()
        interface1.register_mcp_tools([
            {"name": "tool1", "server": "server1"},
        ])

        interface2 = get_tool_interface()
        assert interface2.is_mcp_tool("tool1")


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_tool_name(self):
        """Empty tool name should not be registered."""
        interface = ToolInterface()

        count = interface.register_mcp_tools([
            {"name": "", "server": "server"},
        ])

        assert count == 0

    def test_none_capabilities(self):
        """Tools with None capabilities should be handled."""
        interface = ToolInterface()

        interface.register_mcp_tools([
            {"name": "tool1", "capabilities": None},
        ])

        capabilities = interface.get_capabilities_list()
        # Should not crash, return empty or filtered list
        assert isinstance(capabilities, list)

    def test_tools_list_immutability(self):
        """Modifying returned tools_list should not affect internal state."""
        interface = ToolInterface()
        tools1 = interface.tools_list()

        # Try to modify
        tools1.append({"name": "fake_tool"})

        # Check that internal state is unchanged
        tools2 = interface.tools_list()
        assert len(tools2) == 3
