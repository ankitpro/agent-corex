# Vibe Coding: Zero-Config Local Setup Guide

This guide walks you through setting up Agent-Corex for a seamless **Vibe Coding Experience** — where you install a pack, configure environment variables, and immediately start using MCP tools in Claude Desktop / Cursor / VS Code.

**Time required:** ~5 minutes
**Prerequisites:** Python 3.8+, Claude Desktop / Cursor / VS Code

---

## Quick Start (5 Steps)

### Step 1: Install Agent-Corex CLI

```bash
pip install agent-corex
```

Verify installation:
```bash
agent-corex --version
```

---

### Step 2: Detect Your AI Tools

See which tools are installed and where their configs are stored:

```bash
agent-corex detect
```

**Output example:**
```
Tool                  Installed    Config path
----------------------------------------------
Claude Desktop        Yes          /Users/alice/.claude/claude_desktop_config.json
Cursor                Yes          /Users/alice/.cursor/config/settings.json
VS Code               Yes          /Users/alice/.config/Code/User/settings.json
```

---

### Step 3: Install a Pack

Install the **Vibe Coding Pack** — a curated bundle of essential tools:

```bash
agent-corex install-pack vibe_coding_pack
```

This does 3 things:
1. **Registers the pack** in `~/.agent-corex/installed_servers.json`
2. **Marks servers as enabled:** railway, github, supabase, filesystem, redis
3. **Injects servers** into all detected AI tools (Claude, Cursor, VS Code)

**Output example:**
```
✓ Registered pack: vibe_coding_pack
  Servers enabled: 5
    • railway
    • github
    • supabase
    • filesystem
    • redis

✓ Servers injected into detected tools

Next steps:
  1. Run: agent-corex setup-env        (configure API keys)
  2. Run: agent-corex generate-mcp-config  (create unified config)
  3. Restart your AI tools for changes to take effect
```

---

### Step 4: Set Up Environment Variables

Configure API keys and connection strings:

```bash
agent-corex setup-env
```

