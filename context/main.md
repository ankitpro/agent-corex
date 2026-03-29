# Agent-CoreX CLI — Context Guide

**Entry point for every Claude session.** Read this file first.

---

## Quick Start

1. **First time?** Read this entire file
2. **Returning?** Start with [current_state.md](current_state.md) to see what's changed
3. **Lost?** Jump to the file reference in [file_index.md](file_index.md)

---

## What is Agent-CoreX CLI?

**Agent-CoreX** is a fast, accurate MCP tool retrieval and gateway engine for LLMs with semantic search and enterprise support.

The **CLI** (`agent-corex` command) is a unified tool for:
- **Gateway management**: Run MCP gateway server for Claude Desktop / Cursor / VS Code
- **MCP server injection**: Detect and auto-inject agent-corex into AI tools
- **Tool retrieval**: Semantic search for tools by natural language query
- **Registry browsing**: Browse and install MCP servers from the Agent-CoreX registry
- **Authentication**: Login with API keys, manage credentials
- **Diagnostics**: Health checks, configuration validation, troubleshooting

**Tech stack:**
- Python 3.8+
- Typer for CLI framework
- FastAPI for retrieval API
- Sentence Transformers + FAISS for semantic search
- httpx for HTTP client
- Rich for terminal UI

---

## System Architecture

```
agent-corex/
│
├── agent_core/
│   ├── __init__.py              Version + imports
│   ├── local_config.py          Config file management (~/.agent-corex/config.json)
│   │
│   ├── cli/
│   │   └── main.py              Typer CLI app (1100+ lines) — all 20+ commands
│   │
│   ├── gateway/
│   │   ├── gateway_server.py    MCP gateway (stdio mode)
│   │   ├── tool_router.py       Tool registry dispatch
│   │   └── auth_middleware.py   API key validation
│   │
│   ├── detectors/               Detect AI tool installation
│   │   ├── base.py              Abstract detector
│   │   ├── claude.py            Claude Desktop detector
│   │   ├── cursor.py            Cursor detector
│   │   └── vscode.py            VS Code detector (3 variants)
│   │
│   ├── config_adapters/         Read/write AI tool configs
│   │   ├── base.py              Abstract adapter
│   │   ├── claude.py            Claude Desktop config handler
│   │   ├── cursor.py            Cursor config handler
│   │   └── vscode.py            VS Code config handler (3 variants)
│   │
│   ├── api/
│   │   └── main.py              FastAPI app for /retrieve_tools endpoint
│   │
│   ├── tools/
│   │   ├── mcp/
│   │   │   ├── mcp_client.py    JSON-RPC subprocess protocol
│   │   │   ├── mcp_manager.py   Tool dispatch and execution
│   │   │   └── mcp_loader.py    Config loading (mcp.json)
│   │   ├── registry.py          Tool registry
│   │   └── base_tool.py         Tool base class
│   │
│   ├── retrieval/
│   │   ├── embeddings.py        Embedding generation
│   │   ├── ranker.py            Tool ranking (hybrid / keyword / embedding)
│   │   ├── scorer.py            Scoring logic
│   │   └── hybrid_scorer.py     BM25 + cosine fusion
│   │
│   └── observability/
│       └── tool_selection_tracker.py  Success/failure tracking
│
├── packages/                    Shared libraries (duplicated from enterprise)
├── config/                      Configuration templates
├── examples/                    Usage examples
├── tests/                       Test suite
│
├── pyproject.toml              Project metadata
├── setup.py                    Setup wrapper
└── README.md                   User documentation
```

---

## CLI Command Categories

### **Core Commands** (tool retrieval & API)
- `retrieve` — Semantic search for tools
- `start` — Run retrieval API server
- `health` — Check backend connectivity
- `version` — Show CLI version
- `config` — Show Python/dependencies info

### **Gateway & Injection** (MCP gateway management)
- `serve` — Run MCP gateway in stdio mode (injected into AI tools)
- `init` — Detect and inject agent-corex into Claude / Cursor / VS Code
- `eject` — Remove agent-corex from all detected tools
- `list` — Show all injected MCP servers across tools
- `detect` — Detect installed AI tools and config paths

### **Auth & Account**
- `login` — Authenticate with API key
- `logout` — Remove stored credentials
- `keys` — Show active API key + verify with backend
- `set-url` — Configure backend/frontend URLs

### **MCP Registry & Installation**
- `registry` — Browse installable MCP servers from registry
- `install-mcp` — Install a server into detected tools
- `update` — Re-sync all installed servers with registry

### **Diagnostics**
- `doctor` — Comprehensive system health check (Python, deps, config, backend, injection)
- `status` — Show auth state, tools, injection status, available tools

---

## Data & Configuration

### Local Config File
**Path:** `~/.agent-corex/config.json`

**Contents:**
```json
{
  "api_key": "acx_...",
  "base_url": "http://localhost:8000",
  "frontend_url": "http://localhost:5173",
  "user": {
    "user_id": "user_123",
    "name": "Alice"
  }
}
```

