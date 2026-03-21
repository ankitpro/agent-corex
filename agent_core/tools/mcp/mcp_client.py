import subprocess
import json
import uuid
import os
import sys
import time
import shutil


class MCPClient:

    def __init__(self, name, command, args):
        self.name = name
        self.command = command
        self.args = args
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
                "clientInfo": {
                    "name": "agent-core",
                    "version": "1.0"
                }
            }
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
        notification = {
            "jsonrpc": "2.0",
            "method": "initialized",
            "params": {}
        }

        self.process.stdin.write(json.dumps(notification) + "\n")
        self.process.stdin.flush()

    def resolve_command(self):
        """Resolve command to full path (e.g., npx → C:\\path\\to\\npx.cmd on Windows)"""
        if shutil.which(self.command):
            return self.command
        # If not found in PATH, return as-is and let subprocess try
        return self.command

    def start(self):
        command = self.resolve_command()
        cmd = [command] + self.args
        print(f"cmd: {cmd}")
        env = os.environ.copy()

        if sys.platform.startswith("win"):
            # Windows needs shell=True for npx
            self.process = subprocess.Popen(
                " ".join(cmd),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                shell=True,
                bufsize=1
            )
            time.sleep(1)
            
            if self.process.poll() is not None:
                err = self.process.stderr.read()
                raise RuntimeError(f"MCP server failed to start: {err}")
        else:
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                bufsize=1
            )

        print(f"MCP server started: {self.name}")

    
    def list_tools(self):

        result = self._send_request("tools/list")

        return result.get("tools", [])
    
    def _send_request(self, method, params=None):

        if self.process is None:
            raise RuntimeError("Server not started")

        request_id = str(uuid.uuid4())

        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {}
        }

        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()

        while True:

            line = self.process.stdout.readline()

            if not line:
                err = self.process.stderr.read()
                print("MCP SERVER ERROR:")
                print(err)
                raise RuntimeError("MCP server closed connection")

            response = json.loads(line)

            if response.get("id") == request_id:
                return response["result"]
