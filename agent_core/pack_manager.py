"""
Pack Manager — Handle curated tool bundle installation and tracking.

A "pack" is a curated bundle of MCP servers (e.g., "vibe_coding_pack" = railway, github, supabase, filesystem, redis).
"""

import json
import pathlib
from typing import Optional, Dict, List, Any
from datetime import datetime

from agent_core import local_config


class PackManager:
    """Manage pack installation, tracking, and metadata."""

    INSTALLED_SERVERS_FILE = local_config.CONFIG_DIR / "installed_servers.json"
    PACK_REGISTRY_URL = "https://api.agent-corex.com/packs"  # Future: fetch from backend

    # Hardcoded pack definitions (future: sync from backend)
    PACK_DEFINITIONS = {
        "vibe_coding_pack": {
            "name": "Vibe Coding Pack",
            "description": "Essential tools for fast development: deployment, version control, databases, filesystems",
            "servers": [
                {
                    "name": "railway",
                    "description": "Deploy to Railway.app",
                    "category": "deployment",
                    "env_required": [],
                    "env_optional": [],
                    "command": "npx",
                    "args": ["-y", "@railway/mcp-server"],
                    # No env injection — @railway/mcp-server reads ~/.railway/config.json
                    # set by `railway login`. Setting RAILWAY_TOKEN env var overrides this
                    # with an invalid value and causes "Unauthorized" errors.
                },
                {
                    "name": "github",
                    "description": "GitHub API integration",
                    "category": "developer-tools",
                    "env_required": ["GITHUB_TOKEN"],
                    "env_optional": [],
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-github"],
                    "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"},
                },
                {
                    "name": "supabase",
                    "description": "Supabase Postgres + Auth",
                    "category": "databases",
                    "env_required": ["SUPABASE_ACCESS_TOKEN"],
                    "env_optional": [],
                    "command": "npx",
                    "args": [
                        "-y",
                        "@supabase/mcp-server-supabase",
                        "--access-token",
                        "${SUPABASE_ACCESS_TOKEN}",
                    ],
                },
                {
                    "name": "filesystem",
                    "description": "Read/write files in workspace",
                    "category": "developer-tools",
                    "env_required": [],
                    "env_optional": [],
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem"],
                },
                {
                    "name": "redis",
                    "description": "Redis caching and pub/sub",
                    "category": "databases",
                    "env_required": ["REDIS_URL"],
                    "env_optional": [],
                    "command": "uvx",
                    "args": [
                        "--from",
                        "redis-mcp-server",
                        "redis-mcp-server",
                        "--url",
                        "${REDIS_URL}",
                    ],
                },
            ],
        },
        "data_science_pack": {
            "name": "Data Science Pack",
            "description": "Tools for data analysis and ML: pandas, jupyter, scikit-learn, visualization",
            "servers": [
                {
                    "name": "pandas",
                    "description": "Data manipulation and analysis",
                    "category": "data",
                    "env_required": [],
                    "env_optional": [],
                    "command": "npx",
                    "args": ["-y", "pandas-mcp-server"],
                },
                {
                    "name": "jupyter",
                    "description": "Jupyter notebook integration",
                    "category": "data",
                    "env_required": [],
                    "env_optional": [],
                    "command": "npx",
                    "args": ["-y", "jupyter-mcp-server"],
                },
            ],
        },
    }

    @classmethod
    def list_packs(cls) -> Dict[str, Dict[str, Any]]:
        """List all available packs."""
        return cls.PACK_DEFINITIONS

    @classmethod
    def get_pack(cls, pack_name: str) -> Optional[Dict[str, Any]]:
        """Get pack definition by name."""
        return cls.PACK_DEFINITIONS.get(pack_name)

    @classmethod
    def install_pack(cls, pack_name: str, enable_all: bool = True) -> Dict[str, Any]:
        """
        Install a pack (register servers in installed_servers.json).

        Returns metadata about the installation:
        {
            "pack": pack_name,
            "servers": [list of installed servers],
            "enabled": {server: bool},
            "env_required": {server: [env_vars]},
            "timestamp": ISO timestamp
        }
        """
        pack = cls.get_pack(pack_name)
        if not pack:
            raise ValueError(f"Pack '{pack_name}' not found")

        # Load current installed_servers.json
        data = cls._load_installed()

        # Add servers from this pack
        servers_list = []
        enabled_dict = {}
        env_required_dict = {}

        for server_def in pack["servers"]:
            server_name = server_def["name"]
            servers_list.append(server_name)
            enabled_dict[server_name] = enable_all
            env_required_dict[server_name] = server_def.get("env_required", [])

        # Update file
        data[pack_name] = {
            "servers": servers_list,
            "enabled": enabled_dict,
            "env_required": env_required_dict,
            "installed_at": datetime.utcnow().isoformat() + "Z",
        }

        cls._save_installed(data)

        return {
            "pack": pack_name,
            "servers": servers_list,
            "enabled": enabled_dict,
            "env_required": env_required_dict,
            "timestamp": data[pack_name]["installed_at"],
        }

    @classmethod
    def uninstall_pack(cls, pack_name: str) -> None:
        """Uninstall a pack (remove from installed_servers.json)."""
        data = cls._load_installed()
        if pack_name in data:
            del data[pack_name]
            cls._save_installed(data)

    @classmethod
    def get_installed_packs(cls) -> Dict[str, Dict[str, Any]]:
        """Get all installed packs with their metadata."""
        return cls._load_installed()

    @classmethod
    def get_installed_servers(cls) -> Dict[str, Dict[str, Any]]:
        """Get all installed servers across all packs.

        Returns:
        {
            "railway": {"pack": "vibe_coding_pack", "enabled": true, "env_required": ["RAILWAY_API_KEY"]},
            "github": {"pack": "vibe_coding_pack", "enabled": true, ...},
            ...
        }
        """
        installed_packs = cls._load_installed()
        result = {}

        for pack_name, pack_data in installed_packs.items():
            for server_name in pack_data.get("servers", []):
                enabled = pack_data.get("enabled", {}).get(server_name, False)
                env_req = pack_data.get("env_required", {}).get(server_name, [])
                result[server_name] = {
                    "pack": pack_name,
                    "enabled": enabled,
                    "env_required": env_req,
                }

        return result

    @classmethod
    def toggle_server(cls, pack_name: str, server_name: str, enabled: bool) -> None:
        """Enable/disable a server within a pack."""
        data = cls._load_installed()

        if pack_name not in data:
            raise ValueError(f"Pack '{pack_name}' not installed")

        if server_name not in data[pack_name].get("servers", []):
            raise ValueError(f"Server '{server_name}' not in pack '{pack_name}'")

        if "enabled" not in data[pack_name]:
            data[pack_name]["enabled"] = {}

        data[pack_name]["enabled"][server_name] = enabled
        cls._save_installed(data)

    @classmethod
    def get_servers_for_pack(cls, pack_name: str) -> List[Dict[str, Any]]:
        """Get server definitions for a pack."""
        pack = cls.get_pack(pack_name)
        if not pack:
            return []
        return pack["servers"]

    @classmethod
    def _load_installed(cls) -> Dict[str, Any]:
        """Load installed_servers.json from disk."""
        if not cls.INSTALLED_SERVERS_FILE.exists():
            return {}

        try:
            with open(cls.INSTALLED_SERVERS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    @classmethod
    def _save_installed(cls, data: Dict[str, Any]) -> None:
        """Save installed_servers.json to disk."""
        cls.INSTALLED_SERVERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(cls.INSTALLED_SERVERS_FILE, "w") as f:
            json.dump(data, f, indent=2)
