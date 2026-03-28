# 📋 File Index

Complete reference of all source files with functions, classes, and line numbers.

---

## agent_core/

### `__init__.py`
- `__version__` = "1.1.3"

### `pack_manager.py` (200 lines)
**Pack installation and tracking**
- `PackManager` — Manage pack installation and metadata
  - `list_packs()` → Dict[str, Dict] — List available packs
  - `get_pack(pack_name)` → Optional[Dict] — Get pack definition
  - `install_pack(pack_name, enable_all)` → Dict — Install and register pack
  - `uninstall_pack(pack_name)` → None — Uninstall pack
  - `get_installed_packs()` → Dict — Get all installed packs
  - `get_installed_servers()` → Dict — Get all servers across packs
  - `toggle_server(pack_name, server_name, enabled)` → None — Enable/disable server
  - `get_servers_for_pack(pack_name)` → List[Dict] — Get server definitions
  - `PACK_DEFINITIONS` — Hardcoded pack catalog (vibe_coding_pack, data_science_pack)
  - `INSTALLED_SERVERS_FILE` — Path to ~/.agent-corex/installed_servers.json

### `env_manager.py` (200 lines)
**Environment variable management**
- `EnvManager` — Manage ~/.agent-corex/.env
  - `load_env()` → Dict[str, str] — Load all env vars
  - `save_env(env_vars)` → Path — Save env vars to disk
  - `get_env(key)` → Optional[str] — Get single var
  - `set_env(key, value)` → None — Set single var
  - `delete_env(key)` → None — Delete single var
  - `interactive_setup()` → Dict[str, str] — Interactive prompt
  - `validate_keys(env_vars)` → (bool, List[str]) — Validate format
  - `mask_values(env_vars)` → Dict[str, str] — Mask sensitive values
  - `STANDARD_VARS` — List of known variables with descriptions
  - `ENV_FILE` — Path to ~/.agent-corex/.env

### `mcp_config_generator.py` (150 lines)
**Unified MCP config generation**
- `MCPConfigGenerator` — Generate mcp.json from installed servers
  - `generate_config(include_env)` → Dict[str, Any] — Generate config from AI tools
  - `write_config(config)` → Path — Write config to disk
  - `validate_config(config_path)` → (bool, List[str]) — Validate format
  - `_load_env_file()` → Dict[str, str] — Load .env file
  - `MCP_CONFIG_FILE` — Path to ~/.agent-corex/mcp.json

### `local_config.py`
- `CONFIG_DIR` — Path to ~/.agent-corex
- `CONFIG_FILE` — Path to ~/.agent-corex/config.json
- `load()` — Load config from disk → dict
- `save(data)` — Save config to disk
- `get(key)` → value | None
- `get_api_key()` → str
- `is_logged_in()` → bool
- `get_base_url()` → str
- `get_frontend_url()` → str
- `get_login_url()` → str
- `set_key(key, value)` — Set single key

---

## agent_core/cli/

### `__init__.py`
(empty)

### `main.py` (1300+ lines)
**Typer CLI app with 20+ commands**

**Global:**
- `app` — Typer application instance
- `_version_callback(value)` (line 38) — Handle --version flag
- `_tool_pairs()` (line 63) — Return [(slug, detector, adapter), ...] for 5 AI tools
- `PackManager` — Imported from pack_manager.py

**Commands (alphabetical):**
- `retrieve(query, top_k, method, config)` (line 87) — Semantic search for tools
- `start(host, port, reload, config)` (line 148) — Run FastAPI retrieval server
- `version()` (line 175) — Show CLI version
- `health()` (line 182) — Check backend health
- `set_url(url, frontend)` (line 206) — Set backend/frontend URL
- `config()` (line 237) — Show Python/dependency info
- `serve()` (line 267) — Run MCP gateway (stdio mode)
- `init(yes)` (line 289) — Inject agent-corex into detected tools
- `login(api_key, no_browser)` (line 387) — Store API key
- `status()` (line 470) — Show auth + tools + injection status
- `list_registry()` (line 549) — Browse MCP registry
- `install_mcp(name, tool, yes)` (line 599) — Install server into tools
- `logout(yes)` (line 742) — Remove API key
- `keys()` (line 776) — Show active key + verify
- `detect()` (line 829) — List detected AI tools
- `eject(tool, yes)` (line 858) — Remove agent-corex from tools
- `list_servers(all_tools)` (line 916) — Show injected servers per tool
- `update(yes, tool)` (line 958) — Re-sync servers with registry
- **`install_pack(pack_name, yes)`** (line 1222) — **[NEW]** Install curated tool bundles
- **`generate_mcp_config()`** (line 1372) — **[NEW]** Generate unified mcp.json
- **`setup_env()`** (line 1450) — **[NEW]** Setup environment variables
- `doctor()` (line 1077) — **[ENHANCED]** Diagnose setup issues + pack validation

---

## agent_core/gateway/

