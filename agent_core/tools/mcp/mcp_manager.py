"""MCPManager — server lifecycle management with process safety.

Guarantees:
  - Each server has exactly ONE running process at any time
  - Concurrent start requests are serialized via per-server locks
  - Exponential backoff prevents restart loops (max 5 restarts)
  - LRU eviction keeps running servers <= MAX_RUNNING_SERVERS (10)
  - Watchdog kills all servers if total processes exceed KILL_THRESHOLD (50)
"""

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)

MAX_RUNNING_SERVERS = 10
MAX_RESTART_COUNT = 5
KILL_THRESHOLD = 50  # watchdog kills all if exceeded


class MCPManager:
    """
    Manages MCP server lifecycle.
    Supports lazy loading: servers only start when their tools are first used.
    """

    def __init__(self, lazy_load: bool = True):
        self.tools: list[dict] = []
        self.lazy_load = lazy_load
        self.server_configs: dict[str, dict] = {}

        # State machine per server
        # status: "stopped" | "starting" | "running" | "failed"
        self._states: dict[str, dict[str, Any]] = {}

        # One lock per server — prevents duplicate starts under concurrency
        self._locks: dict[str, threading.Lock] = defaultdict(threading.Lock)

        # Protects mutations to _states dict structure
        self._global_lock = threading.Lock()

    # ------------------------------------------------------------------ #
    # Registration                                                         #
    # ------------------------------------------------------------------ #

    def register_server_config(self, name: str, config: dict) -> None:
        """Store server config for lazy loading."""
        self.server_configs[name] = config
        with self._global_lock:
            if name not in self._states:
                self._states[name] = {
                    "status": "stopped",
                    "client": None,
                    "last_started": None,
                    "last_used": None,
                    "restart_count": 0,
                }
        logger.debug(f"[MCP] registered_config: {name}")

    def register_tools(self, server: str, tools: list[dict]) -> None:
        """Register tool metadata for a server."""
        for tool in tools:
            self.tools.append(
                {
                    "server": server,
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "inputSchema": tool.get("inputSchema") or tool.get("input_schema") or {},
                }
            )

    def register_server(self, name: str, client: Any) -> None:
        """Register an already-started client (used by eager loading)."""
        with self._global_lock:
            self._states[name] = {
                "status": "running",
                "client": client,
                "last_started": time.time(),
                "last_used": time.time(),
                "restart_count": 0,
            }
        logger.info(f"[MCP] registered_running: {name}")

    # ------------------------------------------------------------------ #
    # Queries                                                              #
    # ------------------------------------------------------------------ #

    def get_all_tools(self) -> list[dict]:
        return self.tools

    def get_tools(self) -> list[dict]:
        return self.tools

    def is_server_active(self, server_name: str) -> bool:
        state = self._states.get(server_name, {})
        if state.get("status") != "running":
            return False
        client = state.get("client")
        if client is None:
            return False
        # Verify the underlying process is still alive
        if hasattr(client, "is_running") and not client.is_running():
            with self._global_lock:
                self._states[server_name]["status"] = "stopped"
                self._states[server_name]["client"] = None
            logger.warning(f"[MCP] process_died: {server_name}")
            return False
        return True

    def get_active_servers(self) -> dict:
        return {
            name: state["client"]
            for name, state in self._states.items()
            if state.get("status") == "running" and state.get("client") is not None
        }

    def get_client(self, server_name: str) -> Any | None:
        """Return the running client for a server, or None."""
        state = self._states.get(server_name, {})
        if state.get("status") == "running":
            return state.get("client")
        return None

    def _count_running(self) -> int:
        return sum(1 for s in self._states.values() if s.get("status") == "running")

    # ------------------------------------------------------------------ #
    # Lifecycle                                                            #
    # ------------------------------------------------------------------ #

    def ensure_server_running(self, server_name: str) -> bool:
        """
        Ensure a server is running, starting it if needed.

        Thread-safe: acquires per-server lock to prevent duplicate starts.
        Returns True if running, False if server could not be started.
        """
        # Run watchdog before potentially adding another server
        self.watchdog_check()

        lock = self._locks[server_name]
        with lock:
            # Re-check inside lock — another thread may have just started it
            if self.is_server_active(server_name):
                with self._global_lock:
                    self._states[server_name]["last_used"] = time.time()
                logger.debug(f"[MCP] already_running: {server_name}")
                return True

            state = self._states.get(server_name)
            if state is None:
                logger.error(f"[MCP] unknown_server: {server_name}")
                return False

            if state["status"] == "starting":
                # Another thread grabbed the lock first and is starting it
                logger.debug(f"[MCP] already_starting: {server_name}")
                return False

            if state["status"] == "failed":
                restart_count = state["restart_count"]
                if restart_count >= MAX_RESTART_COUNT:
                    logger.error(
                        f"[MCP] max_restarts_exceeded: {server_name} "
                        f"({restart_count} attempts) — disabled"
                    )
                    return False
                delay = min(2**restart_count, 60)
                logger.warning(
                    f"[MCP] restart_backoff: {server_name} "
                    f"(attempt {restart_count + 1}, waiting {delay}s)"
                )
                time.sleep(delay)

            # Enforce cap — evict least-recently-used server if at limit
            if self._count_running() >= MAX_RUNNING_SERVERS:
                self._evict_lru(exclude=server_name)

            # Mark as starting (other threads will see this and bail)
            with self._global_lock:
                self._states[server_name]["status"] = "starting"

            logger.info(f"[MCP] start_attempt: {server_name}")

            config = self.server_configs.get(server_name)
            if config is None:
                logger.error(f"[MCP] no_config: {server_name}")
                with self._global_lock:
                    self._states[server_name]["status"] = "failed"
                return False

            try:
                from agent_core.tools.mcp.mcp_client import MCPClient

                client = MCPClient(
                    config["name"],
                    config["command"],
                    config["args"],
                    extra_env=config.get("env"),
                )
                client.start()
                client.initialize()

                with self._global_lock:
                    self._states[server_name].update(
                        {
                            "status": "running",
                            "client": client,
                            "last_started": time.time(),
                            "last_used": time.time(),
                        }
                    )

                logger.info(f"[MCP] started: {server_name}")
                return True

            except Exception as e:
                with self._global_lock:
                    self._states[server_name]["status"] = "failed"
                    self._states[server_name]["restart_count"] += 1
                logger.error(f"[MCP] failed: {server_name} — {e}")
                return False

    def _evict_lru(self, exclude: str = "") -> None:
        """Stop the least-recently-used running server to free a slot."""
        running = [
            (name, state)
            for name, state in self._states.items()
            if state.get("status") == "running" and name != exclude
        ]
        if not running:
            return
        lru_name, _ = min(running, key=lambda x: x[1].get("last_used") or 0)
        logger.warning(f"[MCP] evicting_lru: {lru_name}")
        self._stop_server(lru_name)

    def _stop_server(self, server_name: str) -> None:
        """Stop a server and reset its state to stopped."""
        state = self._states.get(server_name, {})
        client = state.get("client")
        if client is not None:
            try:
                client.stop()
            except Exception as e:
                logger.warning(f"[MCP] stop_error: {server_name} — {e}")
        with self._global_lock:
            if server_name in self._states:
                self._states[server_name]["status"] = "stopped"
                self._states[server_name]["client"] = None
        logger.info(f"[MCP] stopped: {server_name}")

    # ------------------------------------------------------------------ #
    # Health check                                                         #
    # ------------------------------------------------------------------ #

    def health_check_server(self, server_name: str) -> bool:
        """
        Check if a server is healthy by inspecting its process state.
        Does NOT spawn a new process — use ensure_server_running() for that.
        """
        if not self.is_server_active(server_name):
            logger.warning(f"[MCP] health_check_failed: {server_name} (not active)")
            return False

        state = self._states.get(server_name, {})
        client = state.get("client")
        if client is None:
            return False

        # is_running() polls the process without spawning anything new
        if hasattr(client, "is_running") and not client.is_running():
            with self._global_lock:
                self._states[server_name]["status"] = "failed"
                self._states[server_name]["client"] = None
            logger.warning(f"[MCP] health_check_failed: {server_name} (process exited)")
            return False

        return True

    # ------------------------------------------------------------------ #
    # Watchdog + shutdown                                                  #
    # ------------------------------------------------------------------ #

    def watchdog_check(self) -> None:
        """
        Safety watchdog: if running servers exceed KILL_THRESHOLD, kill all.
        Prevents runaway process accumulation.
        """
        total = self._count_running()
        if total > KILL_THRESHOLD:
            logger.error(
                f"[MCP] watchdog_triggered: {total} running servers (limit {KILL_THRESHOLD}) "
                "— killing all and resetting"
            )
            self.shutdown()

    def shutdown(self) -> None:
        """Stop all running MCP servers cleanly."""
        logger.info("[MCP] shutdown: stopping all servers")
        for server_name in list(self._states.keys()):
            if self._states[server_name].get("status") == "running":
                self._stop_server(server_name)

    # ------------------------------------------------------------------ #
    # Legacy compatibility (properties used by older code)                #
    # ------------------------------------------------------------------ #

    @property
    def servers(self) -> dict:
        """Legacy compat: dict of name → client for running servers."""
        return self.get_active_servers()

    @property
    def active_servers(self) -> dict:
        """Legacy compat: alias for get_active_servers()."""
        return self.get_active_servers()
