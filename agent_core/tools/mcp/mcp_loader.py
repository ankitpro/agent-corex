import json
import os
import pathlib
import time
from .mcp_client import MCPClient
from .mcp_manager import MCPManager


class MCPLoader:

    def __init__(self, config_path):
        self.config_path = config_path
        self._env_cache = None

    def _load_dotenv(self) -> dict:
        """Load environment variables from ~/.agent-corex/.env"""
        if self._env_cache is not None:
            return self._env_cache

        env_dict = {}
        env_file = pathlib.Path.home() / ".agent-corex" / ".env"

        if env_file.exists():
            try:
                with open(env_file) as f:
                    for line in f:
                        line = line.strip()
                        # Skip comments and empty lines
                        if not line or line.startswith("#"):
                            continue
                        # Parse KEY=VALUE
                        if "=" in line:
                            key, value = line.split("=", 1)
                            env_dict[key.strip()] = value.strip()
                print(f"Loaded {len(env_dict)} environment variables from {env_file}")
            except Exception as e:
                print(f"Warning: Failed to load .env file: {e}")

        self._env_cache = env_dict
        return env_dict

    def load(self):
        """Load MCP servers from config and fetch tools"""
        with open(self.config_path) as f:
            config = json.load(f)

        # Load environment variables from ~/.agent-corex/.env
        env_dict = self._load_dotenv()

        manager = MCPManager()

        for name, server in config["mcpServers"].items():
            try:
                # Merge server-level env + loaded env (server-level takes precedence)
                merged_env = dict(env_dict)
                if "env" in server and isinstance(server["env"], dict):
                    merged_env.update(server["env"])

                client = MCPClient(
                    name,
                    server["command"],
                    server["args"],
                    extra_env=merged_env if merged_env else None,
                )

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
