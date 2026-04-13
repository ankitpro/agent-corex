"""
MCPStdioTransport — minimal sync transport layer for MCP stdio servers.

Wraps a subprocess: sends JSON-newline to stdin, reads one JSON-newline from
stdout per request. All I/O is synchronous (call from a thread if needed).
"""

import json
import subprocess
import sys
from typing import Any, Dict


class MCPStdioTransport:
    """Minimal sync wrapper around an MCP server subprocess."""

    def __init__(self, command: str, args: list, env: dict | None = None):
        self.command = command
        self.args = args
        self.env = env
        self.process: subprocess.Popen | None = None

    def start(self) -> None:
        """Spawn the subprocess."""
        import os

        env = os.environ.copy()
        if self.env:
            env.update(self.env)

        cmd = [self.command] + self.args

        if sys.platform.startswith("win"):
            self.process = subprocess.Popen(
                " ".join(cmd),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True,
                env=env,
                bufsize=1,
            )
        else:
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                bufsize=1,
            )

    def send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Write *payload* as JSON to stdin, read one JSON line from stdout."""
        if self.process is None:
            raise RuntimeError("Transport not started — call start() first")
        self.process.stdin.write(json.dumps(payload) + "\n")
        self.process.stdin.flush()
        line = self.process.stdout.readline()
        if not line:
            stderr = self.process.stderr.read() if self.process.stderr else ""
            raise RuntimeError(f"MCP server closed connection. stderr: {stderr}")
        return json.loads(line)

    def stop(self) -> None:
        """Terminate the subprocess."""
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
        self.process = None
