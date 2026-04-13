# 📝 Change Log

Append-only history of changes to the agent-corex CLI.

---

## 2026-04-13 — v4.0.0 — Thin client rewrite for v2 backend

**What:** Complete rewrite. CLI is now a thin client delegating all intelligence to the v2 backend at `https://api.v2.agent-corex.com`. Removed local ML retrieval, MCP server management, input abstraction, JWT auth, and all optional dependencies. Added `agent_core/client.py` as the sole HTTP layer. MCP server now exposes a single `execute_query` tool.

**Files changed:**
- `agent_core/__init__.py` — version 4.0.0, stripped lazy ML imports
- `agent_core/local_config.py` — simplified to api_url + api_key only
- `agent_core/client.py` — NEW: httpx wrapper for v2 backend
- `agent_core/cli/main.py` — rewritten: run, config, login, logout, health, version, serve
- `agent_core/gateway/gateway_server.py` — rewritten: single execute_query MCP tool
- `pyproject.toml` — v4.0.0, 3 deps only, removed all optional extras
- `.github/workflows/build-binaries.yml` — simplified PyInstaller (no ML excludes)
- `.github/workflows/test-and-release.yml` — simplified test install
- `homebrew/Formula/agent-corex.rb` — v4.0.0, updated caveats
- `tests/` — new test suite: test_client.py, test_cli.py, test_gateway.py

---

## 2026-04-10 — Fix: MCP servers added via CLI not recognized at runtime

**What:** CLI-added MCP servers (`agent-corex mcp add <name>`) were stored in `~/.agent-corex/registry.json` but never loaded by the gateway. The gateway only read `~/.agent-corex/mcp.json`, so `get_capabilities` showed them as "available_but_not_installed" and `retrieve_tools`/`execute_tool` couldn't reach them.

**Files changed:**
- `agent_core/tools/mcp/mcp_loader.py` — Added `load_registry_servers()` method to load MCP servers from `registry.json` into MCPManager with cached tool metadata and background discovery for uncached servers
- `agent_core/gateway/gateway_server.py` — Gateway startup now loads registry.json servers after mcp.json, creating MCPManager if needed (registry-only case). Moved `_on_tools_discovered` callback to outer scope for reuse
- `agent_core/gateway/tool_router.py` — `_run_get_capabilities()` now derives "installed" from 3 sources: runtime MCP registry, `registry.json`, and MCPManager configs. Added pending-server hint in `_run_retrieve_tools()` fallback when servers are registered but tools not yet discovered

---

## 2026-04-07 — v2.4.1 — Phase 9 Admin RBAC + Bug Fixes

**What:** Version bump for consistency across Enterprise repos (frontend, backend, and OSS gateway all at 2.4.1+). Fixed missing `/packs/enabled` endpoint in backend, improved Supabase error handling in frontend.

**Files modified:**
- `pyproject.toml` — bumped to 2.4.1
- `agent_core/__init__.py` — bumped `__version__` to 2.4.1
- `agent_core/gateway/gateway_server.py` — bumped `SERVER_VERSION` to 2.4.1
- `homebrew/Formula/agent-corex.rb` — bumped to 2.4.1
- `context/current_state.md` — updated version and last updated date

**Backend changes (enterprise):**
- Added `GET /packs/enabled` endpoint to return user-enabled packs from `user_packs` table
- Improved error handling in AuthContext for `is_admin` column fetch failures

**Frontend changes (next):**
- Added error handling to profile fetch to prevent crashes on Supabase query failures
- Updated PWA manifest `short_name` to "Agent-CoreX" for consistent mobile display

---

## 2026-04-06 — v2.2.0 — User-Aware Tool Retrieval & MCP Recommendation Engine

**What:** Major feature release — tool retrieval is now user-aware and filtering-aware. Added 3 new public tools for better MCP discovery.

**Key features:**
- **User-aware retrieval** — `retrieve_tools` now calls `/v2/retrieve_tools` with user auth header, backend filters to user's installed MCPs only
- **MCP recommendation engine** — new `recommend_mcps` tool suggests servers based on query intent; new `recommend_mcps_from_stack` suggests complementary servers based on tech stack
- **Enhanced get_capabilities** — shows installed vs available MCPs
- **Recommendations on fallback** — when no tools found, automatically includes MCP recommendations in response
- **Enterprise backend filtering** — `EnhancedRetriever` now filters candidates to user's installed servers, returns `recommended_mcps` field

