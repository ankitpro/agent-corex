# Release Notes

## v1.1.7 (March 29, 2026)

### 📖 Documentation
- **README**: Full documentation for browser-based login flow with terminal output example
- **README**: New dedicated "Authentication" section explaining device-code login, API key fallback, sync, and logout
- **README**: Updated Quick Start — `agent-corex login` (no `--key` required)
- **README**: Updated CLI Reference table with `sync`, `sync --push-only`, and all login variants

### 📦 Installation
```bash
pip install agent-corex==1.1.7        # PyPI
brew install ankitpro/agent-corex/agent-corex  # Homebrew
```

Windows: download `agent-corex-windows-x86_64.exe` from the [releases page](https://github.com/ankitpro/agent-corex/releases/tag/v1.1.7)

---

## v1.1.6 (March 29, 2026)

### ✨ New Features

#### 🔐 Browser-Based CLI Login (Device Code Flow)
`agent-corex login` now opens your browser and authenticates automatically — no more manually copying API keys.

```bash
agent-corex login               # opens browser, polls until complete
agent-corex login --key acx_xxx # API key flow (unchanged)
agent-corex login --no-browser  # prompt for key without browser
```

#### 🔄 Sync Command
New `agent-corex sync` keeps your local CLI in sync with your Agent-CoreX dashboard:

```bash
agent-corex sync            # pull enabled packs/servers → install missing → push local state
agent-corex sync --push-only    # only push local state to backend
```

#### 📊 Enhanced Status
`agent-corex status` now includes a Sync Status section showing installed packs, servers, and connection state.

### 🔧 Updated Behavior
- **`logout`** — now clears JWT session tokens (access_token, refresh_token)
- **`install-pack`** — automatically notifies backend after installation so your dashboard stays in sync
- **`config.json`** — extended to store JWT session alongside API key (backward compatible)

### 📦 Installation
```bash
pip install agent-corex==1.1.6        # PyPI
brew install ankitpro/agent-corex/agent-corex  # Homebrew
```

Windows: download `agent-corex-windows-x86_64.exe` from the [releases page](https://github.com/ankitpro/agent-corex/releases/tag/v1.1.6)

---

## v1.1.5 (March 28, 2026)

### 🔧 Fixes
- **`install-pack` SyntaxError on Windows**: fixed misplaced `from __future__ import annotations` in `config_adapters/claude.py`, `config_adapters/cursor.py` (was appended at end-of-file), and `detectors/base.py` (was injected inside class docstring) — all now correctly placed after module docstring

### 📦 Installation
```bash
pip install agent-corex==1.1.5        # PyPI
brew install ankitpro/agent-corex/agent-corex  # Homebrew
```

Windows: download `agent-corex-windows-x86_64.exe` from the [releases page](https://github.com/ankitpro/agent-corex/releases/tag/v1.1.5)

---

## v1.1.4 (March 28, 2026)

### 🔧 Fixes
- **Railway MCP auth**: switched from `railway-mcp` to official `@railway/mcp-server`; removed `RAILWAY_TOKEN` env injection that was overriding OAuth auth from `railway login`
- **Supabase MCP auth**: `@supabase/mcp-server-supabase` now uses `SUPABASE_ACCESS_TOKEN` (Personal Access Token) instead of `SUPABASE_KEY` (anon key)
- **GitHub MCP env**: added `GITHUB_PERSONAL_ACCESS_TOKEN` mapping so `install-pack` correctly wires `GITHUB_TOKEN` to the expected env var
- **install-pack**: server-specific `env` fields now included when injecting into AI tools (Claude Desktop, VS Code, Cursor)

### ✨ New
- `SUPABASE_ACCESS_TOKEN` added to `setup-env` prompt
- `config/mcp_enterprise.json` — enterprise MCP template (railway/supabase/github/filesystem)
- `.pre-commit-config.yaml` — enforces black formatting for all contributors on every commit

### 📦 Installation
```bash
pip install agent-corex==1.1.4        # PyPI
brew install ankitpro/agent-corex/agent-corex  # Homebrew
```

Windows: download `agent-corex-windows-x86_64.exe` from the [releases page](https://github.com/ankitpro/agent-corex/releases/tag/v1.1.4)

---

## 1.1.3 (March 27, 2026)

### ✨ New Features
- **Lazy MCP Server Loading**: MCP servers now only start when their tools are needed, reducing startup time by ~85% (8.2s → 1.2s) and memory usage by ~50% (450MB → 220MB)
- **Health Check & Auto-Restart**: Automatic health checking with server restart capability for improved reliability
- **Pack Installation via CLI**: Full support for MCP capability packs through CLI commands (improved from 1.1.2)

### 🔧 Improvements
- Optimized server lifecycle management
- Enhanced CLI with pack installation support
- Better resource utilization with lazy loading

### 📦 Downloads
- **Linux x86_64**: `agent-corex-linux-x86_64`
- **macOS arm64 (Intel via Rosetta 2)**: `agent-corex-macos-arm64`
- **Windows x86_64**: `agent-corex-windows-x86_64.exe`

No Python required — standalone binaries included.

### 🐍 Python Package
```bash
pip install agent-corex==1.1.3
```

### 🍺 Homebrew (macOS)
```bash
brew install ankitpro/agent-corex/agent-corex
```

### Installation Options
1. **Binary**: Download from [releases page](https://github.com/ankitpro/agent-corex/releases/tag/v1.1.3)
2. **PyPI**: `pip install agent-corex`
3. **Homebrew**: `brew install ankitpro/agent-corex/agent-corex`
4. **Source**: `pip install git+https://github.com/ankitpro/agent-corex.git`

---

## 1.1.2 (Previous Release)

### Features
- CLI pack support with intelligent filtering
- MCP environment variable injection
- Observability improvements
- Tool discovery enhancements

---

## Upgrading

### From 1.1.2 to 1.1.3
Simply run:
```bash
pip install --upgrade agent-corex
```

Or if using Homebrew:
```bash
brew upgrade ankitpro/agent-corex/agent-corex
```

### Key Benefits
- **Faster Startup**: 85% faster application initialization
- **Lower Memory**: 50% less memory usage
- **Better Reliability**: Automatic server health checks
- **Pack Support**: Install and use MCP capability packs via CLI

---

## Changelog

### All Changes Since 1.1.2
- Implement lazy MCP server loading
- Add health check with auto-restart
- Improve server lifecycle management
- Enhance CLI with better pack installation support
- Optimize resource allocation
- Update documentation

---

## Known Issues
None reported for this release.

## Support
- **GitHub Issues**: https://github.com/ankitpro/agent-corex/issues
- **Discussions**: https://github.com/ankitpro/agent-corex/discussions
- **Author**: Ankit Agarwal (@ankitpro)

---

**Thank you for using Agent-Corex! 🚀**
