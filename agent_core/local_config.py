"""
Manages ~/.agent-corex/config.json — persistent CLI configuration.

Schema:
  {
    "api_key": "acx_...",
    "base_url": "http://localhost:8000",
    "user": { "user_id": "...", "name": "..." }
  }
"""

import json
import os
import pathlib
import stat

CONFIG_DIR = pathlib.Path.home() / ".agent-corex"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_BASE_URL = "http://localhost:8000"
LOGIN_URL = "http://localhost:8000/login?source=cli"


def _ensure_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    # Restrict permissions so only the owner can read the config (Unix only)
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
    tmp = CONFIG_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    if os.name != "nt":
        tmp.chmod(stat.S_IRUSR | stat.S_IWUSR)
    tmp.replace(CONFIG_FILE)


def get(key: str, default=None):
    return load().get(key, default)


def set_key(key: str, value) -> None:
    data = load()
    data[key] = value
    save(data)


def delete_key(key: str) -> None:
    data = load()
    data.pop(key, None)
    save(data)


def get_api_key() -> str | None:
    return get("api_key")


def get_base_url() -> str:
    return get("base_url", DEFAULT_BASE_URL)


def is_logged_in() -> bool:
    return bool(get_api_key())
