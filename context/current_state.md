# 📍 Current State

Recent changes, active work, and next steps.

---

## Last Updated
**2026-03-30** — skill.md install system + `agent-corex apply` command (unreleased, pending v1.3.0)

---

## Current Status

**Version:** 1.2.9 (PyPI/binary) — next release will be **v1.3.0**

**Unreleased (on `main`, not yet tagged):**
- ✅ `agent_core/skill_parser.py` — parse skill.md YAML front matter + markdown body
- ✅ `agent_core/skill_installer.py` — 7-step apply flow (install → env → MCP inject → mcp.json → test → backend sync)
- ✅ `agent-corex apply <url_or_file> [--yes]` CLI command
- ✅ `examples/vibe_coding.skill.md`, `deploy_pack.skill.md`, `custom_server.skill.md`
- ✅ **Slim dependencies** — removed `fastapi`, `uvicorn`, `sentence-transformers`, `faiss-cpu`, `numpy`, `pydantic`, `requests`, `python-dotenv` from core install
  - Core: `typer[all]`, `httpx`, `rich` only (~10MB install vs ~2GB previously)
  - `[ml]` extra: sentence-transformers + faiss-cpu + numpy (for `retrieve` cmd)
  - `[server]` extra: fastapi + uvicorn (for `start` cmd)
  - `[full]` extra: everything
- Backend sync uses existing `POST /user/servers` endpoint (no new backend routes needed)
- To release: bump `__init__.py` + `pyproject.toml` to `1.3.0`, tag `v1.3.0`

---

**v1.2.9 State:** ✅ **COMPLETE** — CLI gateway usage reporting added:
- ✅ `_report_usage()` helper in `gateway_server.py` — POSTs to `/usage/event` in a daemon thread after every `tools/call` (success or failure)
- ✅ Auth header read from `local_config.get_auth_header()` (JWT or API key)
- ✅ Non-blocking — daemon thread, errors silently swallowed, never affects tool execution

**Previous (v1.2.5):** Query observability logging fixed:
- ✅ `_fire_and_forget_log` in `tool_router.py` now uses `daemon=False` so the HTTP POST to `/query/log` completes even when the main thread is blocked on stdin (MCP stdio loop)
- ✅ Binary build triggered via `v1.2.5` tag

**Previous (v1.2.4):** Query observability (OSS gateway logging)
- ✅ Added `_fire_and_forget_log()` to `agent_core/gateway/tool_router.py` — logs each `retrieve_tools` call to the enterprise backend's `/query/log` endpoint in a background thread
- ✅ `__version__` bumped to 1.2.4; binary released as `v1.2.4`
- ⚠️ Known bug: `daemon=True` threads killed by OS in binary context — fixed in v1.2.5

**Previous (v1.1.6):** CLI Auth + Sync System added:
- ✅ Device-code browser login (`agent-corex login`)
- ✅ JWT session stored in `~/.agent-corex/config.json`
- ✅ Token auto-refresh on expiry
- ✅ `agent-corex sync` — bidirectional pack/server sync with backend
- ✅ `agent-corex status` — shows sync state
- ✅ `agent-corex logout` — clears JWT + API key
- ✅ `agent-corex install-pack` — notifies backend after install
- ✅ Backward compatible — API key auth still works

**Previous (v1.1.5):** Vibe Coding Extensions

**State:** ✅ **COMPLETE** — Fully functional Vibe Coding Experience with:
- ✅ Pack system (install-pack, installed_servers.json)
- ✅ Unified MPC config generation (generate-mcp-config)
- ✅ Gateway auto-load with env injection (gateway_server.py)
- ✅ Lazy server startup (mcp_manager.py, mcp_loader.py)
- ✅ Context-aware tool filtering (tool_router.py)
- ✅ AGENT_COREX_API_KEY env variable support
- ✅ Enhanced doctor command with pack validation
- ✅ Comprehensive setup documentation
- ✅ Complete testing checklist