**Files created:**
- `agent_core/gateway/mcp_recommender.py` — local MCP recommendation with `MCP_CATALOG` (20+ servers), keyword-based matching
- `agent_core/gateway/user_mcp_tracker.py` — user MCP state management (local cache + backend sync)
- `packages/tools/user_mcp_service.py` — backend service for fetching user's installed servers from Supabase with Redis caching

**Files modified:**
- `agent_core/gateway/tool_router.py` — added 3 new public tools to `TOOL_REGISTRY`; updated `_run_retrieve_tools()` to use `/v2/retrieve_tools`; added `_run_get_capabilities()`, `_run_recommend_mcps()`, `_run_recommend_mcps_from_stack()`
- `packages/vector/enhanced_retriever.py` — added `installed_servers` parameter; filters candidates to user's MCPs; returns `recommended_mcps` when empty
- `apps/api/routes/v2_retrieval.py` — wires `user_mcp_service` to fetch user's installed servers; passes to retriever

---

## 2026-04-06 — v2.0.1 — MCP Resources and Prompts

**What:** Added MCP resources (static guides) and prompts (workflow suggestions) to help Claude understand and use the 2-tool workflow.

**Resources:**
- `quick-start` — Crisp, token-efficient 2-tool workflow guide (generic for any MCP servers)

**Prompts:**
- `find-tools` — Discover available tools
- `execute-workflow` — Execute tasks step by step

**Files changed:**
- `agent_core/gateway/gateway_server.py` — Added RESOURCES and PROMPTS dicts, handlers for resources/list, resources/read, prompts/list, updated initialize response to advertise capabilities

---

## 2026-04-06 — v2.0.0 — Retrieval-first, token-efficient gateway

**What:** Major breaking change — Claude now sees exactly 2 tools (`retrieve_tools`, `execute_tool`) instead of all 5 static + up to 512 MCP tools. Saves 20k+ tokens per session. All MCP tools are routed internally via a hidden registry.

**Architecture changes:**
- New `agent_core/gateway/capability_provider.py` — derives human-readable capability domains from server names
- `agent_core/gateway/tool_router.py` — split public (`TOOL_REGISTRY`: 2 tools) from internal (`_mcp_registry`, `_ENTERPRISE_TOOLS`); new `_run_execute_tool()` router; `tools_list()` returns only 2 tools with capabilities injected into description
- `agent_core/gateway/gateway_server.py` — removed enterprise auth gate (now inside `_run_execute_tool()`); simplified `_handle_tools_call()`
- `agent_core/api/main.py` — complete rewrite: wired MCPLoader for real MCP pool, added `POST /execute_tool`, added `GET /capabilities`

**Tool output format:** `retrieve_tools` now returns minimal format with capability header: `name — description (inputs: x, y)` instead of `server.name  score%`

**Files changed:**
- `agent_core/gateway/capability_provider.py` — new file
- `agent_core/gateway/tool_router.py` — major refactor
- `agent_core/gateway/gateway_server.py` — minor updates
- `agent_core/api/main.py` — complete rewrite
- `agent_core/__init__.py`, `agent_core/gateway/gateway_server.py`, `pyproject.toml`, `homebrew/Formula/agent-corex.rb` — version bump to 2.0.0

---

## 2026-04-04 — v1.8.1 — retrieve_tools: server prefix + score % in output

**What:** Both the backend and local fallback paths of `retrieve_tools` now show the server name as a prefix (`server.toolname  score%`) and include a `Server: <name>` line per result, so users can see which MCP server each tool belongs to and its relevance score.

**Files changed:**
- `agent_core/gateway/tool_router.py` — backend path: added `_server` lookup for `server.name` prefix and `Server:` line; fallback path: added inline `keyword_score` call to compute and display `score%`, plus same server prefix/line

---

## 2026-04-01 — v1.8.1 — docs: uvx + binary MCP config across all documentation

**What:** Added comprehensive uvx and binary MCP configuration documentation across README, GitHub Pages docs, quickstart, and wiki — covering all three install methods (binary/pip/uvx) for Claude Desktop, Cursor, and VS Code.

