# 📍 Current State

Recent changes, active work, and next steps.

---

**Version:** 4.0.0
**Last Updated:** 2026-04-13

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

None — rewrite complete.

## Next Steps

1. Tag `v4.0.0` to trigger CI (PyPI + binaries + Homebrew)
2. Verify `pip install agent-corex==4.0.0` works
3. Verify `uvx agent-corex run "..."` works
4. Verify `brew upgrade agent-corex` picks up new formula

## Known Issues

None at time of writing.
