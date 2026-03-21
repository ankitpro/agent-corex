import json
import time
from .mcp_client import MCPClient
from .mcp_manager import MCPManager


class MCPLoader:

    def __init__(self, config_path):
        self.config_path = config_path

    def load(self):
        """Load MCP servers from config and fetch tools"""
        with open(self.config_path) as f:
            config = json.load(f)

        manager = MCPManager()

        for name, server in config["mcpServers"].items():
            try:
                client = MCPClient(name, server["command"], server["args"])

                client.start()
                client.initialize()
                time.sleep(0.5)

                tools = client.list_tools()
                manager.register_server(name, client)
                manager.register_tools(name, tools)

            except Exception as e:
                print(f"Failed to load MCP server '{name}': {e}")
                # Continue with other servers
                continue

        return manager
