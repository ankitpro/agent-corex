# ✨ CLI Features & Commands

Complete reference of all CLI commands with examples and behaviors.

---

## Tool Retrieval Commands

### `agent-corex retrieve [QUERY]`
Search for relevant tools by natural language query.

**Usage:**
```bash
agent-corex retrieve "edit a file" --top-k 5 --method hybrid
agent-corex retrieve "deploy to cloud" -k 3 -m embedding
```

**Options:**
- `QUERY` (required) — Tool search query
- `--top-k` / `-k` — Number of results to return (default: 5)
- `--method` / `-m` — Ranking method: keyword | hybrid | embedding (default: hybrid)
- `--config` / `-c` — Path to mcp.json config file (optional)

**Output:**
```
Found 5 tool(s) for: 'edit a file'

1. filesystem
   Edit and manage files in your workspace

2. editor
   Edit text files with syntax highlighting

...
```

**Behavior:**
- Loads tools from local registry or config
- Embeds query using sentence-transformers or OpenAI
- Ranks tools by cosine similarity (or BM25 keyword match)
- Returns top_k results with descriptions

---

### `agent-corex start [OPTIONS]`
Start the Agent-Core retrieval API server (FastAPI).

**Usage:**
```bash
agent-corex start
agent-corex start --host 0.0.0.0 --port 8000 --reload
```

**Options:**
- `--host` / `-h` — Server host (default: 127.0.0.1)
- `--port` / `-p` — Server port (default: 8000)
- `--reload` / `--no-reload` — Enable auto-reload (default: true)
- `--config` / `-c` — Path to mcp.json config file

**Behavior:**
- Starts uvicorn FastAPI server
- Exposes `/retrieve_tools` endpoint
- Auto-reloads on code changes (development mode)
- Logs request/response data

---

### `agent-corex health`
Check if the retrieval API backend is running and healthy.

**Usage:**
```bash
agent-corex health
```

**Output:**
```
Checking http://localhost:8000/health ...
✓ Backend is healthy
```

Or:
```
✗ Backend returned status 500
```

Or:
```
✗ Cannot connect to http://localhost:8000. Is the backend running?
  Change URL:  agent-corex set-url http://your-host:port
```

---

## Gateway & Injection Commands

### `agent-corex serve`
Start the MCP gateway server in stdio mode.

**Usage:**
```bash
agent-corex serve
```

**Behavior:**
- Runs in stdio mode (reads JSON-RPC from stdin, writes to stdout)
- Injected into Claude Desktop / Cursor / VS Code configs
- Implements MCP protocol:
  - `initialize()` → initialized notification
  - `tools/list` → returns available tools
  - `tools/call(name, args)` → executes tool
- Loads tools from local registry + MCP servers
- Filters tools based on user context (if supported)

**Note:** This command is meant to be run automatically by AI tools, not by end users.

---

### `agent-corex init [OPTIONS]`
Detect Claude Desktop / Cursor / VS Code and inject Agent-Corex as an MCP server.

**Usage:**
```bash
agent-corex init
agent-corex init --yes
```

**Options:**
- `--yes` / `-y` — Skip confirmation prompts

**Output:**
```
Scanning for AI tools...

  [+] Claude Desktop: /Users/alice/.claude/claude_desktop_config.json
      Existing servers (will be kept):
        - brave-search
        - filesystem
      Add 'agent-corex' entry in Claude Desktop? [Y/n]: y
      [+] Added. MCP servers now contains 3 server(s):
            - brave-search
            - filesystem
            - agent-corex  <-- agent-corex

  [+] Cursor: /Users/alice/.cursor/config/settings.json
      No existing MCP servers — creating new block.
      Add 'agent-corex' entry in Cursor? [Y/n]: y
      [+] Added. MCP servers now contains 1 server(s):
            - agent-corex  <-- agent-corex
      Backup: /Users/alice/.cursor/config/settings.json.backup.20260328.120000

  [-] VS Code: not detected

Done. Restart the tool for changes to take effect.
```

**Behavior:**
1. Detects all 5 supported AI tools
2. Shows existing MCP servers (will be preserved)
3. Prompts for confirmation (unless --yes)
4. Creates timestamped backup of config before writing
5. Injects agent-corex server definition
6. Displays final server list
7. Instructs user to restart the tool

**Server Definition Injected:**
- Claude/Cursor: `{"command": "agent-corex", "args": ["serve"]}`
- VS Code: `{"type": "stdio", "command": "agent-corex", "args": ["serve"]}`

---

### `agent-corex eject [OPTIONS]`
Remove agent-corex from Claude Desktop / Cursor / VS Code configs.

**Usage:**
```bash
agent-corex eject
agent-corex eject --tool claude --yes
```

**Options:**
- `--tool` / `-t` — Target tool (claude | cursor | vscode | vscode-insiders | vscodium)
- `--yes` / `-y` — Skip confirmation prompts

**Behavior:**
- Removes agent-corex entry from specified tool(s)
- Creates backup before removing
- Preserves other MCP servers
- Instructs user to restart tool

