# Vibe Coding Experience — Testing Checklist

Complete end-to-end testing of the Vibe Coding system.

---

## Pre-Test Setup

- [ ] Fresh Python 3.11+ environment
- [ ] Claude Desktop / Cursor / VS Code installed
- [ ] Internet connection available
- [ ] At least 500MB free disk space

---

## Part 1: CLI Installation & Discovery

### Test: Install CLI
```bash
pip install -e .  # Install from source
agent-corex --version
# Expected: Agent-CoreX 1.1.3+
```
- [ ] Installation succeeds
- [ ] Version output correct

### Test: Detect Tools
```bash
agent-corex detect
```
- [ ] Lists Claude Desktop (if installed)
- [ ] Lists Cursor (if installed)
- [ ] Lists VS Code variants (if installed)
- [ ] Shows correct config paths

---

## Part 2: Pack Installation

### Test: List Available Packs
```bash
agent-corex list-packs
```
- [ ] Shows vibe_coding_pack
- [ ] Shows description
- [ ] Shows server list

### Test: Install Pack
```bash
agent-corex install-pack vibe_coding_pack --yes
```
- [ ] Creates `~/.agent-corex/installed_servers.json`
- [ ] Registers 5 servers (railway, github, supabase, filesystem, redis)
- [ ] Marks all as enabled: true
- [ ] Injects servers into detected AI tools
- [ ] Shows success message

### Verify: Check Installed Servers
```bash
cat ~/.agent-corex/installed_servers.json
```
- [ ] Contains vibe_coding_pack key
- [ ] Lists 5 servers
- [ ] All have enabled: true

---

## Part 3: Environment Setup

### Test: Setup Environment Variables
```bash
agent-corex setup-env
```

When prompted:
- [ ] OPENAI_API_KEY: (skip or enter test key)
- [ ] SUPABASE_URL: (skip or enter test URL)
- [ ] SUPABASE_KEY: (skip or enter test key)
- [ ] REDIS_URL: (skip or enter test URL)
- [ ] RAILWAY_API_KEY: (skip or enter test key)
- [ ] GITHUB_TOKEN: (skip or enter test token)
- [ ] AGENT_COREX_API_KEY: (skip or enter test key)

- [ ] Saves to `~/.agent-corex/.env`
- [ ] Shows masked values
- [ ] Asks for confirmation

### Verify: Check .env File
```bash
cat ~/.agent-corex/.env
```
- [ ] File exists
- [ ] Contains environment variables
- [ ] No plaintext display when cat'd

---

## Part 4: MCP Config Generation

### Test: Generate Config
```bash
agent-corex generate-mcp-config
```
- [ ] Scans all detected AI tools
- [ ] Collects server definitions
- [ ] Creates `~/.agent-corex/mcp.json`
- [ ] Injects environment variables
- [ ] Validates config format

### Verify: Check mcp.json
```bash
cat ~/.agent-corex/mcp.json | jq .mcpServers
```
- [ ] Contains railway, github, supabase, filesystem, redis
- [ ] Each has command, args fields
- [ ] Each has env object with injected variables

### Test: Validate Config
```bash
agent-corex generate-mcp-config
# Should say: ✓ Config is valid
```
- [ ] Config validation passes

---

## Part 5: Gateway Startup

### Test: Start MCP Gateway
```bash
agent-corex serve &
```
- [ ] Starts without errors
- [ ] No port conflicts (uses stdio)
- [ ] Logs "Loaded X tools from local MCP config"
- [ ] Background process starts

### Test: Gateway Responds to JSON-RPC
```bash
# In another terminal:
echo '{"jsonrpc":"2.0","id":1,"method":"initialize"}' | agent-corex serve
```
- [ ] Returns JSON-RPC response
- [ ] Response contains protocolVersion
- [ ] Response contains serverInfo with name

---

## Part 6: Tool Discovery

### Test: List Tools
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | agent-corex serve
```
- [ ] Returns tool list
- [ ] Contains all gateway built-in tools
- [ ] Contains injected MCP tools
- [ ] Tools have name, description, inputSchema

### Test: Tool Filtering
```bash
# No query context = defaults to general query
# Tests: intelligent filtering works
```
- [ ] All built-in tools always included
- [ ] MCP tools ranked/filtered if > 10
- [ ] Filtering uses keyword ranking

---

## Part 7: AI Tool Integration

### Test: Inject into Claude Desktop
1. Check Claude Desktop config:
```bash
cat ~/.claude/claude_desktop_config.json | jq .mcpServers.\"agent-corex\"
```
- [ ] Entry exists
- [ ] command: "agent-corex"
- [ ] args: ["serve"]

2. Restart Claude Desktop
3. Try using a tool in Claude:
```
Use the filesystem tool to create a file:
cat > /tmp/test.txt << EOF
Hello from Claude
EOF
```
- [ ] Claude recognizes filesystem tool
- [ ] Tool executes without errors
- [ ] File is created

### Test: Inject into Cursor
1. Check Cursor config:
```bash
cat ~/.cursor/config/settings.json | jq '.mcpServers."agent-corex"'
```
- [ ] Entry exists with type: "stdio"

2. Restart Cursor
3. Try using a tool in Cursor
- [ ] Cursor recognizes MCP servers
- [ ] Tools work correctly

### Test: Inject into VS Code
1. Check VS Code settings:
```bash
cat ~/.config/Code/User/settings.json | jq '.mcpServers."agent-corex"'
```
- [ ] Entry exists with type: "stdio"

2. Restart VS Code
3. Try using a tool with Claude extension
- [ ] Tools available
- [ ] Tools execute correctly

---

## Part 8: End-to-End Workflows

### Test Workflow 1: Deploy a Todo App
**Prompt in Claude:**
```
Build a simple todo app and deploy it to Railway:
1. Create a Node.js/Express backend with a /todos endpoint
2. Create a React frontend
3. Deploy both to Railway.app

