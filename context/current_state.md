# 📍 Current State

Recent changes, active work, and next steps.

---

**Version:** 4.1.0
**Last Updated:** 2026-04-14

## What Changed — v4.1.0 (2026-04-14)

Local MCP server management with hybrid execution model. Free-tier users plan via backend and execute locally; premium users continue to execute on the backend.

## What Changed — v4.0.0 (2026-04-13)

Complete rewrite. The CLI is now a **thin client** — all intelligence lives in the v2 backend at `https://api.v2.agent-corex.com`.

### What was removed
- `agent_core/retrieval/` — local ML ranking (now in backend)
- `agent_core/input_abstraction/` — local input classification (now in backend)
- `agent_core/tools/` — MCP client/manager/loader (now in backend)
- `agent_core/api/` — local FastAPI server (removed entirely)
- `agent_core/detectors/` — AI tool detection
- `agent_core/config_adapters/` — config injection adapters
- `agent_core/uvx/` — uvx executor/manager
- `agent_core/gateway/tool_router.py`, `backend_router.py`, and 5 other gateway files
- JWT/Supabase session management from `local_config.py`
- All optional dependency groups (ml, server, full, v2, redis)

### What was added
- `agent_core/client.py` — new httpx wrapper for v2 backend (single source of truth)

### What was rewritten
- `agent_core/cli/main.py` — 200 lines, 9 commands: `run`, `config set/show`, `login`, `logout`, `health`, `version`, `serve`
- `agent_core/gateway/gateway_server.py` — 120 lines, single `execute_query` MCP tool
- `agent_core/local_config.py` — 90 lines, api_url + api_key only
- `pyproject.toml` — v4.0.0, 3 deps only (typer, httpx, rich)

## Active Work

v4.1.0 implementation complete. Waiting for CI to confirm Python 3.9/3.10/3.11 matrix passes.

## Next Steps

1. Tag `v4.1.0` to trigger CI (PyPI + binaries + Homebrew)
2. Apply backend changes (B1–B7 in plan) to `agent-corex-backend-2`
3. Verify `agent-corex mcp add railway` writes `~/.agent-corex/mcp.json` and syncs backend
4. Verify `agent-corex run "list my railway projects"` spawns local subprocess and executes locally

## Known Issues

None at time of writing.
