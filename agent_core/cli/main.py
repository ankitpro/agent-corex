"""
Agent-Core CLI interface.

Core commands:
  retrieve      Search for relevant tools by query
  start         Start the Agent-Core retrieval API server
  version       Show version
  health        Check API health
  config        Show configuration info

Gateway / tool management:
  serve         Start the MCP gateway server (used by Claude Desktop / Cursor)
  init          Detect AI tools and inject Agent-Corex as an MCP server
  eject         Remove agent-corex from AI tool configs
  list          List all MCP servers injected across detected tools
  update        Re-fetch registry and update injected server configs

Auth / account:
  login         Validate API key and store credentials
  logout        Remove stored credentials
  keys          Show masked API key + verify with backend

Diagnostics:
  detect        Detect installed AI tools and show config paths
  status        Show auth state, backend status, and injection status per tool
  doctor        Diagnose common setup issues (Python, PATH, config, backend)

Registry / install:
  registry      Browse the installable MCP server catalog
  install-mcp   Install an MCP server from the registry into all detected tools
"""

from __future__ import annotations

import typer
from typing import Optional
import json
import pathlib
from agent_core.pack_manager import PackManager


def _version_callback(value: bool):
    if value:
        from agent_core import __version__

        typer.echo(f"agent-corex {__version__}")
        raise typer.Exit()


app = typer.Typer(
    name="agent-corex",
    help="Fast, accurate MCP tool retrieval engine — with gateway and enterprise support",
    no_args_is_help=True,
)


@app.callback()
def _app_options(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
):
    pass


# ── Shared detector/adapter helper ────────────────────────────────────────────


def _tool_pairs():
    """Return [(slug, detector, adapter), ...] for all 5 supported AI tools."""
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

    return [
        ("claude", ClaudeDesktopDetector(), ClaudeAdapter()),
        ("cursor", CursorDetector(), CursorAdapter()),
        ("vscode", VSCodeDetector(), VSCodeStableAdapter()),
        ("vscode-insiders", VSCodeInsidersDetector(), VSCodeInsidersAdapter()),
        ("vscodium", VSCodiumDetector(), VSCodiumAdapter()),
    ]


# ═══════════════════════════════════════════════════════════════════════════
# Existing commands (preserved exactly)
# ═══════════════════════════════════════════════════════════════════════════


@app.command()
def retrieve(
    query: str = typer.Argument(..., help="Search query for tool retrieval"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Number of results to return"),
    method: str = typer.Option(
        "hybrid", "--method", "-m", help="Ranking method: keyword, hybrid, or embedding"
    ),
    config: Optional[str] = typer.Option(
        None, "--config", "-c", help="Path to mcp.json config file"
    ),
):
    """
    Retrieve the most relevant tools for a given query.

    Example:
        agent-corex retrieve "edit a file" --top-k 5 --method hybrid
    """
    try:
        from agent_core.retrieval.ranker import rank_tools
        from agent_core.tools.registry import ToolRegistry
        from agent_core.tools.mcp.mcp_loader import MCPLoader
        import pathlib

        registry = ToolRegistry()

        if config:
            config_path = pathlib.Path(config)
            if config_path.exists():
                try:
                    loader = MCPLoader(str(config_path))
                    manager = loader.load()
                    tools = manager.get_all_tools()
                except Exception as e:
                    typer.echo(f"Warning: Failed to load MCP servers: {e}", err=True)
                    tools = registry.get_all_tools()
            else:
                typer.echo(f"Config file not found: {config}", err=True)
                tools = registry.get_all_tools()
        else:
            tools = registry.get_all_tools()

        if not tools:
            typer.echo("No tools available", err=True)
            raise typer.Exit(1)

        results = rank_tools(query, tools, top_k=top_k, method=method)

        if not results:
            typer.echo(f"No tools found for query: {query}")
            raise typer.Exit(0)

        typer.echo(f"\nFound {len(results)} tool(s) for: '{query}'\n")
        for i, tool in enumerate(results, 1):
            typer.echo(f"{i}. {tool['name']}")
            typer.echo(f"   {tool.get('description', 'No description')}\n")

    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1)


@app.command()
def start(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Server host"),
    port: int = typer.Option(8000, "--port", "-p", help="Server port"),
    reload: bool = typer.Option(True, "--reload/--no-reload", help="Enable auto-reload"),
    config: Optional[str] = typer.Option(
        None, "--config", "-c", help="Path to mcp.json config file"
    ),
):
    """
    Start the Agent-Core retrieval API server.

    Example:
        agent-corex start --host 0.0.0.0 --port 8000
    """
    import uvicorn
    import os

    if config:
        os.environ["AGENT_CORE_CONFIG"] = config

    typer.echo(f"Starting Agent-Core API server at http://{host}:{port}")
    typer.echo("Press Ctrl+C to stop\n")

    uvicorn.run("agent_core.api.main:app", host=host, port=port, reload=reload, log_level="info")


@app.command()
def version():
    """Show Agent-Core version."""
    from agent_core import __version__

    typer.echo(f"Agent-Core {__version__}")


