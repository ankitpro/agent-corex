# 📋 File Index

Complete reference of all source files with functions and line ranges.

---

**Last Updated:** 2026-04-14 — v4.1.0

---

## `agent_core/__init__.py`

| Symbol | Line | Description |
|--------|------|-------------|
| `__version__` | 6 | `"4.1.0"` |

---

## `agent_core/local_config.py`

| Symbol | Line | Description |
|--------|------|-------------|
| `CONFIG_DIR` | 18 | `~/.agent-corex/` |
| `CONFIG_FILE` | 19 | `~/.agent-corex/config.json` |
| `DEFAULT_API_URL` | 20 | `"https://api.v2.agent-corex.com"` |
| `load()` | 30 | Load config dict from disk |
| `save(data)` | 38 | Atomically write config to disk |
| `get(key, default)` | 52 | Get a single config value |
| `set_key(key, value)` | 57 | Set a key and save |
| `delete_key(key)` | 63 | Remove a key and save |
| `get_api_url()` | 69 | Returns API URL (env > config > default) |
| `get_api_key()` | 76 | Returns API key (env > config) |
| `get_auth_header()` | 82 | Returns `"Bearer <key>"` or None |
| `is_logged_in()` | 87 | Returns True if key is set |
| `validate_api_key_format(key)` | 92 | Checks `acx_` prefix + min length |

---

## `agent_core/client.py`

| Symbol | Line | Description |
|--------|------|-------------|
| `AgentCoreXError` | 14 | Generic backend error |
| `AuthError` | 18 | HTTP 401 |
| `ConnectionError` | 22 | Cannot connect |
| `TimeoutError` | 26 | Request timeout |
| `AgentCoreXClient.__init__` | 37 | Sets `_base`, `_api_key` |
| `AgentCoreXClient._headers` | 44 | Returns headers dict with Bearer auth |
| `AgentCoreXClient._get` | 49 | Sync GET with error translation |
| `AgentCoreXClient._post` | 63 | Sync POST with error translation |
| `AgentCoreXClient._raise_for_status` | 77 | Translates HTTP errors to exceptions |
| `AgentCoreXClient.execute_query` | 88 | `POST /execute/query` |
| `AgentCoreXClient.health` | 96 | `GET /health` |
| `AgentCoreXClient.get_state` | 101 | `GET /state/{ref}` |
| `AgentCoreXClient.retrieve` | 107 | `GET /retrieve/` |
| `AgentCoreXClient.select` | 115 | `GET /select/` |

---

## `agent_core/cli/main.py`

| Symbol | Line | Description |
|--------|------|-------------|
| `app` | 37 | Main Typer app |
| `config_app` | 43 | `config` subcommand group |
| `_make_client()` | 49 | Creates `AgentCoreXClient` from config |
| `_handle_error(exc)` | 54 | Prints clean error + exits 1 |
| `_render_step_normal(i, step)` | 64 | Single-line step output |
| `_render_debug(response)` | 77 | Full debug output with Rich |
| `run(query, debug)` | 108 | `agent-corex run "<query>"` |
| `config_set(pair)` | 127 | `agent-corex config set key=value` |
| `config_show()` | 142 | `agent-corex config show` |
| `login(key)` | 154 | `agent-corex login --key <key>` |
| `logout()` | 175 | `agent-corex logout` |
| `health()` | 181 | `agent-corex health` |
| `version()` | 192 | `agent-corex version` |
| `serve()` | 197 | `agent-corex serve` → starts MCP gateway |

---

## `agent_core/mcp/transport.py`

| Symbol | Line | Description |
|--------|------|-------------|
| `MCPStdioTransport.__init__` | 19 | command, args, env |
| `MCPStdioTransport.start` | 25 | Spawn subprocess (shell=True on Windows) |
| `MCPStdioTransport.send` | 57 | Write JSON+newline, read one line |
| `MCPStdioTransport.stop` | 69 | Terminate subprocess |