---

### `agent-corex list [OPTIONS]`
List all MCP servers currently injected in detected tools.

**Usage:**
```bash
agent-corex list
agent-corex list --all
```

**Options:**
- `--all` / `-a` — Include tools that are not installed

**Output:**
```
Claude Desktop  (/Users/alice/.claude/claude_desktop_config.json)
  agent-corex       agent-corex serve
  brave-search      npx -y @braveai/mcp-server
  filesystem        npx -y @modelcontextprotocol/server-filesystem

Cursor  (/Users/alice/.cursor/config/settings.json)
  agent-corex       agent-corex serve

VS Code: not installed
```

---

### `agent-corex detect`
Detect installed AI tools and show their config paths.

**Usage:**
```bash
agent-corex detect
```

**Output:**
```
Tool                  Installed    Config path
----------------------------------------------
Claude Desktop        Yes          /Users/alice/.claude/claude_desktop_config.json
Cursor                Yes          /Users/alice/.cursor/config/settings.json
VS Code               Yes          /Users/alice/.config/Code/User/settings.json
VS Code Insiders      No           —
VSCodium              No           —

Run  agent-corex init  to inject agent-corex into detected tools.
```

---

## Authentication Commands

### `agent-corex login [OPTIONS]`
Authenticate with your Agent-Corex account and store API key.

**Usage:**
```bash
agent-corex login
agent-corex login --key acx_your_key_here
agent-corex login --no-browser
```

**Options:**
- `--key` / `-k` — API key to store (acx_...)
- `--no-browser` — Skip opening browser, just prompt for key

**Flow:**
1. Opens browser to login page (unless --no-browser)
2. Prompts for API key
3. Validates key format (must start with "acx_")
4. Attempts to validate against backend (gracefully skips if unreachable)
5. Stores key in `~/.agent-corex/config.json`

**Output:**
```
Opening browser: http://localhost:5173/login

After logging in, copy your API key from the dashboard.

Paste your API key (acx_...): ••••••••••••••••••

(Could not reach backend — storing key locally for offline use.)

[+] Logged in as Alice
  Credentials saved to /Users/alice/.agent-corex/config.json
```

---

### `agent-corex logout [OPTIONS]`
Remove stored API key and user info from config.

**Usage:**
```bash
agent-corex logout
agent-corex logout --yes
```

**Options:**
- `--yes` / `-y` — Skip confirmation prompt

---

### `agent-corex keys`
Show the active API key (masked) and account info; verify with backend.

**Usage:**
```bash
agent-corex keys
```

**Output:**
```
Active credentials
  API key : acx_abcd12....5678
  User ID : user_123
  Name    : Alice
  Backend : http://localhost:8000
  Frontend: http://localhost:5173

Verifying key with backend...
[+] Key is valid.
```

---

### `agent-corex set-url [URL] [OPTIONS]`
Set the backend API URL or frontend login page URL.

**Usage:**
```bash
agent-corex set-url http://localhost:8000
agent-corex set-url https://api.example.com
agent-corex set-url http://localhost:5173 --frontend
```

**Options:**
- `URL` (required) — URL to set
- `--frontend` / `-f` — Set frontend URL instead of backend

**Behavior:**
- Saves to `~/.agent-corex/config.json`
- Backend URL used for API calls and MCP servers
- Frontend URL used for `agent-corex login` browser redirect

---

## MCP Registry & Installation

### `agent-corex registry`
Browse all installable MCP servers from the Agent-Corex registry.

**Usage:**
```bash
agent-corex registry
```

**Output:**
```
Available MCP Servers  (47 total)

  DATABASES
    postgres          PostgreSQL database adapter
    mongodb           MongoDB database adapter
    supabase          Supabase Postgres + Auth + Real...  [needs: SUPABASE_URL, SUPABASE_KEY]

  DEVELOPER-TOOLS
    github            GitHub API integration  [needs: GITHUB_TOKEN]
    gitlab            GitLab API integration  [needs: GITLAB_TOKEN]

  WEB
    brave-search      Brave Search API integration  [needs: BRAVE_API_KEY]
    google-search     Google Custom Search  [needs: GOOGLE_API_KEY, GOOGLE_ENGINE_ID]

...

Install any:  agent-corex install-mcp <name>
```

---

### `agent-corex install-mcp [NAME] [OPTIONS]`
Install a named MCP server from the registry into your AI tools.

**Usage:**
```bash
agent-corex install-mcp github
agent-corex install-mcp postgres --tool claude --yes
agent-corex install-mcp github --tool vscode
```

**Options:**
- `NAME` (required) — Registry server slug (e.g., 'github')
- `--tool` / `-t` — Target tool (claude | cursor | vscode | vscode-insiders | vscodium). All if omitted.
- `--yes` / `-y` — Skip confirmation prompts

**Flow:**
1. Fetches server definition from registry
2. Shows server info (description, command, installation notes)
3. Prompts for required environment variables
4. Prompts for optional environment variables (Enter to skip)
5. Injects server definition into each detected tool
6. Instructs user to restart tools