@app.command()
def health():
    """Check API health (requires running server)."""
    import httpx
    from agent_core import local_config

    base_url = local_config.get_base_url()
    typer.echo("Checking Agent-CoreX service...")
    try:
        resp = httpx.get(f"{base_url}/health", timeout=5)
        if resp.status_code == 200:
            typer.echo("✓ Service is healthy")
        else:
            typer.echo(f"✗ Service returned status {resp.status_code}", err=True)
            raise typer.Exit(1)
    except httpx.ConnectError:
        typer.echo("✗ Cannot connect to Agent-CoreX. Check your internet connection.", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"✗ Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="set-url")
def set_url(
    url: str = typer.Argument(..., help="Frontend URL (default: https://www.agent-corex.com)"),
):
    """
    Override the frontend login page URL (for local development only).

    \\b
    Examples:
        agent-corex set-url http://localhost:5173    # local dev
        agent-corex set-url https://www.agent-corex.com  # restore default
    """
    from agent_core import local_config

    url = url.rstrip("/")
    local_config.set_key("frontend_url", url)
    typer.echo(f"✓ Frontend URL set to: {url}")
    typer.echo("  'agent-corex login' will now open this URL in your browser.")


@app.command(name="config")
def show_config():
    """Show configuration information."""
    import pathlib
    from agent_core import __version__

    typer.echo(f"Agent-Core {__version__}\n")
    typer.echo("Configuration:")
    typer.echo(f"  Python version: {__import__('sys').version.split()[0]}")
    typer.echo(f"  Installation path: {pathlib.Path(__import__('agent_core').__file__).parent}")

    deps = {
        "fastapi": "FastAPI",
        "sentence_transformers": "Sentence Transformers",
        "faiss": "FAISS",
    }

    typer.echo("\nDependencies:")
    for module, name in deps.items():
        try:
            __import__(module)
            typer.echo(f"  ✓ {name}")
        except ImportError:
            typer.echo(f"  ✗ {name} (not installed)")


# ═══════════════════════════════════════════════════════════════════════════
# New gateway / management commands
# ═══════════════════════════════════════════════════════════════════════════


@app.command()
def serve():
    """
    Start the MCP gateway server (stdio mode).

    This is the command injected into Claude Desktop / Cursor MCP configs:

    \\b
    {
      "agent-corex": {
        "command": "agent-corex",
        "args": ["serve"]
      }
    }

    Example:
        agent-corex serve
    """
    from agent_core.gateway.gateway_server import run

    run()


@app.command()
def init(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts"),
):
    """
    Detect Claude Desktop / Cursor / VS Code and inject Agent-Corex as an MCP server.

    \\b
    What this does:
      1. Scans for Claude Desktop, Cursor, VS Code, VS Code Insiders, VSCodium
      2. Shows existing MCP servers that will be preserved
      3. Creates a timestamped backup of each config before writing
      4. Merges the agent-corex entry — never overwrites existing servers

    Example:
        agent-corex init
        agent-corex init --yes
    """
    SERVER_NAME = "agent-corex"

    CLAUDE_CURSOR_DEF = {"command": "agent-corex", "args": ["serve"]}
    VSCODE_DEF = {"type": "stdio", "command": "agent-corex", "args": ["serve"]}
    _VSCODE_NAMES = {"VS Code", "VS Code Insiders", "VSCodium"}

    # Build (detector, adapter, server_def) triples from the shared helper
    pairs = [
        (det, adp, VSCODE_DEF if det.name in _VSCODE_NAMES else CLAUDE_CURSOR_DEF)
        for _, det, adp in _tool_pairs()
    ]

    typer.echo("\nScanning for AI tools...\n")

    found_any = False
    vscode_written: list[str] = []  # track VS Code variants that were actually written
    for detector, adapter, server_def in pairs:
        if not detector.is_installed():
            typer.echo(f"  [-] {detector.name}: not detected")
            continue

        cfg_path = adapter.config_path()
        typer.echo(f"  [+] {detector.name}: {cfg_path}")
        found_any = True

        # Show existing servers so the user can see what will be preserved
        existing_servers = adapter.get_servers()
        other_servers = {k: v for k, v in existing_servers.items() if k != SERVER_NAME}

        if other_servers:
            typer.echo("      Existing servers (will be kept):")
            for name in other_servers:
                typer.echo(f"        - {name}")
        else:
            typer.echo("      No existing MCP servers — creating new block.")

        already = SERVER_NAME in existing_servers
        action = "Updated" if already else "Added"

        if not yes:
            verb = "Update" if already else "Add"
            confirmed = typer.confirm(
                f"      {verb} 'agent-corex' entry in {detector.name}?", default=True
            )
            if not confirmed:
                typer.echo("      Skipped.")
                continue

        bak = adapter.inject_server(SERVER_NAME, server_def)

        # Report the final state after the write
        final_servers = adapter.get_servers()
        typer.echo(f"      [+] {action}. MCP servers now contains {len(final_servers)} server(s):")
        for name in final_servers:
            marker = "  <-- agent-corex" if name == SERVER_NAME else ""
            typer.echo(f"            - {name}{marker}")
        if bak:
            typer.echo(f"      Backup: {bak}")

        if detector.name in _VSCODE_NAMES:
            vscode_written.append(detector.name)

    if not found_any:
        typer.echo("\nNo supported AI tools detected.")
        typer.echo("Supported: Claude Desktop, Cursor, VS Code, VS Code Insiders, VSCodium")
        typer.echo("Install one and re-run: agent-corex init")
        raise typer.Exit(1)

    typer.echo("\nDone. Restart the tool for changes to take effect.")

    if vscode_written:
        typer.echo(
            f"\n  Note ({', '.join(vscode_written)}): VS Code writes to settings.json while\n"
            "  running and may overwrite the entry. Fully close and reopen VS Code\n"
            "  so it reads the new config from disk on startup."
        )

    typer.echo("\nRun  agent-corex status  to verify.")


@app.command()
def login(
    api_key: Optional[str] = typer.Option(
        None, "--key", "-k", help="API key to store (acx_...) — skips browser flow"
    ),
    no_browser: bool = typer.Option(
        False, "--no-browser", help="Prompt for API key instead of opening browser"
    ),
):
    """
    Authenticate with Agent-Corex.

    \\b
    Default flow (browser-based, recommended):
      1. Opens browser to complete login
      2. CLI polls for completion automatically
      3. Session stored in ~/.agent-corex/config.json

    \\b
    API key flow (if you already have a key):
        agent-corex login --key acx_your_key_here
        agent-corex login --no-browser

    Example:
        agent-corex login
        agent-corex login --key acx_your_key_here
    """
    import webbrowser
    import time as _time
    from agent_core import local_config

    # ── API key flow (--key or --no-browser) ─────────────────────────────────
    if api_key or no_browser:
        from agent_core.gateway.auth_middleware import validate_api_key_format

        if not api_key:
            if not no_browser:
                login_url = local_config.get_login_url()
                typer.echo(f"\nOpening browser: {login_url}\n")
                try:
                    webbrowser.open(login_url)
                except Exception:
                    pass
                typer.echo("After logging in, copy your API key from the dashboard.\n")
            api_key = typer.prompt("Paste your API key (acx_...)", hide_input=True)

        api_key = api_key.strip()
        if not validate_api_key_format(api_key):
            typer.echo(
                "Invalid API key format. Keys must start with 'acx_' and be 8+ characters.",
                err=True,
            )
            raise typer.Exit(1)

        user_info: dict = {}
        try:
            import httpx

            base_url = local_config.get_base_url()
            with httpx.Client(base_url=base_url, timeout=5.0) as client:
                resp = client.post(
                    "/auth/login",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"api_key": api_key},
                )
                if resp.status_code == 200:
                    user_info = resp.json()
                elif resp.status_code == 401:
                    typer.echo(
                        "Backend rejected the API key. Please check the key and try again.",
                        err=True,
                    )
                    raise typer.Exit(1)
        except ImportError:
            pass
        except Exception:
            typer.echo("(Could not reach backend — storing key locally for offline use.)")

        data = local_config.load()
        data["api_key"] = api_key
        if user_info:
            data["user"] = user_info
        local_config.save(data)
        name = user_info.get("name") or user_info.get("user_id", "")
        suffix = f" as {name}" if name else ""
        typer.echo(f"\n[+] Logged in{suffix}")
        typer.echo(f"  Credentials saved to {local_config.CONFIG_FILE}")
        return

    # ── Device-code browser flow (default) ───────────────────────────────────
    import httpx

    base_url = local_config.get_base_url()
    frontend_url = local_config.get_frontend_url()

    typer.echo("\nLogging in to Agent-CoreX...\n")

    # Step 1: Start CLI session
    try:
        resp = httpx.post(f"{base_url}/auth/cli/start", timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
        device_code = data["device_code"]
        verification_url = data["verification_url"]
    except httpx.ConnectError:
        typer.echo(
            "[error] Cannot connect to Agent-CoreX. Check your internet connection.", err=True
        )
        typer.echo(
            "  Or:  agent-corex login --no-browser  to log in with an API key instead.",
            err=True,
        )
        raise typer.Exit(1)
    except (ValueError, KeyError):
        typer.echo("[error] Unexpected response from Agent-CoreX. Please try again.", err=True)
        typer.echo(
            "  Or:  agent-corex login --no-browser  to log in with an API key instead.",
            err=True,
        )
        raise typer.Exit(1)
    except Exception as exc:
        typer.echo(f"[error] Could not start login session: {exc}", err=True)
        typer.echo(
            "  Tip: agent-corex login --no-browser  to log in with an API key instead.",
            err=True,
        )
        raise typer.Exit(1)

    # Step 2: Show URL
    typer.echo("Open this URL to complete login:\n")
    typer.echo(f"  {verification_url}\n")
    try:
        webbrowser.open(verification_url)
        typer.echo("(Opened in your browser automatically)\n")
    except Exception:
        pass

    typer.echo("Waiting for authentication", nl=False)

    # Step 3: Poll
    deadline = _time.time() + 300
    while _time.time() < deadline:
        _time.sleep(2)
        typer.echo(".", nl=False)
        try:
            poll = httpx.post(
                f"{base_url}/auth/cli/poll", json={"device_code": device_code}, timeout=10.0
            )
            if poll.status_code != 200:
                continue
            result = poll.json()
        except Exception:
            continue
        status = result.get("status", "pending")
        if status == "expired":
            typer.echo("\n\n[error] Login session expired. Please try again.", err=True)
            raise typer.Exit(1)
        if status == "complete":
            typer.echo("\n")
            _save_jwt_session(result, local_config)
            return

    typer.echo("\n\n[error] Login timed out. Please try again.", err=True)
    raise typer.Exit(1)


def _save_jwt_session(result: dict, local_config) -> None:
    """Save JWT session returned from /auth/cli/poll to config."""
    import base64
    import json as _json
    import time as _time

    access_token = result.get("access_token", "")
    expires_at = int(_time.time()) + 3600
    email = result.get("email", "")

    # Decode JWT exp claim
    try:
        payload_b64 = access_token.split(".")[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        payload = _json.loads(base64.b64decode(payload_b64))
        if "exp" in payload:
            expires_at = payload["exp"]
        if not email:
            email = payload.get("email", "")
    except Exception:
        pass

    local_config.save_session(
        access_token=access_token,
        refresh_token=result.get("refresh_token", ""),
        user_id=result.get("user_id", ""),
        email=email,
        expires_at=expires_at,
    )
    typer.echo(f"✓ Logged in successfully!")
    if email:
        typer.echo(f"  User: {email}")
    typer.echo(f"  Session saved to {local_config.CONFIG_FILE}\n")
    typer.echo("You can now run:\n  agent-corex sync\n  agent-corex status\n")


@app.command()
def status():
    """
    Show auth state, config path, MCP injection status, and available tools.

    Example:
        agent-corex status
    """
    from agent_core import local_config, __version__
    from agent_core.gateway.tool_router import ToolRouter

    SERVER_NAME = "agent-corex"

    typer.echo(f"\nagent-corex  v{__version__}\n")

    ok = "[+]"
    no = "[-]"

    # ── Auth ────────────────────────────────────────────────────────────────
    typer.echo("Auth")
    if local_config.is_logged_in():
        user = local_config.get("user") or {}
        name = user.get("name") or user.get("user_id") or "(unknown)"
        typer.echo(f"  {ok} Logged in: Yes  ({name})")
    else:
        typer.echo(f"  {no} Logged in: No")
        typer.echo("    Run: agent-corex login")

    # ── Config ──────────────────────────────────────────────────────────────
    typer.echo("\nConfig")
    typer.echo(f"  Path:   {local_config.CONFIG_FILE}")
    typer.echo(f"  Exists: {'Yes' if local_config.CONFIG_FILE.exists() else 'No'}")

    # ── MCP clients ─────────────────────────────────────────────────────────
    typer.echo("\nMCP Clients")

    any_detected = False
    for _, detector, adapter in _tool_pairs():
        installed = detector.is_installed()
        cfg = adapter.config_path()

        if not installed:
            typer.echo(f"  {no} {detector.name}: not installed")
            continue

        any_detected = True
        injected = adapter.has_server(SERVER_NAME)
        inj_mark = ok if injected else no
        typer.echo(f"  {ok} {detector.name}: detected")
        typer.echo(f"      Config:             {cfg}")
        typer.echo(f"      agent-corex inject: {inj_mark} {'Yes' if injected else 'No'}")

    if not any_detected:
        typer.echo("  (No supported AI tools detected)")

    # ── Available tools ──────────────────────────────────────────────────────
    typer.echo("\nAvailable Tools")
    router = ToolRouter()
    tools = router.tools_list()

    free_tools = [t for t in tools if t.get("annotations", {}).get("tier") == "free"]
    ent_tools = [t for t in tools if t.get("annotations", {}).get("tier") == "enterprise"]

    typer.echo(f"  Free ({len(free_tools)}):")
    for t in free_tools:
        typer.echo(f"    {ok} {t['name']}")

    typer.echo(f"  Enterprise ({len(ent_tools)}):")
    locked = not local_config.is_logged_in()
    for t in ent_tools:
        mark = f"{no} [locked]" if locked else ok
        typer.echo(f"    {mark} {t['name']}")

    if locked and ent_tools:
        typer.echo("\n  Run  agent-corex login  to unlock enterprise tools.")

    # ── Sync status ──────────────────────────────────────────────────────────
    typer.echo("\nSync Status")
    if local_config.is_logged_in():
        import json as _json

        installed_file = local_config.CONFIG_DIR / "installed_servers.json"
        packs_file = local_config.CONFIG_DIR / "installed_packs.json"
        local_servers: list = []
        local_packs: list = []
        try:
            if installed_file.exists():
                local_servers = _json.loads(installed_file.read_text(encoding="utf-8"))
        except Exception:
            pass
        try:
            if packs_file.exists():
                local_packs = _json.loads(packs_file.read_text(encoding="utf-8"))
        except Exception:
            pass
        typer.echo(f"  Installed packs   : {', '.join(local_packs) if local_packs else '(none)'}")
        typer.echo(
            f"  Installed servers : {', '.join(local_servers) if local_servers else '(none)'}"
        )
        typer.echo("  Run: agent-corex sync  (to sync with backend)")
    else:
        typer.echo("  Not connected — run: agent-corex login")

    typer.echo("")


@app.command()
def sync(
    push_only: bool = typer.Option(
        False, "--push-only", help="Only push local state, skip pull/install"
    ),
):
    """
    Sync packs and servers between CLI and backend.

    \\b
    Steps:
      1. Pull enabled packs/servers from backend
      2. Install any missing locally
      3. Push local install state back to backend

    Requires login (run: agent-corex login).

    Example:
        agent-corex sync
        agent-corex sync --push-only
    """
    import json as _json
    import httpx
    from agent_core import local_config

    if not local_config.is_logged_in():
        typer.echo("Not logged in. Run: agent-corex login", err=True)
        raise typer.Exit(1)

    auth_header = local_config.get_auth_header()
    if not auth_header:
        typer.echo("No credentials found. Run: agent-corex login", err=True)
        raise typer.Exit(1)

    base_url = local_config.get_base_url()
    installed_file = local_config.CONFIG_DIR / "installed_servers.json"
    packs_file = local_config.CONFIG_DIR / "installed_packs.json"

    def _load_json_list(path: pathlib.Path) -> list:
        try:
            if path.exists():
                return _json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
        return []

    def _save_json_list(path: pathlib.Path, data: list) -> None:
        path.write_text(_json.dumps(sorted(set(data)), indent=2), encoding="utf-8")

    if not push_only:
        # ── Step 1: Pull from backend ─────────────────────────────────────────
        typer.echo("\nPulling configuration...")
        try:
            resp = httpx.get(
                f"{base_url}/user/servers",
                headers={"Authorization": auth_header},
                timeout=15.0,
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                typer.echo("[error] Authentication failed. Run: agent-corex login", err=True)
            else:
                typer.echo(f"[error] Sync failed (HTTP {exc.response.status_code})", err=True)
            raise typer.Exit(1)
        except Exception as exc:
            typer.echo(f"[error] Could not connect to Agent-CoreX: {exc}", err=True)
            raise typer.Exit(1)

        try:
            remote = resp.json()
        except Exception:
            typer.echo(
                "[error] Agent-CoreX returned an unexpected response. "
                "Try again or run: agent-corex login --no-browser",
                err=True,
            )
            raise typer.Exit(1)
        remote_servers: list = remote.get("enabled_servers", [])
        remote_packs: list = remote.get("enabled_packs", [])
        typer.echo(f"  Remote servers : {', '.join(remote_servers) or 'none'}")
        typer.echo(f"  Remote packs   : {', '.join(remote_packs) or 'none'}")

        # ── Step 2: Install missing ───────────────────────────────────────────
        local_servers = set(_load_json_list(installed_file))
        local_packs = set(_load_json_list(packs_file))

        missing_servers = [s for s in remote_servers if s not in local_servers]
        missing_packs = [p for p in remote_packs if p not in local_packs]

        if missing_servers or missing_packs:
            typer.echo("\nInstalling missing items locally...")
            for srv in missing_servers:
                typer.echo(f"  Installing: {srv}...", nl=False)
                try:
                    result = (
                        PackManager.install_server(srv)
                        if hasattr(PackManager, "install_server")
                        else None
                    )
                    local_servers.add(srv)
                    typer.echo(" ✓")
                except Exception:
                    local_servers.add(srv)  # Mark as tracked even if install fails
                    typer.echo(" (registered)")
            for pack in missing_packs:
                typer.echo(f"  Pack enabled: {pack} ✓")
                local_packs.add(pack)
            _save_json_list(installed_file, list(local_servers))
            _save_json_list(packs_file, list(local_packs))
        else:
            typer.echo("  Local state is up to date.")
    else:
        local_servers = set(_load_json_list(installed_file))
        local_packs = set(_load_json_list(packs_file))

    # ── Step 3: Push local state ──────────────────────────────────────────────
    typer.echo("\nPushing local state...")
    try:
        push_resp = httpx.post(
            f"{base_url}/user/servers",
            headers={"Authorization": auth_header, "Content-Type": "application/json"},
            json={
                "installed_servers": sorted(local_servers),
                "installed_packs": sorted(local_packs),
            },
            timeout=15.0,
        )
        push_resp.raise_for_status()
        try:
            result = push_resp.json()
            typer.echo(
                f"  Synced {result.get('synced_servers', 0)} servers, "
                f"{result.get('synced_packs', 0)} packs."
            )
        except Exception:
            typer.echo("  Synced.")
    except Exception as exc:
        typer.echo(f"  [warn] Push failed (will retry next sync): {exc}")

    typer.echo("\n✓ Sync complete.\n")


@app.command(name="registry")
def list_registry():
    """
    Browse all installable MCP servers from the Agent-Corex registry.

    Example:
        agent-corex registry
    """
    try:
        import httpx
    except ImportError:
        typer.echo("httpx is required. Run: pip install httpx", err=True)
        raise typer.Exit(1)

    from agent_core import local_config

    base_url = local_config.get_base_url()
    typer.echo("\nFetching registry...\n")

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{base_url}/mcp_registry")
            resp.raise_for_status()
            servers = resp.json()
    except Exception as e:
        typer.echo(f"Failed to fetch registry: {e}", err=True)
        raise typer.Exit(1)

    if not servers:
        typer.echo("Registry is empty.")
        return

    # Group by category
    categories: dict[str, list] = {}
    for s in servers:
        cat = s.get("category", "general")
        categories.setdefault(cat, []).append(s)

    typer.echo(f"Available MCP Servers  ({len(servers)} total)\n")
    for cat, entries in sorted(categories.items()):
        typer.echo(f"  {cat.upper()}")
        for s in entries:
            env_note = f"  [needs: {', '.join(s['env_required'])}]" if s.get("env_required") else ""
            desc = s.get("description", "")[:55]
            typer.echo(f"    {s['name']:<22}  {desc}{env_note}")
        typer.echo("")

    typer.echo("Install any:  agent-corex install-mcp <name>")


@app.command(name="install-mcp")
def install_mcp(
    name: str = typer.Argument(..., help="Registry server slug, e.g. 'github'"),
    tool: Optional[str] = typer.Option(
        None,
        "--tool",
        "-t",
        help="Target: claude | cursor | vscode | vscode-insiders | vscodium. All detected if omitted.",
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts"),
):
    """
    Install a named MCP server from the registry into your local AI tools.

    \\b
    What this does:
      1. Fetches the server definition from the Agent-Corex registry
      2. Prompts for any required environment variables (e.g. API tokens)
      3. Injects the server into Claude Desktop, Cursor, and/or VS Code

    Example:
        agent-corex install-mcp github
        agent-corex install-mcp postgres --tool claude --yes
    """
    try:
        import httpx
    except ImportError:
        typer.echo("httpx is required. Run: pip install httpx", err=True)
        raise typer.Exit(1)

    from agent_core import local_config

    # ── Fetch registry entry ────────────────────────────────────────────────
    base_url = local_config.get_base_url()
    typer.echo(f"\nFetching '{name}' from registry...")

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{base_url}/mcp_registry/{name}")
            if resp.status_code == 404:
                typer.echo(f"\n  Server '{name}' not found in registry.", err=True)
                typer.echo("  Browse available servers:  agent-corex registry")
                raise typer.Exit(1)
            resp.raise_for_status()
            entry = resp.json()
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"\nFailed to reach registry: {e}", err=True)
        raise typer.Exit(1)

    # ── Show server info ────────────────────────────────────────────────────
    display_name = entry.get("display_name") or name
    cmd_str = entry["command"] + " " + " ".join(entry.get("args", []))
    typer.echo(f"\n  {display_name}")
    typer.echo(f"  {entry.get('description', '')}")
    typer.echo(f"  Command: {cmd_str}")
    if entry.get("install_note"):
        typer.echo(f"  Note:    {entry['install_note']}")

    # ── Collect environment variables ───────────────────────────────────────
    env_values: dict[str, str] = {}

    env_required: list[str] = entry.get("env_required", [])
    if env_required:
        typer.echo(f"\n  Required environment variables:")
        for key in env_required:
            val = typer.prompt(f"    {key}", hide_input=True)
            if val.strip():
                env_values[key] = val.strip()
            else:
                typer.echo(f"    (skipping {key} — server may not work without it)")

    env_optional: list[str] = entry.get("env_optional", [])
    if env_optional:
        typer.echo(f"\n  Optional environment variables (Enter to skip):")
        for key in env_optional:
            val = typer.prompt(f"    {key}", default="", show_default=False)
            if val.strip():
                env_values[key] = val.strip()

    # ── Build per-tool server definitions ──────────────────────────────────
    base_def: dict = {
        "command": entry["command"],
        "args": entry.get("args", []),
    }
    if env_values:
        base_def["env"] = env_values

    vscode_def = {"type": "stdio", **base_def}

    _VSCODE_KEYS = {"vscode", "vscode-insiders", "vscodium"}
    all_pairs = [
        (slug, det, adp, vscode_def if slug in _VSCODE_KEYS else base_def)
        for slug, det, adp in _tool_pairs()
    ]

    if tool:
        t = tool.lower()
        pairs = [(k, d, a, sd) for k, d, a, sd in all_pairs if k == t]
        if not pairs:
            typer.echo(
                f"\nUnknown tool: {tool!r}. "
                "Use: claude, cursor, vscode, vscode-insiders, vscodium",
                err=True,
            )
            raise typer.Exit(1)
    else:
        pairs = all_pairs

    # ── Inject into each detected tool ──────────────────────────────────────
    typer.echo(f"\nInstalling '{name}' into detected tools...\n")

    any_action = False
    for _, detector, adapter, server_def in pairs:
        if not detector.is_installed():
            typer.echo(f"  [-] {detector.name}: not detected — skipping")
            continue

        already = adapter.has_server(name)
        verb = "Update" if already else "Install"

        if not yes:
            confirmed = typer.confirm(f"  {verb} '{name}' in {detector.name}?", default=True)
            if not confirmed:
                typer.echo("      Skipped.")
                continue

        bak = adapter.inject_server(name, server_def)
        action = "Updated" if already else "Installed"
        typer.echo(f"  [+] {action} in {detector.name}")
        if bak:
            typer.echo(f"      Backup: {bak}")
        any_action = True

    if not any_action:
        typer.echo("\nNo changes made.")
    else:
        typer.echo("\nDone. Restart your tools for changes to take effect.")
        typer.echo("Run  agent-corex status  to verify.")


@app.command()
def logout(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """
    Remove stored API key and user info from ~/.agent-corex/config.json.

    Example:
        agent-corex logout
        agent-corex logout --yes
    """
    from agent_core import local_config

    if not local_config.is_logged_in():
        typer.echo("Not logged in. Nothing to remove.")
        return

    user = local_config.get("user") or {}
    name = user.get("name") or user.get("user_id", "unknown")

    if not yes:
        confirmed = typer.confirm(f"Log out {name}?", default=True)
        if not confirmed:
            typer.echo("Aborted.")
            return

    data = local_config.load()
    for key in (
        "api_key",
        "user",
        "access_token",
        "refresh_token",
        "token_expires_at",
        "user_email",
    ):
        data.pop(key, None)
    local_config.save(data)

    typer.echo("Logged out.")


@app.command()
def keys():
    """
    Show the active API key and account info; verify with backend.

    Example:
        agent-corex keys
    """
    from agent_core import local_config

    if not local_config.is_logged_in():
        typer.echo("Not logged in. Run: agent-corex login", err=True)
        raise typer.Exit(1)

    api_key = local_config.get_api_key()
    user = local_config.get("user") or {}

    masked = api_key[:10] + "..." + api_key[-4:] if len(api_key) > 14 else api_key

    typer.echo("\nActive credentials")
    typer.echo(f"  API key : {masked}")
    typer.echo(f"  User ID : {user.get('user_id', '—')}")
    typer.echo(f"  Name    : {user.get('name', '—')}")

    typer.echo("\nVerifying key...")
    try:
        import httpx

        base_url = local_config.get_base_url()
        with httpx.Client(base_url=base_url, timeout=5.0) as client:
            resp = client.post(
                "/auth/login",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"api_key": api_key},
            )
            if resp.status_code == 200:
                info = resp.json()
                typer.echo("[+] Key is valid.")
                data = local_config.load()
                data["user"] = info
                local_config.save(data)
            elif resp.status_code == 401:
                typer.echo("[-] Key is no longer valid. Run: agent-corex login", err=True)
            else:
                typer.echo(f"[?] Could not verify key (HTTP {resp.status_code}).")
    except ImportError:
        typer.echo("(httpx not installed — skipping remote verification)")
    except Exception:
        typer.echo("(Backend unreachable — cannot verify.)")


@app.command()
def detect():
    """
    Detect installed AI tools (Claude Desktop, Cursor, VS Code) and show config paths.

    Example:
        agent-corex detect
    """
    col_w = 20
    typer.echo(f"\n{'Tool':<{col_w}}  {'Installed':<10}  Config path")
    typer.echo("-" * 70)

    any_found = False
    for _, d, _ in _tool_pairs():
        installed = d.is_installed()
        cfg = d.config_path()
        if installed:
            any_found = True
        status = "Yes" if installed else "No"
        path = str(cfg) if cfg else "—"
        typer.echo(f"{d.name:<{col_w}}  {status:<10}  {path}")

    if not any_found:
        typer.echo("\nNo supported tools detected.")
        typer.echo("Install Claude Desktop, Cursor, or VS Code to get started.")
    else:
        typer.echo("\nRun  agent-corex init  to inject agent-corex into detected tools.")


@app.command()
def eject(
    tool: Optional[str] = typer.Option(
        None,
        "--tool",
        "-t",
        help="Target: claude | cursor | vscode | vscode-insiders | vscodium. Ejects from all if omitted.",
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts"),
):
    """
    Remove the agent-corex MCP entry from Claude Desktop / Cursor / VS Code configs.

    Example:
        agent-corex eject
        agent-corex eject --tool claude --yes
    """
    SERVER_NAME = "agent-corex"
    all_pairs = _tool_pairs()

    if tool:
        t = tool.lower()
        pairs = [(k, d, a) for k, d, a in all_pairs if k == t]
        if not pairs:
            typer.echo(
                f"Unknown tool: {tool!r}. Use: claude, cursor, vscode, vscode-insiders, vscodium",
                err=True,
            )
            raise typer.Exit(1)
    else:
        pairs = all_pairs

    any_action = False
    for _, detector, adapter in pairs:
        if not detector.is_installed():
            typer.echo(f"  [-] {detector.name}: not detected — skipping")
            continue

        if not adapter.has_server(SERVER_NAME):
            typer.echo(f"  [-] {detector.name}: agent-corex not present — skipping")
            continue

        if not yes:
            confirmed = typer.confirm(f"  Remove agent-corex from {detector.name}?", default=True)
            if not confirmed:
                typer.echo("      Skipped.")
                continue

        bak = adapter.remove_server(SERVER_NAME)
        typer.echo(f"  [+] Removed from {detector.name}")
        if bak:
            typer.echo(f"      Backup: {bak}")
        any_action = True

    if not any_action:
        typer.echo("\nNo changes made.")
    else:
        typer.echo("\nDone. Restart the tool for changes to take effect.")


@app.command(name="list")
def list_servers(
    all_tools: bool = typer.Option(
        False,
        "--all",
        "-a",
        help="Include tools that are not installed (show empty rows).",
    ),
):
    """
    List all MCP servers currently injected across detected tools.

    Example:
        agent-corex list
        agent-corex list --all
    """
    any_output = False

    for _, detector, adapter in _tool_pairs():
        if not detector.is_installed():
            if all_tools:
                typer.echo(f"\n{detector.name}: not installed")
            continue

        servers = adapter.get_servers()
        typer.echo(f"\n{detector.name}  ({adapter.config_path()})")

        if not servers:
            typer.echo("  (no servers configured)")
            any_output = True
            continue

        # Column widths
        name_w = max(len(n) for n in servers) + 2
        for name, cfg in servers.items():
            cmd = cfg.get("command", "")
            args = " ".join(str(a) for a in cfg.get("args", []))
            typer.echo(f"  {name:<{name_w}}  {cmd} {args}".rstrip())
        any_output = True

    if not any_output:
        typer.echo("\nNo supported AI tools detected. Run  agent-corex detect  for details.")


@app.command()
def update(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts"),
    tool: Optional[str] = typer.Option(
        None,
        "--tool",
        "-t",
        help="Limit to one tool: claude | cursor | vscode | vscode-insiders | vscodium",
    ),
):
    """
    Re-fetch all installed MCP servers from the registry and update their configs.

    For every server injected across your AI tools, this command fetches the
    latest definition from the Agent-Corex registry and re-injects it if anything
    has changed (command, args, or env).

    Example:
        agent-corex update
        agent-corex update --tool claude --yes
    """
    try:
        import httpx
    except ImportError:
        typer.echo("httpx is required. Run: pip install httpx", err=True)
        raise typer.Exit(1)

    from agent_core import local_config

    base_url = local_config.get_base_url()
    all_pairs = _tool_pairs()

    if tool:
        t = tool.lower()
        all_pairs = [(k, d, a) for k, d, a in all_pairs if k == t]
        if not all_pairs:
            typer.echo(
                f"Unknown tool: {tool!r}. Use: claude, cursor, vscode, vscode-insiders, vscodium",
                err=True,
            )
            raise typer.Exit(1)

    _VSCODE_KEYS = {"vscode", "vscode-insiders", "vscodium"}

    # Cache registry responses so we only fetch each server name once
    _registry_cache: dict[str, dict | None] = {}

    def _fetch_entry(name: str) -> dict | None:
        if name in _registry_cache:
            return _registry_cache[name]
        try:
            with httpx.Client(timeout=8.0) as client:
                resp = client.get(f"{base_url}/mcp_registry/{name}")
                entry = resp.json() if resp.status_code == 200 else None
        except Exception:
            entry = None
        _registry_cache[name] = entry
        return entry

    def _build_def(entry: dict, vscode: bool) -> dict:
        base: dict = {"command": entry["command"], "args": entry.get("args", [])}
        if vscode:
            base = {"type": "stdio", **base}
        return base

    total_checked = total_updated = 0
    typer.echo("\nChecking for updates...\n")

    for slug, detector, adapter in all_pairs:
        if not detector.is_installed():
            continue

        servers = adapter.get_servers()
        is_vscode = slug in _VSCODE_KEYS

        for server_name, current_def in servers.items():
            if server_name == "agent-corex":
                continue  # agent-corex updates itself via pip

            total_checked += 1
            entry = _fetch_entry(server_name)
            if entry is None:
                typer.echo(f"  [?] {detector.name} / {server_name}: not in registry — skipping")
                continue

            new_def = _build_def(entry, is_vscode)

            # Compare only the fields we care about
            changed = (
                current_def.get("command") != new_def.get("command")
                or current_def.get("args") != new_def.get("args")
                or (is_vscode and current_def.get("type") != "stdio")
            )

            if not changed:
                typer.echo(f"  [=] {detector.name} / {server_name}: up to date")
                continue

            typer.echo(f"  [!] {detector.name} / {server_name}: update available")
            typer.echo(
                f"      current:  {current_def.get('command')} {' '.join(str(a) for a in current_def.get('args', []))}"
            )
            typer.echo(
                f"      registry: {new_def.get('command')} {' '.join(str(a) for a in new_def.get('args', []))}"
            )

            if not yes:
                confirmed = typer.confirm(
                    f"      Update '{server_name}' in {detector.name}?", default=True
                )
                if not confirmed:
                    typer.echo("      Skipped.")
                    continue

            # Preserve env vars the user set — only update command/args/type
            merged = {**current_def, **{k: v for k, v in new_def.items() if k != "env"}}
            bak = adapter.inject_server(server_name, merged)
            typer.echo(f"      [+] Updated")
            if bak:
                typer.echo(f"      Backup: {bak}")
            total_updated += 1

    typer.echo(f"\nChecked {total_checked} server(s). Updated {total_updated}.")
    if total_updated:
        typer.echo("Restart your AI tools for changes to take effect.")


@app.command()
def doctor():
    """
    Diagnose common setup issues.

    Checks Python version, dependencies, config file, backend connectivity,
    API key validity, and MCP injection status across all detected tools.

    Example:
        agent-corex doctor
    """
    import sys
    import shutil

    ok = "[+]"
    warn = "[!]"
    no = "[-]"
    issues: list[str] = []

    typer.echo("\nagent-corex doctor\n")

    # ── 1. Python version ────────────────────────────────────────────────────
    typer.echo("Python")
    major, minor = sys.version_info.major, sys.version_info.minor
    if major >= 3 and minor >= 8:
        typer.echo(f"  {ok} Python {major}.{minor} (>= 3.8 required)")
    else:
        typer.echo(f"  {no} Python {major}.{minor} — 3.8+ required")
        issues.append("Upgrade Python to 3.8 or newer.")

    # ── 2. Key dependencies ──────────────────────────────────────────────────
    typer.echo("\nDependencies")
    for pkg in ("httpx", "typer", "rich"):
        try:
            __import__(pkg)
            typer.echo(f"  {ok} {pkg}")
        except ImportError:
            typer.echo(f"  {no} {pkg} missing")
            issues.append(f"Install missing package:  pip install {pkg}")

    # ── 3. Config file ───────────────────────────────────────────────────────
    typer.echo("\nConfig")
    from agent_core import local_config

    cfg_path = local_config.CONFIG_FILE
    if cfg_path.exists():
        try:
            import json as _json

            _json.loads(cfg_path.read_text(encoding="utf-8"))
            typer.echo(f"  {ok} Config file exists and is valid JSON ({cfg_path})")
        except Exception:
            typer.echo(f"  {no} Config file exists but is not valid JSON ({cfg_path})")
            issues.append(f"Fix or delete corrupted config: {cfg_path}")
    else:
        typer.echo(f"  {warn} Config file not found — run  agent-corex login  first")
        issues.append("Run:  agent-corex login --key <your-api-key>")

    # ── 4. Auth ──────────────────────────────────────────────────────────────
    typer.echo("\nAuth")
    if local_config.is_logged_in():
        user = local_config.get("user") or {}
        name = user.get("name") or user.get("user_id") or "(unknown)"
        typer.echo(f"  {ok} Logged in as {name}")
    else:
        typer.echo(f"  {no} Not logged in")
        issues.append("Run:  agent-corex login --key <your-api-key>")

    # ── 5. Service connectivity ───────────────────────────────────────────────
    typer.echo("\nService")
    base_url = local_config.get_base_url()
    try:
        import httpx as _httpx

        resp = _httpx.get(f"{base_url}/health", timeout=5.0)
        if resp.status_code == 200:
            typer.echo(f"  {ok} Agent-CoreX service reachable")
        else:
            typer.echo(f"  {warn} Service responded with HTTP {resp.status_code}")
            issues.append(f"Agent-CoreX service returned unexpected status {resp.status_code}.")
    except Exception as e:
        typer.echo(f"  {no} Service unreachable: {e}")
        issues.append("Cannot reach Agent-CoreX. Check your internet connection.")

    # ── 6. API key verification ───────────────────────────────────────────────
    typer.echo("\nAPI Key")
    api_key = local_config.get("api_key")
    if not api_key:
        typer.echo(f"  {no} No API key stored")
    else:
        masked = api_key[:10] + "…" + api_key[-4:] if len(api_key) > 14 else "****"
        try:
            import httpx as _httpx

            resp = _httpx.post(
                f"{base_url}/auth/login",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=5.0,
            )
            if resp.status_code == 200:
                typer.echo(f"  {ok} Key valid: {masked}")
            else:
                typer.echo(f"  {no} Key rejected (HTTP {resp.status_code}): {masked}")
                issues.append("API key is invalid. Run:  agent-corex login --key <new-key>")
        except Exception:
            typer.echo(f"  {warn} Key stored ({masked}) — could not verify (service unreachable)")

    # ── 7. Tool detection + injection ────────────────────────────────────────
    typer.echo("\nAI Tools")
    SERVER_NAME = "agent-corex"
    any_found = False
    any_injected = False
    for _, detector, adapter in _tool_pairs():
        if not detector.is_installed():
            typer.echo(f"  {no} {detector.name}: not installed")
            continue
        any_found = True
        injected = adapter.has_server(SERVER_NAME)
        mark = ok if injected else warn
        status = "injected" if injected else "NOT injected"
        typer.echo(f"  {mark} {detector.name}: {status}")
        if injected:
            any_injected = True

    if not any_found:
        typer.echo(f"  {no} No supported AI tools detected")
        issues.append("Install Claude Desktop, Cursor, or VS Code, then run  agent-corex init")
    elif not any_injected:
        issues.append("agent-corex is not injected into any tools. Run:  agent-corex init")

    # ── PATH check ───────────────────────────────────────────────────────────
    typer.echo("\nPATH")
    exe = shutil.which("agent-corex")
    if exe:
        typer.echo(f"  {ok} agent-corex found at {exe}")
    else:
        typer.echo(f"  {no} agent-corex not found in PATH")
        issues.append(
            "Add the Python Scripts directory to your PATH, or reinstall:  pip install agent-corex"
        )

    # ── Pack system ──────────────────────────────────────────────────────────
    typer.echo("\nPack System")
    installed_packs = PackManager.get_installed_packs()
    if installed_packs:
        typer.echo(f"  {ok} {len(installed_packs)} pack(s) installed")
        for pack_name, pack_data in installed_packs.items():
            servers = pack_data.get("servers", [])
            enabled = sum(1 for s in servers if pack_data.get("enabled", {}).get(s, False))
            typer.echo(f"      • {pack_name}: {enabled}/{len(servers)} servers enabled")
    else:
        typer.echo(f"  {warn} No packs installed")
        issues.append("Install a pack:  agent-corex install-pack vibe_coding_pack")

    # ── MCP Config ───────────────────────────────────────────────────────────
    typer.echo("\nMCP Configuration")
    mcp_config_file = pathlib.Path.home() / ".agent-corex" / "mcp.json"
    env_file = pathlib.Path.home() / ".agent-corex" / ".env"

    if mcp_config_file.exists():
        typer.echo(f"  {ok} mcp.json found: {mcp_config_file}")
        # Validate mcp.json
        from agent_core.mcp_config_generator import MCPConfigGenerator

        is_valid, errors = MCPConfigGenerator.validate_config(mcp_config_file)
        if is_valid:
            typer.echo(f"      ✓ Config is valid")
        else:
            for error in errors:
                typer.echo(f"      ✗ {error}")
                issues.append(f"Invalid mcp.json: {error}")
    else:
        typer.echo(f"  {warn} mcp.json not found")
        issues.append("Generate config:  agent-corex generate-mcp-config")

    if env_file.exists():
        from agent_core.env_manager import EnvManager

        env_vars = EnvManager.load_env()
        typer.echo(f"  {ok} .env file found with {len(env_vars)} variable(s)")
    else:
        typer.echo(f"  {warn} .env file not found")
        issues.append("Setup environment variables:  agent-corex setup-env")

    # ── Summary ──────────────────────────────────────────────────────────────
    typer.echo("\n" + "─" * 50)
    if not issues:
        typer.echo(f"{ok} All checks passed. Your setup looks healthy.")
    else:
        typer.echo(f"{warn} Found {len(issues)} issue(s):\n")
        for i, issue in enumerate(issues, 1):
            typer.echo(f"  {i}. {issue}")


@app.command(name="install-pack")
def install_pack(
    pack_name: str = typer.Argument(..., help="Pack name to install (e.g. vibe_coding_pack)"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts"),
):
    """
    Install all MCP servers for a capability pack.

    A pack bundles multiple related capabilities and their MCP servers.

    This command:
    1. Registers the pack in ~/.agent-corex/installed_servers.json
    2. Marks servers as enabled
    3. Prepares to install them into detected AI tools

    \\b
    Example:
        agent-corex install-pack vibe_coding_pack
        agent-corex install-pack vibe_coding_pack --yes
    """
    # Get pack definition
    pack = PackManager.get_pack(pack_name)
    if not pack:
        typer.echo(f"\n✗ Pack '{pack_name}' not found.", err=True)
        available = list(PackManager.list_packs().keys())
        typer.echo(f"\nAvailable packs: {', '.join(available)}", err=True)
        raise typer.Exit(1)

    # Show pack info
    typer.echo(f"\n{pack['name']}")
    typer.echo(f"{pack['description']}")

    servers = PackManager.get_servers_for_pack(pack_name)
    typer.echo(f"\nServers to install ({len(servers)}):")
    for server in servers:
        env_note = (
            f"  (requires: {', '.join(server['env_required'])})" if server["env_required"] else ""
        )
        typer.echo(f"  • {server['name']}: {server['description']}{env_note}")

    # Confirm
    if not yes:
        confirmed = typer.confirm(
            f"\nRegister pack '{pack_name}' and install {len(servers)} server(s)?", default=True
        )
        if not confirmed:
            typer.echo("Aborted.")
            raise typer.Exit(0)

    # Register pack in installed_servers.json
    try:
        result = PackManager.install_pack(pack_name, enable_all=True)
        typer.echo(f"\n✓ Registered pack: {pack_name}")
        typer.echo(f"  Servers enabled: {len(result['servers'])}")
        for srv in result["servers"]:
            typer.echo(f"    • {srv}")
    except Exception as e:
        typer.echo(f"\n✗ Failed to register pack: {e}", err=True)
        raise typer.Exit(1)

    # Now inject into all detected tools
    typer.echo(f"\nInjecting servers into detected tools...")

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

    tools = [
        ("claude", ClaudeDesktopDetector(), ClaudeAdapter()),
        ("cursor", CursorDetector(), CursorAdapter()),
        ("vscode", VSCodeDetector(), VSCodeStableAdapter()),
        ("vscode-insiders", VSCodeInsidersDetector(), VSCodeInsidersAdapter()),
        ("vscodium", VSCodiumDetector(), VSCodiumAdapter()),
    ]

    any_installed = False
    for tool_slug, detector, adapter in tools:
        if not detector.is_installed():
            continue

        for server in servers:
            server_name = server["name"]
            base_def = {
                "command": server["command"],
                "args": server.get("args", []),
            }
            if server.get("env"):
                base_def["env"] = server["env"]

            # VS Code needs "type": "stdio"
            if tool_slug in {"vscode", "vscode-insiders", "vscodium"}:
                server_def = {"type": "stdio", **base_def}
            else:
                server_def = base_def

            try:
                adapter.inject_server(server_name, server_def)
                any_installed = True
            except Exception as e:
                typer.echo(f"  ⚠ {detector.name}/{server_name}: {e}")

    if any_installed:
        typer.echo(f"\n✓ Servers injected into detected tools")
    else:
        typer.echo(f"\n⚠ No tools detected. Run: agent-corex init")

    typer.echo(f"\nNext steps:")
    typer.echo(f"  1. Run: agent-corex setup-env        (configure API keys)")
    typer.echo(f"  2. Run: agent-corex generate-mcp-config  (create unified config)")
    typer.echo(f"  3. Restart your AI tools for changes to take effect")

    # Notify backend (non-fatal — if not logged in, silently skip)
    _notify_backend_pack_installed(pack_name, [s["name"] for s in servers])


def _notify_backend_pack_installed(pack_name: str, server_names: list) -> None:
    """Push pack install state to backend. Non-fatal if not logged in or backend unreachable."""
    import json as _json
    from agent_core import local_config

    auth_header = local_config.get_auth_header()
    if not auth_header:
        return  # Not logged in — skip notification

    base_url = local_config.get_base_url()
    installed_file = local_config.CONFIG_DIR / "installed_servers.json"
    packs_file = local_config.CONFIG_DIR / "installed_packs.json"

    def _load(path) -> list:
        try:
            if path.exists():
                return _json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
        return []

    # Update local tracking files
    local_servers = set(_load(installed_file)) | set(server_names)
    local_packs = set(_load(packs_file)) | {pack_name}
    try:
        installed_file.write_text(_json.dumps(sorted(local_servers), indent=2), encoding="utf-8")
        packs_file.write_text(_json.dumps(sorted(local_packs), indent=2), encoding="utf-8")
    except Exception:
        pass

    # Push to backend
    try:
        import httpx

        httpx.post(
            f"{base_url}/user/servers",
            headers={"Authorization": auth_header, "Content-Type": "application/json"},
            json={
                "installed_servers": sorted(local_servers),
                "installed_packs": sorted(local_packs),
            },
            timeout=10.0,
        )
    except Exception:
        pass  # Non-fatal


@app.command(name="generate-mcp-config")
def generate_mcp_config():
    """
    Generate ~/.agent-corex/mcp.json from all installed MCP servers.

    This command:
    1. Scans all detected AI tools for MCP servers
    2. Merges them into a unified config file
    3. Injects environment variables if ~/.agent-corex/.env exists

    The generated config can be used by:
    - agent-corex serve (MCP gateway)
    - Local MCP client connections

    \\b
    Example:
        agent-corex generate-mcp-config
    """
    from agent_core.mcp_config_generator import MCPConfigGenerator

    typer.echo("\nGenerating MCP configuration...\n")
    typer.echo("Scanning installed tools:")

    try:
        config = MCPConfigGenerator.generate_config(include_env=True)
        config_file = MCPConfigGenerator.write_config(config)

        servers = config.get("mcpServers", {})

        typer.echo(f"\n✓ Generated {config_file}")
        typer.echo(f"  Servers collected: {len(servers)}")
        for name in sorted(servers.keys()):
            typer.echo(f"    • {name}")

        # Validate the config
        is_valid, errors = MCPConfigGenerator.validate_config(config_file)
        if is_valid:
            typer.echo(f"\n✓ Config is valid and ready to use")
        else:
            typer.echo(f"\n⚠ Config has warnings:")
            for error in errors:
                typer.echo(f"    • {error}")

        typer.echo(f"\nNext steps:")
        typer.echo(f"  • Run: agent-corex serve        (start MCP gateway)")
        typer.echo(f"  • Run: agent-corex status       (verify setup)")

    except Exception as e:
        typer.echo(f"\n✗ Error generating config: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="setup-env")
def setup_env():
    """
    Set up environment variables for MCP servers in ~/.agent-corex/.env.

    This command:
    1. Prompts for common API keys and connection strings
    2. Saves them securely in ~/.agent-corex/.env
    3. These are automatically injected into all MCP servers

    Supported variables include:
    - OPENAI_API_KEY, ANTHROPIC_API_KEY
    - SUPABASE_URL, SUPABASE_KEY, SUPABASE_ACCESS_TOKEN
    - REDIS_URL, RAILWAY_API_KEY, RENDER_API_KEY
    - GITHUB_TOKEN, AGENT_COREX_API_KEY

    \\b
    Example:
        agent-corex setup-env
    """
    from agent_core.env_manager import EnvManager

    typer.echo("\n=== Agent-Corex Environment Setup ===\n")
    typer.echo("Configure API keys and connection strings.")
    typer.echo("Press Enter to skip a variable or keep the existing value.\n")

    # Interactive setup
    new_env = EnvManager.interactive_setup()

    if not new_env:
        typer.echo("\nNo environment variables set.")
        return

    # Validate
    is_valid, errors = EnvManager.validate_keys(new_env)

    if not is_valid:
        typer.echo("\n⚠ Validation warnings:")
        for error in errors:
            typer.echo(f"  • {error}")

    # Confirm save
    confirmed = typer.confirm(
        f"\nSave {len(new_env)} variable(s) to ~/.agent-corex/.env?", default=True
    )
    if not confirmed:
        typer.echo("Aborted.")
        return

    # Save
    try:
        env_file = EnvManager.save_env(new_env)
        masked = EnvManager.mask_values(new_env)

        typer.echo(f"\n✓ Saved {env_file}")
        typer.echo(f"  Variables configured: {len(new_env)}")
        for k, v in sorted(masked.items()):
            typer.echo(f"    • {k} = {v}")

        typer.echo(f"\nNext step:")
        typer.echo(f"  Run: agent-corex generate-mcp-config")
    except Exception as e:
        typer.echo(f"\n✗ Error saving environment: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
