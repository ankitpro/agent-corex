"""
Capability provider — maps MCP server names to human-readable capability domains.

Used by ToolRouter.tools_list() to inject a capability summary into the
retrieve_tools description so Claude knows what domains are available
before making its first retrieve_tools call.

No external dependencies. Works inside PyInstaller binary.
"""

from __future__ import annotations

# Maps lowercase substrings of server names to human-readable capability labels.
# Evaluated in order; first match wins.
SERVER_CAPABILITY_MAP: list[tuple[str, str]] = [
    ("filesystem", "filesystem"),
    ("github", "github"),
    ("playwright", "browser automation"),
    ("chrome", "browser automation"),
    ("devtools", "browser automation"),
    ("postgresql", "database"),
    ("postgres", "database"),
    ("supabase", "database"),
    ("redis", "cache / redis"),
    ("qdrant", "vector search"),
    ("railway", "railway deployments"),
    ("shell", "shell commands"),
    ("bash", "shell commands"),
    ("docker", "docker"),
    ("kubernetes", "kubernetes"),
    ("slack", "slack"),
    ("notion", "notion"),
    ("linear", "linear"),
    ("jira", "jira"),
    ("stripe", "stripe"),
    ("aws", "aws"),
    ("gcp", "gcp"),
    ("azure", "azure"),
]


def get_capabilities(server_names: list[str]) -> list[str]:
    """
    Map a list of MCP server names to unique capability domain labels.

    Args:
        server_names: List of server names from mcp.json (e.g. ["filesystem", "railway", "github"])

    Returns:
        Deduplicated list of human-readable capability labels,
        in the order they are first encountered.
        Servers that match no known pattern get their own name as the label.
    """
    seen: set[str] = set()
    result: list[str] = []
    for server in server_names:
        lower = server.lower()
        matched = False
        for substring, label in SERVER_CAPABILITY_MAP:
            if substring in lower:
                if label not in seen:
                    seen.add(label)
                    result.append(label)
                matched = True
                break
        if not matched:
            # Unknown server: use the server name itself as a capability label
            if server not in seen:
                seen.add(server)
                result.append(server)
    return result
