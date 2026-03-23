---
layout: page
title: Quick Start Guide
description: Get Agent-Corex running in 5 minutes
permalink: /quickstart/
---

# Quick Start (5 Minutes)

---

## Step 1 — Install

Pick any one method:

**Homebrew** (macOS / Linux — no Python required):
```bash
brew tap ankitpro/agent-corex
brew install agent-corex
```

**Direct binary** (macOS arm64):
```bash
curl -fsSL https://github.com/ankitpro/agent-corex/releases/latest/download/agent-corex-macos-arm64 \
  -o /usr/local/bin/agent-corex && chmod +x /usr/local/bin/agent-corex
```

**Direct binary** (Linux x86_64):
```bash
curl -fsSL https://github.com/ankitpro/agent-corex/releases/latest/download/agent-corex-linux-x86_64 \
  -o /usr/local/bin/agent-corex && chmod +x /usr/local/bin/agent-corex
```

**Windows** — [download agent-corex-windows-x86_64.exe](https://github.com/ankitpro/agent-corex/releases/latest/download/agent-corex-windows-x86_64.exe) and run it, or via PowerShell:
```powershell
Invoke-WebRequest -Uri https://github.com/ankitpro/agent-corex/releases/latest/download/agent-corex-windows-x86_64.exe -OutFile agent-corex.exe
```

**pip** (Python 3.8+):
```bash
pip install agent-corex
```

---

## Step 2 — Verify

```bash
agent-corex --version
# agent-corex 1.1.0
```

---

## Step 3 — Connect to Your AI Tools

```bash
# Authenticate
agent-corex login --key acx_your_key

# See which tools (Claude Desktop, Cursor, VS Code, etc.) are installed
agent-corex detect

# Inject agent-corex as an MCP server into all detected tools
agent-corex init
```

Example output:
```
Scanning for AI tools...

  [+] Claude Desktop: /Users/you/Library/Application Support/Claude/claude_desktop_config.json
      Existing servers (will be kept): filesystem, git
      Add 'agent-corex' entry? [Y/n]: Y
      [+] Injected. Backup saved.

  [+] VS Code: /Users/you/Library/Application Support/Code/User/mcp.json
      Add 'agent-corex' entry? [Y/n]: Y
      [+] Injected. Backup saved.

Done. Restart your AI tools for changes to take effect.
```

Restart Claude Desktop / Cursor / VS Code — Agent-CoreX will appear as an available MCP server.

---

## Step 4 — Verify Setup

```bash
agent-corex status
```

```
agent-corex  v1.1.0

Auth
  [+] Logged in: Yes

MCP Clients
  [+] Claude Desktop: detected
      agent-corex inject: [+] Yes
  [+] VS Code: detected
      agent-corex inject: [+] Yes
```

If something looks wrong:
```bash
agent-corex doctor   # runs 7 health checks and shows exactly what to fix
```

---

## Step 5 — Browse & Install MCP Servers

```bash
agent-corex registry              # browse the marketplace catalog
agent-corex install-mcp github    # install the GitHub MCP server
agent-corex install-mcp postgres  # install Postgres
agent-corex list                  # see all currently installed servers
agent-corex update                # pull latest configs from registry
```

---

## Useful Commands

```bash
agent-corex detect             # detect AI tools
agent-corex init               # inject into all tools
agent-corex eject              # remove from all tools
agent-corex status             # full status report
agent-corex doctor             # health diagnostics
agent-corex keys               # show/verify API key
agent-corex logout             # remove credentials
```

---

## Next Steps

- [Full Installation Guide](installation.md) — all install methods, SHA256 verification, troubleshooting
- [MCP Setup Guide](/mcp-setup) — detailed per-tool configuration
- [GitHub Releases](https://github.com/ankitpro/agent-corex/releases) — changelogs and all binary downloads
