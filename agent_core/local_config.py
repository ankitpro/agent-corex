"""
Local configuration management for Agent-CoreX.

Schema (~/.agent-corex/config.json):
  {
    "api_url": "https://api.v2.agent-corex.com",
    "api_key": "acx_..."
  }
"""

from __future__ import annotations

import json
import os
import stat
import tempfile
from pathlib import Path
from typing import Any, Optional

CONFIG_DIR = Path.home() / ".agent-corex"
CONFIG_FILE = CONFIG_DIR / "config.json"
DEFAULT_API_URL = "https://api.v2.agent-corex.com"


def _ensure_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if os.name != "nt":
        CONFIG_DIR.chmod(stat.S_IRWXU)


def load() -> dict:
    """Return parsed config dict; empty dict if file doesn't exist."""
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save(data: dict) -> None:
    """Atomically write config dict to ~/.agent-corex/config.json."""
    _ensure_dir()
    fd, tmp = tempfile.mkstemp(dir=CONFIG_DIR, prefix=".config_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        if os.name != "nt":
            os.chmod(tmp, stat.S_IRUSR | stat.S_IWUSR)
        os.replace(tmp, CONFIG_FILE)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def get(key: str, default: Any = None) -> Any:
    """Get a single config value."""
    return load().get(key, default)


def set_key(key: str, value: Any) -> None:
    """Set a single config key and save."""
    data = load()
    data[key] = value
    save(data)


def delete_key(key: str) -> None:
    """Remove a key from config."""
    data = load()
    data.pop(key, None)
    save(data)


def get_api_url() -> str:
    """Return backend API URL. Env var > config file > default."""
    return (
        os.environ.get("AGENT_COREX_API_URL")
        or get("api_url")
        or DEFAULT_API_URL
    )


def get_api_key() -> Optional[str]:
    """Return API key. Env var AGENT_COREX_API_KEY > config file api_key."""
    return os.environ.get("AGENT_COREX_API_KEY") or get("api_key") or None


def get_auth_header() -> Optional[str]:
    """Return 'Bearer <key>' for backend requests, or None if no key set."""
    key = get_api_key()
    return f"Bearer {key}" if key else None


def is_logged_in() -> bool:
    """Return True if an API key is configured."""
    return bool(get_api_key())


def validate_api_key_format(key: str) -> bool:
    """Basic format check: must start with 'acx_' and be at least 12 chars."""
    return isinstance(key, str) and key.startswith("acx_") and len(key) > 12