**Output:**
```
Fetching 'github' from registry...

  GitHub
  GitHub API integration and utilities
  Command: npx -y @modelcontextprotocol/server-github
  Note:    Ensure you have a valid GitHub token with appropriate scopes

  Required environment variables:
    GITHUB_TOKEN: •••••••••••••••••••••

  Optional environment variables (Enter to skip):
    GITHUB_REPO: (default to current repo)

Installing 'github' into detected tools...

  [+] Installed in Claude Desktop
      Backup: /Users/alice/.claude/claude_desktop_config.json.backup.20260328.120000

  [+] Installed in Cursor
      Backup: /Users/alice/.cursor/config/settings.json.backup.20260328.120001

  [-] VS Code: not detected — skipping

Done. Restart your tools for changes to take effect.
Run  agent-corex status  to verify.
```

---

### `agent-corex update [OPTIONS]`
Re-fetch all installed MCP servers from the registry and update their configs.

**Usage:**
```bash
agent-corex update
agent-corex update --tool claude --yes
```

**Options:**
- `--yes` / `-y` — Skip confirmation prompts
- `--tool` / `-t` — Limit to one tool

**Behavior:**
1. Scans all detected tools for injected MCP servers
2. For each server, fetches latest definition from registry
3. Compares current vs. registry versions
4. Prompts for confirmation if changes detected
5. Updates config file with new command/args/env
6. Creates backup before updating

**Output:**
```
Checking for updates...

  [=] Claude Desktop / agent-corex: up to date
  [!] Claude Desktop / github: update available
      current:  npx -y @modelcontextprotocol/server-github
      registry: npx -y @modelcontextprotocol/server-github --version 2.0
      Update 'github' in Claude Desktop? [Y/n]: y
      [+] Updated
      Backup: /Users/alice/.claude/claude_desktop_config.json.backup.20260328.120002

  [=] Cursor / agent-corex: up to date
  [=] Cursor / github: up to date

Checked 3 server(s). Updated 1.
Restart your AI tools for changes to take effect.
```

---

## Configuration Commands

### `agent-corex config`
Show Python version and installed dependencies.

**Usage:**
```bash
agent-corex config
```

**Output:**
```
Agent-Core 1.1.3

Configuration:
  Python version: 3.11.7
  Installation path: /Users/alice/.venv/lib/python3.11/site-packages/agent_core

Dependencies:
  ✓ FastAPI
  ✓ Sentence Transformers
  ✓ FAISS
```

---

### `agent-corex version`
Show Agent-Core CLI version.

**Usage:**
```bash
agent-corex version
agent-corex --version
agent-corex -V
```

**Output:**
```
Agent-Core 1.1.3
```

---

## Status & Diagnostics

### `agent-corex status`
Show auth state, config path, MCP injection status, and available tools.

**Usage:**
```bash
agent-corex status
```

**Output:**
```
agent-corex  v1.1.3

Auth
  [+] Logged in: Yes  (Alice)

Config
  Path:   /Users/alice/.agent-corex/config.json
  Exists: Yes

MCP Clients
  [+] Claude Desktop: detected
      Config:             /Users/alice/.claude/claude_desktop_config.json
      agent-corex inject: [+] Yes

  [+] Cursor: detected
      Config:             /Users/alice/.cursor/config/settings.json
      agent-corex inject: [+] Yes

  [+] VS Code: detected
      Config:             /Users/alice/.config/Code/User/settings.json
      agent-corex inject: [-] No

  [-] VS Code Insiders: not installed

Available Tools
  Free (5):
    [+] filesystem
    [+] github
    [+] brave-search
    [+] calculator
    [+] web-search

  Enterprise (3):
    [+] postgres
    [+] mongodb
    [+] supabase
```

---

### `agent-corex doctor`
Comprehensive system health check.

**Usage:**
```bash
agent-corex doctor
```

**Checks:**
1. Python version (3.8+)
2. Required packages (FastAPI, httpx, typer, etc.)
3. Config file existence
4. Backend connectivity
5. API key validity
6. MCP injection status in each tool
7. Available tools count

**Output:**
```
agent-corex doctor

Python
  [+] Version 3.11.7 (3.8+ required)

Packages
  [+] fastapi
  [+] httpx
  [+] typer
  [+] sentence-transformers
  [!] faiss-cpu (optional but recommended for faster retrieval)

Config
  [+] File exists: /Users/alice/.agent-corex/config.json
  [+] API key valid
  [+] Backend reachable: http://localhost:8000

Injection Status
  [+] Claude Desktop: agent-corex injected
  [+] Cursor: agent-corex injected
  [-] VS Code: agent-corex NOT injected

Available Tools
  [+] 47 tools available
  [+] 5 free tier
  [+] 42 enterprise tier (unlocked with API key)

✓ All checks passed!
```

---

## Global Options

All commands support:
- `--help` / `-h` — Show command help
- `--version` / `-V` — Show CLI version

---

**Last Updated:** 2026-03-28