### `__init__.py`
(empty)

### `gateway_server.py` — **[ENHANCED]**
- **`run()`** — **[ENHANCED]** Main entry point, start stdio MCP server
  - Now loads ~/.agent-corex/.env and injects env vars into mcp.json
  - Uses lazy_load=True by default
  - Logs: "Loaded X tools from local MCP config (lazy loading enabled)"
- `_send(obj)` — Write JSON-RPC message to stdout
- `_error_response(req_id, code, message, data)` — Error response
- `_ok_response(req_id, result)` — Success response
- `_handle_initialize(req_id, params, router)` — Handle initialize request
- `_handle_tools_list(req_id, params, router)` — Handle tools/list request
- `_handle_tools_call(req_id, params, router)` — Handle tools/call request

### `tool_router.py` — **[ENHANCED]**
- `ToolRouter` — Tool registry facade with intelligent filtering
  - `__init__(self)` — Load tools from registry
  - **`tools_list(max_mcp_tools=10, query=None)`** — **[ENHANCED]** Get filtered tools
    - Now accepts optional query parameter for context-aware filtering
    - Uses hybrid ranking when query provided
    - Falls back to keyword ranking for default context
  - `get_tool_by_name(name)` → tool_schema | None
  - `categorize_tools()` → dict[category, [tools]]

### `auth_middleware.py` — **[ENHANCED]**
- **`get_stored_api_key()`** — **[ENHANCED]** Get API key from:
  1. AGENT_COREX_API_KEY environment variable (highest priority)
  2. ~/.agent-corex/config.json (stored via login)
- `is_authenticated()` → bool
- `check_auth()` → dict | None
- `validate_api_key_format(key)` → bool

---

## agent_core/detectors/

### `__init__.py`
- Imports all detector classes

### `base.py`
- `BaseDetector` (abstract)
  - `is_installed()` → bool
  - `config_path()` → Path | None
  - `name` → str

### `claude.py`
- `ClaudeDesktopDetector(BaseDetector)`
  - `name` = "Claude Desktop"
  - `is_installed()` — Check ~/Library or %APPDATA%
  - `config_path()` → ~/.claude/claude_desktop_config.json

### `cursor.py`
- `CursorDetector(BaseDetector)`
  - `name` = "Cursor"
  - `is_installed()` — Check ~/Library or %APPDATA%
  - `config_path()` → ~/.cursor/config/settings.json

### `vscode.py`
- `VSCodeDetector(BaseDetector)` — VS Code stable
  - `name` = "VS Code"
  - `config_path()` → ~/.config/Code/User/settings.json
- `VSCodeInsidersDetector(BaseDetector)` — VS Code Insiders
  - `name` = "VS Code Insiders"
- `VSCodiumDetector(BaseDetector)` — VSCodium open-source
  - `name` = "VSCodium"

---

## agent_core/config_adapters/

### `__init__.py`
- Imports all adapter classes

### `base.py`
- `BaseConfigAdapter` (abstract)
  - `config_path()` → Path
  - `get_servers()` → dict[name, definition]
  - `has_server(name)` → bool
  - `inject_server(name, definition)` → backup_path | None
  - `remove_server(name)` → backup_path | None

### `claude.py`
- `ClaudeAdapter(BaseConfigAdapter)` — Handle Claude Desktop MCP config (JSON)
  - Reads/writes `~/.claude/claude_desktop_config.json`
  - Structure: `{"mcpServers": {name: definition, ...}}`

### `cursor.py`
- `CursorAdapter(BaseConfigAdapter)` — Handle Cursor MCP config (JSON)
  - Reads/writes `~/.cursor/config/settings.json`
  - Structure: `{"mcpServers": {name: definition, ...}}`

### `vscode.py`
- `VSCodeStableAdapter(BaseConfigAdapter)` — Handle VS Code settings.json
- `VSCodeInsidersAdapter(BaseConfigAdapter)` — Handle VS Code Insiders settings.json
- `VSCodiumAdapter(BaseConfigAdapter)` — Handle VSCodium settings.json
  - All read/write `settings.json` under respective config directories
  - Structure: `{"mcpServers": {name: definition, ...}}`

---

## agent_core/tools/

### `__init__.py`

### `base_tool.py`
- `BaseTool` — Tool base class
  - `name` → str
  - `description` → str
  - `schema` → dict
  - `execute(arguments)` → result

### `registry.py`
- `ToolRegistry` — In-memory tool catalog
  - `get_all_tools()` → [tool_schema]
  - `get_tool_by_name(name)` → tool_schema | None
  - `register(tool)` → None
  - `categories()` → [str]

---

## agent_core/tools/mcp/

### `__init__.py`

### `mcp_client.py` (300+ lines)
**JSON-RPC subprocess communication**

- `MCPClient` — JSON-RPC client
  - `__init__(command, args, env)` — Spawn subprocess
  - `initialize()` → capabilities
  - `list_tools()` → [tool_schema]
  - `call_tool(name, arguments)` → {content, isError}
  - `shutdown()` → None
  - `_send_request(method, params)` → response
  - `_parse_response(raw)` → parsed_json