**Files changed:**
- `README.md` — Option 4 (uvx install), new "Using Agent-CoreX as an MCP Server" section with binary and uvx JSON config snippets for all supported tools
- `docs/installation.md` — Method 4 (uvx), uv install instructions, per-version pinning, uvx MCP config in "After Installing"
- `docs/mcp-setup.md` — All install methods in Step 1, new "Manual config — uvx" section, `uvx: command not found` troubleshooting entry
- `docs/quickstart.md` — uvx option in Step 1, new "Manual MCP config — uvx" section
- `agent-corex.wiki/MCP-Setup.md` — uvx callout after auto-setup, new "Manual Setup — uvx" section for all tools

---

## 2026-04-01 — v1.8.0 — uvx-native system: pack manager, MCP registry, executor, mcp-config

**What:** Full `uvx agent-corex` support — works as CLI, pack manager, MCP server manager,
task executor, and stdio MCP server when launched by Claude Desktop / Cursor / VS Code.

**New modules (`agent_core/uvx/`):**
- `registry.py` — persistent `~/.agent-corex/registry.json` for installed packs + MCP servers
- `pack_manager.py` — `PackManager`: fetches pack definitions from `GET /packs/<name>`, installs required MCP servers, persists to registry
- `mcp_manager.py` — `MCPManager`: fetches server configs from `GET /mcp_servers/<name>`, persists to registry
- `executor.py` — `Executor`: `execute_task` (retrieve + POST /execute_tool) and `get_tool_plan` (dry-run)

**New CLI commands:**
- `uvx agent-corex pack list / install <name> / remove <name>`
- `uvx agent-corex mcp` — starts stdio MCP gateway (for Claude/Cursor/VSCode)
- `uvx agent-corex mcp list / add <name> / remove <name>`
- `uvx agent-corex execute "<task>"` — auto-selects tool + executes
- `uvx agent-corex plan "<task>"` — dry-run plan with ranked tools
- `uvx agent-corex mcp-config` — prints ready-to-paste MCP JSON for all tools

**Auth improvements:**
- `init --uvx` — injects uvx-based MCP entry with `AGENT_COREX_API_KEY` in the `env` block
- `local_config.get_api_key()` now checks `AGENT_COREX_API_KEY` env var first (benefits gateway usage/query logging)
- Auth error messages across all modules now link to `https://www.agent-corex.com/dashboard/keys`

**Files changed:**
- `agent_core/uvx/` (new directory — 5 files)
- `agent_core/cli/main.py` — ~380 lines added (8 new commands + init --uvx)
- `agent_core/local_config.py` — `get_api_key()` env-var priority
- `agent_core/gateway/auth_middleware.py` — dashboard URL in error messages
- `agent_core/gateway/gateway_server.py` — `SERVER_VERSION = "1.8.0"`
- `agent_core/__init__.py` — `__version__ = "1.8.0"`
- `pyproject.toml` — version 1.8.0 + uvx comment block
- `homebrew/Formula/agent-corex.rb` — version 1.8.0

---

## 2026-03-31 — v1.7.0 — Custom Pack + Custom MCP Server install support

**What:** `install-pack` now detects UUID-format pack IDs and routes them to the new
`/custom/packs/{id}/install` endpoint (auth required). Custom servers are installed via
their stored `install_command + args` and written into `~/.agent-corex/mcp.json`.

**Files changed:**
- `apps/cli/commands/install.py` — UUID detection via regex; `_run_custom_pack()` fetches
  pack from backend with auth headers, installs registry servers as before, installs custom
  servers via stored `install_command + args`. `_write_custom_servers_to_mcp_config()` merges
  custom server definitions into `~/.agent-corex/mcp.json`.
- `agent_core/__init__.py` — `__version__ = "1.7.0"`
- `agent_core/gateway/gateway_server.py` — `SERVER_VERSION = "1.7.0"`
- `pyproject.toml` — version 1.7.0
- `homebrew/Formula/agent-corex.rb` — version 1.7.0

---

## 2026-03-31 — v1.6.0 — Backend-driven Qdrant retrieval, no local ML models

**What:** `retrieve_tools` now calls the enterprise backend's `/retrieve_tools` endpoint
(Qdrant-backed, multi-signal scoring) instead of loading sentence-transformers locally.
Scores logged as nested objects so Query History score bars populate in the dashboard.

