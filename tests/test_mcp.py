"""
Tests for MCP (Model Context Protocol) integration.
"""

import pytest
from agent_core.tools.mcp.mcp_manager import MCPManager
from agent_core.tools.mcp.mcp_client import MCPClient


class TestMCPManager:
    """Tests for MCPManager class."""

    def test_register_and_get_tools(self):
        """Verify tools can be registered and retrieved."""
        manager = MCPManager()
        tools = [
            {"name": "list_files", "description": "List files in a directory", "input_schema": {}}
        ]
        manager.register_tools("filesystem", tools)
        all_tools = manager.get_all_tools()
        assert len(all_tools) == 1
        assert all_tools[0]["name"] == "list_files"
        assert all_tools[0]["server"] == "filesystem"

    def test_schema_normalization(self):
        """Verify input_schema is normalized to schema."""
        manager = MCPManager()
        tools = [
            {"name": "test_tool", "description": "Test tool", "input_schema": {"type": "object"}}
        ]
        manager.register_tools("test_server", tools)
        all_tools = manager.get_all_tools()
        assert "schema" in all_tools[0]
        assert all_tools[0]["schema"] == {"type": "object"}

    def test_multiple_servers(self):
        """Verify tools from multiple servers are aggregated."""
        manager = MCPManager()

        fs_tools = [{"name": "read_file", "description": "Read a file", "input_schema": {}}]
        memory_tools = [{"name": "recall", "description": "Recall from memory", "input_schema": {}}]

        manager.register_tools("filesystem", fs_tools)
        manager.register_tools("memory", memory_tools)

        all_tools = manager.get_all_tools()
        assert len(all_tools) == 2
        names = [tool["name"] for tool in all_tools]
        assert "read_file" in names
        assert "recall" in names

    def test_register_server(self):
        """Verify server clients can be registered."""
        manager = MCPManager()
        # Mock client (we don't actually start a process)
        mock_client = MCPClient("test", "echo", [])
        manager.register_server("test_server", mock_client)
        assert "test_server" in manager.servers
        assert manager.servers["test_server"] == mock_client

    def test_empty_manager(self):
        """Verify empty manager returns empty tool list."""
        manager = MCPManager()
        assert manager.get_all_tools() == []

    def test_get_tools_alias(self):
        """Verify get_tools() is an alias for get_all_tools()."""
        manager = MCPManager()
        tools = [{"name": "dummy", "description": "Dummy tool", "input_schema": {}}]
        manager.register_tools("test", tools)
        assert manager.get_tools() == manager.get_all_tools()


class TestMCPClient:
    """Tests for MCPClient class."""

    def test_resolve_command(self):
        """Verify resolve_command returns a string."""
        client = MCPClient("test", "npx", [])
        # resolve_command should return a string (command name)
        cmd = client.resolve_command()
        assert isinstance(cmd, str)
        assert len(cmd) > 0

    def test_resolve_command_returns_input_for_missing(self):
        """Verify resolve_command returns input if not found in PATH."""
        # Use a command that definitely won't be in PATH
        client = MCPClient("test", "definitely_not_a_real_command_xyz", [])
        cmd = client.resolve_command()
        assert cmd == "definitely_not_a_real_command_xyz"

    def test_client_initialization(self):
        """Verify MCPClient initializes with correct attributes."""
        client = MCPClient("test_server", "npx", ["-y", "@test/server"])
        assert client.name == "test_server"
        assert client.command == "npx"
        assert client.args == ["-y", "@test/server"]
        assert client.process is None
