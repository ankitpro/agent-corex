---
layout: page
title: MCP Setup Guide — Connect Claude Desktop, Cursor & VS Code
description: One-command setup to connect Agent-CoreX as an MCP server to Claude Desktop, Cursor, and VS Code
permalink: /mcp-setup/
---

# MCP Setup Guide

Connect Agent-CoreX to **Claude Desktop**, **Cursor**, and **VS Code** in under 2 minutes.

Agent-CoreX runs as a local MCP gateway server. Once connected, Claude Desktop, Cursor, and VS Code can discover and call all Agent-CoreX tools directly — no manual config editing required.

---

## How it works

```
Claude Desktop / Cursor
        │  launches on startup
        ▼
  agent-corex serve        ← MCP gateway (stdio JSON-RPC 2.0)
        │
        ├── tools/list  →  returns all tools (free + enterprise)
        └── tools/call  →  routes to the right handler
```

The `agent-corex init` command writes a single entry into your tool's MCP config file. Claude or Cursor then launch `agent-corex serve` automatically whenever they need tools.

---

## Step 1 — Install

Choose any method:

**Homebrew** (macOS / Linux):
```bash
brew tap ankitpro/agent-corex && brew install agent-corex
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

**Windows** (PowerShell as Administrator):
```powershell
Invoke-WebRequest `
  -Uri https://github.com/ankitpro/agent-corex/releases/latest/download/agent-corex-windows-x86_64.exe `
  -OutFile "$env:SystemRoot\System32\agent-corex.exe"
```

**pip** (Python 3.8+):
```bash
pip install agent-corex
```

**uvx** (no install — requires [uv](https://docs.astral.sh/uv/)):
```bash
uvx agent-corex init   # run any command without installing
```

> If you use uvx, skip to [Manual config — uvx](#manual-config--uvx) below — the `init` command auto-injects the binary path, not the uvx path.

Verify:

```bash
agent-corex version
# agent-corex 1.0.3
```

---

## Step 2 — Run init

```bash
agent-corex init
```

The command:

1. Scans for Claude Desktop and Cursor on your machine
2. Prints all **existing** MCP servers that will be preserved
3. Asks for confirmation before touching any file
4. Creates a **timestamped backup** of the config
5. Merges **only** the `agent-corex` entry — nothing else changes

### Example output

```
Scanning for AI tools...

  [+] Claude Desktop: C:\Users\you\AppData\Roaming\Claude\claude_desktop_config.json
      Existing servers (will be kept):
        - filesystem
        - git
      Add 'agent-corex' entry in Claude Desktop? [Y/n]: Y
      [+] Added. mcpServers now contains 3 server(s):
            - agent-corex  <-- agent-corex
            - filesystem
            - git
      Backup: claude_desktop_config.20260323_120000.bak
  [-] Cursor: not detected

Done. Restart the tool for changes to take effect.
Run  agent-corex status  to verify.
```

### Skip confirmation

```bash
agent-corex init --yes
```

---

## Step 3 — Restart your tool

Restart Claude Desktop or Cursor. The tool will now launch `agent-corex serve` in the background and Agent-CoreX tools will appear alongside your other MCP servers.

---

## Step 4 — Verify

```bash
agent-corex status
```

```
agent-corex  v1.0.3

Auth
  [-] Logged in: No
    Run: agent-corex login

Config
  Path:   C:\Users\you\.agent-corex\config.json
  Exists: No

MCP Clients
  [+] Claude Desktop: detected
      Config:             C:\Users\you\AppData\Roaming\Claude\claude_desktop_config.json
      agent-corex inject: [+] Yes
  [-] Cursor: not installed

Available Tools
  Free (2):
    [+] retrieve_tools
    [+] list_mcp_servers
  Enterprise (3):
    [-] [locked] github_search
    [-] [locked] web_search
    [-] [locked] database_query

  Run  agent-corex login  to unlock enterprise tools.