**Files changed:**
- `agent_core/gateway/tool_router.py` — `_run_retrieve_tools()` rewritten to HTTP GET
  `{base_url}/retrieve_tools`; logs nested `{score, semantic_score, capability_score,
  success_rate}` per tool via `_fire_and_forget_log()`. Offline fallback to keyword ranker.
  `tools_list()` ranking replaced with lightweight keyword token scoring (no ML model load).
  `retrieve_tools` schema: removed `method` parameter (backend decides ranking strategy).
- `agent_core/__init__.py` — `__version__ = "1.6.0"`
- `agent_core/gateway/gateway_server.py` — `SERVER_VERSION = "1.1.0"`
- `pyproject.toml` — version 1.6.0
- `CLAUDE.md` — created: Claude rules for OSS repo (workflow, version bump files, pitfalls)

---

## 2026-03-31 — v1.5.0 — MCP tool execution captured in enterprise dashboard

**What:** Every `tools/call` through the gateway now fires a POST to `/query/log` on the enterprise backend, so tool executions appear on the dashboard's Queries, Usage, and Overview pages.

**Files changed:**
- `agent_core/gateway/gateway_server.py` — added `_log_query_event()`: fire-and-forget POST to `/query/log` called after every `tools/call` (free tools + enterprise tools, success + failure). Query label: `[tool_name]: arg_hint` (extracts first meaningful argument). Same stdlib-only urllib pattern as `_report_usage()` for PyInstaller binary compatibility.
- `agent_core/__init__.py` — bumped `__version__` to 1.5.0
- `pyproject.toml` — bumped version to 1.5.0

**Dashboard pages now receiving data:**
- `/dashboard/queries` — full query history with tool name + arg hint
- `/dashboard/usage` — 30-day chart (reads from `query_events`)
- `/dashboard` (Overview) — queries-this-month count

---

## 2026-03-30 — v1.4.0 — V2 intelligent retrieval (Qdrant + OpenAI + Supabase)

**What:** Added complete V2 retrieval pipeline — Qdrant Cloud vector DB, OpenAI embeddings (text-embedding-3-small), LLM enrichment (gpt-4o-mini), and per-user tool filtering via Supabase.

**Files changed:**
- `agent_core/__init__.py` — bumped `__version__` to 1.4.0 (**required for binary --version**)
- `packages/vector/__init__.py` — new module init
- `packages/vector/embeddings.py` — OpenAI embeddings with Redis/memory cache
- `packages/vector/llm_enricher.py` — gpt-4o-mini generates summary/tags/examples per tool
- `packages/vector/qdrant_store.py` — Qdrant Cloud client (COSINE collection, batch upsert)
- `packages/vector/indexer.py` — tool enrichment + embedding + upsert pipeline (batch 50)
- `packages/vector/retriever.py` — hybrid scoring (0.7 vector + 0.3 keyword), user_tools filter
- `apps/api/main.py` — /v2/retrieve_tools, /v2/index_tools, /v2/track_installation, /v2/index_loaded_tools
- `scripts/test_v2.py` — integration test
- `pyproject.toml` — v1.4.0, [v2] extras group
- `.github/workflows/build-binaries.yml` — added "Stamp version from tag" step (bug fix: binaries were showing old version)

**Root cause fix:** Binary was showing 1.3.1 because `agent_core/__init__.py.__version__` was never updated. PyInstaller bundles the source at build time — `pyproject.toml` version is irrelevant to the binary. The workflow now stamps `__init__.py` from the git tag as a safety net, and the source file is always updated manually too.

---

## 2026-03-30 — v1.3.1 — packages/mcp_server stdlib stdio protocol server

**What:** Added `packages/mcp_server/` — a minimal stdlib stdio MCP protocol server exposing `retrieve_tools` and `execute_tool` over JSON-RPC 2.0, no external dependencies.

**Files changed:**
- `packages/mcp_server/__init__.py` — package init
- `packages/mcp_server/server.py` — stdio JSON-RPC 2.0 loop
- `packages/mcp_server/protocol.py` — MCP protocol helpers
- `packages/mcp_server/tool_adapter.py` — tool adapter utilities
- `implementation and testing.md` — add Ollama Colab URL note
- `nextFeatures.MD` — formatting + tool ranking / caching / auto-install notes

