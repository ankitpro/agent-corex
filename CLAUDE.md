# Agent-CoreX OSS — Claude Rules

Auto-loaded by Claude Code at the start of every session. Keep this file up to date.

---

## Start of Every Session

1. Read `context/current_state.md` — what changed last, current version, active work
2. Read `context/file_index.md` — exact file locations and line ranges before touching any file
3. Check `context/main.md` for architecture overview if context is unclear

---

## Repo Purpose

The **OSS `agent-corex` CLI** is a thin client for the Agent-CoreX v2 backend.

Key responsibilities:
- `agent-corex run "<query>"` — send query to backend, display structured response
- `agent-corex serve` — MCP stdio server for Claude Desktop / Cursor / VS Code
- Config management — store API key and backend URL in `~/.agent-corex/config.json`

All intelligence lives in the backend (`agent-corex-backend-2`). The CLI is intentionally minimal.

---

## Architecture — Critical Rules

### The CLI does NOT contain intelligence

`agent_core/client.py` is the sole HTTP layer. It calls `POST /execute/query` and returns the response verbatim. The CLI formats and displays it. That's all.

Never add:
- Local tool retrieval or ranking
- Local input extraction or classification
- Local MCP server management

### Config schema is minimal

`~/.agent-corex/config.json` contains only:
```json
{"api_url": "...", "api_key": "acx_..."}
```

No JWT tokens, no Supabase refresh, no session state.

### MCP server exposes exactly 1 tool

`gateway_server.py` must always return exactly `["execute_query"]` from `tools/list`. Never add more tools — the backend handles everything.

### Network calls use httpx (not urllib)

`agent_core/client.py` uses `httpx` (sync). This is safe — httpx is a hard dependency and is bundled in the PyInstaller binary.

---

## Mandatory Workflow — Code Changes

**Every time you modify code:**

1. Read the relevant file(s) first
2. Check `context/file_index.md` for line ranges of functions you're touching
3. Make the source code change
4. Update context files:
   - `context/file_index.md` — if line numbers, function signatures, or files changed
   - `context/current_state.md` — describe what changed and why
   - `context/change_log.md` — prepend a new dated entry (see format below)
   - `context/main.md` — only if architecture changed

---

## Release Process — Every Version Bump

### Files to update — ALL required before tagging

| File | What to change |
|------|---------------|
| `agent_core/__init__.py` | `__version__ = "X.Y.Z"` |
| `pyproject.toml` | `version = "X.Y.Z"` under `[project]` |
| `agent_core/gateway/gateway_server.py` | `SERVER_VERSION` is imported from `__version__` — no manual change needed |
| `homebrew/Formula/agent-corex.rb` | `version "X.Y.Z"` — CI also patches this |
| `context/current_state.md` | Update `**Version:**` and `**Last Updated**` |
| `context/change_log.md` | Prepend new entry at top |
| `context/main.md` | Update `**Last Updated:**` footer |

### Commit, tag, push

```bash
git add agent_core/__init__.py pyproject.toml homebrew/Formula/agent-corex.rb \
        context/current_state.md context/change_log.md context/main.md

git commit -m "release: vX.Y.Z — <one-line description>"
git push origin refs/heads/main:refs/heads/main

git tag vX.Y.Z
git push origin vX.Y.Z

git checkout prod
git merge refs/heads/main --no-edit
git push origin refs/heads/prod:refs/heads/prod
git checkout main
```

### What CI does automatically after the tag

| Workflow | What it does |
|----------|-------------|
| `test-and-release.yml` | pytest on Python 3.9/3.10/3.11, then publishes to PyPI |
| `build-binaries.yml` | PyInstaller binaries (Linux/macOS/Windows), attaches to GitHub Release |
| `update-homebrew-tap.yml` | Downloads `.sha256` files, patches Homebrew tap formula |

---

## change_log.md Entry Format

```markdown
## YYYY-MM-DD — vX.Y.Z — <title>

**What:** One sentence summary.

**Files changed:**
- `path/to/file.py` — what changed and why
```

Always prepend (newest at top). Never edit existing entries.

---

## Common Pitfalls

- **`main` ref is ambiguous** — use `refs/heads/main` in git push commands
- **`SERVER_VERSION` in gateway_server.py** — imported from `__init__.__version__`, no manual bump needed
- **Homebrew formula** — CI patches it, but also update manually to keep in sync
- **context files are mandatory** — always update after every change

---

## Key File Locations

| File | Purpose |
|------|---------|
| `agent_core/cli/main.py` | All CLI commands |
| `agent_core/gateway/gateway_server.py` | MCP stdio server |
| `agent_core/client.py` | httpx backend wrapper |
| `agent_core/local_config.py` | `~/.agent-corex/config.json` |
| `agent_core/__init__.py` | `__version__` |
| `pyproject.toml` | Package metadata |
| `context/` | Living documentation |

---

**Last Updated:** 2026-04-13 — v4.0.0
