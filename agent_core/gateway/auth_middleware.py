"""
Auth Middleware — validates API keys for enterprise tool access.

Reads the API key from ~/.agent-corex/config.json.
Returns structured MCP errors on failure — never crashes, never hides tools.

Error shape (returned to caller, not raised):
  {
    "error": {
      "code": "AUTH_REQUIRED",
      "message": "Login required. Run: agent-corex login"
    }
  }
"""

from __future__ import annotations

from agent_core import local_config


AUTH_ERROR_RESPONSE = {
    "error": {
        "code": "AUTH_REQUIRED",
        "message": (
            "Enterprise tool requires authentication. "
            "Run: agent-corex login  or visit https://agent-corex.ai/login"
        ),
    }
}

INVALID_KEY_RESPONSE = {
    "error": {
        "code": "AUTH_INVALID",
        "message": (
            "API key is invalid or empty. "
            "Run: agent-corex login  to refresh your credentials."
        ),
    }
}


def get_stored_api_key() -> str | None:
    """Read the API key from ~/.agent-corex/config.json."""
    return local_config.get_api_key()


def is_authenticated() -> bool:
    """Return True if a non-empty API key exists in local config."""
    key = get_stored_api_key()
    return bool(key and key.strip())


def check_auth() -> dict | None:
    """
    Validate authentication.

    Returns:
      None   — if authenticated (caller may proceed)
      dict   — error response payload (caller must return this to the MCP client)
    """
    key = get_stored_api_key()
    if not key:
        return AUTH_ERROR_RESPONSE
    if not key.strip():
        return INVALID_KEY_RESPONSE
    return None


def validate_api_key_format(api_key: str) -> bool:
    """Basic format check — real validation happens server-side."""
    return bool(api_key) and api_key.startswith("acx_") and len(api_key) > 8
