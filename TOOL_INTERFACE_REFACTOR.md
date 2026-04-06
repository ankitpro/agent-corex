# Tool Interface Refactor — Retrieval-First Architecture

## Overview

Complete refactoring of the tool interface layer to enforce the **retrieval-first, 3-tool architecture**.

**Core Principle:** LLM sees ONLY 3 tools. Everything else is hidden backend routing.

---

## Architecture

### Before: Problem

```
LLM ──────────────────┐
                      ├─→ github_search
                      ├─→ web_search
                      ├─→ database_query
                      ├─→ filesystem_tool
                      ├─→ ... (many more MCPs)
                      └─→ retrieve_tools, execute_tool

❌ LLM can see everything
❌ No decision-making structure
❌ No optimal routing
❌ Tool selection is fragmented
```

### After: Clean Architecture

```
LLM ──────┬─────────────────────────────────────┐
          │                                     │
          ├─→ get_capabilities()                │
          │   (understand domain)               │
          │                                     │
          ├─→ retrieve_tools(query)             │ Only 3
          │   (find relevant tools)             │ Tools
          │                                     │
          ├─→ execute_tool(name, args)          │
          │   (run selected tool)               │
          │                                     │
          └────────────────┬─────────────────┘
                           │
                   Backend Router
                           │
         ┌─────────────────┼──────────────────┐
         │                 │                  │
         ↓                 ↓                  ↓
      MCP Tools      Internal Tools    External APIs
    (github, etc.)   (search, etc.)    (HTTP calls)

✅ LLM sees exactly 3 tools
✅ Clear 3-step workflow
✅ Backend handles routing
✅ Schema management internal
```

---

## Files Created

### 1. **tool_interface.py** (210 LOC)

Enforces the 3-tool architecture.

**Key Class:** `ToolInterface`

**Responsibilities:**
- Maintain registry of ONLY 3 public tools
- Store MCP tools internally (never expose)
- Store internal tools internally (never expose)
- Provide `tools_list()` that always returns exactly 3 tools
- Validate tool existence and type

**Invariant:**
```python
assert len(tool_interface.tools_list()) == 3
```

**Usage:**
```python
interface = get_tool_interface()

# What LLM sees
public_tools = interface.tools_list()
# Always returns: [get_capabilities, retrieve_tools, execute_tool]

# What backend uses
mcp_tool_schema = interface.get_mcp_tool("deploy")  # Internal only
if interface.is_mcp_tool("deploy"):
    # Route to MCP execution
    pass
```

---

### 2. **tool_executor.py** (280 LOC)

Executes the 3 tools transparently.

**Key Class:** `LocalToolExecutor`

**Responsibilities:**
- Execute get_capabilities
- Execute retrieve_tools
- Execute execute_tool
- Handle input validation
- Route to backend components
- Error handling and logging

**Methods:**
- `execute_get_capabilities()` → list of capabilities
- `execute_retrieve_tools(query, top_k)` → list of relevant tools
- `execute_execute_tool(tool_name, arguments)` → tool result

**Usage:**
```python
executor = LocalToolExecutor(retriever=retriever, router=router)

# Handle LLM tool call
if tool_call.name == "retrieve_tools":
    result = await executor.execute_retrieve_tools(
        query=tool_call.arguments["query"]
    )
    return result

# Backend handles everything, LLM gets clean response
```

---

### 3. **system_prompt_v3.md** (280 LOC)

LLM system prompt enforcing the 3-tool flow.

