# 📋 File Index

Complete reference of all source files with functions, classes, and line numbers.

---

## agent_core/

### `__init__.py`
- `__version__` = "2.0.0"

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

### `capability_provider.py` — **[NEW]**
- `SERVER_CAPABILITY_MAP` — List of (substring, label) tuples mapping server names to domains
- `get_capabilities(server_names)` → list[str] — Map server names to capability labels

### `gateway_server.py` — **[ENHANCED]**
- **`SERVER_VERSION`** = "2.0.0" — MCP server version
- **`run()`** — Main entry point, start stdio MCP server
  - Loads ~/.agent-corex/mcp.json + ~/.agent-corex/registry.json and env vars, routes requests via ToolRouter
- `_send(obj)` — Write JSON-RPC message to stdout
- `_error_response(req_id, code, message, data)` — Error response
- `_ok_response(req_id, result)` — Success response
- `_log_query_event(tool_name, arguments)` — Fire-and-forget log to /query/log
- `_report_usage(tool_name, status, latency_ms)` — Fire-and-forget log to /usage/event
- `_handle_initialize(req_id, params, router)` — Handle initialize request
- `_handle_tools_list(req_id, params, router)` — **[SIMPLIFIED]** Returns only 2 tools
- `_handle_tools_call(req_id, params, router)` — **[SIMPLIFIED]** Removed enterprise gate

### `tool_router.py` — **[MAJOR REFACTOR]**
- `TOOL_REGISTRY` — **[CHANGED]** Now contains ONLY 2 tools: retrieve_tools, execute_tool
- `_ENTERPRISE_TOOLS` — **[NEW]** Internal routing table for github_search, web_search, database_query
- `ToolRouter` — Central tool router with internal MCP registry
  - `__init__(extra_tools, mcp_manager)` — Initialize with 2 public tools + hidden MCP registry
  - `_registry` — Public tools (2 only): retrieve_tools, execute_tool
  - `_mcp_registry` — **[NEW]** Internal MCP tools (never sent to Claude)
  - `add_mcp_tools(tools)` — **[CHANGED]** Adds to _mcp_registry only (not _registry)
  - `tools_list()` — **[SIMPLIFIED]** Returns exactly 2 tools with capabilities injected
  - `get_capabilities()` — Derives capability domains from server names
  - `_run_get_capabilities(args)` — **[UPDATED]** Derives "installed" from runtime MCP registry + registry.json + MCPManager configs
  - `get_meta(tool_name)` — **[ENHANCED]** Checks all 3 registries
  - `get_server(tool_name)` — **[UPDATED]** Checks _mcp_registry only
  - `is_enterprise(tool_name)` — **[UPDATED]** Checks _ENTERPRISE_TOOLS
  - `execute_free_tool(tool_name, arguments)` — Routes to retrieve_tools or execute_tool
  - `_run_execute_tool(args)` — **[NEW]** Central routing to MCP/enterprise tools
  - `_run_retrieve_tools(args)` — **[UPDATED]** Returns minimal format with capability header
  - `_run_mcp_tool(tool_name, server_name, arguments)` — Execute MCP tool via MCPManager
  - `_run_list_mcp_servers()` — **[REMOVED]** No longer exposed

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

### `mcp_loader.py` — **[ENHANCED]** (330+ lines)
**Load mcp.json + registry.json config with lazy loading support**

- `TOOLS_CACHE_FILE` — Path to ~/.agent-corex/tools_cache.json
- `REGISTRY_FILE` — Path to ~/.agent-corex/registry.json
- `MCPLoader` — Config loader with lazy startup
  - `__init__(config_path)` — Load mcp.json
  - `load_with_cache(add_tools_callback)` — Fast startup: cached tools + background discovery
  - **`load_registry_servers(manager, add_tools_callback)`** — **[NEW]** Load CLI-added servers from registry.json into MCPManager. Skips duplicates already in mcp.json. Loads cached tool metadata and starts background discovery for uncached servers.
  - `load(lazy_load=True)` — Synchronous load (legacy, non-gateway)
  - `_load_dotenv()` → dict — Load ~/.agent-corex/.env
  - `_build_server_config(name, server, env_dict)` → dict | None
  - `_read_cache()` → dict[str, list]
  - `_write_cache(servers_tools)` → None
  - `_background_discover(config, env_dict, add_tools_callback)` → None

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

### `main.py` — **[MAJOR REWRITE]**
**FastAPI retrieval & execution server — wired to real MCP pool**

- `_mcp_tool_pool` — Real MCP tools from ~/.agent-corex/mcp.json
- `_mcp_manager` — MCPManager instance (lazy-loaded)
- `_load_mcp_tools()` — Background thread: load MCP tools via MCPLoader
- `ExecuteToolRequest` — Pydantic model: {tool_name: str, arguments: dict}
- `@app.get("/health")` — Health check with real tool count
- `@app.get("/tools")` — **[UPDATED]** Returns from real MCP pool with minimal metadata
- `@app.get("/endpoints")` — List all available endpoints
- `@app.get("/retrieve_tools")` — **[UPDATED]** Uses real MCP pool, keyword ranking only
- `@app.post("/execute_tool")` — **[NEW]** Execute tool by name via MCPManager
- `@app.get("/capabilities")` — **[NEW]** Return available capability domains

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
