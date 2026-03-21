# MCP Server Setup Guide for Agent-CoreX

This guide shows you how to configure MCP servers with Agent-CoreX to expand your tool capabilities.

## What are MCP Servers?

MCP (Model Context Protocol) servers are plugins that expose tools to Agent-CoreX. They allow you to:
- Connect to file systems
- Access persistent memory
- Execute git commands
- Automate browsers
- And much more!

## Quick Start (5 minutes)

### 1. Create Configuration File

Create `config/mcp.json`:

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

### 2. Start Agent-CoreX

```bash
pip install uvicorn
uvicorn apps.api.main:app --reload
```

### 3. Verify Tools Loaded

```bash
curl http://localhost:8000/health
# Should show: {"status": "ok", "tools_loaded": 42, ...}
```

### 4. Try a Query

```bash
curl "http://localhost:8000/retrieve_tools?query=file operations&top_k=5"
```

Done! 🎉

## Available MCP Servers

### Official MCP Servers

| Server | Command | Installation | Purpose |
|--------|---------|--------------|---------|
| **Filesystem** | npx | `npx @modelcontextprotocol/server-filesystem` | Read/write files |
| **Memory** | npx | `npx @modelcontextprotocol/server-memory` | Persistent memory |
| **Git** | uvx | `uvx mcp-server-git` | Git operations |
| **Puppeteer** | npx | `npx @modelcontextprotocol/server-puppeteer` | Browser automation |
| **Sequential Thinking** | npx | `npx @modelcontextprotocol/server-sequential-thinking` | Extended reasoning |

### Full Configuration Examples

#### Filesystem Server

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

Tools: `read_file`, `write_file`, `list_directory`, `create_file`, etc.

#### Memory Server

```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    }
  }
}
```

Tools: `store_memory`, `retrieve_memory`, `clear_memory`, etc.

#### Git Server

```json
{
  "mcpServers": {
    "git": {
      "command": "uvx",
      "args": ["mcp-server-git"]
    }
  }
}
```

Tools: `git_clone`, `git_commit`, `git_push`, `git_diff`, etc.

#### Puppeteer Server (Browser Automation)

```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
    }
  }
}
```

Tools: `browser_screenshot`, `browser_click`, `browser_navigate`, etc.

## Advanced Configuration

### Use Custom MCP Config File

```bash
# Set environment variable
export MCP_CONFIG=/path/to/your/mcp.json

# Start the server
uvicorn apps.api.main:app --reload
```

### Multiple Servers

You can configure as many servers as you need:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "./workspace"]
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    },
    "git": {
      "command": "uvx",
      "args": ["mcp-server-git"]
    },
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
    },
    "sequential_thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    }
  }
}
```

### Reload Without Restart

After updating `config/mcp.json`, reload tools without restarting:

```bash
curl -X POST http://localhost:8000/reload
```

Response:
```json
{
  "status": "reloaded",
  "tools_loaded": 87,
  "message": "Successfully loaded 87 tools"
}
```

## Troubleshooting

### "Command not found"

```
OSError: [Errno 2] No such file or directory: 'npx'
```

**Solution:** Install Node.js
```bash
# macOS
brew install node

# Ubuntu
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### "Server failed to start"

```
Failed to load MCP server 'filesystem': ...
```

**Solution:** Verify the configuration
```bash
# Check if npx is available
npx --version

# Test the server manually
npx -y @modelcontextprotocol/server-filesystem ./workspace
```

### Tools Not Loading

**Check the health endpoint:**
```bash
curl http://localhost:8000/health
```

**Check the server logs for errors:**
```bash
# The API prints startup messages about which servers loaded
# Look for [OK] or [WARN] messages
```

**Verify your MCP config is valid JSON:**
```bash
# Use a JSON validator or Python
python -m json.tool config/mcp.json
```

## API Endpoints for MCP Management

### Health Check

```bash
curl http://localhost:8000/health
```

Response shows how many tools are loaded from all sources.

### List All Tools

```bash
curl http://localhost:8000/tools?limit=50
```

### Get Specific Tool

```bash
curl http://localhost:8000/tools/read_file
```

### Reload Configuration

```bash
curl -X POST http://localhost:8000/reload
```

Useful after updating `config/mcp.json`.

## Python Integration

### Load Custom Config

```python
import os
from packages.tools.mcp.mcp_loader import MCPLoader

# Use custom config
os.environ["MCP_CONFIG"] = "/path/to/your/mcp.json"

loader = MCPLoader(os.environ["MCP_CONFIG"])
manager = loader.load()
tools = manager.get_all_tools()
```

### Combine Local and MCP Tools

```python
from packages.tools.registry import ToolRegistry
from packages.tools.mcp.mcp_loader import MCPLoader
from agent_core import rank_tools

# Local tools
registry = ToolRegistry()
registry.register({"name": "my_tool", "description": "My custom tool"})

# MCP tools
loader = MCPLoader("config/mcp.json")
manager = loader.load()

# Combine
all_tools = registry.get_all_tools() + manager.get_all_tools()

# Use with ranking
results = rank_tools("edit a file", all_tools, top_k=5)
```

## Creating Your Own MCP Server

To create a custom MCP server, see the [MCP Specification](https://spec.modelcontextprotocol.io/).

Basic template:

```python
import json
import sys

def handle_initialize():
    return {
        "jsonrpc": "2.0",
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "serverInfo": {"name": "my-server", "version": "1.0.0"}
        }
    }

def handle_list_tools():
    return {
        "jsonrpc": "2.0",
        "result": {
            "tools": [
                {
                    "name": "my_tool",
                    "description": "A custom tool",
                    "inputSchema": {"type": "object"}
                }
            ]
        }
    }

# Main loop
while True:
    line = sys.stdin.readline()
    request = json.loads(line)
    
    if request.get("method") == "initialize":
        response = handle_initialize()
    elif request.get("method") == "tools/list":
        response = handle_list_tools()
    
    print(json.dumps(response))
    sys.stdout.flush()
```

## Performance Tips

1. **Use keyword method for fast responses:** `?method=keyword`
2. **Cache tool lists:** Servers take 1-5 seconds to start
3. **Limit top_k for real-time:** Use `?top_k=3` for speed
4. **Monitor memory:** Each server uses ~50-100MB

## Support

- **Issues:** https://github.com/ankitpro/agent-corex/issues
- **MCP Spec:** https://spec.modelcontextprotocol.io/
- **MCP Servers:** https://github.com/modelcontextprotocol/servers

Happy configuring! 🚀
