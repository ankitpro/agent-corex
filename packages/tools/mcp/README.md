# MCP Integration

This module provides complete MCP (Model Context Protocol) client implementation for Agent-Core.

## Components

### MCPClient (mcp_client.py)

Low-level JSON-RPC client for communicating with MCP servers via stdio.

**Features:**
- Subprocess management
- JSON-RPC 2.0 communication
- Initialization handshake
- Tool listing

**Example:**
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

for tool in tools:
    print(f"- {tool['name']}")
```

### MCPLoader (mcp_loader.py)

Loads MCP server configuration and initializes clients.

**Features:**
- JSON config parsing
- Client creation and startup
- Error handling and graceful degradation

**Example:**
```python
from packages.tools.mcp.mcp_loader import MCPLoader

loader = MCPLoader("config/mcp.json")
manager = loader.load()
```

### MCPManager (mcp_manager.py)

Aggregates tools from multiple MCP clients.

**Features:**
- Multi-client management
- Tool merging and normalization
- Server failure resilience
- Tool metadata extraction

**Example:**
```python
from packages.tools.mcp.mcp_manager import MCPManager

manager = MCPManager(clients)
all_tools = manager.get_all_tools()
```

## Architecture

```
MCPLoader
    └── reads config/mcp.json
        └── creates MCPClient instances
            └── starts subprocess
                └── initializes via JSON-RPC
                    └── lists tools

MCPManager
    └── receives MCPClient instances
        └── calls list_tools() on each
            └── merges and normalizes results
                └── returns combined tool list
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
    }
  }
}
```

## Supported MCP Servers

### Official MCP Servers

| Server | NPM Package | Purpose |
|--------|-------------|---------|
| **Filesystem** | @modelcontextprotocol/server-filesystem | File operations |
| **Memory** | @modelcontextprotocol/server-memory | Persistent memory |
| **Git** | mcp-server-git (via uvx) | Git operations |
| **Puppeteer** | @modelcontextprotocol/server-puppeteer | Browser automation |
| **Sequential Thinking** | @modelcontextprotocol/server-sequential-thinking | Extended reasoning |

### Installation

```bash
# NPX packages (automatic download)
npx -y @modelcontextprotocol/server-filesystem

# UVX packages
pip install uv
uvx mcp-server-git
```

## Usage Examples

### Basic Usage

```python
from packages.tools.mcp.mcp_loader import MCPLoader
from packages.tools.mcp.mcp_manager import MCPManager

# Load servers from config
loader = MCPLoader("config/mcp.json")
manager = loader.load()

# Get all tools
tools = manager.get_all_tools()
print(f"Loaded {len(tools)} tools")
```

### With Retrieval Engine

```python
from packages.tools.mcp.mcp_loader import MCPLoader
from packages.retrieval.ranker import rank_tools

loader = MCPLoader("config/mcp.json")
manager = loader.load()

tools = manager.get_all_tools()
results = rank_tools("query", tools, top_k=5)
```

### Error Handling

```python
from packages.tools.mcp.mcp_loader import MCPLoader

try:
    loader = MCPLoader("config/mcp.json")
    manager = loader.load()
except Exception as e:
    print(f"Failed to load MCP servers: {e}")
    # Fallback to local tools only
```

## Adding New MCP Servers

### Step 1: Update Configuration

Edit `config/mcp.json`:

```json
{
  "mcpServers": {
    "my_new_server": {
      "command": "npx",
      "args": [
        "-y",
        "@my-org/mcp-server-name"
      ]
    }
  }
}
```

### Step 2: Verify Installation

```bash
npx -y @my-org/mcp-server-name --help
```

### Step 3: Restart API

```bash
# The server will be loaded automatically
uvicorn apps.api.main:app --reload
```

### Step 4: Verify Tools Loaded

```bash
curl "http://localhost:8000/retrieve_tools?query=test"
```

## Error Handling

### Server Startup Failures

If a server fails to start:
1. Error is logged
2. Loading continues with other servers
3. Failed server is skipped

```
[ERROR] Failed to start MCP server 'my_server': ...
[INFO] Continuing with remaining servers
```

### Tool Listing Failures

If `list_tools()` fails:
1. Error is caught
2. Empty tool list returned for that server
3. Other servers continue normally

### Graceful Degradation

The system degrades gracefully:
- 3 servers working, 1 fails → use 3 servers
- All servers fail → use local tools only
- Network error → retry with exponential backoff

## Performance

### Startup Time

- Per server: 1-2 seconds
- Total (3 servers): 3-6 seconds

### Tool Listing

- Per server: ~50-100ms
- Total (3 servers): ~150-300ms

### Caching

Tool lists can be cached:

```python
import json
from packages.tools.mcp.mcp_loader import MCPLoader

loader = MCPLoader("config/mcp.json")
manager = loader.load()

# Cache tools
tools = manager.get_all_tools()
with open("tools_cache.json", "w") as f:
    json.dump(tools, f)
```

## Troubleshooting

### "Command not found"

```
OSError: [Errno 2] No such file or directory: 'npx'
```

Solution: Install Node.js
```bash
curl https://nodejs.org -o node.js
# or
brew install node
```

### "Server initialization failed"

```
RuntimeError: MCP server closed connection during initialize
```

Solution: Verify server is compatible with Agent-Core's MCP protocol version.

### "No tools returned"

1. Check `config/mcp.json` is valid JSON
2. Verify `command` and `args` are correct
3. Check server logs for errors
4. Try running server manually

```bash
npx -y @modelcontextprotocol/server-filesystem ./workspace
```

### High Memory Usage

Each server instance uses ~50-100MB. For many servers, consider:
1. Running servers separately
2. Using a process manager
3. Horizontal scaling

## Future Enhancements

- [ ] HTTP transport for remote MCP servers
- [ ] Health monitoring and auto-restart
- [ ] Dynamic server registration
- [ ] Tool execution with validation
- [ ] Caching with TTL
- [ ] Server pooling
- [ ] Load balancing across multiple instances

## References

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [MCP GitHub](https://github.com/modelcontextprotocol/servers)
- [Agent-Core MCP Integration](../mcp/README.md)
