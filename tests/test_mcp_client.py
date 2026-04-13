"""Tests for agent_core.mcp.client — mocks subprocess.Popen."""

import json
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from agent_core.mcp.client import MCPClient, _resolve_command

# ── _resolve_command ──────────────────────────────────────────────────────────


def test_resolve_npx_on_non_windows():
    with patch("sys.platform", "linux"):
        assert _resolve_command("npx") == "npx"


def test_resolve_npx_on_windows():
    with patch("sys.platform", "win32"):
        assert _resolve_command("npx") == "npx.cmd"


def test_resolve_python():
    assert _resolve_command("python") == "python"


def test_resolve_uvx_found():
    with patch("shutil.which", return_value="/usr/bin/uvx"):
        assert _resolve_command("uvx") == "uvx"


def test_resolve_uvx_not_found():
    with patch("shutil.which", return_value=None):
        with pytest.raises(RuntimeError, match="uvx not found"):
            _resolve_command("uvx")


# ── MCPClient ─────────────────────────────────────────────────────────────────


def _make_mock_process(stdout_lines: list[str]):
    """Build a mock Popen process with preset stdout lines."""
    process = MagicMock()
    process.poll.return_value = None
    stdout = iter(stdout_lines)
    process.stdout.readline.side_effect = lambda: next(stdout, "")
    process.stdin.write = MagicMock()
    process.stdin.flush = MagicMock()
    process.stderr.read.return_value = ""
    return process


def _init_response(req_id: str) -> str:
    return json.dumps({"jsonrpc": "2.0", "id": req_id, "result": {"protocolVersion": "2024-11-05"}})


def test_list_tools_success():
    tools_response = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": "TOOLS_ID",
            "result": {
                "tools": [
                    {"name": "list_projects", "description": "List projects"},
                    {"name": "create_project", "description": "Create a project"},
                ]
            },
        }
    )

    with (
        patch("agent_core.mcp.client._resolve_command", return_value="npx"),
        patch("agent_core.mcp.transport.subprocess.Popen") as mock_popen,
        patch("sys.platform", "linux"),
        patch("time.sleep"),
    ):

        # Build a process that streams: init response, then tools/list response
        # We need to control what readline() returns based on the call context
        process = MagicMock()
        process.poll.return_value = None
        process.stderr.read.return_value = ""

        # stdin.write captures the request_id from the first write (initialize)
        written_ids = []

        def capture_write(data):
            try:
                msg = json.loads(data.strip())
                if "id" in msg:
                    written_ids.append(msg["id"])
            except Exception:
                pass

        process.stdin.write.side_effect = capture_write
        process.stdin.flush = MagicMock()

        # stdout provides the init response first, then tools/list response
        call_count = [0]

        def readline_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                # Return initialize response using the captured id
                req_id = written_ids[0] if written_ids else "dummy"
                return json.dumps({"jsonrpc": "2.0", "id": req_id, "result": {}}) + "\n"
            elif call_count[0] == 2:
                # Return tools/list response using the second id
                req_id = written_ids[1] if len(written_ids) > 1 else "dummy2"
                return (
                    json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "id": req_id,
                            "result": {
                                "tools": [{"name": "list_projects", "description": "List projects"}]
                            },
                        }
                    )
                    + "\n"
                )
            return ""

        process.stdout.readline.side_effect = readline_side_effect
        mock_popen.return_value = process

        client = MCPClient("railway", "npx", ["-y", "@railway/mcp-server"])
        client.start()
        tools = client.list_tools()

    assert len(tools) == 1
    assert tools[0]["name"] == "list_projects"


def test_call_tool_success():
    with (
        patch("agent_core.mcp.client._resolve_command", return_value="npx"),
        patch("agent_core.mcp.transport.subprocess.Popen") as mock_popen,
        patch("sys.platform", "linux"),
        patch("time.sleep"),
    ):

        process = MagicMock()
        process.poll.return_value = None
        process.stderr.read.return_value = ""

        written_ids = []

        def capture_write(data):
            try:
                msg = json.loads(data.strip())
                if "id" in msg:
                    written_ids.append(msg["id"])
            except Exception:
                pass

        process.stdin.write.side_effect = capture_write
        process.stdin.flush = MagicMock()

        call_count = [0]

        def readline():
            call_count[0] += 1
            if call_count[0] == 1:
                req_id = written_ids[0] if written_ids else "x"
                return json.dumps({"jsonrpc": "2.0", "id": req_id, "result": {}}) + "\n"
            elif call_count[0] == 2:
                req_id = written_ids[1] if len(written_ids) > 1 else "y"
                return (
                    json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "id": req_id,
                            "result": {"content": "project-a\nproject-b"},
                        }
                    )
                    + "\n"
                )
            return ""

        process.stdout.readline.side_effect = readline
        mock_popen.return_value = process

        client = MCPClient("railway", "npx", ["-y", "@railway/mcp-server"])
        client.start()
        result = client.call_tool("list_projects", {})

    assert result == {"content": "project-a\nproject-b"}


def test_stop_terminates_process():
    with (
        patch("agent_core.mcp.client._resolve_command", return_value="npx"),
        patch("agent_core.mcp.transport.subprocess.Popen") as mock_popen,
        patch("sys.platform", "linux"),
        patch("time.sleep"),
    ):

        process = MagicMock()
        process.poll.return_value = None
        process.stderr.read.return_value = ""

        written_ids = []

        def capture_write(data):
            try:
                msg = json.loads(data.strip())
                if "id" in msg:
                    written_ids.append(msg["id"])
            except Exception:
                pass

        process.stdin.write.side_effect = capture_write
        process.stdin.flush = MagicMock()

        def readline():
            req_id = written_ids[0] if written_ids else "x"
            return json.dumps({"jsonrpc": "2.0", "id": req_id, "result": {}}) + "\n"

        process.stdout.readline.side_effect = readline
        mock_popen.return_value = process

        client = MCPClient("railway", "npx", ["-y", "@railway/mcp-server"])
        client.start()
        client.stop()

    process.terminate.assert_called_once()
