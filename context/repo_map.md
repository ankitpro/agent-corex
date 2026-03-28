# 🏗️ Repository Architecture Map

High-level module structure and responsibilities.

---

## Directory Structure

```
agent-corex/
│
├── agent_core/                           # Main package
│   ├── __init__.py                       Version (__version__) + imports
│   ├── local_config.py                   Config file I/O (~/.agent-corex/config.json)
│   │
│   ├── cli/
│   │   ├── __init__.py
│   │   └── main.py                       Typer CLI app (1100+ lines) — all 20+ commands
│   │
│   ├── gateway/                          # MCP gateway server
│   │   ├── __init__.py
│   │   ├── gateway_server.py             Main gateway (stdio mode)
│   │   ├── tool_router.py                Tool registry dispatch + filtering
│   │   └── auth_middleware.py            API key validation + format checking
│   │
│   ├── detectors/                        # Detect installed AI tools
│   │   ├── __init__.py
│   │   ├── base.py                       Abstract detector base class
│   │   ├── claude.py                     Claude Desktop detector
│   │   ├── cursor.py                     Cursor detector
│   │   └── vscode.py                     VS Code detector (3 variants: stable, insiders, vscodium)
│   │
│   ├── config_adapters/                  # Read/write AI tool configs
│   │   ├── __init__.py
│   │   ├── base.py                       Abstract config adapter base class
│   │   ├── claude.py                     Claude Desktop config (JSON)
│   │   ├── cursor.py                     Cursor config (JSON)
│   │   └── vscode.py                     VS Code settings (JSON in settings.json)
│   │
│   ├── api/                              # FastAPI retrieval API
│   │   ├── __init__.py
│   │   └── main.py                       FastAPI app + /retrieve_tools endpoint
│   │
│   ├── tools/                            # Tool management
│   │   ├── __init__.py
│   │   ├── base_tool.py                  Tool base class
│   │   ├── registry.py                   In-memory tool registry
│   │   └── mcp/
│   │       ├── __init__.py
│   │       ├── mcp_client.py             JSON-RPC subprocess protocol (initialize, tools/list, tools/call)
│   │       ├── mcp_manager.py            Tool dispatch and execution
│   │       └── mcp_loader.py             Load mcp.json config + caching
│   │
│   ├── retrieval/                        # Semantic search & ranking
│   │   ├── __init__.py
│   │   ├── embeddings.py                 Embedding generation
│   │   ├── ranker.py                     Ranking orchestrator (hybrid / keyword / embedding)
│   │   ├── scorer.py                     Similarity scoring
│   │   └── hybrid_scorer.py              BM25 + cosine similarity fusion
│   │
│   ├── observability/                    # Metrics & feedback
│   │   ├── __init__.py
│   │   └── tool_selection_tracker.py     Success/failure tracking for ranking feedback
│   │
│   ├── detectors/                        # (note: also listed above under gateway section)
│   └── config_adapters/                  # (note: also listed above under gateway section)
│
├── packages/                             # Shared libraries (duplicated from enterprise)
│   ├── __init__.py
│   ├── retrieval/                        # Retrieval algorithms
│   ├── tools/                            # Tool base classes + MCP integration
│   └── cache/                            # Caching utilities
│
├── config/                               # Configuration templates
│   ├── mcp.json                          Example MCP server definitions
│   └── registry_example.json             Example MCP registry format
│
├── examples/                             # Usage examples
│   └── basic_usage.py                    Minimal retrieval example
│
├── tests/                                # Test suite
│   ├── __init__.py
│   ├── test_api.py                       API tests
│   ├── test_mcp.py                       MCP protocol tests
│   └── test_retrieval.py                 Retrieval tests
│
├── context/                              # Documentation (THIS FOLDER)
│   ├── main.md                           Entry point
│   ├── repo_map.md                       This file — architecture
│   ├── file_index.md                     File-by-file reference
│   ├── features.md                       CLI commands & behaviors
│   ├── current_state.md                  Recent changes & next work
│   └── change_log.md                     Append-only history
│
├── pyproject.toml                        Project metadata (setuptools)
├── setup.py                              Setup wrapper (deprecated)
├── README.md                             User-facing documentation
├── LICENSE                               MIT License
└── .gitignore                            Git ignore rules
```

