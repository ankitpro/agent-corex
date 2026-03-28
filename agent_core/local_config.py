"""
Manages ~/.agent-corex/config.json — persistent CLI configuration.

Schema:
  {
    "api_key": "acx_...",           # API key (legacy auth, still supported)
    "base_url": "http://localhost:8000",
    "frontend_url": "http://localhost:5173",
    "user": { "user_id": "...", "name": "..." },

    # JWT session (from device-code login flow):
    "access_token":     "eyJ...",   # Supabase JWT
    "refresh_token":    "...",
    "token_expires_at": 1234567890, # Unix timestamp
    "user_email":       "..."
  }
"""

from __future__ import annotations

import json
import os
import pathlib
import stat
import time
from typing import Optional

CONFIG_DIR = pathlib.Path.home() / ".agent-corex"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_FRONTEND_URL = "http://localhost:5173"


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


# ── API key helpers (existing — unchanged) ───────────────────────────────────

def get_api_key() -> Optional[str]:
    return get("api_key")


def get_base_url() -> str:
    return get("base_url", DEFAULT_BASE_URL)


def get_frontend_url() -> str:
    return get("frontend_url", DEFAULT_FRONTEND_URL)


def get_login_url() -> str:
    return f"{get_frontend_url()}/login?source=cli"


# ── JWT session helpers (new — device-code login flow) ───────────────────────

def save_session(
    access_token: str,
    refresh_token: str,
    user_id: str,
    email: str = "",
    expires_at: Optional[int] = None,
) -> None:
    """Persist JWT session tokens to config.json alongside any existing API key."""
    data = load()
    data["access_token"] = access_token
    data["refresh_token"] = refresh_token
    data["token_expires_at"] = expires_at or int(time.time()) + 3600
    if not data.get("user"):
        data["user"] = {}
    data["user"]["user_id"] = user_id
    if email:
        data["user_email"] = email
        data["user"]["name"] = email
    save(data)


def get_access_token() -> Optional[str]:
    """Return the stored JWT access token, or None if missing/expired."""
    data = load()
    token = data.get("access_token")
    if not token:
        return None
    expires_at = data.get("token_expires_at", 0)
    if expires_at and time.time() > expires_at - 60:
        # Expired or about to expire — try refresh
        refreshed = try_refresh_token()
        return refreshed
    return token


def get_refresh_token() -> Optional[str]:
    return get("refresh_token")


def try_refresh_token() -> Optional[str]:
    """
    Attempt to refresh the JWT using the stored refresh_token.
    Updates config on success. Returns new access_token or None.
    """
    data = load()
    refresh_token = data.get("refresh_token")
    if not refresh_token:
        return None

    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY", "")

    # Try to derive Supabase URL from frontend_url if not set via env
    if not supabase_url:
        return None

    try:
        import httpx
        resp = httpx.post(
            f"{supabase_url}/auth/v1/token?grant_type=refresh_token",
            headers={
                "apikey": supabase_anon_key,
                "Content-Type": "application/json",
            },
            json={"refresh_token": refresh_token},
            timeout=10.0,
        )
        if resp.status_code != 200:
            return None
        result = resp.json()
        new_access = result["access_token"]
        new_refresh = result.get("refresh_token", refresh_token)
        expires_in = result.get("expires_in", 3600)

        data["access_token"] = new_access
        data["refresh_token"] = new_refresh
        data["token_expires_at"] = int(time.time()) + expires_in
        save(data)
        return new_access
    except Exception:
        return None


def clear_session() -> None:
    """Remove JWT tokens from config (keeps API key if present)."""
    data = load()
    for key in ("access_token", "refresh_token", "token_expires_at", "user_email"):
        data.pop(key, None)
    save(data)


def get_auth_header() -> Optional[str]:
    """
    Return 'Bearer <token>' for CLI → backend requests.

    Priority:
      1. JWT access token (from device-code login)
      2. API key
    Returns None if neither is available.
    """
    token = get_access_token()
    if token:
        return f"Bearer {token}"
    key = get_api_key()
    if key:
        return f"Bearer {key}"
    return None


# ── Auth state ────────────────────────────────────────────────────────────────

def is_logged_in() -> bool:
    """
    Return True if the user is authenticated via either:
      - A stored API key (acx_...), OR
      - A valid JWT session (access_token + not expired / refreshable)
    """
    if get_api_key():
        return True
    data = load()
    if not data.get("access_token"):
        return False
    expires_at = data.get("token_expires_at", 0)
    if expires_at and time.time() > expires_at - 60:
        # Expired — try refresh
        return try_refresh_token() is not None
    return True


def get_user_email() -> str:
    return get("user_email", "")
