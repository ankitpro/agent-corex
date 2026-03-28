"""
Environment Manager — Setup and manage ~/.agent-corex/.env file.

The .env file stores API keys and connection strings that are injected
into all MCP servers when they start.
"""

import pathlib
from typing import Dict, Tuple, List, Optional
from datetime import datetime


class EnvManager:
    """Manage environment variables in ~/.agent-corex/.env"""

    ENV_FILE = pathlib.Path.home() / ".agent-corex" / ".env"

    # Standard variables to prompt for
    STANDARD_VARS = [
        {
            "key": "OPENAI_API_KEY",
            "description": "OpenAI API key (sk-... format, optional)",
            "sensitive": True,
            "required": False,
        },
        {
            "key": "ANTHROPIC_API_KEY",
            "description": "Anthropic API key (optional)",
            "sensitive": True,
            "required": False,
        },
        {
            "key": "SUPABASE_URL",
            "description": "Supabase project URL (https://... format, optional)",
            "sensitive": False,
            "required": False,
        },
        {
            "key": "SUPABASE_KEY",
            "description": "Supabase API key (optional)",
            "sensitive": True,
            "required": False,
        },
        {
            "key": "REDIS_URL",
            "description": "Redis connection URL (redis://..., optional)",
            "sensitive": True,
            "required": False,
        },
        {
            "key": "SUPABASE_ACCESS_TOKEN",
            "description": "Supabase Personal Access Token for MCP server (get from supabase.com/dashboard/account/tokens)",
            "sensitive": True,
            "required": False,
        },
        {
            "key": "RAILWAY_API_KEY",
            "description": "Railway.app API key (for deployment, optional)",
            "sensitive": True,
            "required": False,
        },
        {
            "key": "RENDER_API_KEY",
            "description": "Render.com API key (for deployment, optional)",
            "sensitive": True,
            "required": False,
        },
        {
            "key": "GITHUB_TOKEN",
            "description": "GitHub personal access token (optional)",
            "sensitive": True,
            "required": False,
        },
        {
            "key": "AGENT_COREX_API_KEY",
            "description": "Agent-Corex API key (acx_..., optional)",
            "sensitive": True,
            "required": False,
        },
    ]

    @classmethod
    def load_env(cls) -> Dict[str, str]:
        """Load all environment variables from .env file."""
        env_vars = {}

        if not cls.ENV_FILE.exists():
            return env_vars

        try:
            with open(cls.ENV_FILE) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        env_vars[k.strip()] = v.strip()
        except Exception:
            pass

        return env_vars

    @classmethod
    def save_env(cls, env_vars: Dict[str, str]) -> pathlib.Path:
        """Save environment variables to .env file."""
        cls.ENV_FILE.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            "# Agent-Corex environment variables",
            "# Generated: " + datetime.utcnow().isoformat() + "Z",
            "# These are injected into all MCP servers",
            "",
        ]

        for k, v in env_vars.items():
            lines.append(f"{k}={v}")

        lines.append("")  # Trailing newline

        with open(cls.ENV_FILE, "w") as f:
            f.write("\n".join(lines))

        return cls.ENV_FILE

    @classmethod
    def get_env(cls, key: str) -> Optional[str]:
        """Get a single environment variable."""
        env_vars = cls.load_env()
        return env_vars.get(key)

    @classmethod
    def set_env(cls, key: str, value: str) -> None:
        """Set a single environment variable."""
        env_vars = cls.load_env()
        env_vars[key] = value
        cls.save_env(env_vars)

    @classmethod
    def delete_env(cls, key: str) -> None:
        """Delete a single environment variable."""
        env_vars = cls.load_env()
        env_vars.pop(key, None)
        cls.save_env(env_vars)

    @classmethod
    def interactive_setup(cls) -> Dict[str, str]:
        """
        Interactive prompt for environment variables.

        Returns the new/updated env dict.
        """
        import typer

        existing_env = cls.load_env()
        new_env = dict(existing_env)

        for var_config in cls.STANDARD_VARS:
            key = var_config["key"]
            description = var_config["description"]
            existing = existing_env.get(key)

            # Show prompt
            if existing:
                typer.echo(f"\n  {key} (currently set, press Enter to keep)")
            else:
                typer.echo(f"\n  {key}")
                typer.echo(f"    {description}")

            # Get input
            val = typer.prompt(
                f"    {key}",
                default=existing or "",
                hide_input=var_config["sensitive"],
                show_default=False,
            )

            # Update
            if val and val.strip():
                new_env[key] = val.strip()
            elif key not in new_env:
                # User skipped and no existing value
                pass

        return new_env

    @classmethod
    def validate_keys(cls, env_vars: Dict[str, str]) -> Tuple[bool, List[str]]:
        """
        Validate environment variable values.

        Returns (is_valid, list_of_errors)
        """
        errors = []

        # Check API key formats
        if "OPENAI_API_KEY" in env_vars:
            if not env_vars["OPENAI_API_KEY"].startswith("sk-"):
                errors.append("OPENAI_API_KEY should start with 'sk-'")

        if "ANTHROPIC_API_KEY" in env_vars:
            if not env_vars["ANTHROPIC_API_KEY"].startswith("sk-"):
                errors.append("ANTHROPIC_API_KEY should start with 'sk-'")

        if "GITHUB_TOKEN" in env_vars:
            if not env_vars["GITHUB_TOKEN"].startswith("ghp_") and not env_vars[
                "GITHUB_TOKEN"
            ].startswith("github_pat_"):
                errors.append("GITHUB_TOKEN should start with 'ghp_' or 'github_pat_'")

        if "SUPABASE_URL" in env_vars:
            if not env_vars["SUPABASE_URL"].startswith("https://"):
                errors.append("SUPABASE_URL should start with 'https://'")

        if "REDIS_URL" in env_vars:
            if not env_vars["REDIS_URL"].startswith("redis://"):
                errors.append("REDIS_URL should start with 'redis://'")

        if "AGENT_COREX_API_KEY" in env_vars:
            if not env_vars["AGENT_COREX_API_KEY"].startswith("acx_"):
                errors.append("AGENT_COREX_API_KEY should start with 'acx_'")

        return len(errors) == 0, errors

    @classmethod
    def mask_values(cls, env_vars: Dict[str, str]) -> Dict[str, str]:
        """Return a copy with sensitive values masked."""
        masked = {}
        for k, v in env_vars.items():
            is_sensitive = any(var["key"] == k and var["sensitive"] for var in cls.STANDARD_VARS)
            if is_sensitive:
                masked[k] = v[:4] + "..." + v[-4:] if len(v) > 8 else "****"
            else:
                masked[k] = v
        return masked
