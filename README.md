# Agent-CoreX

🚀 **Production-ready MCP tool retrieval engine + CLI for AI agents**

Agent-CoreX solves a critical problem in LLM systems:

> When you have hundreds of tools, how do you select the *right few* without blowing up the context window?

---

<a href="https://www.producthunt.com/products/agent-corex-intelligent-tool-selection" target="_blank" rel="noopener noreferrer">
  <img src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=1103833&theme=light" alt="Agent-Corex on Product Hunt" width="250" height="54" />
</a>

**Quick links:** [PyPI](https://pypi.org/project/agent-corex/) · [Docs](https://ankitpro.github.io/agent-corex/) · [Releases](https://github.com/ankitpro/agent-corex/releases/latest) · [GitHub](https://github.com/ankitpro/agent-corex)

---

## Install

### Option 1 — Homebrew (macOS / Linux, no Python required)

```bash
brew tap ankitpro/agent-corex
brew install agent-corex
```

### Option 2 — Direct binary download (no Python required)

```bash
# macOS (arm64 — M1/M2/M3 and Intel via Rosetta 2)
curl -fsSL https://github.com/ankitpro/agent-corex/releases/latest/download/agent-corex-macos-arm64 \
  -o /usr/local/bin/agent-corex && chmod +x /usr/local/bin/agent-corex

# Linux x86_64
curl -fsSL https://github.com/ankitpro/agent-corex/releases/latest/download/agent-corex-linux-x86_64 \
  -o /usr/local/bin/agent-corex && chmod +x /usr/local/bin/agent-corex
```

**Windows** — run PowerShell **as Administrator**:

```powershell
# Installs to System32 — works from any terminal after this
Invoke-WebRequest `
  -Uri https://github.com/ankitpro/agent-corex/releases/latest/download/agent-corex-windows-x86_64.exe `
  -OutFile "$env:SystemRoot\System32\agent-corex.exe"
agent-corex --version
```

No admin access? See the [per-user install →](https://ankitpro.github.io/agent-corex/installation/#per-user-install-no-admin-required)

### Option 3 — pip (Python 3.8+)

```bash
pip install agent-corex
```

> All three methods give you the same `agent-corex` CLI. Homebrew and the binary downloads require no Python installation.

---

## Quick Start

```bash
# 1. Log in — opens your browser automatically, saves credentials locally
agent-corex login

# 2. Detect installed AI tools (Claude Desktop, Cursor, VS Code, etc.)
agent-corex detect

# 3. Inject agent-corex as an MCP server into all detected tools
agent-corex init

# 4. Verify everything is working
agent-corex status

# Run diagnostics if anything looks wrong
agent-corex doctor
```

---

## Authentication

Agent-CoreX uses a **browser-based login flow** (like GitHub CLI or Vercel CLI) — no manual key copying required.

### Login (recommended)

```bash
agent-corex login
```

What happens:
1. A unique verification URL is generated and printed in the terminal
2. Your browser opens automatically to `https://agent-corex.com/cli-auth?code=...`
3. You log in with your Agent-CoreX account (email, Google, or GitHub)
4. The CLI detects the completed login and saves your session locally
5. Done — credentials are stored in `~/.agent-corex/config.json`

```
$ agent-corex login

Logging in to Agent-CoreX...

Open this URL to complete login:

  https://agent-corex.com/cli-auth?code=a1b2c3d4-...

(Opened in your browser automatically)

Waiting for authentication.......

✓ Logged in successfully!
  User: you@example.com
  Session saved to ~/.agent-corex/config.json

You can now run:
  agent-corex sync
  agent-corex status
```

### Login with API key (alternative)

If you prefer to use an API key directly:

```bash
# Paste your key (from the dashboard → API Keys)
agent-corex login --key acx_your_key_here

# Or: open the dashboard in browser, then prompt for key
agent-corex login --no-browser
```

### Sync with dashboard

After logging in, sync your locally installed packs and servers with your Agent-CoreX dashboard:

```bash
agent-corex sync
```

What sync does:
1. **Pulls** packs/servers you enabled in the dashboard → installs any missing locally
2. **Pushes** your local install state → dashboard shows what's installed

```bash
agent-corex sync --push-only   # only push local state, skip pull/install
```

### Logout

```bash
agent-corex logout
```

Clears all credentials (session tokens + API key) from `~/.agent-corex/config.json`.

---

## CLI Reference

### Setup & Auth

| Command | Description |
|---------|-------------|
| `agent-corex login` | **Log in via browser** — opens browser, saves session automatically |
| `agent-corex login --key <key>` | Log in with an API key directly |
| `agent-corex login --no-browser` | Prompt for API key without opening browser |
| `agent-corex logout` | Remove all stored credentials |
| `agent-corex sync` | Sync installed packs/servers with dashboard |
| `agent-corex sync --push-only` | Push local state to dashboard only |
| `agent-corex keys` | Show masked API key + live backend verification |

### Tool Detection & Injection

| Command | Description |
|---------|-------------|
| `agent-corex detect` | Detect installed AI tools and show config paths |
| `agent-corex init [--yes]` | Inject agent-corex MCP entry into all detected tools |
| `agent-corex eject [--tool <t>] [--yes]` | Remove agent-corex from tool configs |
| `agent-corex status` | Auth state, sync status, backend ping, injection status per tool |

### MCP Server Management

| Command | Description |
|---------|-------------|
| `agent-corex list` | List all MCP servers injected across detected tools |
| `agent-corex registry` | Browse the installable MCP server catalog |
| `agent-corex install-mcp <name> [--yes]` | Install any registry server into detected tools |
| `agent-corex install-pack <name> [--yes]` | Install a curated pack of MCP servers |
| `agent-corex update [--yes]` | Re-fetch registry and update injected server configs |

### Diagnostics

| Command | Description |
|---------|-------------|
| `agent-corex doctor` | Full health check: Python, PATH, config, backend, API key, injection |
| `agent-corex health` | Quick backend health check |
| `agent-corex version` | Print installed version |

### Gateway

| Command | Description |
|---------|-------------|
| `agent-corex serve` | Start the MCP gateway server (stdio — invoked by AI tools) |

### Tool Retrieval

| Command | Description |
|---------|-------------|
| `agent-corex retrieve "<query>"` | Semantic search for relevant tools |

---

## Supported AI Tools

| Tool | Platform |
|------|----------|
| Claude Desktop | macOS, Windows |
| Cursor | macOS, Windows, Linux |
| VS Code | macOS, Windows, Linux |
| VS Code Insiders | macOS, Windows, Linux |
| VSCodium | macOS, Windows, Linux |

---

## How It Works

```
Your AI tool (Claude / Cursor / VS Code)
         │  stdio
         ▼
  agent-corex serve        ← MCP gateway (single entry point)
         │
         ├─ retrieve_tools(query) → semantic search over all tools
         ├─ execute_tool(name, args) → routes call to correct MCP server
         └─ auth_check → validates Enterprise API key
```

The gateway exposes a small, fixed set of tools to Claude/Cursor instead of hundreds.
This cuts context tokens by ~60% and keeps the LLM focused.

---

## MCP Marketplace

Browse and install any MCP server with one command:

```bash
agent-corex registry              # browse catalog
agent-corex install-mcp github    # install GitHub MCP server
agent-corex install-mcp postgres  # install Postgres MCP server
agent-corex list                  # see all currently installed servers
agent-corex update                # pull latest configs from registry
```

---

## Tool Retrieval (Python API)

```python
from agent_core.retrieval.ranker import rank_tools

tools = rank_tools("edit a file", all_tools, top_k=5, method="hybrid")
# Returns: ["edit_file", "write_file", "create_file", ...]
```

Three ranking methods:
- `keyword` — fast exact-match, no model required
- `embedding` — semantic similarity via `sentence-transformers`
- `hybrid` (**recommended**) — 30% keyword + 70% semantic

---

## Releases & CI/CD

Every tag push triggers:

| Workflow | What it does |
|----------|-------------|
| `build-binaries.yml` | PyInstaller binaries for Linux x86_64, macOS arm64, Windows x86_64 + SHA256 sidecars |
| `publish.yml` | Publishes to PyPI |
| `update-homebrew-tap.yml` | Auto-patches the Homebrew formula with new version + SHA256s |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

```bash
git clone https://github.com/ankitpro/agent-corex
cd agent-corex
pip install -e ".[dev]"
pytest
```
