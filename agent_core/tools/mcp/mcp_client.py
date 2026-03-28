import logging
import subprocess
import json
import uuid
import os
import sys
import time
import shutil

logger = logging.getLogger(__name__)


class MCPClient:

    def __init__(self, name, command, args, extra_env=None):
        self.name = name
        self.command = command
        self.args = args
        self.extra_env = extra_env or {}
        self.process = None

    def initialize(self):
        request_id = str(uuid.uuid4())
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "agent-corex", "version": "1.0"},
            },
        }
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()

        while True:
            line = self.process.stdout.readline()
            if not line:
                raise RuntimeError("MCP server closed connection during initialize")
            response = json.loads(line)
            if response.get("id") == request_id:
                break

        # send initialized notification
        notification = {"jsonrpc": "2.0", "method": "initialized", "params": {}}

        self.process.stdin.write(json.dumps(notification) + "\n")
        self.process.stdin.flush()

    def resolve_command(self):
        """Resolve command to full path (e.g., npx → C:\\path\\to\\npx.cmd on Windows)"""
        if shutil.which(self.command):
            return self.command
        # If not found in PATH, return as-is and let subprocess try
        return self.command

    def start(self):
        if self.is_running():
            # Guard: never spawn a second process for the same client instance
            return

        command = self.resolve_command()
        cmd = [command] + self.args
        logger.debug(f"[MCP] spawn: {cmd}")
        env = os.environ.copy()
        # Inject extra environment variables (from .env file or config)
        if self.extra_env:
            env.update(self.extra_env)

        if sys.platform.startswith("win"):
            # Windows needs shell=True for npx.
            # Force UTF-8 encoding — the default cp1252/charmap breaks on servers
            # that emit non-ASCII characters (e.g. emoji in railway-mcp output).
            self.process = subprocess.Popen(
                " ".join(cmd),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
                shell=True,
                bufsize=1,
            )
            time.sleep(1)

            if self.process.poll() is not None:
                err = self.process.stderr.read()
                self.process = None
                raise RuntimeError(f"MCP server failed to start: {err}")
        else:
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
                bufsize=1,
            )

        logger.info(f"[MCP] process started: {self.name}")

    def stop(self):
        """Terminate the MCP server process cleanly."""
        if self.process is None:
            return
        try:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)
        except Exception as e:
            logger.warning(f"[MCP] error stopping {self.name}: {e}")
        finally:
            self.process = None
        logger.info(f"[MCP] process stopped: {self.name}")

    def is_running(self) -> bool:
        """Return True if the server process is currently alive."""
        return self.process is not None and self.process.poll() is None

    def list_tools(self):

        result = self._send_request("tools/list")

        return result.get("tools", [])

    def call_tool(self, tool_name: str, arguments: dict):
        """Call a tool on this MCP server and return the result."""
        result = self._send_request("tools/call", {"name": tool_name, "arguments": arguments})
        return result

    def _send_request(self, method, params=None):

        if self.process is None:
            raise RuntimeError("Server not started")

        request_id = str(uuid.uuid4())

        request = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}}

        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()

        while True:

            line = self.process.stdout.readline()

            if not line:
                err = self.process.stderr.read()
                logger.error(f"[MCP] server stderr: {self.name}\n{err}")
                raise RuntimeError("MCP server closed connection")

            response = json.loads(line)

            if response.get("id") == request_id:
                return response["result"]
