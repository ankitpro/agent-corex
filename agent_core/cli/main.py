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

import typer
from typing import Optional
import json

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
        None, "--version", "-V",
        callback=_version_callback, is_eager=True,
        help="Show version and exit.",
    ),
):
    pass


# ── Shared detector/adapter helper ────────────────────────────────────────────

def _tool_pairs():
    """Return [(slug, detector, adapter), ...] for all 5 supported AI tools."""
    from agent_core.detectors import (
        ClaudeDesktopDetector, CursorDetector,
        VSCodeDetector, VSCodeInsidersDetector, VSCodiumDetector,
    )
    from agent_core.config_adapters import (
        ClaudeAdapter, CursorAdapter,
        VSCodeStableAdapter, VSCodeInsidersAdapter, VSCodiumAdapter,
    )
    return [
        ("claude",          ClaudeDesktopDetector(),  ClaudeAdapter()),
        ("cursor",          CursorDetector(),          CursorAdapter()),
        ("vscode",          VSCodeDetector(),          VSCodeStableAdapter()),
        ("vscode-insiders", VSCodeInsidersDetector(),  VSCodeInsidersAdapter()),
        ("vscodium",        VSCodiumDetector(),        VSCodiumAdapter()),
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
    typer.echo(f"Checking {base_url}/health ...")
    try:
        resp = httpx.get(f"{base_url}/health", timeout=5)
        if resp.status_code == 200:
            typer.echo("✓ Backend is healthy")
        else:
            typer.echo(f"✗ Backend returned status {resp.status_code}", err=True)
            raise typer.Exit(1)
    except httpx.ConnectError:
        typer.echo(f"✗ Cannot connect to {base_url}. Is the backend running?", err=True)
        typer.echo("  Change URL:  agent-corex set-url http://your-host:port", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"✗ Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="set-url")
def set_url(
    url: str = typer.Argument(..., help="URL to set (backend API or frontend)"),
    frontend: bool = typer.Option(
        False, "--frontend", "-f",
        help="Set the frontend URL (login page) instead of the backend API URL",
    ),
):
    """
    Set the backend API URL or frontend URL, saved to ~/.agent-corex/config.json.

    \\b
    Examples:
        agent-corex set-url http://localhost:8000          # backend API (default)
        agent-corex set-url http://localhost:5173 --frontend  # frontend login page
        agent-corex set-url https://api.example.com
        agent-corex set-url https://app.example.com --frontend
    """
    from agent_core import local_config

    url = url.rstrip("/")
    if frontend:
        local_config.set_key("frontend_url", url)
        typer.echo(f"✓ Frontend URL set to: {url}")
        typer.echo("  'agent-corex login' will now open this URL in your browser.")
    else:
        local_config.set_key("base_url", url)
        typer.echo(f"✓ Backend URL set to: {url}")
        typer.echo("  Run  agent-corex health  to verify the connection.")


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
    vscode_written: list[str] = []   # track VS Code variants that were actually written
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
        None, "--key", "-k", help="API key to store (acx_...)"
    ),
    no_browser: bool = typer.Option(
        False, "--no-browser", help="Skip opening browser, just prompt for key"
    ),
):
    """
    Authenticate with Agent-Corex and store your API key.

    \\b
    Flow:
      1. Get an API key from your Agent-Corex dashboard
      2. Paste it here — stored in ~/.agent-corex/config.json
      3. Use  agent-corex set-url  to point to a different backend if needed

    Example:
        agent-corex login
        agent-corex login --key acx_your_key_here
        agent-corex login --no-browser
    """
    import webbrowser
    from agent_core import local_config
    from agent_core.gateway.auth_middleware import validate_api_key_format

    if not api_key:
        if not no_browser:
            login_url = local_config.get_login_url()
            typer.echo(f"\nOpening browser: {login_url}\n")
            try:
                webbrowser.open(login_url)
            except Exception:
                typer.echo("Could not open browser automatically.")
            typer.echo("After logging in, copy your API key from the dashboard.\n")

        api_key = typer.prompt("Paste your API key (acx_...)", hide_input=True)

    api_key = api_key.strip()

    if not validate_api_key_format(api_key):
        typer.echo(
            "Invalid API key format. Keys must start with 'acx_' and be at least 8 characters.",
            err=True,
        )
        raise typer.Exit(1)

    # Try to validate against the backend (gracefully skip if unreachable)
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
                typer.echo("Backend rejected the API key. Please check the key and try again.", err=True)
                raise typer.Exit(1)
    except ImportError:
        pass  # httpx not installed — skip remote validation
    except Exception:
        # Backend unreachable — store key locally anyway (offline mode)
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

    typer.echo("")


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
    typer.echo(f"\nFetching registry from {base_url}...\n")

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
        None, "--tool", "-t",
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
        typer.echo("  Check your backend URL:  agent-corex status")
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
            confirmed = typer.confirm(
                f"  {verb} '{name}' in {detector.name}?", default=True
            )
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
    data.pop("api_key", None)
    data.pop("user", None)
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
    typer.echo(f"  Backend  : {local_config.get_base_url()}")
    typer.echo(f"  Frontend : {local_config.get_frontend_url()}")

    typer.echo("\nVerifying key with backend...")
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
        None, "--tool", "-t",
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
        False, "--all", "-a",
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
        None, "--tool", "-t",
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
            typer.echo(f"      current:  {current_def.get('command')} {' '.join(str(a) for a in current_def.get('args', []))}")
            typer.echo(f"      registry: {new_def.get('command')} {' '.join(str(a) for a in new_def.get('args', []))}")

            if not yes:
                confirmed = typer.confirm(f"      Update '{server_name}' in {detector.name}?", default=True)
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

    # ── 5. Backend connectivity ───────────────────────────────────────────────
    typer.echo("\nBackend")
    base_url = local_config.get_base_url()
    typer.echo(f"  URL: {base_url}")
    try:
        import httpx as _httpx
        resp = _httpx.get(f"{base_url}/health", timeout=5.0)
        if resp.status_code == 200:
            typer.echo(f"  {ok} Reachable (status 200)")
        else:
            typer.echo(f"  {warn} Responded with HTTP {resp.status_code}")
            issues.append(f"Backend at {base_url} returned unexpected status {resp.status_code}.")
    except Exception as e:
        typer.echo(f"  {no} Unreachable: {e}")
        issues.append(f"Cannot reach backend at {base_url}. Check the URL or run the server.")

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
            typer.echo(f"  {warn} Key stored ({masked}) — could not verify (backend unreachable)")

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
        issues.append("Add the Python Scripts directory to your PATH, or reinstall:  pip install agent-corex")

    # ── Summary ──────────────────────────────────────────────────────────────
    typer.echo("\n" + "─" * 50)
    if not issues:
        typer.echo(f"{ok} All checks passed. Your setup looks healthy.")
    else:
        typer.echo(f"{warn} Found {len(issues)} issue(s):\n")
        for i, issue in enumerate(issues, 1):
            typer.echo(f"  {i}. {issue}")


if __name__ == "__main__":
    app()
