"""
Skill Installer — Orchestrate the full `agent-corex apply` flow.

Steps:
  1. Parse skill.md (already done by caller)
  2. Run optional install command
  3. Collect missing env vars (prompt user)
  4. Persist env vars to ~/.agent-corex/.env
  5. Inject MCP servers into detected AI tools
  6. Generate/update ~/.agent-corex/mcp.json
  7. Run test prompt (if provided)
  8. POST /user/install to backend (non-blocking)
"""

from __future__ import annotations

import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple

from agent_core.skill_parser import SkillSpec

# ── Public entry point ────────────────────────────────────────────────────────


class SkillInstaller:
    """
    Drives the apply workflow for a parsed SkillSpec.

    Usage::

        spec = skill_parser.parse(content)
        installer = SkillInstaller(spec, yes=False, verbose=True)
        installer.run()
    """

    def __init__(self, spec: SkillSpec, *, yes: bool = False, verbose: bool = True):
        self.spec = spec
        self.yes = yes
        self.verbose = verbose

    # ── Main orchestration ────────────────────────────────────────────────────

    def run(self) -> bool:
        """
        Execute the full install flow.

        Returns True on success, False if the user aborted.
        Raises on unrecoverable errors.
        """
        spec = self.spec
        self._echo(f"\n{'='*60}")
        self._echo(f"  Applying skill: {spec.name}  ({spec.type})")
        self._echo(f"{'='*60}\n")

        if spec.description:
            # Print first non-empty paragraph
            first_para = next((p.strip() for p in spec.description.split("\n\n") if p.strip()), "")
            if first_para:
                self._echo(f"  {first_para}\n")

        # 1. Run install command
        if spec.install:
            if not self._step_run_install(spec.install):
                return False

        # 2. Collect env vars
        env_values = self._step_collect_env(spec.env)

        # 3. Persist env to ~/.agent-corex/.env
        if env_values:
            self._step_save_env(env_values)

        # 4. Inject MCP servers
        if spec.type == "pack":
            servers_installed = self._step_install_pack_servers(spec.requires)
        else:
            # type == "server" — inject from connect block
            servers_installed = self._step_install_server(spec.name, spec.connect, env_values)

        # 5. Regenerate ~/.agent-corex/mcp.json
        self._step_generate_mcp_config()

        # 6. Run test prompt
        if spec.test:
            self._step_run_test(spec.test)

        # 7. Backend sync (fire-and-forget, no failure on error)
        self._step_backend_sync(spec.name, servers_installed, list(env_values.keys()))

        self._echo(f"\n✓ Skill '{spec.name}' applied successfully.\n")

        if spec.ai_instructions:
            self._echo("AI Instructions:")
            self._echo(f"  {spec.ai_instructions.strip()}\n")

        return True

    # ── Steps ─────────────────────────────────────────────────────────────────

    def _step_run_install(self, install_cmd: str) -> bool:
        """Step 1 — Run optional pre-install shell command."""
        self._echo(f"[1/7] Running install command:")
        self._echo(f"      $ {install_cmd}\n")

        if not self.yes:
            try:
                import typer

                confirmed = typer.confirm("  Run this command?", default=True)
                if not confirmed:
                    self._echo("  Skipped.\n")
                    return True
            except Exception:
                pass

        try:
            result = subprocess.run(
                install_cmd,
                shell=True,
                check=False,
                text=True,
                capture_output=False,
            )
            if result.returncode != 0:
                self._echo(f"\n  ⚠ install command exited with code {result.returncode}")
                if not self.yes:
                    try:
                        import typer

                        if not typer.confirm("  Continue anyway?", default=False):
                            return False
                    except Exception:
                        pass
            else:
                self._echo(f"\n  ✓ Install command succeeded.\n")
        except Exception as exc:
            self._echo(f"\n  ✗ Failed to run install command: {exc}")
            return False

        return True

    def _step_collect_env(self, env_spec: Dict[str, str]) -> Dict[str, str]:
        """
        Step 2 — Collect env vars.

        Loads existing values from ~/.agent-corex/.env first.
        Only prompts for missing required vars (and optionally optional ones).
        Returns a dict of {KEY: value} for vars that should be saved/updated.
        """
        if not env_spec:
            return {}

        from agent_core.env_manager import EnvManager

        existing = EnvManager.load_env()

        required_missing: List[str] = []
        optional_missing: List[str] = []

        for key, req_level in env_spec.items():
            if key not in existing or not existing[key]:
                if req_level == "required":
                    required_missing.append(key)
                else:
                    optional_missing.append(key)

        if not required_missing and not optional_missing:
            self._echo("[2/7] All environment variables already configured.\n")
            return {}

        self._echo(f"[2/7] Collecting environment variables...")

        collected: Dict[str, str] = {}

        # Required vars — always prompt
        if required_missing:
            self._echo(f"\n  Required:")
            for key in required_missing:
                val = self._prompt_secret(f"  Enter {key}")
                if val:
                    collected[key] = val
                else:
                    self._echo(f"  ⚠ {key} skipped — server may not work without it")

        # Optional vars — prompt but allow skip
        if optional_missing:
            self._echo(f"\n  Optional (press Enter to skip):")
            for key in optional_missing:
                val = self._prompt_optional(f"  Enter {key}")
                if val:
                    collected[key] = val

        self._echo("")
        return collected

    def _step_save_env(self, env_values: Dict[str, str]) -> None:
        """Step 3 — Merge new env vars into ~/.agent-corex/.env."""
        from agent_core.env_manager import EnvManager

        existing = EnvManager.load_env()
        merged = {**existing, **env_values}
        env_file = EnvManager.save_env(merged)
        self._echo(f"[3/7] Saved {len(env_values)} env var(s) to {env_file}\n")

    def _step_install_pack_servers(self, server_names: List[str]) -> List[str]:
        """
        Step 4 (pack) — Install each server from the registry into detected tools.

        Reuses the same logic as `agent-corex install-mcp` but non-interactively.
        Returns list of successfully injected server names.
        """
        if not server_names:
            self._echo("[4/7] No servers to install.\n")
            return []

        self._echo(
            f"[4/7] Installing {len(server_names)} MCP server(s): {', '.join(server_names)}\n"
        )

        from agent_core import local_config
        from agent_core.env_manager import EnvManager

        env_store = EnvManager.load_env()
        installed: List[str] = []

        try:
            import httpx
        except ImportError:
            self._echo("  ✗ httpx is required. Run: pip install httpx")
            return installed

        base_url = local_config.get_base_url()

        for name in server_names:
            self._echo(f"  • {name}")
            try:
                with httpx.Client(timeout=10.0) as client:
                    resp = client.get(f"{base_url}/mcp_registry/{name}")
                    if resp.status_code == 404:
                        self._echo(f"    ✗ Not found in registry — skipping")
                        continue
                    resp.raise_for_status()
                    entry = resp.json()
            except Exception as exc:
                self._echo(f"    ✗ Registry fetch failed: {exc} — skipping")
                continue

            # Build env for this server (substitute from env store)
            server_env: Dict[str, str] = {}
            for req_key in entry.get("env_required", []):
                if req_key in env_store:
                    server_env[req_key] = env_store[req_key]

            server_def: Dict[str, Any] = {
                "command": entry["command"],
                "args": entry.get("args", []),
            }
            if server_env:
                server_def["env"] = server_env

            vscode_def = {"type": "stdio", **server_def}

            injected = _inject_into_all_tools(name, server_def, vscode_def)
            if injected:
                installed.append(name)
                self._echo(f"    ✓ Injected into: {', '.join(injected)}")
            else:
                self._echo(f"    – No detected tools to inject into")

        self._echo("")
        return installed

    def _step_install_server(
        self,
        name: str,
        connect: Optional[Dict[str, Any]],
        env_values: Dict[str, str],
    ) -> List[str]:
        """
        Step 4 (server) — Inject a single server from the connect block.

        Returns list of tool names injected into.
        """
        if not connect:
            self._echo("[4/7] No connect block — skipping MCP injection.\n")
            return []

        self._echo(f"[4/7] Installing MCP server '{name}' from skill connect block...\n")

        # Build env for the server definition
        server_env: Dict[str, str] = {}
        raw_env = connect.get("env", {}) or {}
        if isinstance(raw_env, dict):
            for k, v in raw_env.items():
                # Resolve ${VAR} placeholders from env_values
                resolved = _resolve_env_placeholder(str(v), env_values)
                if resolved:
                    server_env[k] = resolved

        server_def: Dict[str, Any] = {
            "command": connect.get("command", "npx"),
            "args": connect.get("args", []),
        }
        if server_env:
            server_def["env"] = server_env

        vscode_def = {"type": "stdio", **server_def}

        injected = _inject_into_all_tools(name, server_def, vscode_def)
        if injected:
            self._echo(f"  ✓ Injected into: {', '.join(injected)}\n")
        else:
            self._echo("  – No detected tools to inject into\n")

        return injected

    def _step_generate_mcp_config(self) -> None:
        """Step 5 — Regenerate ~/.agent-corex/mcp.json."""
        try:
            from agent_core.mcp_config_generator import MCPConfigGenerator

            config = MCPConfigGenerator.generate_config(include_env=True)
            config_file = MCPConfigGenerator.write_config(config)
            n_servers = len(config.get("mcpServers", {}))
            self._echo(f"[5/7] Updated {config_file} ({n_servers} server(s))\n")
        except Exception as exc:
            self._echo(f"[5/7] Could not update mcp.json: {exc}\n")

    def _step_run_test(self, test_prompt: str) -> None:
        """
        Step 6 — Show test prompt to the user.

        We don't execute it automatically (would need LLM context), but we
        display it prominently so the user or AI agent can run it.
        """
        self._echo(f"[6/7] Test prompt (run this to verify the skill works):")
        self._echo(f'\n      "{test_prompt}"\n')

    def _step_backend_sync(
        self,
        pack_name: str,
        tools_installed: List[str],
        env_keys: List[str],
    ) -> None:
        """
        Step 7 — Sync install state to backend via POST /user/servers (fire-and-forget).

        Sends installed server names and pack name to Supabase via the backend.
        Env key names are logged locally only — values are never sent.
        Silently ignores errors so install always succeeds offline.
        """
        from agent_core import local_config

        auth_header = local_config.get_auth_header()
        if not auth_header:
            self._echo("[7/7] Not logged in — skipping backend sync.\n")
            return

        # POST /user/servers — the existing sync endpoint used by agent-corex sync
        payload = {
            "installed_servers": tools_installed,
            "installed_packs": [pack_name] if pack_name else [],
        }

        try:
            import httpx

            base_url = local_config.get_base_url()
            with httpx.Client(timeout=8.0) as client:
                resp = client.post(
                    f"{base_url}/user/servers",
                    json=payload,
                    headers={"Authorization": auth_header},
                )
                if resp.status_code in (200, 201):
                    self._echo(f"[7/7] Synced install to backend.\n")
                else:
                    self._echo(f"[7/7] Backend sync returned {resp.status_code} — continuing.\n")
        except Exception:
            # Non-blocking — offline use is fully supported
            self._echo("[7/7] Backend sync skipped (offline or not reachable).\n")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _echo(self, msg: str) -> None:
        if self.verbose:
            print(msg)

    def _prompt_secret(self, label: str) -> str:
        """Prompt for a sensitive value, hiding input."""
        try:
            import typer

            val = typer.prompt(label, hide_input=True, default="", show_default=False)
            return val.strip()
        except Exception:
            import getpass

            return getpass.getpass(f"{label}: ").strip()

    def _prompt_optional(self, label: str) -> str:
        """Prompt for an optional value."""
        try:
            import typer

            val = typer.prompt(label, default="", show_default=False)
            return val.strip()
        except Exception:
            val = input(f"{label} (optional): ")
            return val.strip()


