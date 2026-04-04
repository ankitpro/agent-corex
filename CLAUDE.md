# Agent-CoreX OSS — Claude Rules

Auto-loaded by Claude Code at the start of every session. Keep this file up to date.

---

## Start of Every Session

1. Read `context/current_state.md` — what changed last, current version, active work
2. Read `context/file_index.md` — exact file locations before touching any file
3. Check `context/main.md` for architecture overview if context is unclear

---

## Repo Purpose

The **OSS `agent-corex` CLI** is the installable binary users run locally.
It is the **client** to the enterprise backend (`agent-corex-enterprise`).

Key responsibilities:
- MCP gateway server (`agent-corex serve`) — bridges Claude Desktop / Cursor / VS Code to MCP servers
- Tool retrieval — calls **backend `/retrieve_tools`** for Qdrant-backed semantic search (no local ML)
- Auth management — stores API key in `~/.agent-corex/config.json`
- MCP registry browser, injection into AI tools, diagnostics

The enterprise backend lives at `agent-corex-enterprise/`. Changes to API contracts must be coordinated.

---

## Architecture — Critical Rules

### Retrieval is backend-only, never local ML

`_run_retrieve_tools()` in `agent_core/gateway/tool_router.py` calls the enterprise backend's
`/retrieve_tools` endpoint (Qdrant-backed, multi-signal scoring). It does **not** load
sentence-transformers or any ML model locally. Local ML is only kept as an offline fallback.

`tools_list()` uses lightweight keyword token scoring for protocol-level tool filtering —
no model loading, no network calls. Heavy semantic ranking belongs in `_run_retrieve_tools()`.

### Score logging format — nested objects, not flat floats

`_fire_and_forget_log()` in `tool_router.py` must send scores as nested objects:
```python
scores[tool_name] = {
    "score":            float,   # combined final score
    "semantic_score":   float,   # cosine similarity
    "capability_score": float,   # capability match
    "success_rate":     float,   # historical success rate
}
```
Flat `{tool_name: float}` is the OLD format. The enterprise DB stores JSONB; the frontend
reads nested objects to render score breakdown bars. Never revert to flat floats.

### Network calls are stdlib-only (PyInstaller safe)

All HTTP calls use `urllib.request`, not `httpx` or `requests`. The binary is built with
PyInstaller and cannot bundle heavy dependencies. SSL: try `certifi` bundle first, fall back
to default context.

### Fire-and-forget threads must use `daemon=False`

Background logging threads (`_fire_and_forget_log`, `_report_usage`, `_log_query_event`) must
use `threading.Thread(target=_do, daemon=False)`. `daemon=True` threads are killed by the OS
when the main thread blocks on stdin (MCP stdio loop) — this caused v1.2.4 to silently drop
all query logs.

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

### Versioning scheme (SemVer)

| Bump | When |
|------|------|
| patch `Z` | Bug fix, non-breaking tweak | `1.6.0 → 1.6.1` |
| minor `Y` | New feature, new command, backward-compatible | `1.6.0 → 1.7.0` |
| major `X` | Breaking CLI or config format change | `1.6.0 → 2.0.0` |

### Files to update — ALL required before tagging

| File | What to change |
|------|---------------|
| `agent_core/__init__.py` | `__version__ = "X.Y.Z"` — **this is what `agent-corex --version` reads at runtime** |
| `pyproject.toml` | `version = "X.Y.Z"` under `[project]` — PyPI metadata |
| `agent_core/gateway/gateway_server.py` | `SERVER_VERSION = "X.Y.Z"` — reported in MCP `initialize` response |
| `homebrew/Formula/agent-corex.rb` | `version "X.Y.Z"` — CI also patches this, but keep in sync |
| `context/current_state.md` | Update `**Version:**` line and `**Last Updated**` date |
| `context/change_log.md` | Prepend new entry at top (see format below) |
| `context/main.md` | Update `**Last Updated:**` footer date |

> The `test-and-release.yml` CI workflow stamps `pyproject.toml` from the git tag automatically,
> but **source files must still be updated manually** — the tag is the source of truth,
> the source files must match it.

### Commit, tag, push sequence

