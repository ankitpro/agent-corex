# Agent-CoreX CLI — Context Guide

**Entry point for every Claude session.** Read this file first.

---

## Architecture — v4.0.0

```
User / LLM
    │
    ├── CLI: agent-corex run "<query>"
    │         └── AgentCoreXClient.execute_query()
    │                   └── POST /execute/query → backend v2
    │
    └── MCP: execute_query tool (stdio JSON-RPC)
              └── AgentCoreXClient.execute_query()
                        └── POST /execute/query → backend v2
```

**Backend URL:** `https://api.v2.agent-corex.com`

The CLI is a **thin client**. Zero local intelligence:
- No local tool retrieval
- No local input classification
- No local MCP server management
- No JWT/session logic

---

## Design Principles

| Layer | Role |
|-------|------|
| backend | Brain — query decomposition, tool selection, input extraction, execution |
| CLI | Interface — format and display backend responses |
| MCP server | Bridge — expose a single `execute_query` tool to Claude/Cursor |

---

## Key Files

| File | Purpose |
|------|---------|
| `agent_core/cli/main.py` | All CLI commands (Typer) |
| `agent_core/gateway/gateway_server.py` | MCP stdio server (single tool) |
| `agent_core/client.py` | httpx wrapper for v2 backend |
| `agent_core/local_config.py` | `~/.agent-corex/config.json` (api_url, api_key) |
| `agent_core/__init__.py` | `__version__` |
| `pyproject.toml` | Package metadata, deps, entry point |

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `agent-corex run "<query>"` | Execute a task |
| `agent-corex run "<query>" --debug` | Execute with full step details |
| `agent-corex config set api_url=<url>` | Set backend URL |
| `agent-corex config set api_key=<key>` | Set API key |
| `agent-corex config show` | Show current config |
| `agent-corex login --key <key>` | Store + verify API key |
| `agent-corex logout` | Remove stored API key |
| `agent-corex health` | Check backend health |
| `agent-corex version` | Print version |
| `agent-corex serve` | Start MCP stdio server |

---

## MCP Tool

The gateway exposes exactly **one tool**:

```json
{
  "name": "execute_query",
  "description": "Execute any task using Agent-CoreX.",
  "inputSchema": {"query": "string"}
}
```

---

## Config Schema

`~/.agent-corex/config.json`:
```json
{"api_url": "https://api.v2.agent-corex.com", "api_key": "acx_..."}
```

Auth priority: `AGENT_COREX_API_KEY` env > config file.
URL priority: `AGENT_COREX_API_URL` env > config file > default.

---

## Installation

```bash
pip install agent-corex          # PyPI
uvx agent-corex serve            # uvx (no install)
brew install agent-corex         # Homebrew
# or download binary from GitHub Releases
```

---

**Last Updated:** 2026-04-13 — v4.0.0