# ── Injection helper (shared between pack + server paths) ─────────────────────


def _inject_into_all_tools(
    server_name: str,
    server_def: Dict[str, Any],
    vscode_def: Dict[str, Any],
) -> List[str]:
    """
    Inject a server definition into all detected AI tools.

    Returns a list of tool slugs that were successfully updated.
    """
    try:
        from agent_core.detectors import (
            ClaudeDesktopDetector,
            CursorDetector,
            VSCodeDetector,
            VSCodeInsidersDetector,
            VSCodiumDetector,
        )
        from agent_core.config_adapters import (
            ClaudeAdapter,
            CursorAdapter,
            VSCodeStableAdapter,
            VSCodeInsidersAdapter,
            VSCodiumAdapter,
        )
    except ImportError:
        return []

    _VSCODE_KEYS = {"vscode", "vscode-insiders", "vscodium"}

    tool_pairs = [
        ("claude", ClaudeDesktopDetector(), ClaudeAdapter()),
        ("cursor", CursorDetector(), CursorAdapter()),
        ("vscode", VSCodeDetector(), VSCodeStableAdapter()),
        ("vscode-insiders", VSCodeInsidersDetector(), VSCodeInsidersAdapter()),
        ("vscodium", VSCodiumDetector(), VSCodiumAdapter()),
    ]

    injected: List[str] = []

    for slug, detector, adapter in tool_pairs:
        if not detector.is_installed():
            continue
        definition = vscode_def if slug in _VSCODE_KEYS else server_def
        try:
            adapter.add_server(server_name, definition)
            injected.append(slug)
        except Exception:
            pass

    return injected


def _resolve_env_placeholder(value: str, env_values: Dict[str, str]) -> str:
    """
    Resolve ${VAR_NAME} placeholders in a string using env_values.

    Falls back to checking os.environ for non-sensitive vars.
    """
    import re
    import os

    def _replacer(m: re.Match) -> str:
        var = m.group(1)
        return env_values.get(var) or os.environ.get(var) or m.group(0)

    return re.sub(r"\$\{([^}]+)\}", _replacer, value)
