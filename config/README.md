# Configuration

This directory contains configuration files for Agent-Core.

## Files

### mcp.json

Configuration for MCP (Model Context Protocol) servers.

**Structure:**
```json
{
  "mcpServers": {
    "server_name": {
      "command": "command_to_run",
      "args": ["arg1", "arg2", ...]
    }
  }
}
```

**Example:**
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

**Common MCP Servers:**

| Server | Command | Arguments |
|--------|---------|-----------|
| filesystem | npx | @modelcontextprotocol/server-filesystem, ./workspace |
| memory | npx | @modelcontextprotocol/server-memory |
| git | uvx | mcp-server-git |
| puppeteer | npx | @modelcontextprotocol/server-puppeteer |

### mcp_enterprise.json

Template for enterprise integrations (Railway, GitHub, Supabase). Copy this to `~/.agent-corex/mcp.json` for enterprise use.

**Required setup before use:**
- **Railway**: Run `railway login` (uses `~/.railway/config.json` — do NOT set `RAILWAY_TOKEN` env var as it overrides OAuth auth)
- **GitHub**: Set `GITHUB_TOKEN` in `~/.agent-corex/.env` (`ghp_...` or `github_pat_...` format)
- **Supabase**: Set `SUPABASE_ACCESS_TOKEN` in `~/.agent-corex/.env` — this is a **Personal Access Token** from [supabase.com/dashboard/account/tokens](https://supabase.com/dashboard/account/tokens), NOT the anon/service key

```bash
# Copy enterprise template to user config
cp config/mcp_enterprise.json ~/.agent-corex/mcp.json

# Set required env vars
agent-corex setup-env
```

## Adding a New Server

1. Edit `mcp.json`
2. Add new server entry:
   ```json
   "server_name": {
     "command": "command",
     "args": ["arg1", "arg2"]
   }
   ```
3. Restart the API server

The server will be loaded automatically on startup.

## Troubleshooting

**"Failed to start MCP server"** error:
- Check that the command is available in PATH
- Verify arguments are correct
- Ensure the server is compatible with Agent-Core

**Tools not loading:**
- Check server is configured correctly
- Run `curl http://localhost:8000/retrieve_tools?query=test`
- Check server logs for errors
