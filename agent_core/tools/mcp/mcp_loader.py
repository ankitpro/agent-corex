from __future__ import annotations
import json
import logging
import pathlib
import threading
import time
from .mcp_client import MCPClient
from .mcp_manager import MCPManager

logger = logging.getLogger(__name__)

TOOLS_CACHE_FILE = pathlib.Path.home() / ".agent-corex" / "tools_cache.json"
REGISTRY_FILE = pathlib.Path.home() / ".agent-corex" / "registry.json"
SELF_COMMANDS = {"agent-corex", "agent_corex"}


class MCPLoader:

    def __init__(self, config_path):
        self.config_path = config_path
        self._env_cache = None

    def _load_dotenv(self) -> dict:
        """Load environment variables from ~/.agent-corex/.env"""
        if self._env_cache is not None:
            return self._env_cache

        env_dict = {}
        env_file = pathlib.Path.home() / ".agent-corex" / ".env"

        if env_file.exists():
            try:
                with open(env_file) as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            key, value = line.split("=", 1)
                            env_dict[key.strip()] = value.strip()
                logger.info(f"[MCP] loaded {len(env_dict)} env vars from {env_file}")
            except Exception as e:
                logger.warning(f"[MCP] failed to load .env: {e}")

        self._env_cache = env_dict
        return env_dict

    def _parse_config(self) -> tuple[dict, dict]:
        """Parse mcp.json and env, return (config, env_dict)."""
        with open(self.config_path) as f:
            config = json.load(f)
        return config, self._load_dotenv()

    def _build_server_config(self, name: str, server: dict, env_dict: dict) -> dict | None:
        """Build a resolved server config dict, or None if it should be skipped."""
        cmd = server.get("command", "")
        if cmd in SELF_COMMANDS or name == "agent-corex":
            logger.info(f"[MCP] skipping self-referential server: {name!r}")
            return None

        merged_env = dict(env_dict)
        if "env" in server and isinstance(server["env"], dict):
            resolved_server_env = {
                k: (
                    env_dict.get(v[2:-1], v)
                    if (isinstance(v, str) and v.startswith("${") and v.endswith("}"))
                    else v
                )
                for k, v in server["env"].items()
            }
            merged_env.update(resolved_server_env)

        resolved_args = [
            merged_env.get(a[2:-1], a) if (a.startswith("${") and a.endswith("}")) else a
            for a in server.get("args", [])
        ]

        return {
            "name": name,
            "command": server["command"],
            "args": resolved_args,
            "env": merged_env if merged_env else None,
        }

    # ------------------------------------------------------------------ #
    # Fast startup path (used by gateway)                                 #
    # ------------------------------------------------------------------ #

    def load_with_cache(self, add_tools_callback=None) -> MCPManager:
        """
        Fast startup: returns immediately using cached tool metadata.

        1. Registers all server configs from mcp.json (instant)
        2. Populates tool metadata from tools_cache.json (instant, <10ms)
        3. Starts a background thread to rediscover tools and refresh cache
           — calls add_tools_callback(tools) when discovery updates the list

        This ensures the gateway always starts within milliseconds, never
        hitting the 30-second MCP connection timeout.
        """
        config, env_dict = self._parse_config()
        manager = MCPManager(lazy_load=True)

        # Step 1: register configs immediately (no processes spawned)
        for name, server in config.get("mcpServers", {}).items():
            server_config = self._build_server_config(name, server, env_dict)
            if server_config:
                manager.register_server_config(name, server_config)

        # Step 2: load tool metadata from cache (instant)
        cached_tools_by_server = self._read_cache()
        if cached_tools_by_server:
            for server_name, tools in cached_tools_by_server.items():
                manager.register_tools(server_name, tools)
            total = sum(len(t) for t in cached_tools_by_server.values())
            logger.info(
                f"[MCP] loaded {total} tools from cache for {len(cached_tools_by_server)} servers"
            )
        else:
            logger.info(
                "[MCP] no tools cache found — MCP tools will appear after background discovery"
            )

        # Step 3: background discovery to refresh cache
        thread = threading.Thread(
            target=self._background_discover,
            args=(config, env_dict, add_tools_callback),
            daemon=True,
            name="mcp-discovery",
        )
        thread.start()

        return manager

    # ------------------------------------------------------------------ #
    # Registry loading (servers added via CLI `mcp add`)                  #
    # ------------------------------------------------------------------ #

    def load_registry_servers(
        self, manager: MCPManager, add_tools_callback=None
    ) -> list[str]:
        """
        Load MCP servers from ~/.agent-corex/registry.json into the manager.

        Registry servers are those added via ``agent-corex mcp add <name>``.
        Servers already registered from mcp.json are skipped (mcp.json wins).

        Returns list of server names that were newly registered.
        """
        if not REGISTRY_FILE.exists():
            logger.info("[MCP] no registry.json found — skipping registry servers")
            return []

        try:
            data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"[MCP] failed to read registry.json: {e}")
            return []

        env_dict = self._load_dotenv()
        registered: list[str] = []

        for name, server in data.get("mcp_servers", {}).items():
            # mcp.json takes precedence — skip duplicates
            if name in manager.server_configs:
                logger.debug(
                    f"[MCP] registry server {name!r} already loaded from mcp.json — skipping"
                )
                continue

            server_config = self._build_server_config(name, server, env_dict)
            if server_config:
                manager.register_server_config(name, server_config)
                registered.append(name)
                logger.info(f"[MCP] registered from registry: {name}")

        if not registered:
            return []

        logger.info(
            f"[MCP] loaded {len(registered)} servers from registry.json: "
            f"{', '.join(registered)}"
        )

        # Populate tool metadata from cache for registry servers
        cached = self._read_cache()
        for name in registered:
            if name in cached:
                tools = cached[name]
                manager.register_tools(name, tools)
                if add_tools_callback and tools:
                    stamped = []
                    for t in tools:
                        t_copy = dict(t)
                        t_copy["server"] = name
                        stamped.append(t_copy)
                    try:
                        add_tools_callback(name, stamped)
                    except Exception as e:
                        logger.warning(f"[MCP] registry callback error for {name}: {e}")

        # Background discovery for servers with no cached tools
        uncached = [n for n in registered if n not in cached]
        if uncached:
            raw_data = data.get("mcp_servers", {})
            registry_config = {
                "mcpServers": {name: raw_data[name] for name in uncached}
            }
            thread = threading.Thread(
                target=self._background_discover,
                args=(registry_config, env_dict, add_tools_callback),
                daemon=True,
                name="mcp-registry-discovery",
            )
            thread.start()
            logger.info(
                f"[MCP] background discovery started for {len(uncached)} "
                f"uncached registry servers: {', '.join(uncached)}"
            )

        return registered

    def _read_cache(self) -> dict[str, list]:
        """Read tools cache. Returns {server_name: [tool_dicts]} or {}."""
        if not TOOLS_CACHE_FILE.exists():
            return {}
        try:
            data = json.loads(TOOLS_CACHE_FILE.read_text(encoding="utf-8"))
            return {k: v.get("tools", []) for k, v in data.get("servers", {}).items()}
        except Exception as e:
            logger.warning(f"[MCP] cache read failed: {e}")
            return {}

    def _write_cache(self, servers_tools: dict[str, list]) -> None:
        """Write tools cache to disk."""
        try:
            data = {
                "timestamp": time.time(),
                "servers": {name: {"tools": tools} for name, tools in servers_tools.items()},
            }
            TOOLS_CACHE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
            logger.info(
                f"[MCP] tools cache written ({sum(len(t) for t in servers_tools.values())} tools)"
            )
        except Exception as e:
            logger.warning(f"[MCP] cache write failed: {e}")

    def _background_discover(self, config: dict, env_dict: dict, add_tools_callback) -> None:
        """
        Background thread: discover tools from all servers, write cache,
        notify gateway of new/updated tools via callback.
        """
        logger.info("[MCP] background discovery started")
        servers_tools: dict[str, list] = {}

        for name, server in config.get("mcpServers", {}).items():
            server_config = self._build_server_config(name, server, env_dict)
            if not server_config:
                continue

            temp_client = None
            try:
                temp_client = MCPClient(
                    name,
                    server_config["command"],
                    server_config["args"],
                    extra_env=server_config.get("env"),
                )
                logger.info(f"[MCP] start_attempt (bg discovery): {name}")
                temp_client.start()
                temp_client.initialize()
                time.sleep(0.1)
                tools = temp_client.list_tools()
                servers_tools[name] = tools
                logger.info(f"[MCP] bg discovered {len(tools)} tools from {name}")

                # Notify gateway so tools/list reflects new tools immediately
                if add_tools_callback and tools:
                    try:
                        add_tools_callback(name, tools)
                    except Exception as e:
                        logger.warning(f"[MCP] callback error for {name}: {e}")

            except Exception as e:
                logger.warning(f"[MCP] bg discovery failed for {name!r}: {e}")
            finally:
                if temp_client is not None:
                    temp_client.stop()

        if servers_tools:
            self._write_cache(servers_tools)

        logger.info("[MCP] background discovery complete")

    # ------------------------------------------------------------------ #
    # Legacy synchronous path (kept for non-gateway use cases)            #
    # ------------------------------------------------------------------ #

    def load(self, lazy_load: bool = True):
        """
        Synchronous load — discovers all server tools before returning.
        Use load_with_cache() for the gateway to avoid startup timeouts.
        """
        config, env_dict = self._parse_config()
        manager = MCPManager(lazy_load=lazy_load)

        for name, server in config.get("mcpServers", {}).items():
            server_config = self._build_server_config(name, server, env_dict)
            if not server_config:
                continue

            try:
                if lazy_load:
                    manager.register_server_config(name, server_config)

                    temp_client = None
                    try:
                        temp_client = MCPClient(
                            name,
                            server_config["command"],
                            server_config["args"],
                            extra_env=server_config.get("env"),
                        )
                        logger.info(f"[MCP] start_attempt (discovery): {name}")
                        temp_client.start()
                        temp_client.initialize()
                        time.sleep(0.1)
                        tools = temp_client.list_tools()
                        manager.register_tools(name, tools)
                        logger.info(f"[MCP] discovered {len(tools)} tools from {name}")
                    except Exception as e:
                        logger.warning(f"[MCP] could not discover tools for {name!r}: {e}")
                    finally:
                        if temp_client is not None:
                            temp_client.stop()

                else:
                    client = MCPClient(
                        name,
                        server_config["command"],
                        server_config["args"],
                        extra_env=server_config.get("env"),
                    )
                    logger.info(f"[MCP] start_attempt (eager): {name}")
                    client.start()
                    client.initialize()
                    time.sleep(0.5)
                    tools = client.list_tools()
                    manager.register_server(name, client)
                    manager.register_tools(name, tools)
                    logger.info(f"[MCP] started (eager): {name} with {len(tools)} tools")

            except Exception as e:
                logger.error(f"[MCP] failed to load server {name!r}: {e}")
                continue

        return manager