Use the filesystem, railway, and github tools.
```

Expected result:
- [ ] Filesystem tool creates files
- [ ] Railway tool configured
- [ ] GitHub integration works (if enabled)
- [ ] Files saved to workspace

### Test Workflow 2: Setup Database
**Prompt in Claude:**
```
Create a Supabase database with schema:
- users table (id, email, created_at)
- posts table (id, user_id, content, created_at)
- Create foreign key from posts to users

Use the supabase tool.
```

Expected result:
- [ ] Supabase server starts
- [ ] Tables created
- [ ] Foreign keys established

### Test Workflow 3: Multiple Tools
**Prompt in Claude:**
```
1. Create a .env.example file using filesystem
2. List GitHub repos using github tool
3. Setup Redis cache key using redis tool
```

Expected result:
- [ ] All 3 tools available
- [ ] Each executes independently
- [ ] Results combined correctly

---

## Part 9: Diagnostics

### Test: Doctor Command
```bash
agent-corex doctor
```

Check all sections:
- [ ] Python version ✓
- [ ] Dependencies ✓
- [ ] Config file ✓
- [ ] Auth status
- [ ] Backend connectivity
- [ ] API key validity
- [ ] AI Tools injection status
- [ ] PATH checks ✓
- [ ] Pack System ✓
- [ ] MCP Configuration ✓

Expected:
- [ ] All checks pass or show actionable errors
- [ ] No crashes or timeouts

### Test: Status Command
```bash
agent-corex status
```
- [ ] Shows auth state
- [ ] Shows injection status per tool
- [ ] Lists available tools
- [ ] Shows free vs enterprise tools

---

## Part 10: Lazy Server Startup

### Test: Monitor Server Startup
1. Install pack
2. Start gateway with verbose output:
```bash
RUST_LOG=debug agent-corex serve 2>&1 | grep -i "server"
```

3. Call a tool from first server:
```bash
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"tool_from_railway","arguments":{}}}' | agent-corex serve
```

Expected:
- [ ] Railway server NOT started at gateway startup
- [ ] Railway server started when first tool called
- [ ] Tool executes correctly
- [ ] No timeout or crash

---

## Part 11: Error Handling

### Test: Missing API Key
1. Remove OPENAI_API_KEY from .env
2. Call a tool that needs it
3. Expected: Tool fails gracefully with helpful error

- [ ] Error message is clear
- [ ] No crash
- [ ] Gateway continues running

### Test: Invalid Server Definition
1. Manually edit mcp.json to break a server definition
2. Restart gateway
3. Expected: Load warning, gateway still works

- [ ] Error logged to stderr
- [ ] Gateway starts
- [ ] Other tools still available

### Test: Server Crash Recovery
1. Manually kill a running server
2. Call a tool from that server again
3. Expected: Server restarts automatically

- [ ] Server restarted
- [ ] Tool executes
- [ ] No manual intervention needed

---

## Part 12: Performance

### Test: Load Time
```bash
time agent-corex serve
# Measure from start to ready
```
- [ ] Gateway starts in < 2 seconds
- [ ] Load time doesn't increase with pack size

### Test: Tool Execution
```bash
# Time a simple tool call
time echo '{"jsonrpc":"2.0","id":3,"method":"tools/call",...}' | agent-corex serve
```
- [ ] Response time < 500ms for local tools
- [ ] No memory leaks after multiple calls

---

## Test Summary

### Passing Criteria

For a PASS, all of:
- [ ] Parts 1-6 complete successfully
- [ ] All 3 end-to-end workflows (Part 8) pass
- [ ] Doctor command passes all checks (Part 9)
- [ ] No crashes or hangs

### Known Limitations

- Requires valid API keys for cloud services (Railway, Supabase, etc.)
- Backend connectivity not required for local tools
- Some tests may need network access

### Notes

- Run tests in isolation (don't run all 3 workflows in parallel)
- Use `--yes` flag to skip confirmations for automated testing
- Capture all output for debugging if tests fail

---

## Test Execution Template

```bash
#!/bin/bash
set -e

echo "=== Vibe Coding Integration Tests ==="

# Part 1: Install
pip install -e .
agent-corex --version

# Part 2: Pack
agent-corex install-pack vibe_coding_pack --yes

# Part 3: Env
# Manual step: agent-corex setup-env

# Part 4: Config
agent-corex generate-mcp-config

# Part 5: Gateway
timeout 5 agent-corex serve &
sleep 2

# Part 6-7: Tools & Integration
# Manual: Test in Claude Desktop

# Part 9: Diagnostics
agent-corex doctor

echo "=== All tests passed! ==="
```

---

**Last Updated:** 2026-03-28
**Test Coverage:** 11 major sections + 30+ individual tests