---

## Module Responsibilities

### **cli/main.py** — Typer CLI Interface
**Primary user-facing interface.**

**Responsibilities:**
- Parse CLI arguments via Typer
- Route commands to respective handlers
- Display formatted output (typer.echo)
- Handle interactive prompts (typer.prompt, typer.confirm)
- Show help text and examples

**Commands:**
- Tool retrieval: `retrieve`, `start`, `health`, `version`, `config`
- Gateway: `serve`, `init`, `eject`, `list`, `detect`, `status`
- Auth: `login`, `logout`, `keys`, `set-url`
- Registry: `registry`, `install-mcp`, `update`
- Diagnostics: `doctor`

**Dependencies:** typer, local_config, detectors, config_adapters, ToolRouter

---

### **gateway/gateway_server.py** — MCP Stdio Server
**Runs in stdio mode, injected into Claude Desktop / Cursor / VS Code.**

**Responsibilities:**
- Accept JSON-RPC 2.0 requests over stdin
- Implement MCP protocol (initialize, tools/list, tools/call)
- Call ToolRouter to fetch/filter tools
- Call MCPManager to execute tools
- Return JSON-RPC responses over stdout

**Protocol:**
- `initialize(protocolVersion, ...)` → `initialized` notification
- `tools/list` → returns all available tools
- `tools/call(name, arguments)` → executes tool, returns result

**Dependencies:** tool_router, mcp_manager, FastMCP

---

### **gateway/tool_router.py** — Tool Discovery & Dispatch
**Registry facade with filtering logic.**

**Responsibilities:**
- Load tool schemas from registry
- Apply filtering (query context, user permissions, etc.)
- Match tool names to MCP server implementations
- Return filtered tool list for `tools/list` MCP request

**Key methods:**
- `tools_list(context=None, query=None, top_k=5)` — Retrieve filtered tools
- `get_tool_by_name(name)` — Get single tool schema
- `categorize_tools()` — Organize tools by category

**Dependencies:** tool_indexer, mcp_loader, local_config

---

### **detectors/base.py & implementations**
**Detect installed AI tools and config paths.**

**Responsibilities:**
- Locate AI tool installation directories
- Return config file path for each tool
- Determine if tool is installed

**Implementations:**
- `ClaudeDesktopDetector` — Locate Claude Desktop config
- `CursorDetector` — Locate Cursor config
- `VSCodeDetector`, `VSCodeInsidersDetector`, `VSCodiumDetector` — Locate VS Code configs

**Key methods:**
- `is_installed()` — bool
- `config_path()` → Path
- `name` → str (display name)

---

### **config_adapters/base.py & implementations**
**Read and write AI tool MCP server configurations.**

**Responsibilities:**
- Read existing MCP server definitions from config file
- Inject/update MCP server entries
- Remove MCP server entries
- Create timestamped backups before writing

**Implementations:**
- `ClaudeAdapter` — Handle Claude Desktop MCP config (JSON)
- `CursorAdapter` — Handle Cursor MCP config (JSON)
- `VSCodeAdapter` variants — Handle VS Code settings.json (mcpServers key)

**Key methods:**
- `get_servers()` → dict[name, definition]
- `has_server(name)` → bool
- `inject_server(name, definition)` → backup_path | None
- `remove_server(name)` → backup_path | None
- `config_path()` → Path

---

### **tools/mcp/mcp_client.py** — JSON-RPC Protocol
**Subprocess communication with MCP servers.**

**Responsibilities:**
- Launch MCP server subprocess
- Send JSON-RPC 2.0 requests (initialize, tools/list, tools/call)
- Parse JSON-RPC responses
- Handle protocol errors and timeouts

**Key methods:**
- `initialize()` → schema confirmation
- `list_tools()` → [tool_schema]
- `call_tool(name, arguments)` → {content, isError}

**Dependencies:** subprocess, json, stdio/HTTP transport

---

