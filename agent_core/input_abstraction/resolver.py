"""Context resolver — resolves internal parameters from local context.

Resolution sources (in priority order):
  1. Server config environment variables (baked in by MCPLoader)
  2. Local config (~/.agent-corex/config.json)
  3. Runtime context (os.getcwd())
  4. Static/default values

This resolver is stateless — it reads from config at call time so changes
are always picked up.
"""

from __future__ import annotations

import os
from typing import Any, Optional

from .models import InternalParam


class ContextResolver:
    """Resolves internal parameters from local context.

    Resolution strategies:
        workspace_path: from server_config["env"] or os.getcwd()
        user_id: from local_config user.user_id
        config_key: from server_config["env"][key]
        auth_token, auth_secret, auth_key: from server env
        static: hardcoded static_value
        auto_resolved: generic internal param (resolved to None — skip injection)
    """

    def resolve_all(
        self,
        internal_params: list[InternalParam],
        server_config: dict,
    ) -> dict[str, Any]:
        """Resolve all internal parameters and return dict of param_name -> value.

        Only includes params that can be resolved. Params that resolve to None
        are omitted (MCP server may have its own defaults).

        Args:
            internal_params: List of InternalParam to resolve
            server_config: Server config dict with "env" key

        Returns:
            {param_name: resolved_value} for all resolvable params
        """
        result = {}
        for param in internal_params:
            value = self._resolve_single(param, server_config)
            if value is not None:
                result[param.name] = value
        return result

    def _resolve_single(self, param: InternalParam, server_config: dict) -> Any:
        """Resolve a single internal parameter.

        Returns:
            Resolved value, or None if cannot be resolved
        """
        strategy = param.resolution_strategy

        if strategy == "workspace_path":
            return self._resolve_workspace_path(server_config)
        elif strategy == "user_id":
            return self._resolve_user_id()
        elif strategy == "config_key" and param.config_key:
            return self._resolve_config_key(param.config_key, server_config)
        elif strategy in ("auth_token", "auth_secret", "auth_key"):
            # These are already in the MCP server's environment by MCPLoader
            # We don't re-inject them since the MCP server handles auth itself
            return None
        elif strategy == "static":
            return param.static_value
        elif strategy == "auto_resolved":
            # Generic internal param — no specific resolution strategy
            return None
        else:
            # Unknown strategy — skip
            return None

    def _resolve_workspace_path(self, server_config: dict) -> Optional[str]:
        """Resolve workspace path.

        Priority:
          1. server_config["env"]["RAILWAY_WORKSPACE_PATH"] or similar
          2. os.getcwd() (current working directory, usually project root)

        Returns:
            Resolved path, or None
        """
        # Check server config environment variables
        env = server_config.get("env", {})
        if isinstance(env, dict):
            # Check for known workspace path environment variables
            for key in ["RAILWAY_WORKSPACE_PATH", "WORKSPACE_PATH", "PROJECT_PATH"]:
                value = env.get(key)
                if value:
                    return value

        # Fall back to current working directory
        # When the user runs agent-corex from their project root,
        # os.getcwd() is the workspace.
        try:
            return os.getcwd()
        except Exception:
            return None

    def _resolve_user_id(self) -> Optional[str]:
        """Resolve user_id from local config.

        Returns:
            User ID if available, or None
        """
        try:
            from agent_core import local_config

            config = local_config.get_config()
            return config.get("user", {}).get("user_id")
        except Exception:
            return None

    def _resolve_config_key(self, key: str, server_config: dict) -> Any:
        """Resolve a parameter from server config environment.

        Args:
            key: Environment variable key (e.g., "GITHUB_TOKEN")
            server_config: Server config dict

        Returns:
            Environment variable value, or None
        """
        env = server_config.get("env", {})
        if isinstance(env, dict):
            return env.get(key)
        return None