---

## 2026-03-30 — v1.3.0 — slim deps + skill.md install system

### Dependency cleanup

**What:** Removed 8 unnecessary packages from core install. The CLI gateway/injection/registry/auth use case requires only 3 packages (`typer`, `httpx`, `rich`). Heavy ML and server packages moved to optional extras.

**Removed from core dependencies:**
- `fastapi` — only used by `agent-corex start` → moved to `[server]` extra
- `uvicorn` — only used by `agent-corex start` → moved to `[server]` extra
- `sentence-transformers` — only used by `agent-corex retrieve` → moved to `[ml]` extra
- `faiss-cpu` — only used by `agent-corex retrieve` → moved to `[ml]` extra
- `numpy` — only used by `agent-corex retrieve` → moved to `[ml]` extra
- `pydantic` — not imported anywhere in `agent_core/`
- `requests` — not imported anywhere in `agent_core/`
- `python-dotenv` — not imported; `.env` parsing is done with a custom stdlib parser

**New install matrix:**
| Command | Install |
|---------|---------|
| `pip install agent-corex` | Core only (gateway, init, registry, auth, apply) |
| `pip install "agent-corex[ml]"` | + retrieve command |
| `pip install "agent-corex[server]"` | + start command |
| `pip install "agent-corex[full]"` | Everything |
| `pip install -e .` | Dev (OSS contributors) |

**Files changed:**
- `pyproject.toml` — slimmed `[dependencies]`, added `[ml]`, `[server]`, `[full]` extras
- `requirements.txt` — updated to core deps only with comments for optionals
- `agent_core/cli/main.py` — `retrieve`: catches `ImportError` with install hint; `start`: checks for uvicorn before running with install hint; `config`: shows optional deps with install commands

---

### skill.md install system + `agent-corex apply`

**What:** Declarative, AI-readable install spec system inspired by Smithery, extended for Agent-CoreX packs and MCP orchestration.

**New files:**

**What:** Declarative, AI-readable install spec system inspired by Smithery, extended for Agent-CoreX packs and MCP orchestration.

**New files:**
- `agent_core/skill_parser.py` — Parses YAML front matter + markdown body from skill.md files into a `SkillSpec` dataclass. Works with PyYAML if installed, falls back to a built-in minimal YAML parser (zero extra deps).
- `agent_core/skill_installer.py` — Orchestrates 7-step apply flow: run install command → collect/save env vars → inject MCP servers (pack or single server) → regenerate mcp.json → show test prompt → sync to backend via `POST /user/servers`.
- `examples/vibe_coding.skill.md` — Pack: github + railway + supabase + filesystem + redis
- `examples/deploy_pack.skill.md` — Pack: railway + render, with npm pre-install command
- `examples/custom_server.skill.md` — Single server: postgres via connect block

**Modified files:**
- `agent_core/cli/main.py` — Added `apply` command (before `generate-mcp-config`); updated module docstring

**New CLI command:**
```
agent-corex apply <url_or_file> [--yes]
```

**Backend sync:** Uses existing `POST /user/servers` endpoint — no new backend routes needed.

**To release as v1.3.0:**
1. Bump `agent_core/__init__.py` → `"1.3.0"`
2. Bump `pyproject.toml` → `"1.3.0"`
3. Update `homebrew/Formula/agent-corex.rb` → `version "1.3.0"`
4. Commit + push + `git tag v1.3.0 && git push origin v1.3.0`

---

## 2026-03-29 — v1.2.5 — Fix: non-daemon logging thread in binary

**What:** Changed `daemon=True` → `daemon=False` in `_fire_and_forget_log()` inside `tool_router.py`.

**Root cause:** In the PyInstaller binary, the main thread is blocked indefinitely on `sys.stdin` (MCP stdio loop). Python's OS-level scheduler can terminate daemon threads attached to a blocked main thread before the HTTP POST to `/query/log` completes. Non-daemon threads are not subject to this termination.

**Files Changed:**
- `agent_core/gateway/tool_router.py` line 46 — `daemon=True` → `daemon=False`
- `agent_core/__init__.py` — `__version__` bumped to `"1.2.5"`
- `pyproject.toml` — `version` bumped to `"1.2.5"`
- `homebrew/Formula/agent-corex.rb` — `version` bumped to `"1.2.5"`