```bash
# Stage all version files + context
git add agent_core/__init__.py \
        agent_core/gateway/gateway_server.py \
        pyproject.toml \
        homebrew/Formula/agent-corex.rb \
        context/current_state.md \
        context/change_log.md \
        context/main.md

# Single release commit
git commit -m "release: vX.Y.Z — <one-line description>"

# Push to main
git push origin refs/heads/main:refs/heads/main

# Tag — THIS triggers GitHub Actions (PyPI + binaries + Homebrew tap)
git tag vX.Y.Z
git push origin vX.Y.Z

# Sync prod branch (triggers Render if wired)
git checkout prod
git merge refs/heads/main --no-edit
git push origin refs/heads/prod:refs/heads/prod
git checkout main
```

> **Note on ambiguous refs:** This repo has both a `main` branch and a `main` tag in some
> environments. Always use `refs/heads/main` explicitly in push commands to avoid the
> "matches more than one" error.

### What CI does automatically after the tag

| Workflow | What it does |
|----------|-------------|
| `test-and-release.yml` | pytest on Python 3.9/3.10/3.11, then publishes to PyPI |
| `build-binaries.yml` | PyInstaller binaries for Linux x86_64, macOS arm64, Windows x86_64; attaches to GitHub Release |
| `update-homebrew-tap.yml` | Downloads `.sha256` files, patches Homebrew tap with new version + hashes |

You do **not** need to manually update SHA256 hashes — CI handles it.

### Verify after ~10 minutes

- [ ] GitHub Release at `github.com/ankitpro/agent-corex/releases/tag/vX.Y.Z` has 3 binaries + 3 `.sha256` files
- [ ] `pip install agent-corex==X.Y.Z` works
- [ ] `brew upgrade agent-corex` picks up new version
- [ ] `agent-corex --version` prints `X.Y.Z`

---

## change_log.md Entry Format

```markdown
## YYYY-MM-DD — vX.Y.Z — <title>

**What:** One sentence summary.

**Files changed:**
- `path/to/file.py` — what changed and why
- `path/to/other.py` — what changed and why
```

Always prepend (newest at top). Never edit existing entries.

---

## Deployment Branches

| Branch | Purpose |
|--------|---------|
| `main` | Development — all feature work goes here |
| `prod` | Production — mirrors main after release; triggers Render if wired |

Always push to `main` first, then merge to `prod`.

---

## Key File Locations

| File | Purpose |
|------|---------|
| `agent_core/gateway/tool_router.py` | Tool registry, `_run_retrieve_tools()`, `tools_list()` |
| `agent_core/gateway/gateway_server.py` | MCP stdio server, `_log_query_event()`, `_report_usage()` |
| `agent_core/gateway/auth_middleware.py` | API key validation from `~/.agent-corex/config.json` |
| `agent_core/__init__.py` | `__version__` — read by CLI at runtime |
| `agent_core/local_config.py` | Read/write `~/.agent-corex/config.json` |
| `agent_core/cli/main.py` | All CLI commands (Typer app) |
| `pyproject.toml` | Package metadata, version, dependencies, extras |
| `requirements-binary.txt` | Dependencies bundled in PyInstaller binary |
| `context/` | Living documentation — keep in sync with every change |

---

## Backend Integration Points

The OSS gateway talks to the enterprise backend at `base_url` from `~/.agent-corex/config.json`
(default: `https://www.agent-corex.com`).

| Endpoint | Called from | Purpose |
|----------|-------------|---------|
| `GET /retrieve_tools?query=&top_k=` | `tool_router._run_retrieve_tools()` | Qdrant-backed semantic search |
| `POST /query/log` | `tool_router._fire_and_forget_log()` | Log retrieve_tools queries + scores to DB |
| `POST /query/log` | `gateway_server._log_query_event()` | Log every tool execution to DB |
| `POST /usage/event` | `gateway_server._report_usage()` | Track tool execution for billing |

All backend calls are fire-and-forget daemon=False threads. They must never block or crash tool execution.

---

## Common Pitfalls

- **`daemon=True` drops logs** — always use `daemon=False` for background logging threads
- **flat score format is wrong** — scores must be nested `{score, semantic_score, capability_score, success_rate}`, not flat floats
- **`main` ref is ambiguous** — use `refs/heads/main` in git push commands
- **SERVER_VERSION in gateway_server.py** — easy to forget; bump it with every release
- **homebrew formula** — CI patches it, but also update it manually to keep source in sync
- **context files are mandatory** — always update `current_state.md` and `change_log.md` after every change, not just releases

---

**Last Updated:** 2026-03-31 — v1.6.0

@.agent-memory/CLAUDE.md
