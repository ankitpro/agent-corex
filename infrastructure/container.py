"""
infrastructure/container.py

Centralised DI container for all singleton service lifetimes.
Replaces scattered module-level globals across packages/vector/ and agent_core/.

All services use:
  - Lazy initialization (created on first access)
  - Thread-safe guards (threading.Lock per resource)
  - Idempotent access (repeated calls return same instance)
  - Graceful degradation (optional services like Redis return None if env vars absent)
"""

from __future__ import annotations

import logging
import os
import threading
from typing import Any, Optional

logger = logging.getLogger(__name__)


class Container:
    """
    Owns and lazily initialises all long-lived service clients.

    Services managed:
      qdrant_client    — QdrantClient (QDRANT_URL, QDRANT_API_KEY)
      openai_client    — openai.OpenAI (OPENAI_API_KEY)
      redis_bytes      — redis.Redis(decode_responses=False) — for embeddings cache
      redis_str        — redis.Redis(decode_responses=True)  — for retriever/enricher cache
      supabase_client  — supabase.Client (SUPABASE_URL, SUPABASE_KEY)
      tool_registry    — ToolRegistry()
      tool_interface   — ToolInterface()

    Thread safety: One Lock per resource to allow concurrent initialization of different services.
    """

    def __init__(self) -> None:
        # Qdrant
        self._qdrant_client: Optional[Any] = None
        self._qdrant_lock = threading.Lock()

        # OpenAI
        self._openai_client: Optional[Any] = None
        self._openai_lock = threading.Lock()

        # Redis — two clients with different decode_responses settings
        self._redis_bytes: Optional[Any] = None
        self._redis_bytes_lock = threading.Lock()

        self._redis_str: Optional[Any] = None
        self._redis_str_lock = threading.Lock()

        # Supabase
        self._supabase_client: Optional[Any] = None
        self._supabase_lock = threading.Lock()

        # ToolRegistry
        self._tool_registry: Optional[Any] = None
        self._tool_registry_lock = threading.Lock()

        # ToolInterface
        self._tool_interface: Optional[Any] = None
        self._tool_interface_lock = threading.Lock()

    # ── Qdrant ────────────────────────────────────────────────────────────────

    def get_qdrant_client(self) -> Any:
        """Get or create the Qdrant client singleton. Thread-safe.

        Raises KeyError if QDRANT_URL or QDRANT_API_KEY env vars are missing.
        """
        with self._qdrant_lock:
            if self._qdrant_client is not None:
                return self._qdrant_client

            from qdrant_client import QdrantClient

            url = os.environ["QDRANT_URL"]  # Will raise KeyError if missing
            api_key = os.environ["QDRANT_API_KEY"]  # Will raise KeyError if missing

            self._qdrant_client = QdrantClient(url=url, api_key=api_key)
            logger.info(f"Qdrant client initialised → {url}")
            return self._qdrant_client

    # ── OpenAI ────────────────────────────────────────────────────────────────

    def get_openai_client(self) -> Any:
        """Get or create the OpenAI client singleton. Thread-safe.

        Raises KeyError if OPENAI_API_KEY env var is missing.
        """
        with self._openai_lock:
            if self._openai_client is not None:
                return self._openai_client

            from openai import OpenAI

            api_key = os.environ["OPENAI_API_KEY"]  # Will raise KeyError if missing
            self._openai_client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialised")
            return self._openai_client

    # ── Redis (two variants) ──────────────────────────────────────────────────
    #
    # Why two Redis clients?
    # - embeddings.py uses decode_responses=False (gets bytes)
    # - retriever.py and llm_enricher.py use decode_responses=True (gets str)
    #
    # Both json.loads() calls work with either type, but existing code relies
    # on the specific decode setting it was written against. Providing two
    # distinct clients avoids silent behavior changes.
    #
    # If a future refactor wants to collapse to one client, it would require
    # embeddings.py to call .decode() or rely on json.loads() accepting bytes.
    # Outside scope of this task.

    def get_redis_bytes(self) -> Optional[Any]:
        """Get or create Redis client with decode_responses=False.

        Used by: embeddings.py (stores/reads raw bytes via json.loads(bytes))

        Returns None gracefully if REDIS_URL env var is missing or connection fails.
        """
        with self._redis_bytes_lock:
            if self._redis_bytes is not None:
                return self._redis_bytes

            redis_url = os.getenv("REDIS_URL")
            if not redis_url:
                logger.debug("REDIS_URL not set; Redis (bytes) unavailable")
                return None

            try:
                import redis

                client = redis.from_url(redis_url, decode_responses=False)
                client.ping()
                self._redis_bytes = client
                logger.info("Redis (bytes) connected")
                return self._redis_bytes
            except Exception as e:
                logger.warning(f"Redis (bytes) unavailable: {e}")
                return None

    def get_redis_str(self) -> Optional[Any]:
        """Get or create Redis client with decode_responses=True.

        Used by: retriever.py, llm_enricher.py (read str via json.loads(str))

        Returns None gracefully if REDIS_URL env var is missing or connection fails.
        """
        with self._redis_str_lock:
            if self._redis_str is not None:
                return self._redis_str

            redis_url = os.getenv("REDIS_URL")
            if not redis_url:
                logger.debug("REDIS_URL not set; Redis (str) unavailable")
                return None

            try:
                import redis

                client = redis.from_url(redis_url, decode_responses=True)
                client.ping()
                self._redis_str = client
                logger.info("Redis (str) connected")
                return self._redis_str
            except Exception as e:
                logger.warning(f"Redis (str) unavailable: {e}")
                return None

    # ── Supabase ──────────────────────────────────────────────────────────────

    def get_supabase_client(self) -> Any:
        """Get or create the Supabase client singleton. Thread-safe.

        Raises KeyError if SUPABASE_URL or SUPABASE_KEY env vars are missing.
        """
        with self._supabase_lock:
            if self._supabase_client is not None:
                return self._supabase_client

            from supabase import create_client

            url = os.environ["SUPABASE_URL"]  # Will raise KeyError if missing
            key = os.environ["SUPABASE_KEY"]  # Will raise KeyError if missing

            self._supabase_client = create_client(url, key)
            logger.info("Supabase client initialised")
            return self._supabase_client

    # ── ToolRegistry ──────────────────────────────────────────────────────────

    def get_tool_registry(self) -> Any:
        """Get or create the ToolRegistry singleton. Thread-safe.

        Used by: apps/api/main.py (enterprise backend tool registry)
        """
        with self._tool_registry_lock:
            if self._tool_registry is not None:
                return self._tool_registry

            from agent_core.tools.registry import ToolRegistry

            self._tool_registry = ToolRegistry()
            logger.info("ToolRegistry created")
            return self._tool_registry

    # ── ToolInterface ─────────────────────────────────────────────────────────

    def get_tool_interface(self) -> Any:
        """Get or create the ToolInterface singleton. Thread-safe.

        Used by: agent_core/gateway/tool_executor.py (local tool execution interface)
        """
        with self._tool_interface_lock:
            if self._tool_interface is not None:
                return self._tool_interface

            from agent_core.gateway.tool_interface import ToolInterface

            self._tool_interface = ToolInterface()
            logger.info("ToolInterface created")
            return self._tool_interface

    # ── Reset (for /reload endpoint) ──────────────────────────────────────────

    def reset_tool_registry(self) -> None:
        """Reset only the ToolRegistry singleton.

        Called by the /reload endpoint in apps/api/main.py.
        """
        with self._tool_registry_lock:
            self._tool_registry = None
            logger.info("ToolRegistry reset")

    def reset(self) -> None:
        """Full container reset — clears all cached instances.

        Not called in normal operation; primarily for testing.
        """
        for lock_name in [
            "_qdrant_lock",
            "_openai_lock",
            "_redis_bytes_lock",
            "_redis_str_lock",
            "_supabase_lock",
            "_tool_registry_lock",
            "_tool_interface_lock",
        ]:
            lock = getattr(self, lock_name)
            with lock:
                attr = lock_name.replace("_lock", "")
                if hasattr(self, attr):
                    setattr(self, attr, None)
        logger.info("Container reset")

    # ── FastAPI Depends() providers ───────────────────────────────────────────
    # These enable gradual migration to FastAPI Depends() pattern.
    # Not required for Phase 4; added for future use.

    def qdrant_dep(self) -> Any:
        """FastAPI dependency provider for QdrantClient."""
        return self.get_qdrant_client()

    def openai_dep(self) -> Any:
        """FastAPI dependency provider for OpenAI client."""
        return self.get_openai_client()

    def redis_bytes_dep(self) -> Optional[Any]:
        """FastAPI dependency provider for Redis (bytes) client."""
        return self.get_redis_bytes()

    def redis_str_dep(self) -> Optional[Any]:
        """FastAPI dependency provider for Redis (str) client."""
        return self.get_redis_str()

    def supabase_dep(self) -> Any:
        """FastAPI dependency provider for Supabase client."""
        return self.get_supabase_client()

    def tool_registry_dep(self) -> Any:
        """FastAPI dependency provider for ToolRegistry."""
        return self.get_tool_registry()

    def tool_interface_dep(self) -> Any:
        """FastAPI dependency provider for ToolInterface."""
        return self.get_tool_interface()


# ── Module-level singleton ────────────────────────────────────────────────────

_container: Optional[Container] = None
_container_lock = threading.Lock()


def get_container() -> Container:
    """Return the global Container singleton. Thread-safe.

    Creates the container on first call; subsequent calls return the same instance.
    """
    global _container
    if _container is not None:
        return _container

    with _container_lock:
        if _container is None:
            _container = Container()
            logger.debug("Container singleton created")

    return _container