---

## What Works ✅

### Core Retrieval
- ✅ `agent-corex retrieve` — Semantic search for tools
- ✅ `agent-corex start` — FastAPI retrieval API server
- ✅ Tool ranking (keyword, embedding, hybrid methods)

### Gateway & Injection
- ✅ `agent-corex serve` — MCP gateway (stdio mode)
- ✅ `agent-corex init` — Inject into Claude Desktop, Cursor, VS Code (5 variants)
- ✅ `agent-corex eject` — Remove from tools
- ✅ `agent-corex list` — Show injected servers
- ✅ `agent-corex detect` — Discover AI tools

### Authentication
- ✅ `agent-corex login` — Store API key
- ✅ `agent-corex logout` — Remove credentials
- ✅ `agent-corex keys` — Show masked key + verify
- ✅ `agent-corex set-url` — Configure backend/frontend URLs

### Registry & Installation
- ✅ `agent-corex registry` — Browse MCP servers
- ✅ `agent-corex install-mcp` — Install server into tools
- ✅ `agent-corex update` — Re-sync all servers

### Configuration & Diagnostics
- ✅ `agent-corex config` — Show dependencies
- ✅ `agent-corex health` — Check backend
- ✅ `agent-corex status` — Show auth + injection + tools
- ✅ `agent-corex doctor` — Comprehensive health check

---

## What's Missing for Vibe Coding ❌

### Part 1: Pack System
- ❌ `agent-corex install-pack <pack>` — Install curated tool bundles
- ❌ `~/.agent-corex/installed_servers.json` — Track installed servers per pack
- ❌ Server metadata (capabilities, tags, enabled state)

### Part 2: Unified MCP Config Generation
- ❌ `agent-corex generate-mcp-config` — Generate ~/.agent-corex/mcp.json
- ❌ Read env from ~/.agent-corex/.env
- ❌ Inject env variables into server definitions

### Part 3: MCP Gateway Auto-Load
- ❌ gateway_server.py load ~/.agent-corex/mcp.json on startup
- ❌ Register tool metadata without starting servers yet

### Part 4: Lazy Server Startup
- ❌ mcp_manager.py start servers on-demand (when first tool from that server is used)
- ❌ Server status tracking + restart on failure

### Part 5: Tool Discovery / Filtering
- ❌ MCP gateway `/retrieve_tools` endpoint (use internal tool indexer)
- ❌ Intelligent tool filtering based on context/query

### Part 6: API Key Integration
- ❌ Support `AGENT_COREX_API_KEY` environment variable
- ❌ Include Authorization header in all backend calls

### Part 7: Automatic Tool Execution Flow
- ❌ Full flow: Claude → MCP → Agent-Corex backend → MCP server

### Part 8: Zero-Config UX
- ❌ `agent-corex setup-env` — Guided env variable setup
- ❌ Simplified install flow (setup-env → install-pack → generate-config → serve)

### Part 9: Validation Command
- ❌ Extend `doctor` with pack validation
- ❌ Check env variables, MCP config validity, server installability

### Part 10: Documentation
- ❌ `docs/vibe_coding_local_setup.md` — Step-by-step guide
- ❌ Test prompts and examples

### Part 11: Testing
- ❌ Test full vibe coding flow end-to-end

---

## Architecture Readiness

### ✅ Ready to Extend
- `local_config.py` — Can store installed_servers.json easily
- `cli/main.py` — Structure ready for new commands
- `gateway/tool_router.py` — Can be extended with filtering logic
- `detectors/` + `config_adapters/` — Stable, no changes needed
- `tools/mcp/mcp_manager.py` — Can be extended with lazy startup

### ⚠️ Needs Updates
- **mcp_loader.py** — Currently loads all servers eagerly; needs lazy init
- **gateway_server.py** — No env injection; needs to read mcp.json
- **tool_router.py** — No filtering; needs query context support

