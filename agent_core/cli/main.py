"""
Agent-CoreX CLI — thin client for the v2 backend.

Usage:
  agent-corex run "<query>"
  agent-corex run "<query>" --debug
  agent-corex run "<query>" --local      # force local execution (free tier)
  agent-corex run "<query>" --remote     # force remote execution (premium)
  agent-corex mcp list
  agent-corex mcp add <server>
  agent-corex mcp remove <server>
  agent-corex mcp show
  agent-corex mcp sync
  agent-corex discover [<query>]
  agent-corex search "<query>" [--top-k N]
  agent-corex config set api_url=<url>
  agent-corex config set api_key=<key>
  agent-corex config show
  agent-corex login --key <key>
  agent-corex logout
  agent-corex health
  agent-corex version
"""

from __future__ import annotations

import json
import sys
import time
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agent_core import __version__
from agent_core import local_config
from agent_core.client import (
    AgentCoreXClient,
    AgentCoreXError,
    AuthError,
    ConnectionError,
    TimeoutError,
)

console = Console()
err_console = Console(stderr=True)

app = typer.Typer(
    name="agent-corex",
    help="Agent-CoreX — execute any task with a single query.",
    no_args_is_help=True,
    add_completion=False,
)
config_app = typer.Typer(name="config", help="Manage configuration.", no_args_is_help=True)
mcp_app = typer.Typer(name="mcp", help="Manage local MCP servers.", no_args_is_help=True)
app.add_typer(config_app, name="config")
app.add_typer(mcp_app, name="mcp")


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_client() -> AgentCoreXClient:
    return AgentCoreXClient(
        api_url=local_config.get_api_url(),
        api_key=local_config.get_api_key(),
    )


def _handle_error(exc: Exception) -> None:
    if isinstance(exc, AuthError):
        err_console.print(f"[red]Authentication failed:[/red] {exc}")
        err_console.print("Run: [bold]agent-corex login --key <key>[/bold]")
    elif isinstance(exc, ConnectionError):
        err_console.print(f"[red]Connection error:[/red] {exc}")
        err_console.print(f"Backend URL: [dim]{local_config.get_api_url()}[/dim]")
        err_console.print("Override with: [dim]agent-corex config set api_url=<url>[/dim]")
    elif isinstance(exc, TimeoutError):
        err_console.print(f"[yellow]Timeout:[/yellow] {exc}")
    else:
        err_console.print(f"[red]Error:[/red] {exc}")
    raise typer.Exit(1)


def _render_step_normal(i: int, step: dict, local: bool = False) -> None:
    tool = step.get("tool") or "unknown"
    if step.get("needs_input"):
        missing = ", ".join(step.get("missing_inputs", []))
        console.print(f"[yellow]Step {i}: {tool} — needs input:[/yellow] {missing}")
    elif step.get("skipped"):
        reason = step.get("skip_reason") or "low confidence"
        console.print(f"[dim]Step {i}: {tool} — skipped ({reason})[/dim]")
    elif not step.get("success"):
        err = step.get("error") or "execution failed"
        console.print(f"[red]Step {i}: {tool} — {err}[/red]")
    else:
        preview = step.get("preview") or ""
        mode = "[dim](local)[/dim]" if local else ""
        if preview:
            console.print(f"[green]{tool}[/green] {mode} → {preview}")
        else:
            console.print(f"[green]{tool}[/green] {mode} → done")


def _render_debug(response: dict, local: bool = False) -> None:
    query = response.get("query", "")
    steps = response.get("steps", [])
    total_ms = response.get("total_latency_ms", 0)

    mode_str = "[dim](local execution)[/dim]" if local else "[dim](remote execution)[/dim]"
    console.print(f"\n[bold]Query:[/bold] {query}  {mode_str}\n")

    for i, step in enumerate(steps, 1):
        tool = step.get("tool") or "unknown"
        server = step.get("server") or "—"
        intent = step.get("intent") or "—"
        latency = step.get("latency_ms", 0)
        inputs = step.get("inputs") or {}
        missing = step.get("missing_inputs") or []
        preview = step.get("preview") or ""
        error = step.get("error") or ""

        if step.get("needs_input"):
            status_str = "[yellow]needs input[/yellow]"
        elif step.get("skipped"):
            status_str = f"[dim]skipped ({step.get('skip_reason', '')})[/dim]"
        elif step.get("success"):
            status_str = "[green]success[/green]"
        else:
            status_str = "[red]failed[/red]"

        console.print(f"[bold]Step {i}:[/bold] {tool}  [{status_str}]  [dim]{latency}ms[/dim]")
        console.print(f"  Server:  {server}")
        console.print(f"  Intent:  {intent}")
        if inputs:
            console.print(f"  Inputs:  {json.dumps(inputs, separators=(',', ':'))}")
        if missing:
            console.print(f"  [yellow]Missing: {', '.join(missing)}[/yellow]")
        if preview:
            console.print(f"  Preview: {preview}")
        if error:
            console.print(f"  [red]Error:   {error}[/red]")
        if step.get("ref"):
            console.print(f"  Ref:     [dim]{step['ref']}[/dim]")
        console.print()

    console.print(f"[dim]Total: {len(steps)} step(s), {total_ms}ms[/dim]")


