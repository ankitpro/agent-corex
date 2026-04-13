"""
Agent-CoreX CLI — thin client for the v2 backend.

Usage:
  agent-corex run "<query>"
  agent-corex run "<query>" --debug
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
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

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
app.add_typer(config_app, name="config")


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


def _render_step_normal(i: int, step: dict) -> None:
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
        if preview:
            console.print(f"[green]{tool}[/green] → {preview}")
        else:
            console.print(f"[green]{tool}[/green] → done")


def _render_debug(response: dict) -> None:
    query = response.get("query", "")
    steps = response.get("steps", [])
    total_ms = response.get("total_latency_ms", 0)

    console.print(f"\n[bold]Query:[/bold] {query}\n")

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
            status_str = f"[yellow]needs input[/yellow]"
        elif step.get("skipped"):
            status_str = f"[dim]skipped ({step.get('skip_reason', '')})[/dim]"
        elif step.get("success"):
            status_str = f"[green]success[/green]"
        else:
            status_str = f"[red]failed[/red]"

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


# ── Commands ──────────────────────────────────────────────────────────────────


@app.command()
def run(
    query: str = typer.Argument(..., help="Natural language query to execute"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Show full execution details"),
) -> None:
    """Execute a task using Agent-CoreX."""
    client = _make_client()
    try:
        response = client.execute_query(query)
    except (AgentCoreXError, ConnectionError, TimeoutError, AuthError) as exc:
        _handle_error(exc)
        return

    if debug:
        _render_debug(response)
    else:
        steps = response.get("steps", [])
        if not steps:
            console.print("[yellow]No steps returned.[/yellow]")
            return
        for i, step in enumerate(steps, 1):
            _render_step_normal(i, step)
        total_ms = response.get("total_latency_ms", 0)
        console.print(f"\n[dim]{len(steps)} step(s) — {total_ms}ms[/dim]")


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
        client.health()
    except AuthError:
        err_console.print("[red]Key rejected by backend.[/red] Check your API key.")
        raise typer.Exit(1)
    except (ConnectionError, TimeoutError) as exc:
        err_console.print(f"[yellow]Warning:[/yellow] Could not verify key ({exc}). Saving anyway.")

    local_config.set_key("api_key", key)
    console.print(f"[green]Logged in.[/green] Key saved: {key[:8]}...")


@app.command()
def logout() -> None:
    """Remove stored API key."""
    local_config.delete_key("api_key")
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