### 🔧 Needs New
- New file: `pack_manager.py` — Pack installation + registry
- New file: `env_manager.py` — Environment variable setup
- New endpoint: `POST /setup-env` (internal use by CLI)
- New endpoint: `GET /capabilities` (map tools to capabilities)

---

## Next Implementation Steps

### Phase 1: Pack System (Parts 1-2)
1. Create `pack_manager.py` — Install pack, track servers
2. Add `install-pack` command to CLI
3. Add `generate-mcp-config` command
4. Create `~/.agent-corex/installed_servers.json` format

### Phase 2: Gateway Improvements (Parts 3-5)
5. Update `mcp_loader.py` for lazy initialization
6. Update `gateway_server.py` to read mcp.json + inject env
7. Add filtering to `tool_router.py`

### Phase 3: Setup Flow (Parts 6-8)
8. Create `env_manager.py` for setup-env command
9. Add `AGENT_COREX_API_KEY` support
10. Create `setup-env` command

### Phase 4: Validation & Docs (Parts 9-10)
11. Extend `doctor` command with pack validation
12. Create `docs/vibe_coding_local_setup.md`
13. Create test prompts

### Phase 5: Testing (Part 11)
14. End-to-end integration tests
15. Fresh machine test

---

## Known Issues / Risks

### ⚠️ Server Startup Performance
- All MCP servers started eagerly in gateway
- Large packs (10+ servers) = slow startup time
- **Fix:** Implement lazy server startup (Part 4)

### ⚠️ Environment Variable Handling
- Currently manually set in shell or config file
- No guided setup flow
- **Fix:** Add `setup-env` command (Part 8)

### ⚠️ Tool Filtering
- No intelligent filtering in `tools/list`
- Returns all tools regardless of query context
- **Fix:** Implement /retrieve_tools filtering (Part 5)

### ⚠️ Error Messages
- `doctor` command is good but could be more actionable
- Some failures cascade without clear recovery steps
- **Fix:** Add inline recovery suggestions

---

## Dependencies

**Runtime:**
- Python 3.8+
- typer (CLI framework)
- fastapi + uvicorn (API server)
- httpx (HTTP client)
- sentence-transformers (embeddings)
- faiss-cpu (vector search)
- pydantic (validation)
- python-dotenv (env file support)
- rich (terminal formatting)

**Development:**
- pytest (testing)
- black (formatting)
- mypy (type checking)
- ruff (linting)

---

## Configuration Format

### ~/.agent-corex/config.json
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

### ~/.agent-corex/.env (to be created)
```
RAILWAY_API_KEY=...
GITHUB_TOKEN=...
SUPABASE_URL=...
SUPABASE_KEY=...
```

### ~/.agent-corex/installed_servers.json (to be created)
```json
{
  "vibe_coding_pack": [
    "railway",
    "github",
    "supabase",
    "filesystem",
    "redis"
  ],
  "enabled": {
    "railway": true,
    "github": true,
    "supabase": false
  }
}
```

### ~/.agent-corex/mcp.json (to be created)
```json
{
  "mcpServers": {
    "railway": {
      "command": "npx",
      "args": ["-y", "railway-mcp-server"],
      "env": {
        "RAILWAY_API_KEY": "..."
      }
    }
  }
}
```

---

## Deployment Pipeline

**Development:** `python -m agent_core.cli.main --help`
**Local install:** `pip install -e .`
**Production:** `pip install agent-corex` from PyPI

No changes needed to deployment — new features add commands, don't break existing ones.

---

## Context Files Status

- ✅ `main.md` — Up to date
- ✅ `repo_map.md` — Up to date
- ✅ `file_index.md` — Up to date
- ✅ `features.md` — Comprehensive
- ✅ `current_state.md` — This file
- 📝 `change_log.md` — To be populated

---

**Last Updated:** 2026-03-28
**Next Review:** After Part 1 implementation
