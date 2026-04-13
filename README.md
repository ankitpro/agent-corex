# Agent-CoreX

Execute any task with a single natural language query.

Agent-CoreX is a **thin CLI + MCP client** for the Agent-CoreX v2 backend. All intelligence — query decomposition, tool selection, input extraction, and execution — lives in the backend.

---

## Install

```bash
# pip
pip install agent-corex

# uvx (no install required)
uvx agent-corex run "list my supabase projects"

# Homebrew (macOS / Linux)
brew tap ankitpro/agent-corex
brew install agent-corex

# Binary — download from GitHub Releases
# https://github.com/ankitpro/agent-corex/releases/latest
```

---

## Quickstart

```bash
# Authenticate
agent-corex login --key acx_your_api_key

# Run a query
agent-corex run "list my supabase projects"

# Debug mode — see full execution pipeline
agent-corex run "create a github repo called my-app" --debug
```

---

## CLI Reference

```
agent-corex run "<query>"                 Execute a task
agent-corex run "<query>" --debug         Show full step details
agent-corex config set api_url=<url>      Set backend URL
agent-corex config set api_key=<key>      Set API key
agent-corex config show                   Show current config
agent-corex login --key <key>             Store and verify API key
agent-corex logout                        Remove stored API key
agent-corex health                        Check backend status
agent-corex version                       Print version
agent-corex serve                         Start MCP server (for Claude/Cursor)
```

---

## MCP Usage

Agent-CoreX exposes a single MCP tool — `execute_query` — for use with Claude Desktop, Cursor, and other MCP-compatible clients.

### Claude Desktop / Cursor

Add to your MCP config:

```json
{
  "agent-corex": {
    "command": "agent-corex",
    "args": ["serve"],
    "env": {
      "AGENT_COREX_API_KEY": "acx_your_api_key"
    }
  }
}
```

### uvx (no install required)

```json
{
  "agent-corex": {
    "command": "uvx",
    "args": ["agent-corex", "serve"],
    "env": {
      "AGENT_COREX_API_KEY": "acx_your_api_key"
    }
  }
}
```

Once connected, use Claude naturally — it will call `execute_query` automatically:

> "List my Supabase projects"
> "Create a GitHub repo called my-app and add a README"
> "Deploy my Railway service"

---

## Examples

```bash
# List Supabase projects
agent-corex run "list my supabase projects"

# Multi-step: list and analyze
agent-corex run "list my supabase projects and show their sizes"

# Debug mode — see intents, tools, inputs, latency
agent-corex run "deploy my railway service" --debug

# Missing input — backend will ask what's needed
agent-corex run "deploy service"
```

---

## Configuration

Config is stored at `~/.agent-corex/config.json`:

```json
{
  "api_url": "https://api.v2.agent-corex.com",
  "api_key": "acx_..."
}
```

Override via environment variables:
```bash
AGENT_COREX_API_KEY=acx_...        # takes priority over config file
AGENT_COREX_API_URL=http://...     # for local development
```

---

## Architecture

```
User / LLM
    │
    ├── CLI: agent-corex run "<query>"
    │         └── POST /execute/query → backend v2
    │                   (decompose → retrieve → select → execute)
    │
    └── MCP: execute_query tool
              └── POST /execute/query → backend v2
```

The CLI is intentionally minimal:
- **backend** = brain (query decomposition, tool selection, execution)
- **CLI** = interface (send query, display response)
- **MCP** = bridge (expose single tool to LLMs)

---

## License

MIT — see [LICENSE](LICENSE)
