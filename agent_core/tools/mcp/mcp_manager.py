class MCPManager:

    def __init__(self):
        self.servers = {}
        self.tools = []

    def register_server(self, name, client):
        """Register an MCP client by server name"""
        self.servers[name] = client

    def register_tools(self, server, tools):
        """Register tools from a server"""
        for tool in tools:
            tool_obj = {
                "server": server,
                "name": tool["name"],
                "description": tool.get("description", ""),
                "schema": tool.get("input_schema", {})
            }
            self.tools.append(tool_obj)

    def get_all_tools(self):
        """Get all registered tools"""
        return self.tools

    def get_tools(self):
        """Alias for get_all_tools()"""
        return self.tools