**Impact:** Query events now appear in the enterprise dashboard Queries tab when using the installed binary.

---

## 2026-03-29 — v1.2.4 — Query observability: OSS gateway logging

**What:** Added fire-and-forget query logging to the OSS MCP gateway so every `retrieve_tools` call is recorded in the enterprise backend's `query_events` table. Also bumped version to 1.2.4.

**Files Changed:**
- `agent_core/gateway/tool_router.py` — Added `_fire_and_forget_log()` helper + call after `_run_retrieve_tools` returns results
- `agent_core/__init__.py` — `__version__` bumped to `"1.2.4"`
- `pyproject.toml` — `version` bumped to `"1.2.4"`

**Known issue:** `daemon=True` caused thread to be killed in binary context — fixed in v1.2.5.

---

## 2026-03-29 — v1.1.6 — CLI Auth + Sync System

### CLI Authentication + Sync (Device-Code Flow)
**What:** Replaced API-key-only login with browser-based device-code flow (like GitHub CLI / Vercel CLI). Added sync command. Bumped version to 1.1.6.

**Files Changed:**
- `agent_core/local_config.py` — Added JWT session helpers: `save_session()`, `get_access_token()`, `get_refresh_token()`, `try_refresh_token()`, `clear_session()`, `get_auth_header()`, `get_user_email()`. Updated `is_logged_in()` to accept both API key and JWT.
- `agent_core/cli/main.py` — Updated `login` (device-code default + API key via `--key`/`--no-browser`), added `sync` command, updated `status` (sync section), updated `logout` (clears JWT), updated `install-pack` (calls `_notify_backend_pack_installed`).
- `agent_core/__init__.py` — Bumped `__version__` to `"1.1.6"`
- `pyproject.toml` — Bumped `version` to `"1.1.6"`

**New CLI Commands:**
- `agent-corex sync` — Pull enabled packs/servers from backend, install missing, push local state
- `agent-corex sync --push-only` — Only push local state to backend (used internally after install-pack)

**Updated Behavior:**
- `agent-corex login` (no flags) — Opens browser to device-code URL, polls backend for JWT
- `agent-corex login --key acx_xxx` — API key flow (backward compatible, unchanged)
- `agent-corex login --no-browser` — Prompts for API key without browser
- `agent-corex logout` — Now also clears JWT tokens (access_token, refresh_token, expires_at)
- `agent-corex status` — New "Sync Status" section showing installed packs/servers
- `agent-corex install-pack <name>` — Now notifies backend after install (non-fatal)

**config.json Schema Extended:**
```json
{
  "api_key": "acx_...",           // existing — unchanged
  "access_token": "eyJ...",        // NEW — Supabase JWT
  "refresh_token": "...",          // NEW
  "token_expires_at": 1234567890,  // NEW — Unix timestamp
  "user_email": "..."              // NEW
}
```

---

## 2026-03-28 (Enterprise MCP Auth Fixes)

### Fixed Enterprise MCP Authentication
- **Status:** Complete
- **Files changed:**
  - `agent_core/env_manager.py` — Added `SUPABASE_ACCESS_TOKEN` to STANDARD_VARS (Supabase PAT for MCP server, distinct from `SUPABASE_KEY` anon key)
  - `config/mcp_enterprise.json` — New file: template for enterprise MCPs (railway/supabase/github/filesystem) with correct auth config
  - `config/README.md` — Added enterprise template section with setup instructions
- **Root cause fixes:**
  1. **Railway**: `RAILWAY_TOKEN` env var overrides `~/.railway/config.json` OAuth token with an invalid value. Fix: no env injection for railway entry — CLI uses config.json set by `railway login`
  2. **Supabase**: `SUPABASE_KEY` (anon JWT) was passed to `@supabase/mcp-server-supabase` which requires a PAT. Fix: use `SUPABASE_ACCESS_TOKEN` from supabase.com/dashboard/account/tokens

---

## 2026-03-28

### Created Context Folder Structure
- **Status:** Complete documentation setup
- **Files created:**
  - `context/main.md` — Overview and quick start guide
  - `context/repo_map.md` — Architecture and module responsibilities
  - `context/file_index.md` — Complete file reference with functions and line numbers
  - `context/features.md` — Comprehensive CLI command documentation
  - `context/current_state.md` — Status of implementation, what's missing for Vibe Coding
  - `context/change_log.md` — This file
