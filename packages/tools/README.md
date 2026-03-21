# Tools Package

The tools package manages tool definitions, registration, and MCP (Model Context Protocol) integration.

## Components

### 1. **registry.py** - Tool Registry
In-memory registry for storing and retrieving tools.

```python
from packages.tools.registry import ToolRegistry

registry = ToolRegistry()

# Register a tool
registry.register({
    "name": "edit_file",
    "description": "Edit a file with line-based changes"
})

# Get all tools
tools = registry.get_all_tools()
```

**Features:**
- Simple in-memory storage
- No persistence (loads fresh each session)
- Suitable for small tool sets

### 2. **mcp/** - MCP Integration
Complete MCP (Model Context Protocol) client implementation for connecting to MCP servers.

#### **mcp_client.py** - MCP Client
Manages communication with a single MCP server via stdio.

```python
from packages.tools.mcp.mcp_client import MCPClient

client = MCPClient(
    name="filesystem",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "./workspace"]
)

client.start()
client.initialize()
tools = client.list_tools()
```

**Features:**
- JSON-RPC 2.0 communication
- Subprocess-based stdio transport
- Automatic initialization handshake
- Error handling and logging

#### **mcp_loader.py** - MCP Loader
Loads and initializes MCP clients from configuration.

```python
from packages.tools.mcp.mcp_loader import MCPLoader

loader = MCPLoader("config/mcp.json")
manager = loader.load()
```

**Features:**
- Reads MCP servers from JSON config
- Creates and starts clients
- Handles startup failures gracefully

#### **mcp_manager.py** - MCP Manager
Aggregates tools from multiple MCP clients.

```python
from packages.tools.mcp.mcp_manager import MCPManager

manager = MCPManager(clients)
tools = manager.get_all_tools()
```

**Features:**
- Merges tools from multiple servers
- Graceful degradation on server failures
- Tool metadata normalization

## Tool Schema

Tools follow this schema:

```json
{
  "name": "tool_name",
  "description": "What this tool does",
  "server": "mcp_server_name",
  "schema": {
    "type": "object",
    "properties": { /* ... */ }
  }
}
```

## Configuration

MCP servers are configured in `config/mcp.json`:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "./workspace"
      ]
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    }
  }
}
```

## Usage Examples

### Register Local Tools

```python
from packages.tools.registry import ToolRegistry

registry = ToolRegistry()

registry.register({
    "name": "edit_file",
    "description": "Edit a file with line-based changes"
})

registry.register({
    "name": "write_file",
    "description": "Create or overwrite a file"
})

tools = registry.get_all_tools()
```

### Load Tools from MCP

```python
from packages.tools.mcp.mcp_loader import MCPLoader
from packages.tools.mcp.mcp_manager import MCPManager

# Load MCP servers from config
loader = MCPLoader("config/mcp.json")
manager = loader.load()

# Get all tools from MCP servers
tools = manager.get_all_tools()
```

### Combine Local and MCP Tools

```python
from packages.tools.registry import ToolRegistry
from packages.tools.mcp.mcp_loader import MCPLoader
from packages.tools.mcp.mcp_manager import MCPManager

# Local tools
registry = ToolRegistry()
registry.register({"name": "local_tool", "description": "A local tool"})

# MCP tools
loader = MCPLoader("config/mcp.json")
mcp_manager = loader.load()

# Combine
all_tools = registry.get_all_tools() + mcp_manager.get_all_tools()
```

## MCP Servers

### Supported Servers

Agent-Core works with any MCP-compatible server. Common examples:

| Server | Command | Purpose |
|--------|---------|---------|
| **filesystem** | `npx @modelcontextprotocol/server-filesystem` | File operations |
| **memory** | `npx @modelcontextprotocol/server-memory` | Persistent memory |
| **git** | `uvx mcp-server-git` | Git operations |
| **puppeteer** | `npx @modelcontextprotocol/server-puppeteer` | Browser automation |
| **sequential-thinking** | `npx @modelcontextprotocol/server-sequential-thinking` | Extended thinking |

### Adding New MCP Servers

1. Update `config/mcp.json`:

```json
{
  "mcpServers": {
    "my_new_server": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-my-server"]
    }
  }
}
```

2. Reload the manager:

```python
loader = MCPLoader("config/mcp.json")
manager = loader.load()
```

## Error Handling

### Server Startup Failures

If an MCP server fails to start, the loader logs the error and continues with other servers:

```
[ERROR] Failed to start MCP server 'filesystem': ...
[INFO] Continuing with remaining servers
```

### Tool Execution Failures

Tool failures are handled gracefully. The manager returns error details instead of crashing.

## Performance Considerations

- **Cold start:** First initialization takes 1-5 seconds (starting all servers)
- **Tool listing:** ~100ms per server
- **Caching:** Consider caching tool lists if loading is slow

## Testing

Run MCP-related tests:

```bash
pytest tests/ -k "mcp" -v
```

## Future Enhancements

- [ ] Dynamic server registration (add servers at runtime)
- [ ] Server health monitoring
- [ ] Automatic server restart on failure
- [ ] Tool caching with TTL
- [ ] HTTP transport for remote servers
- [ ] Tool execution with argument validation
