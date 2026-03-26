class MCPManager:
    """
    Manages MCP clients and tool registration.
    Supports lazy loading of servers: servers are only started when their tools are used.
    """

    def __init__(self, lazy_load=True):
        self.servers = {}  # All registered servers
        self.active_servers = {}  # Currently active (running) servers
        self.tools = []  # All registered tools
        self.lazy_load = lazy_load  # Enable lazy loading
        self.server_configs = {}  # Server config for lazy loading

    def register_server(self, name, client):
        """Register an MCP client by server name"""
        self.servers[name] = client
        self.active_servers[name] = client

    def register_server_config(self, name, config):
        """Store server config for lazy loading"""
        self.server_configs[name] = config

    def register_tools(self, server, tools):
        """Register tools from a server"""
        for tool in tools:
            tool_obj = {
                "server": server,
                "name": tool["name"],
                "description": tool.get("description", ""),
                "schema": tool.get("input_schema", {}),
            }
            self.tools.append(tool_obj)

    def get_all_tools(self):
        """Get all registered tools"""
        return self.tools

    def get_tools(self):
        """Alias for get_all_tools()"""
        return self.tools

    def is_server_active(self, server_name: str) -> bool:
        """Check if a server is currently active (running)"""
        return server_name in self.active_servers

    def get_active_servers(self) -> dict:
        """Get all active servers"""
        return dict(self.active_servers)

    async def ensure_server_running(self, server_name: str) -> bool:
        """
        Ensure a server is running, starting it if needed (for lazy loading).

        Returns:
            True if server is running, False if failed to start
        """
        if self.is_server_active(server_name):
            # Server already running
            return True

        if not self.lazy_load:
            # Lazy loading disabled
            return False

        # Get server from registered servers
        if server_name not in self.servers:
            return False

        try:
            client = self.servers[server_name]
            # Start the server if it has a start method
            if hasattr(client, "start"):
                await client.start() if hasattr(client.start, "__await__") else client.start()
            self.active_servers[server_name] = client
            return True
        except Exception as e:
            print(f"Failed to start server {server_name}: {e}")
            return False

    async def health_check_server(self, server_name: str) -> bool:
        """
        Check if a server is healthy and restart if needed.

        Returns:
            True if server is healthy, False otherwise
        """
        if not self.is_server_active(server_name):
            return False

        try:
            client = self.active_servers[server_name]
            # Check if server has a health check method
            if hasattr(client, "health_check"):
                health_ok = await client.health_check() if hasattr(client.health_check, "__await__") else client.health_check()
                if not health_ok:
                    # Server unhealthy, try to restart
                    if hasattr(client, "stop"):
                        await client.stop() if hasattr(client.stop, "__await__") else client.stop()
                    del self.active_servers[server_name]
                    return await self.ensure_server_running(server_name)
                return True
            return True
        except Exception:
            return False
