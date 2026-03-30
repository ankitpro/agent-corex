# packages/mcp_server/server.py

import sys
import json
from agent_core.tools import retrieve_tools, execute_tool

def send(response):
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()

for line in sys.stdin:
    request = json.loads(line)

    method = request.get("method")
    params = request.get("params", {})

    if method == "initialize":
        send({
            "id": request["id"],
            "result": {
                "capabilities": {
                    "tools": True
                }
            }
        })

    elif method == "tools/list":
        tools = retrieve_tools("")

        send({
            "id": request["id"],
            "result": {
                "tools": tools
            }
        })

    elif method == "tools/call":
        result = execute_tool(
            params["name"],
            params["arguments"]
        )

        send({
            "id": request["id"],
            "result": result
        })