### `mcp_manager.py` (200+ lines)
**Tool dispatch and execution**

- `MCPManager` — Tool manager
  - `__init__(servers_config)` — Initialize with server definitions
  - `get_all_tools()` → [tool_schema]
  - `get_tool_by_name(name)` → tool_schema | None
  - `call_tool(tool_name, arguments, context=None)` → result
  - `start_server(name)` → MCPClient
  - `shutdown_server(name)` → None
  - `_get_server_for_tool(name)` → server_name

### `mcp_loader.py` — **[ENHANCED]** (200+ lines)
**Load mcp.json config with lazy loading support**

- `MCPLoader` — Config loader with lazy startup
  - `__init__(config_path)` — Load mcp.json
  - **`load(lazy_load=True)`** — **[ENHANCED]** Load MCP servers
    - New parameter: lazy_load (default True)
    - If lazy_load=True:
      - Servers NOT started immediately
      - Server configs registered
      - Tools metadata registered (started briefly to list tools, then stopped)
      - Servers started on-demand when first tool used
    - If lazy_load=False: Legacy behavior (all servers started immediately)
  - `_load_dotenv()` → dict — Load ~/.agent-corex/.env
  - `validate_config()` → bool
  - `_load_from_file(path)` → dict
  - `_build_manager()` → MCPManager

---

## agent_core/retrieval/

### `__init__.py`

### `embeddings.py` (100+ lines)
- `EmbeddingProvider` (abstract)
- `SentenceTransformerProvider` — Use sentence-transformers
  - `embed(text)` → vector
  - `embed_batch(texts)` → [vectors]
- `EmbeddingService` — Singleton service
  - `embed(text)` → vector (with caching)

### `ranker.py` (200+ lines)
- `rank_tools(query, tools, top_k, method)` → ranked_tools
- Supports methods: "keyword", "embedding", "hybrid"

### `scorer.py`
- `cosine_similarity(v1, v2)` → float
- `ScoreResult` — Named tuple with tool + score

### `hybrid_scorer.py`
- `HybridScorer` — BM25 + cosine fusion
  - `score(query, tools)` → [(tool, score), ...]

---

## agent_core/observability/

### `__init__.py`

### `tool_selection_tracker.py`
- `ToolSelectionTracker` — Track tool selection success/failure
  - `log_selection(tool_name, context, success)` → None
  - `get_feedback_for_query(query)` → feedback_data

---

## agent_core/api/

### `__init__.py`

### `main.py` (500+ lines)
**FastAPI retrieval server**

- `app` — FastAPI instance
- `@app.get("/health")` — Health check
- `@app.get("/retrieve_tools")` — Semantic search for tools
  - Parameters: `query`, `top_k`, `method`
- `@app.get("/tools")` — List all tools
- `@app.get("/mcp_registry")` — Get MCP registry

---

## packages/

Duplicated from agent-corex-enterprise:
- `retrieval/` — Ranking algorithms
- `tools/` — MCP integration
- `cache/` — Caching utilities

---

## docs/

### `vibe_coding_local_setup.md` — **[NEW - 300 lines]**
**Complete Vibe Coding setup guide**
- Quick start (5 steps)
- Step-by-step installation
- Environment setup
- MCP config generation
- AI tool verification
- File structure reference
- Troubleshooting section
- Example prompts (deploy, database, full-stack)
- Advanced pack management
- How it works (startup sequence, lazy loading)

### `TESTING_CHECKLIST.md` — **[NEW - 400 lines]**
**Comprehensive end-to-end testing**
- 12 major test sections
- 30+ individual test cases
- Pre-test setup
- Per-section verification steps
- Integration workflow tests
- Error handling tests
- Performance benchmarks
- Test execution template
- Passing criteria and known limitations

## config/

### `mcp.json`
Example MCP server configuration

### `registry_example.json`
Example MCP registry format

---

## tests/

### `test_api.py`
- Test `/retrieve_tools` endpoint
- Test ranking methods

### `test_mcp.py`
- Test MCP protocol (initialize, tools/list, tools/call)
- Test subprocess communication

### `test_retrieval.py`
- Test embedding generation
- Test ranking (keyword, hybrid, embedding)

---

## Configuration Files

### `pyproject.toml`
- Project metadata
- Dependencies
- Entry point: `agent-corex = "agent_core.cli.main:app"`

### `setup.py`
Wrapper (deprecated)

### `README.md`
User-facing documentation

---

## Context Files (THIS FOLDER)

- `main.md` — Overview and quick start
- `repo_map.md` — Architecture and modules
- `file_index.md` — This file
- `features.md` — CLI commands and behaviors
- `current_state.md` — Recent changes and next work
- `change_log.md` — Append-only history

---

**Last Updated:** 2026-03-28