**Key Sections:**
- Core Principle
- The 3-Tool Flow (detailed walkthrough)
- Critical Rules (✅ DO, ❌ DON'T)
- Example Conversations
- Input Validation
- Error Handling

**Enforces:**
1. Call get_capabilities first
2. Use capabilities to decide domain
3. Call retrieve_tools to find tools
4. Validate required inputs
5. Call execute_tool with complete arguments
6. Never skip steps
7. Never access tools directly

---

## The 3-Tool Contract

### Tool 1: get_capabilities

**Purpose:** Discover available capability domains

**Input:** None (no parameters required)

**Output:**
```json
{
  "capabilities": [
    {
      "name": "github",
      "description": "Manage repositories, commits, and pull requests",
      "example_tasks": [
        "push code",
        "create repository",
        "open pull request"
      ]
    },
    ...
  ]
}
```

**Key Points:**
- No tool names (only capability names)
- No tool schemas
- High-level understanding only
- Used to contextualize user intent

---

### Tool 2: retrieve_tools

**Purpose:** Find the best tools for a query

**Input:**
```json
{
  "query": "string (required) - natural language description",
  "top_k": "integer (optional, 1-10, default 5)"
}
```

**Output:**
```json
{
  "selected_capability": "github",
  "capability_confidence": 0.85,
  "tools": [
    {
      "name": "push-code",
      "description": "Push commits to GitHub repository",
      "required_inputs": ["repository", "branch", "message"],
      "confidence_score": 0.95,
      "category": "version_control",
      "tags": ["git", "push"]
    }
  ]
}
```

**Key Points:**
- Uses hybrid ranking (semantic + keyword + usage + recency)
- Returns top 3-5 tools only
- Includes required_inputs (minimal schema)
- Confidence scores guide LLM decision
- Capability filtering applied if high confidence

---

### Tool 3: execute_tool

**Purpose:** Execute the selected tool

**Input:**
```json
{
  "tool_name": "string (required) - exact name from retrieve_tools",
  "arguments": {
    "repository": "my-repo",
    "branch": "main",
    "message": "fix: bug"
  }
}
```

**Output (Success):**
```json
{
  "success": true,
  "result": {
    "message": "Pushed 3 commits to main",
    "url": "https://github.com/user/repo/commits/main"
  }
}
```

**Output (Error):**
```json
{
  "error": "Missing required input: repository"
}
```

**Key Points:**
- Validates required inputs
- Fetches full schema internally
- Routes to MCP/internal/external backend
- Executes tool
- Tracks usage (for ranking feedback)
- Returns structured error on failure

---

## Integration Points

### 1. Gateway Server (`gateway_server.py`)

**Update needed:**
```python
from agent_core.gateway.tool_interface import get_tool_interface
from agent_core.gateway.tool_executor import LocalToolExecutor

class GatewayServer:
    def __init__(self):
        self.interface = get_tool_interface()
        self.executor = LocalToolExecutor(...)

    def handle_tools_list(self):
        # Only return 3 tools
        return self.interface.tools_list()

    def handle_tool_call(self, tool_name, arguments):
        if tool_name == "get_capabilities":
            return await self.executor.execute_get_capabilities()
        elif tool_name == "retrieve_tools":
            return await self.executor.execute_retrieve_tools(...)
        elif tool_name == "execute_tool":
            return await self.executor.execute_execute_tool(...)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
```

### 2. Tool Router (`tool_router.py`)

**Update needed:**
```python
# Still exists for internal use, but NOT exposed via tools_list
from agent_core.gateway.tool_interface import get_tool_interface

# Register MCP tools internally (not for LLM)
interface = get_tool_interface()
interface.register_mcp_tools(mcp_tools)

# When execute_tool is called, route internally
def route_tool_execution(tool_name, arguments):
    if interface.is_mcp_tool(tool_name):
        # Route to MCP
        return mcp_manager.execute(tool_name, arguments)
    elif interface.is_internal_tool(tool_name):
        # Route to internal
        return internal_router.execute(tool_name, arguments)
    else:
        raise ValueError(f"Tool not found: {tool_name}")
```

### 3. API Endpoints (`/v2/retrieve_tools`, `/v2/execute_tool`)

Already exist and work with the 3-tool architecture.

No changes needed — just ensure they:
1. Call enhanced retriever for retrieve_tools
2. Route properly for execute_tool
3. Track usage data

---

## Validation Checklist

After refactor, verify:

- [ ] `tools_list()` returns EXACTLY 3 tools
- [ ] `get_capabilities` tool is present
- [ ] `retrieve_tools` tool is present
- [ ] `execute_tool` tool is present
- [ ] No MCP tools are in `tools_list()`
- [ ] No internal tools are in `tools_list()`
- [ ] `interface.register_mcp_tools()` works for backend
- [ ] `interface.get_mcp_tool()` works for routing
- [ ] System prompt is loaded with v3 rules
- [ ] Tool executor handles all 3 tools
- [ ] Error handling returns proper error format
- [ ] Usage tracking is called on execution

---

## Testing

### Unit Tests

```python
# Test tool interface
def test_tools_list_returns_exactly_3():
    interface = ToolInterface()
    tools = interface.tools_list()
    assert len(tools) == 3
    assert tools[0]["name"] == "get_capabilities"
    assert tools[1]["name"] == "retrieve_tools"
    assert tools[2]["name"] == "execute_tool"

def test_mcp_tools_not_exposed():
    interface = ToolInterface()
    interface.register_mcp_tools([
        {"name": "deploy", "description": "..."}
    ])
    tools = interface.tools_list()
    assert len(tools) == 3  # Still 3, not 4
    assert interface.is_mcp_tool("deploy")
    assert not interface.is_public_tool("deploy")

# Test tool executor
async def test_execute_retrieve_tools():
    executor = LocalToolExecutor(retriever=mock_retriever)
    result = await executor.execute_retrieve_tools("deploy backend")
    assert result["selected_capability"] in [None, "deployment"]
    assert len(result["tools"]) <= 5

async def test_execute_tool_validation():
    executor = LocalToolExecutor()
    result = await executor.execute_execute_tool("", {})
    assert "error" in result
    assert "tool_name is required" in result["error"]
```

### Integration Test

```python
async def test_full_3_tool_flow():
    interface = get_tool_interface()
    executor = LocalToolExecutor(...)

    # Step 1: Get capabilities
    caps = await executor.execute_get_capabilities()
    assert "capabilities" in caps
    assert len(caps["capabilities"]) > 0

    # Step 2: Retrieve tools
    tools = await executor.execute_retrieve_tools("push code")
    assert tools["selected_capability"] in [None, "github"]
    assert len(tools["tools"]) > 0

    # Step 3: Execute tool
    tool_name = tools["tools"][0]["name"]
    result = await executor.execute_execute_tool(
        tool_name,
        {"repo": "my-repo", "branch": "main"}
    )
    # Should succeed or return clear error
    assert "result" in result or "error" in result
```

---

## Migration Guide

### Step 1: Update Gateway Server

Replace tool registry in `gateway_server.py`:
```python
# OLD
tools = self._load_all_mcp_tools()
# NEW
interface = get_tool_interface()
tools = interface.tools_list()  # Returns exactly 3
```

### Step 2: Update Tool Calling

Replace tool call handler:
```python
# OLD
if tool_name in mcp_tools:
    result = mcp_manager.execute(tool_name, args)
# NEW
executor = LocalToolExecutor(retriever=retriever, router=router)
result = await executor.execute_tool(tool_name, args)
```

### Step 3: Update System Prompt

Load new system prompt:
```python
# OLD
system_prompt = load_prompt("system_prompt_v2.md")
# NEW
system_prompt = load_prompt("system_prompt_v3.md")
```

### Step 4: Test

Run full flow test to verify:
1. Only 3 tools visible
2. get_capabilities works
3. retrieve_tools works
4. execute_tool works
5. MCP tools still execute (internally)

---

## Benefits

✅ **Clean Architecture**
- Single responsibility: each tool has one job
- Backend routing is transparent to LLM
- No tool explosion problem

✅ **Improved Decisions**
- LLM forced to understand capability first
- Forced to find relevant tools before executing
- Forced to validate inputs

✅ **Better Performance**
- Smaller tool set = faster LLM reasoning
- retrieve_tools uses hybrid ranking
- execute_tool can validate early

✅ **Scalability**
- Add 1000 MCP tools → still only 3 visible
- Schema management on backend
- No tool list bloat

✅ **Maintainability**
- Clear contracts for each tool
- Easy to test
- System prompt clearly guides behavior

---

## Troubleshooting

**Issue: LLM sees more than 3 tools**
- Check `tools_list()` in gateway_server
- Verify `ToolInterface.tools_list()` is being called
- Ensure no extra tools are registered elsewhere

**Issue: MCP tools not executing**
- Check `execute_tool` routing logic
- Verify `interface.get_mcp_tool()` finds the tool
- Check tool_router handles the tool

**Issue: retrieve_tools returns wrong tools**
- Check retriever is initialized properly
- Verify Qdrant has tools indexed
- Check capability resolver is working

---

## Summary

| Component | Purpose | Status |
|-----------|---------|--------|
| `tool_interface.py` | Enforce 3-tool architecture | ✅ Created |
| `tool_executor.py` | Execute 3 tools transparently | ✅ Created |
| `system_prompt_v3.md` | Guide LLM behavior | ✅ Created |
| `gateway_server.py` | Integration point | ⏳ Update needed |
| `tool_router.py` | Internal routing | ⏳ Update needed |
| Tests | Validation | ⏳ Create needed |

---

This refactor ensures Agent-CoreX operates with perfect clarity and structure.