- **Reason:** Document existing CLI structure for future development; prepare for Vibe Coding Experience implementation
- **Impact:** None — documentation only

---

## 2026-03-28

### Implemented 11-Part Vibe Coding Experience — COMPLETE

**Status:** ✅ All parts implemented and integrated

**Summary:**
Complete implementation of seamless Vibe Coding Experience where users can install packs, setup environment variables, and immediately use MCP tools in Claude/Cursor/VS Code.

**Parts Completed:**

**Part 1-2: Pack System & Config Generation**
- **Files created:**
  - `agent_core/pack_manager.py` (200 lines) — Pack installation and tracking
  - `agent_core/mcp_config_generator.py` (150 lines) — Unified config generation
  - `agent_core/env_manager.py` (200 lines) — Environment variable management
- **Files modified:**
  - `agent_core/cli/main.py` — Added install-pack, generate-mcp-config, setup-env commands
  - `agent_core/cli/main.py` line 36-37 — Added PackManager import

**Part 3-4: Gateway & Lazy Loading**
- **Files modified:**
  - `agent_core/gateway/gateway_server.py` lines 130-180 — Enhanced to:
    - Load ~/.agent-corex/mcp.json on startup
    - Inject environment variables from ~/.agent-corex/.env
    - Use lazy_load=True for servers
  - `agent_core/tools/mcp/mcp_loader.py` lines 42-79 — Updated load() to:
    - Support lazy_load parameter (default True)
    - Register server configs without starting
    - Stop servers after listing tools (to save resources)

**Part 5-6: Tool Filtering & API Key Integration**
- **Files modified:**
  - `agent_core/gateway/tool_router.py` lines 143-211 — Enhanced tools_list() to:
    - Accept optional query parameter for context-aware filtering
    - Use hybrid ranking when query provided
    - Track filtering decisions
  - `agent_core/gateway/auth_middleware.py` lines 42-55 — Updated get_stored_api_key() to:
    - Check AGENT_COREX_API_KEY env var first (highest priority)
    - Fall back to ~/.agent-corex/config.json
    - Support CI/CD and containerized environments

**Part 9: Enhanced Doctor Command**
- **Files modified:**
  - `agent_core/cli/main.py` lines 1200-1240 — Added Pack System validation:
    - Check installed packs
    - Verify mcp.json validity
    - Check .env file
    - Provide actionable guidance

**Part 10-11: Documentation & Testing**
- **Files created:**
  - `docs/vibe_coding_local_setup.md` (300 lines) — Complete setup guide with:
    - 5-step quick start
    - Troubleshooting section
    - Example prompts (deploy, database, full-stack)
    - File structure reference
  - `docs/TESTING_CHECKLIST.md` (400 lines) — Comprehensive testing with:
    - 12 major test sections
    - 30+ individual test cases
    - Pre-test setup checklist
    - Pass/fail criteria

**Impact:**
- ✅ No breaking changes to existing commands
- ✅ All existing functionality preserved
- ✅ New commands are opt-in (pack system)
- ✅ Gateway improvements are transparent to users
- ✅ Backward compatible with legacy mcp.json configs

**Data Files Involved:**
- `~/.agent-corex/installed_servers.json` — Track installed packs
- `~/.agent-corex/.env` — Store API keys
- `~/.agent-corex/mcp.json` — Unified server config
- `~/.agent-corex/config.json` — User credentials (existing)

**User Flow:**
```
Install     → agent-corex install-pack vibe_coding_pack
Setup Env   → agent-corex setup-env
Generate    → agent-corex generate-mcp-config
Verify      → agent-corex doctor
Restart     → Restart Claude/Cursor/VS Code
Use Tools   → Available in AI tool's MCP interface
```

**Testing:**
- Manual testing checklist provided
- Fresh machine setup verified
- End-to-end workflows documented
- Error handling tested

**Documentation:**
- Quick start guide (5 steps, ~5 minutes)
- Troubleshooting section
- Example prompts for common tasks
- Testing checklist with 30+ test cases
- Context files updated

**Breaking Changes:** None
**Deprecations:** None
**New Dependencies:** None
**Migration Required:** No

---

**Last Updated:** 2026-03-28
