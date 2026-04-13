# 📋 File Index

Complete reference of all source files with functions and line ranges.

---

**Last Updated:** 2026-04-13 — v4.0.0

---

## `agent_core/__init__.py`

| Symbol | Line | Description |
|--------|------|-------------|
| `__version__` | 6 | `"4.0.0"` |

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