---

## `agent_core/mcp/client.py`

| Symbol | Line | Description |
|--------|------|-------------|
| `_resolve_command` | 27 | npx→npx.cmd on Windows, uvx check |
| `MCPClient.__init__` | 44 | name, command, args, env |
| `MCPClient.start` | 58 | Start transport + MCP initialize handshake |
| `MCPClient._initialize` | 79 | MCP initialize + initialized notification |
| `MCPClient.list_tools` | 116 | `tools/list` RPC |
| `MCPClient.call_tool` | 121 | `tools/call` RPC |
| `MCPClient._send` | 128 | Core JSON-RPC send+receive |
| `MCPClient.stop` | 152 | Terminate transport |

---

## `agent_core/mcp/manager.py`

| Symbol | Line | Description |
|--------|------|-------------|
| `MCPManager.__init__` | 26 | servers dict, tool_map dict |
| `MCPManager.from_local_store` | 33 | Build from ~/.agent-corex/mcp.json |
| `MCPManager.register` | 49 | Manually register a client (tests) |
| `MCPManager.get_tools_for_server` | 55 | Start server + list tools |
| `MCPManager.call_tool` | 65 | Execute tool synchronously |
| `MCPManager.call_tool_async` | 92 | Async wrapper via asyncio.to_thread |
| `MCPManager.shutdown_all` | 103 | Stop all running servers |
| `MCPManager._get_or_start` | 113 | Get client; start if not initialized |

---

## `agent_core/mcp/registry.py`

| Symbol | Line | Description |
|--------|------|-------------|
| `MCPRegistry.__init__` | 19 | Load bundled mcp_registry.json |
| `MCPRegistry.list_all` | 30 | Return all active entries |
| `MCPRegistry.get` | 34 | Get entry by name |
| `MCPRegistry.to_mcp_config_entry` | 38 | Convert to mcp.json format |

---

## `agent_core/mcp/local_store.py`

| Symbol | Line | Description |
|--------|------|-------------|
| `LocalStore.__init__` | 34 | Sets _dir, _mcp_file, _installed_file |
| `LocalStore.load_raw` | 41 | Full mcp.json contents |
| `LocalStore.load_mcp_config` | 48 | mcpServers dict only |
| `LocalStore.save_raw` | 53 | Write mcp.json |
| `LocalStore.add_server` | 58 | Add/update server in mcp.json |
| `LocalStore.remove_server` | 69 | Remove server from mcp.json |
| `LocalStore.list_servers` | 80 | Names of configured servers |
| `LocalStore.load_installed` | 86 | Read installed_servers.json |
| `LocalStore.mark_installed` | 92 | Record install timestamp |
| `LocalStore.mark_removed` | 99 | Remove from installed record |
| `LocalStore.is_installed` | 106 | Check if server is installed |

---

## `agent_core/gateway/gateway_server.py`

| Symbol | Line | Description |
|--------|------|-------------|
| `SERVER_NAME` | 28 | `"agent-corex"` |
| `SERVER_VERSION` | 29 | Imported from `__version__` |
| `PROTOCOL_VERSION` | 30 | `"2024-11-05"` |
| `TOOLS` | 33 | Single-element list: `execute_query` |
| `_ok(id_, result)` | 59 | JSON-RPC success response |
| `_err(id_, code, message)` | 63 | JSON-RPC error response |
| `_write(obj)` | 67 | Write JSON-RPC message to stdout |
| `_format_response(response)` | 73 | Format QueryResponse as readable text |
| `_handle_initialize(id_, params)` | 98 | `initialize` handler |
| `_handle_tools_list(id_, params)` | 110 | `tools/list` handler |
| `_handle_tools_call(id_, params)` | 114 | `tools/call` handler |
| `_dispatch(message)` | 155 | Route JSON-RPC to handler |
| `run()` | 171 | Main stdio read loop |