### AI Tool Config Paths
- **Claude Desktop:** `~/.claude/claude_desktop_config.json`
- **Cursor:** `~/.cursor/config/settings.json`
- **VS Code:** `~/.config/Code/User/settings.json`
- **VS Code Insiders:** `~/.config/Code - Insiders/User/settings.json`
- **VSCodium:** `~/.config/VSCodium/User/settings.json`

### MCP Server Definition Format
Injected into AI tools as:
```json
{
  "agent-corex": {
    "command": "agent-corex",
    "args": ["serve"]
  }
}
```

Or for VS Code (with `type: stdio`):
```json
{
  "agent-corex": {
    "type": "stdio",
    "command": "agent-corex",
    "args": ["serve"]
  }
}
```

---

## Request Flow

### `/retrieve_tools?query=...&top_k=N`
```
Query
  |
  v
EmbeddingService.embed(query)
  |
  v
numpy cosine similarity: (n_tools, 1536) @ (1536,)
  |
  v
argsort descending, take top_k
  |
  v
Return tool definitions
```

### Tool Execution Flow (`serve` command)
```
Claude Desktop / Cursor / VS Code
  |
  v
stdio MCP protocol (JSON-RPC 2.0)
  |
  v
gateway_server.py (stdio mode)
  |
  v
ToolRouter.get_tools() → list all tools
  |
  v
MCPManager.call_tool(name, args) → execute
  |
  v
Return result to client
```

---

## Key Features

✅ **Zero-config injection** — Detect and auto-inject into 5 AI tools
✅ **Semantic search** — Embed tools, rank by cosine similarity
✅ **MCP gateway** — Stdio server for Claude Desktop / Cursor / VS Code
✅ **Multi-tool support** — Claude, Cursor, VS Code, VS Code Insiders, VSCodium
✅ **Authentication** — API key validation against backend
✅ **Rate limiting** — Free tier limits + paid plans
✅ **Graceful fallbacks** — Works offline, backend optional
✅ **Hybrid ranking** — Keyword search + semantic + BM25 fusion
✅ **Schema caching** — Tool schemas cached locally
✅ **Timestamped backups** — Config backups before injection

---

## Existing Strengths

- **Clean separation**: detectors (discovery) / adapters (config I/O) / CLI (user commands)
- **No side effects**: All CLI commands are safe, non-destructive operations
- **Backups**: Every config write creates timestamped backup
- **Cross-platform**: Handles Windows/macOS/Linux path handling
- **Progressive disclosure**: Doctor command surfaces issues progressively
- **Hybrid ranking**: Supports keyword, embedding, and hybrid search modes
- **Async-ready**: Core packages designed for async execution

---

## Gaps / Next Steps

### Missing for Vibe Coding Experience:
1. **Pack system** — No way to install curated tool bundles (e.g., "Developer Pack")
2. **Auto-registration** — `install-pack` doesn't exist yet
3. **Unified MCP config** — No `generate-mcp-config` command
4. **Lazy server startup** — All servers initialized eagerly
5. **Tool filtering** — No intelligent tool discovery based on context
6. **API key support** — `AGENT_COREX_API_KEY` env var not used in MCP gateway
7. **Setup flow** — No guided `setup-env` command

---

## Development

- **Language:** Python 3.8+
- **Entry point:** `agent_core.cli.main:app` (Typer)
- **Run locally:** `python -m agent_core.cli.main --help`
- **Install locally:** `pip install -e .`
- **Run tests:** `pytest`
- **Deployment:** PyPI (`agent-corex` package)

---

## Mandatory Workflow

**EVERY TIME** you modify code:

1. Read relevant context files before making changes
2. Identify all impacted files (check file_index.md)
3. Make changes to source code
4. Update ALL impacted context files:
   - `file_index.md` (if lines changed, functions modified, new classes)
   - `current_state.md` (note what you changed)
   - `change_log.md` (append new entry with date)
   - `repo_map.md` (only if architecture changed)

---

## Version Increment Checklist

**EVERY TIME you release a new version** (e.g. v1.2.4 → v1.2.5), update ALL of these files:

### Source files (code)
| File | What to change |
|------|---------------|
| `agent_core/__init__.py` | `__version__ = "X.Y.Z"` |
| `pyproject.toml` | `version = "X.Y.Z"` under `[project]` |
| `homebrew/Formula/agent-corex.rb` | `version "X.Y.Z"` |

### Context files (docs)
| File | What to change |
|------|---------------|
| `context/current_state.md` | Update "**Version:** X.Y.Z" and "Last Updated" date |
| `context/change_log.md` | Append new `## YYYY-MM-DD — vX.Y.Z — <title>` entry |
| `context/main.md` | Update "**Last Updated:**" footer date |

### Git / GitHub
1. `git add` all changed files
2. `git commit -m "release: vX.Y.Z — <short description>"`
3. `git push origin main`
4. `git tag vX.Y.Z && git push origin vX.Y.Z`  ← triggers GitHub Actions binary build

### After the release
- GitHub Actions (`build-binaries.yml`) automatically builds Linux/macOS/Windows binaries and attaches them to the GitHub Release.
- Update `homebrew/Formula/agent-corex.rb` SHA256 placeholders once binaries are published (get hashes from the `.sha256` files in the release).

---

**Last Updated:** 2026-03-29