You'll be prompted for optional API keys:
- `OPENAI_API_KEY` (sk-...)
- `SUPABASE_URL` (https://...)
- `SUPABASE_KEY`
- `REDIS_URL` (redis://...)
- `RAILWAY_API_KEY`
- `RENDER_API_KEY`
- `GITHUB_TOKEN` (ghp_...)
- `AGENT_COREX_API_KEY` (acx_...)

**Press Enter to skip any variable.** These are saved in `~/.agent-corex/.env`.

---

### Step 5: Generate Unified MCP Config

Merge all server definitions into a single config file:

```bash
agent-corex generate-mcp-config
```

This reads all server definitions from your AI tools and creates `~/.agent-corex/mcp.json` with environment variables injected.

**Output example:**
```
✓ Generated /Users/alice/.agent-corex/mcp.json
  Servers collected: 5
    • railway
    • github
    • supabase
    • filesystem
    • redis

✓ Config is valid and ready to use
```

---

## Done! Restart Your Tools

Restart Claude Desktop, Cursor, or VS Code to load the new MCP servers.

Now you can use Vibe tools in Claude:

### Example Prompts

**1. Deploy a backend:**
```
Build a simple Node.js API with Express and deploy it to Railway.
Include:
- /api/hello endpoint
- .env file for configuration
- Deploy to Railway using railway-mcp-server
```

**2. Setup a database:**
```
Create a Supabase project schema with users and posts tables.
Use the supabase-mcp-server to create the schema.
```

**3. Build a full stack app:**
```
Build a todo app with:
- Next.js frontend (filesystem server to create files)
- Supabase backend (database)
- Redis caching
- Deploy to Railway
```

---

## Verify Everything Works

Check your setup:

```bash
agent-corex doctor
```

**Example output:**
```
agent-corex doctor

Python
  [+] Python 3.11.7 (>= 3.8 required)

Dependencies
  [+] httpx
  [+] typer
  [+] rich

Config
  [+] Config file exists and is valid JSON

Auth
  [+] Logged in as Alice

Backend
  URL: http://localhost:8000
  [+] Reachable (status 200)

API Key
  [+] Key valid: acx_abcd12....5678

AI Tools
  [+] Claude Desktop: injected
  [+] Cursor: injected
  [+] VS Code: NOT injected

PATH
  [+] agent-corex found at /Users/alice/.venv/bin/agent-corex

Pack System
  [+] 1 pack(s) installed
      • vibe_coding_pack: 5/5 servers enabled

MCP Configuration
  [+] mcp.json found
      ✓ Config is valid
  [+] .env file found with 8 variable(s)

──────────────────────────────────────
[+] All checks passed. Your setup looks healthy.
```

---

## File Structure

After setup, your `~/.agent-corex/` directory contains:

```
~/.agent-corex/
├── config.json                  # Your API key (created via login)
├── .env                         # Environment variables (created via setup-env)
├── installed_servers.json       # Installed packs (created via install-pack)
├── mcp.json                     # Unified MCP config (created via generate-mcp-config)
└── tool_cache/                  # Cached tool schemas
```

---

## Troubleshooting

### "Tool not found" in Claude

**Solution:** Make sure you:
1. Ran `agent-corex install-pack vibe_coding_pack` ✓
2. Ran `agent-corex generate-mcp-config` ✓
3. **Restarted Claude/Cursor/VS Code** ✓

### "Command failed: permission denied"

**Solution:** Make sure agent-corex is in your PATH:
```bash
which agent-corex
```

If not found, reinstall:
```bash
pip install --upgrade agent-corex
```

### "Enterprise tool requires authentication"

**Solution:** Log in with your API key:
```bash
agent-corex login --key acx_your_key_here
```

Or set the env var:
```bash
export AGENT_COREX_API_KEY=acx_your_key_here
```

### "Cannot reach backend"

**Solution:** Backend is optional for local MCP servers. If you need enterprise features, ensure your backend is running:
```bash
agent-corex health
```

If unreachable, set the correct URL:
```bash
agent-corex set-url http://your-backend:8000
```

---

## Available Packs

### Vibe Coding Pack
Essential tools for fast development:
- **railway** — Deploy to Railway.app
- **github** — GitHub API integration
- **supabase** — Postgres + Auth
- **filesystem** — File operations
- **redis** — Caching & pub/sub

```bash
agent-corex install-pack vibe_coding_pack
```

### Data Science Pack
Tools for data analysis:
- **pandas** — Data manipulation
- **jupyter** — Notebook integration

```bash
agent-corex install-pack data_science_pack
```

---

## Advanced: Manage Packs

### List installed packs
```bash
agent-corex status
```

### Enable/disable a server in a pack
Edit `~/.agent-corex/installed_servers.json`:
```json
{
  "vibe_coding_pack": {
    "servers": ["railway", "github", "supabase", "filesystem", "redis"],
    "enabled": {
      "railway": true,
      "github": true,
      "supabase": false,
      "filesystem": true,
      "redis": true
    }
  }
}
```

Then regenerate config:
```bash
agent-corex generate-mcp-config
```

### Uninstall a pack
Remove the entry from `~/.agent-corex/installed_servers.json` and regenerate:
```bash
agent-corex generate-mcp-config
```

---

## How It Works

### Startup Sequence

1. **You run:** `agent-corex install-pack vibe_coding_pack`
   - Packs registered in `installed_servers.json`
   - Servers injected into Claude/Cursor/VS Code configs

2. **You run:** `agent-corex setup-env`
   - API keys saved to `~/.agent-corex/.env`

3. **You run:** `agent-corex generate-mcp-config`
   - Reads all server configs from AI tools
   - Reads API keys from `.env`
   - Merges into unified `mcp.json`

4. **Claude starts:**
   - Runs `agent-corex serve`
   - Loads `~/.agent-corex/mcp.json`
   - Injects env variables into servers
   - Tools available in `tools/list`

5. **Claude uses a tool:**
   - MCP gateway routes to correct server
   - Server starts (lazy load)
   - Tool executes with injected env vars
   - Result returned to Claude

### Lazy Server Startup

Servers are **not started** until their tools are actually used:
- Install 20 servers? No performance penalty.
- Use 3 of them? Only those 3 are started.
- Servers auto-restart if they crash.

---

## Next Steps

- **Read the full CLI docs:** `agent-corex --help`
- **Check specific command:** `agent-corex install-pack --help`
- **View your setup:** `agent-corex status`
- **Diagnose issues:** `agent-corex doctor`

---

## Questions?

- Visit the docs: https://github.com/ankitpro/agent-corex
- File an issue: https://github.com/ankitpro/agent-corex/issues
- Check the CLI help: `agent-corex --help`

---

**Last Updated:** 2026-03-28
**Agent-Corex Version:** 1.1.3+