```

---

## What gets written — Claude Desktop & Cursor

`init` performs a **targeted merge** — it reads the existing file, adds one key, and writes it back. All other content is left exactly as-is.

**Before:**

```json
{
  "preferences": { "sidebarMode": "code" },
  "mcpServers": {
    "filesystem": { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem"] },
    "git":        { "command": "uvx", "args": ["mcp-server-git"] }
  }
}
```

**After `agent-corex init`:**

```json
{
  "preferences": { "sidebarMode": "code" },
  "mcpServers": {
    "filesystem": { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem"] },
    "git":        { "command": "uvx", "args": ["mcp-server-git"] },
    "agent-corex": {
      "command": "agent-corex",
      "args": ["serve"]
    }
  }
}
```

Only the `agent-corex` key is added. `preferences`, `filesystem`, `git`, and all other keys are untouched.

---

## What gets written — VS Code

VS Code (1.99+) stores MCP servers inside `settings.json` under a nested `mcp.servers` block. Agent-CoreX adds the `type: "stdio"` field required by VS Code.

**Before (excerpt from settings.json):**

```json
{
  "workbench.colorTheme": "Default Dark+",
  "editor.fontSize": 14
}
```

**After `agent-corex init`:**

```json
{
  "workbench.colorTheme": "Default Dark+",
  "editor.fontSize": 14,
  "mcp": {
    "servers": {
      "agent-corex": {
        "type": "stdio",
        "command": "agent-corex",
        "args": ["serve"]
      }
    }
  }
}
```

All existing settings are preserved. Only the `mcp.servers.agent-corex` entry is added.

> **VS Code restart required** — VS Code holds settings.json in memory while running. Fully close and reopen VS Code so it reads the updated file from disk. `init` will remind you of this automatically.

---

## Manual config — uvx

If you prefer not to install `agent-corex` globally (using [uv](https://docs.astral.sh/uv/) instead), point the MCP config at `uvx` directly. The AI tool will download and cache `agent-corex` automatically on first launch.

**Claude Desktop / Cursor** (`claude_desktop_config.json` / `mcp.json`):

```json
{
  "mcpServers": {
    "agent-corex": {
      "command": "uvx",
      "args": ["agent-corex", "serve"]
    }
  }
}
```

**VS Code** (`settings.json`):

```json
{
  "mcp": {
    "servers": {
      "agent-corex": {
        "type": "stdio",
        "command": "uvx",
        "args": ["agent-corex", "serve"]
      }
    }
  }
}
```

**Pin to a specific version** (recommended for reproducible team setups):

```json
"args": ["agent-corex@1.8.0", "serve"]
```

> `uvx` must be on your PATH for this to work. Run `which uvx` (macOS/Linux) or `where uvx` (Windows) to verify. Install uv from [astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/).

---

## Config file locations

| Tool | Platform | Path |
|------|----------|------|
| Claude Desktop | Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Claude Desktop | macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Claude Desktop | Linux | `~/.config/Claude/claude_desktop_config.json` |
| Cursor | Windows | `%APPDATA%\Cursor\User\mcp.json` |
| Cursor | macOS | `~/Library/Application Support/Cursor/User/mcp.json` |
| Cursor | Linux | `~/.config/Cursor/User/mcp.json` |
| VS Code | Windows | `%APPDATA%\Code\User\settings.json` |
| VS Code | macOS | `~/Library/Application Support/Code/User/settings.json` |
| VS Code | Linux | `~/.config/Code/User/settings.json` |
| VS Code Insiders | Windows | `%APPDATA%\Code - Insiders\User\settings.json` |
| VS Code Insiders | macOS | `~/Library/Application Support/Code - Insiders/User/settings.json` |
| VSCodium | Windows | `%APPDATA%\VSCodium\User\settings.json` |
| VSCodium | macOS | `~/Library/Application Support/VSCodium/User/settings.json` |

---

## Backups

A backup is created **before every write**, named with a timestamp:

```
claude_desktop_config.20260323_120000.bak
```

The backup lives in the same directory as the original. To restore:

```bash
# Windows
copy "%APPDATA%\Claude\claude_desktop_config.20260323_120000.bak" "%APPDATA%\Claude\claude_desktop_config.json"

# macOS / Linux
cp "~/Library/Application Support/Claude/claude_desktop_config.20260323_120000.bak" \
   "~/Library/Application Support/Claude/claude_desktop_config.json"
```

---

## Authenticate for enterprise tools

Free tools (`retrieve_tools`, `list_mcp_servers`) work without an account. Enterprise tools require an API key.

```bash
agent-corex login
```

This opens `https://agent-corex.ai/login` in your browser. Log in, copy your API key, and paste it when prompted. The key is stored in `~/.agent-corex/config.json`.

---

## All CLI commands

| Command | What it does |
|---------|-------------|
| `agent-corex init` | Detect Claude/Cursor and inject gateway entry (merges, never replaces) |
| `agent-corex init --yes` | Same, skip all confirmation prompts |
| `agent-corex serve` | Start the MCP gateway server (called automatically by Claude/Cursor) |
| `agent-corex login` | Authenticate and save API key to `~/.agent-corex/config.json` |
| `agent-corex status` | Show auth state, config path, injection status, available tools |
| `agent-corex retrieve "query"` | Search for tools from the CLI |

---

## Troubleshooting

### `uvx: command not found` in AI tool logs

The AI tool inherits the system PATH, which may differ from your terminal PATH. Make sure `uvx` is accessible system-wide:

```bash
# macOS / Linux — add to ~/.zshrc or ~/.bashrc then restart your terminal and the AI tool
export PATH="$HOME/.local/bin:$PATH"

# Verify
which uvx
uvx --version
```

On macOS, if you installed uv via `curl`, it goes to `~/.local/bin/uvx`. If your AI tool still can't find it, use the full path in the config:

```json
{
  "mcpServers": {
    "agent-corex": {
      "command": "/Users/you/.local/bin/uvx",
      "args": ["agent-corex", "serve"]
    }
  }
}
```

### `agent-corex: command not found` after init

The `agent-corex` binary must be on your PATH so Claude/Cursor can launch `agent-corex serve`.

```bash
# Check if it's reachable
which agent-corex        # macOS/Linux
where agent-corex        # Windows

# If not found, add pip's script directory to PATH
# On Windows (PowerShell):
$env:PATH += ";$env:APPDATA\Python\Scripts"

# On macOS/Linux (add to ~/.bashrc or ~/.zshrc):
export PATH="$HOME/.local/bin:$PATH"
```

### Claude/Cursor doesn't show Agent-CoreX tools

1. Run `agent-corex status` and confirm `agent-corex inject: [+] Yes`
2. Fully restart the tool (quit + reopen, not just refresh)
3. Check the tool's MCP log for errors

### VS Code doesn't show Agent-CoreX tools

VS Code holds `settings.json` in memory while running. If you ran `init` while VS Code was open:

1. **Fully close VS Code** (all windows, not just the editor tab)
2. Reopen VS Code — it reads `settings.json` fresh on startup
3. Run `agent-corex status` and confirm `agent-corex inject: [+] Yes`

If VS Code still doesn't show the tools, verify the `mcp` block is in `settings.json`:

```bash
# Windows PowerShell
Get-Content "$env:APPDATA\Code\User\settings.json" | Select-String "mcp"

# macOS / Linux
grep -A5 '"mcp"' ~/Library/Application\ Support/Code/User/settings.json
```

### I accidentally ran init and want to undo

Restore from the backup created by `init`:

```bash
# The backup name is printed after each init run, e.g.:
# Backup: claude_desktop_config.20260323_120000.bak
cp "~/Library/Application Support/Claude/claude_desktop_config.20260323_120000.bak" \
   "~/Library/Application Support/Claude/claude_desktop_config.json"
```

### Enterprise tools show `AUTH_REQUIRED`

Run `agent-corex login` to store your API key. Free tools always work without authentication.

---

## Next steps

- [API Reference](/api) — use Agent-CoreX from Python or REST
- [Quick Start](/quickstart) — 5-minute overview
- [GitHub](https://github.com/ankitpro/agent-corex) — source code and issues