def _execute_locally(
    client: AgentCoreXClient,
    response: dict,
    debug: bool,
) -> None:
    """Execute the planned steps locally using MCPManager, report results back."""
    from agent_core.mcp.manager import MCPManager

    steps = response.get("steps", [])
    query_id = response.get("query_id")
    mgr = MCPManager.from_local_store()

    executed_steps = []
    try:
        for i, step in enumerate(steps):
            if step.get("needs_input"):
                missing = ", ".join(step.get("missing_inputs", []))
                console.print(
                    f"[yellow]Step {i+1}: {step.get('tool')} — needs input:[/yellow] {missing}"
                )
                executed_steps.append(step)
                break

            if step.get("skipped"):
                reason = step.get("skip_reason") or "low confidence"
                console.print(f"[dim]Step {i+1}: {step.get('tool')} — skipped ({reason})[/dim]")
                executed_steps.append(step)
                continue

            server = step.get("server")
            tool = step.get("tool")
            inputs = step.get("inputs") or {}

            if not server or not tool:
                executed_steps.append(step)
                continue

            if server not in mgr.servers:
                err_console.print(
                    f"[red]Server '{server}' not installed locally.[/red] "
                    f"Run: agent-corex mcp add {server}"
                )
                raise typer.Exit(1)

            step_start = time.monotonic()
            try:
                result = mgr.call_tool(server, tool, inputs)
                latency_ms = int((time.monotonic() - step_start) * 1000)
                success = True
                error = None
            except Exception as exc:
                latency_ms = int((time.monotonic() - step_start) * 1000)
                result = None
                success = False
                error = str(exc)
                err_console.print(f"[red]Tool execution failed:[/red] {exc}")

            # Report to backend for state tracking
            preview = ""
            ref = None
            try:
                payload = {
                    "query_id": query_id,
                    "step_index": i,
                    "server": server,
                    "tool": tool,
                    "inputs": inputs,
                    "output": result,
                    "success": success,
                    "error": error,
                    "latency_ms": latency_ms,
                }
                report = client.submit_result(payload)
                ref = report.get("ref")
                preview = report.get("preview", "")
            except Exception:
                # Non-fatal — display output directly if backend reporting fails
                if isinstance(result, dict):
                    content = result.get("content", str(result))
                    lines = str(content).strip().splitlines()
                    preview = "\n".join(lines[:5])
                elif result is not None:
                    preview = str(result)[:200]

            executed_step = dict(step)
            executed_step.update(
                {
                    "success": success,
                    "error": error,
                    "ref": ref,
                    "preview": preview,
                    "latency_ms": latency_ms,
                }
            )
            executed_steps.append(executed_step)

        # Render output
        updated = dict(response)
        updated["steps"] = executed_steps
        total_ms = sum(s.get("latency_ms", 0) for s in executed_steps)
        updated["total_latency_ms"] = total_ms

        if debug:
            _render_debug(updated, local=True)
        else:
            for i, step in enumerate(executed_steps, 1):
                _render_step_normal(i, step, local=True)
            console.print(f"\n[dim]{len(executed_steps)} step(s) — {total_ms}ms[/dim]")

    finally:
        mgr.shutdown_all()


# ── run command ───────────────────────────────────────────────────────────────