### **tools/mcp/mcp_manager.py** — Tool Dispatch & Execution
**Maps tools to servers and executes them.**

**Responsibilities:**
- Maintain tool → server mapping
- Route tool execution requests to correct server
- Handle multi-user session isolation (enterprise)
- Track execution success/failure

**Key methods:**
- `get_all_tools()` → [tool_schema]
- `get_tool_by_name(name)` → tool_schema | None
- `call_tool(tool_name, arguments, context=None)` → result

**Dependencies:** mcp_client, mcp_loader, tool_registry

---

### **tools/mcp/mcp_loader.py** — Config Loading
**Parse mcp.json and load server definitions.**

**Responsibilities:**
- Load MCP server definitions from mcp.json
- Validate server definitions
- Cache tool schemas locally (.agent_core_tool_cache.json)
- Handle missing or invalid configs gracefully

**Key methods:**
- `load()` → MCPManager
- `save_cache(tools)` → None
- `get_cache()` → cached_tools | None

---

### **retrieval/** — Search & Ranking
**Semantic search and ranking algorithms.**

**Modules:**
- `embeddings.py` — Generate embeddings via sentence-transformers
- `ranker.py` — Orchestrate ranking by method (keyword/hybrid/embedding)
- `scorer.py` — Cosine similarity scoring
- `hybrid_scorer.py` — BM25 + cosine fusion

**Key methods:**
- `rank_tools(query, tools, top_k, method)` → ranked_tools

---

### **local_config.py** — Configuration File Management
**Read/write ~/.agent-corex/config.json**

**Responsibilities:**
- Load config from disk
- Save config to disk
- Get/set individual keys
- Detect login state
- Return URLs (backend, frontend)

**Key methods:**
- `load()` → dict
- `save(dict)` → None
- `get_api_key()` → str
- `is_logged_in()` → bool
- `get_base_url()` → str
- `set_key(key, value)` → None

---

## Data Flow Diagrams

### MCP Gateway Startup
```
AI Tool (Claude Desktop / Cursor / VS Code)
  ↓
Runs: agent-corex serve
  ↓
gateway_server.py (stdio mode)
  ↓
Load MCP config (mcp.json)
  ↓
MCPLoader → MCPManager → Tool cache
  ↓
Listen for JSON-RPC on stdin
  ↓
Ready to accept tools/list and tools/call
```

### Tool Retrieval Flow (`retrieve` command)
```
User: agent-corex retrieve "edit a file"
  ↓
cli/main.py:retrieve()
  ↓
ToolRegistry.get_all_tools()
  ↓
Embedding.embed(query)
  ↓
ranker.rank_tools(query, tools, method)
  ↓
Return top_k results
  ↓
Display formatted output
```

### MCP Server Injection Flow (`init` command)
```
User: agent-corex init
  ↓
Detect all 5 AI tools (Claude, Cursor, VS Code variants)
  ↓
For each detected tool:
  ├─ Show current MCP servers
  ├─ Prompt user for confirmation
  ├─ Build agent-corex server definition
  ├─ Create backup of current config
  └─ Inject agent-corex entry into config file
  ↓
Display status and tell user to restart tools
```

---

## Architecture Patterns

### **Detector + Adapter Pattern**
- `Detector` — Detect tool installation, return config path
- `Adapter` — Read/write that config file
- Combined: Safe, atomic config updates with backups

### **Router Pattern**
- `ToolRouter` — Facade for tool discovery
- Hides complexity of tool indexing + filtering
- Single entry point for `gateway_server.py`

### **Manager Pattern**
- `MCPManager` — Owns tool-to-server mapping
- `MCPClient` — Protocol-level communication
- Clear separation: dispatch vs. protocol

### **Provider Pattern**
- `EmbeddingProvider` — Abstract interface
- Multiple implementations (OpenAI, Ollama, Transformers)
- Easy to swap providers

---

## Deployment Stages

1. **Development:** `python -m agent_core.cli.main --help`
2. **Package:** `pip install -e .` (local)
3. **Distribution:** `pip install agent-corex` (PyPI)
4. **Entry point:** `agent-corex` command available globally

---

**Last Updated:** 2026-03-28