@app.command()
def run(
    query: str = typer.Argument(..., help="Natural language query to execute"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Show full execution details"),
    local: bool = typer.Option(False, "--local", help="Force local execution (free tier)"),
    remote: bool = typer.Option(False, "--remote", help="Force remote execution (premium)"),
) -> None:
    """Execute a task using Agent-CoreX.

    Free tier: backend plans, you execute locally via your installed MCP servers.
    Premium:   backend executes on its own workspace (no local servers needed).
    """
    client = _make_client()
    use_remote = remote or (local_config.is_premium() and not local)

    if use_remote:
        # Premium / forced-remote path — backend executes
        try:
            response = client.execute_query(query)
        except (AgentCoreXError, ConnectionError, TimeoutError, AuthError) as exc:
            _handle_error(exc)
            return
        if debug:
            _render_debug(response, local=False)
        else:
            steps = response.get("steps", [])
            if not steps:
                console.print("[yellow]No steps returned.[/yellow]")
                return
            for i, step in enumerate(steps, 1):
                _render_step_normal(i, step, local=False)
            total_ms = response.get("total_latency_ms", 0)
            console.print(f"\n[dim]{len(steps)} step(s) — {total_ms}ms[/dim]")
    else:
        # Free-tier path — backend plans, client executes locally
        try:
            plan = client.plan_query(query)
        except (AgentCoreXError, ConnectionError, TimeoutError, AuthError) as exc:
            _handle_error(exc)
            return
        _execute_locally(client, plan, debug)


# ── mcp subcommands ───────────────────────────────────────────────────────────


@mcp_app.command("list")
def mcp_list() -> None:
    """List all available MCP servers in the Agent-CoreX catalog."""
    client = _make_client()
    try:
        servers = client.list_available_servers()
    except (AgentCoreXError, ConnectionError, TimeoutError, AuthError) as exc:
        _handle_error(exc)
        return

    if not servers:
        console.print("[yellow]No servers in catalog.[/yellow]")
        return

    table = Table(title="Available MCP Servers", show_header=True)
    table.add_column("Name", style="bold")
    table.add_column("Description")
    table.add_column("Status", style="dim")
    for s in servers:
        table.add_row(s.get("name", ""), s.get("description", ""), s.get("status", ""))
    console.print(table)


@mcp_app.command("add")
def mcp_add(
    server_name: str = typer.Argument(..., help="Server name to add (e.g. railway)"),
) -> None:
    """Add an MCP server — installs it locally and syncs to backend."""
    from agent_core.mcp.registry import MCPRegistry
    from agent_core.mcp.local_store import LocalStore

    if not local_config.is_logged_in():
        err_console.print("[red]Not logged in.[/red] Run: agent-corex login --key <key>")
        raise typer.Exit(1)

    registry = MCPRegistry()
    entry = registry.get(server_name)
    if not entry:
        err_console.print(
            f"[red]'{server_name}' not in bundled registry.[/red]\n"
            "You can add it manually by editing [dim]~/.agent-corex/mcp.json[/dim]"
        )
        raise typer.Exit(1)

    store = LocalStore()
    store.add_server(
        server_name,
        command=entry["command"],
        args=entry["args"],
    )
    store.mark_installed(server_name)

    # Sync to backend
    client = _make_client()
    try:
        client.add_server(server_name)
        console.print(f"[green]Added[/green] {server_name}")
        env_required = entry.get("env_required", [])
        if env_required:
            console.print(
                f"[yellow]Note:[/yellow] This server requires env vars: " + ", ".join(env_required)
            )
    except AgentCoreXError as exc:
        console.print(
            f"[yellow]Added locally[/yellow] but backend sync failed: {exc}\n"
            "The server is still usable locally."
        )

    console.print(f"\n[dim]Restart your terminal or IDE to pick up the new MCP server.[/dim]")


@mcp_app.command("remove")
def mcp_remove(
    server_name: str = typer.Argument(..., help="Server name to remove"),
) -> None:
    """Remove a local MCP server and sync the removal to the backend."""
    from agent_core.mcp.local_store import LocalStore

    store = LocalStore()
    removed = store.remove_server(server_name)
    store.mark_removed(server_name)

    if not removed:
        err_console.print(f"[yellow]'{server_name}' was not in ~/.agent-corex/mcp.json[/yellow]")

    # Sync to backend
    if local_config.is_logged_in():
        client = _make_client()
        try:
            client.remove_server(server_name)
        except AgentCoreXError as exc:
            console.print(f"[yellow]Backend sync failed:[/yellow] {exc}")

    console.print(f"[green]Removed[/green] {server_name}")


@mcp_app.command("show")
def mcp_show() -> None:
    """Show locally configured servers and their backend sync status."""
    from agent_core.mcp.local_store import LocalStore

    store = LocalStore()
    local_servers = set(store.list_servers())

    remote_servers: set = set()
    if local_config.is_logged_in():
        client = _make_client()
        try:
            rows = client.list_user_servers()
            remote_servers = {r.get("server_name", "") for r in rows}
        except Exception:
            pass

    if not local_servers and not remote_servers:
        console.print("[yellow]No servers configured.[/yellow] Run: agent-corex mcp add <server>")
        return

    all_servers = local_servers | remote_servers
    table = Table(title="Your MCP Servers", show_header=True)
    table.add_column("Server", style="bold")
    table.add_column("Local")
    table.add_column("Synced to backend")
    for name in sorted(all_servers):
        loc = "[green]yes[/green]" if name in local_servers else "[dim]no[/dim]"
        rem = "[green]yes[/green]" if name in remote_servers else "[dim]no[/dim]"
        table.add_row(name, loc, rem)
    console.print(table)


@mcp_app.command("sync")
def mcp_sync() -> None:
    """Pull backend server list and reconcile with local ~/.agent-corex/mcp.json."""
    from agent_core.mcp.registry import MCPRegistry
    from agent_core.mcp.local_store import LocalStore

    if not local_config.is_logged_in():
        err_console.print("[red]Not logged in.[/red] Run: agent-corex login --key <key>")
        raise typer.Exit(1)

    client = _make_client()
    try:
        remote_rows = client.list_user_servers()
    except (AgentCoreXError, ConnectionError, TimeoutError, AuthError) as exc:
        _handle_error(exc)
        return

    store = LocalStore()
    registry = MCPRegistry()
    local_set = set(store.list_servers())
    remote_set = {r.get("server_name", "") for r in remote_rows}

    added = 0
    for name in remote_set - local_set:
        entry = registry.get(name)
        if entry:
            store.add_server(name, command=entry["command"], args=entry["args"])
            store.mark_installed(name)
            added += 1
            console.print(f"[green]+[/green] {name} (pulled from backend)")
        else:
            console.print(
                f"[yellow]?[/yellow] {name} — not in bundled registry; edit mcp.json manually"
            )

    if added == 0 and not (remote_set - local_set):
        console.print("[dim]Already in sync.[/dim]")
    else:
        console.print(f"[green]Sync complete.[/green] Added {added} server(s).")


# ── discover / search ────────────────────────────────────────────────────────


@app.command()
def discover(
    query: Optional[str] = typer.Argument(None, help="What you want to do (optional)"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Show raw tool data"),
) -> None:
    """Show what you can do with your installed MCP servers.

    If no servers are installed, shows recommended servers to try.
    """
    client = _make_client()
    try:
        result = client.discover_capabilities(query=query, debug=debug)
    except (AgentCoreXError, ConnectionError, TimeoutError, AuthError) as exc:
        _handle_error(exc)
        return

    capabilities = result.get("capabilities", [])
    recommendations = result.get("recommended_servers", [])
    message = result.get("message")

    if capabilities:
        for cap in capabilities:
            server = cap.get("server", "")
            title = cap.get("title", f"Use {server} tools")
            examples = cap.get("examples", [])
            console.print(f"[bold green]{title}[/bold green]  [dim]({server})[/dim]")
            for ex in examples:
                console.print(f"  [dim]•[/dim] {ex}")
        console.print()
    elif recommendations:
        if message:
            console.print(f"[yellow]{message}[/yellow]\n")
        console.print("[bold]Recommended servers to install:[/bold]")
        for rec in recommendations:
            name = rec.get("name", "")
            reason = rec.get("reason", "")
            examples = rec.get("examples", [])
            console.print(f"\n  [bold]{name}[/bold]  — {reason}")
            for ex in examples:
                console.print(f"    [dim]•[/dim] {ex}")
            console.print(f"    [dim]Install:[/dim] agent-corex mcp add {name}")
        console.print()
    else:
        console.print("[yellow]No capabilities found. Try:[/yellow] agent-corex mcp add <server>")

    if debug:
        installed = result.get("installed_servers")
        tools_considered = result.get("tools_considered")
        if installed is not None:
            console.print(f"[dim]Installed servers: {installed}[/dim]")
        if tools_considered:
            console.print(f"[dim]Tools considered: {len(tools_considered)}[/dim]")


@app.command()
def search(
    query: str = typer.Argument(..., help="What you want to do"),
    top_k: int = typer.Option(5, "--top-k", "-n", help="Max results"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Show scores and metadata"),
) -> None:
    """Search for tools matching your query across installed MCP servers.

    If no servers are installed, suggests servers that have relevant tools.
    """
    client = _make_client()
    try:
        result = client.search_tools(query=query, top_k=top_k, debug=debug)
    except (AgentCoreXError, ConnectionError, TimeoutError, AuthError) as exc:
        _handle_error(exc)
        return

    tools = result.get("tools", [])
    recommendations = result.get("recommended_servers", [])

    if tools:
        table = Table(title=f"Tools for: {query}", show_header=True)
        table.add_column("Tool", style="bold")
        table.add_column("Server", style="dim")
        table.add_column("Description")
        if debug:
            table.add_column("Score", style="dim")
        for t in tools:
            row = [t.get("name", ""), t.get("server", ""), t.get("description", "")]
            if debug:
                row.append(str(round(t.get("final_score") or 0.0, 3)))
            table.add_row(*row)
        console.print(table)
    elif recommendations:
        console.print(
            f"[yellow]No installed servers have tools matching '{query}'.[/yellow]\n"
            "[bold]Servers that could help:[/bold]"
        )
        for rec in recommendations:
            name = rec.get("name", "")
            reason = rec.get("reason", "")
            examples = rec.get("examples", [])
            console.print(f"\n  [bold]{name}[/bold]  — {reason}")
            for ex in examples:
                console.print(f"    [dim]•[/dim] {ex}")
            console.print(f"    [dim]Install:[/dim] agent-corex mcp add {name}")
        console.print()
    else:
        console.print(f"[yellow]No tools found for:[/yellow] {query}")

    if debug:
        installed = result.get("installed_servers")
        if installed is not None:
            console.print(f"[dim]Filtered to servers: {installed}[/dim]")


# ── config, login, logout, health, version, serve ────────────────────────────


@config_app.command("set")
def config_set(
    pair: str = typer.Argument(..., help="key=value pair (api_url or api_key)"),
) -> None:
    """Set a configuration value."""
    if "=" not in pair:
        err_console.print("[red]Error:[/red] Expected format: key=value")
        raise typer.Exit(1)
    key, _, value = pair.partition("=")
    key = key.strip()
    value = value.strip()
    allowed = {"api_url", "api_key"}
    if key not in allowed:
        err_console.print(f"[red]Unknown key:[/red] {key!r}. Allowed: {', '.join(sorted(allowed))}")
        raise typer.Exit(1)
    local_config.set_key(key, value)
    console.print(f"[green]Set[/green] {key} = {value if key != 'api_key' else value[:8] + '...'}")


@config_app.command("show")
def config_show() -> None:
    """Show current configuration."""
    api_url = local_config.get_api_url()
    api_key = local_config.get_api_key()
    masked = (api_key[:8] + "...") if api_key else "[dim]not set[/dim]"

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold")
    table.add_column("Value")
    table.add_row("api_url", api_url)
    table.add_row("api_key", masked)
    table.add_row("premium", str(local_config.is_premium()))
    table.add_row("config file", str(local_config.CONFIG_FILE))
    console.print(table)


@app.command()
def login(
    key: Optional[str] = typer.Option(None, "--key", "-k", help="API key (acx_...)"),
) -> None:
    """Store and verify your Agent-CoreX API key."""
    if not key:
        key = typer.prompt("API key", hide_input=True)

    if not local_config.validate_api_key_format(key):
        err_console.print("[red]Invalid key format.[/red] Expected: acx_... (min 12 chars)")
        raise typer.Exit(1)

    # Verify key against backend
    client = AgentCoreXClient(api_url=local_config.get_api_url(), api_key=key)
    try:
        health_resp = client.health()
    except AuthError:
        err_console.print("[red]Key rejected by backend.[/red] Check your API key.")
        raise typer.Exit(1)
    except (ConnectionError, TimeoutError) as exc:
        err_console.print(f"[yellow]Warning:[/yellow] Could not verify key ({exc}). Saving anyway.")
        health_resp = {}

    local_config.set_key("api_key", key)
    # Persist is_premium if backend returns it
    if health_resp.get("is_premium") is not None:
        local_config.set_key("is_premium", health_resp["is_premium"])
    console.print(f"[green]Logged in.[/green] Key saved: {key[:8]}...")


@app.command()
def logout() -> None:
    """Remove stored API key."""
    local_config.delete_key("api_key")
    local_config.delete_key("is_premium")
    console.print("[green]Logged out.[/green]")


@app.command()
def health() -> None:
    """Check Agent-CoreX backend health."""
    client = _make_client()
    try:
        result = client.health()
        status = result.get("status", "unknown")
        version = result.get("version", "unknown")
        console.print(f"[green]Backend:[/green] {status}  [dim](v{version})[/dim]")
        console.print(f"[dim]URL: {local_config.get_api_url()}[/dim]")
    except (AgentCoreXError, ConnectionError, TimeoutError, AuthError) as exc:
        _handle_error(exc)


@app.command()
def version() -> None:
    """Print the CLI version."""
    console.print(f"agent-corex {__version__}")


@app.command()
def serve() -> None:
    """Start the MCP stdio server (for Claude Desktop / Cursor / VS Code)."""
    from agent_core.gateway.gateway_server import run as gateway_run

    gateway_run()


if __name__ == "__main__":
    app()
