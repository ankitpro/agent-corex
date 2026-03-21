"""
Agent-Core CLI interface.

Provides command-line tools for managing and using Agent-Core.
"""

import typer
from typing import Optional
import json

app = typer.Typer(
    name="agent-corex",
    help="Fast, accurate MCP tool retrieval engine for LLMs",
    no_args_is_help=True
)


@app.command()
def retrieve(
    query: str = typer.Argument(..., help="Search query for tool retrieval"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Number of results to return"),
    method: str = typer.Option("hybrid", "--method", "-m", help="Ranking method: keyword, hybrid, or embedding"),
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Path to mcp.json config file")
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

        # Load tools
        registry = ToolRegistry()

        # Try to load MCP servers if config provided
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

        # Retrieve tools
        results = rank_tools(query, tools, top_k=top_k, method=method)

        if not results:
            typer.echo(f"No tools found for query: {query}")
            raise typer.Exit(0)

        # Display results
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
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Path to mcp.json config file")
):
    """
    Start the Agent-Core API server.

    Example:
        agent-corex start --host 0.0.0.0 --port 8000
    """
    import uvicorn
    import os

    # Set config path if provided
    if config:
        os.environ["AGENT_CORE_CONFIG"] = config

    typer.echo(f"Starting Agent-Core API server at http://{host}:{port}")
    typer.echo("Press Ctrl+C to stop\n")

    uvicorn.run(
        "agent_core.api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


@app.command()
def version():
    """Show Agent-Core version."""
    from agent_core import __version__
    typer.echo(f"Agent-Core {__version__}")


@app.command()
def health():
    """Check API health (requires running server)."""
    import requests
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        if response.status_code == 200:
            typer.echo("✓ Agent-Core API is healthy")
        else:
            typer.echo(f"✗ Agent-Core API returned status {response.status_code}", err=True)
    except requests.exceptions.ConnectionError:
        typer.echo("✗ Cannot connect to Agent-Core API. Is it running?", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"✗ Error: {str(e)}", err=True)
        raise typer.Exit(1)


@app.command()
def config():
    """Show configuration information."""
    import pathlib
    from agent_core import __version__

    typer.echo(f"Agent-Core {__version__}\n")
    typer.echo("Configuration:")
    typer.echo(f"  Python version: {__import__('sys').version.split()[0]}")
    typer.echo(f"  Installation path: {pathlib.Path(__import__('agent_core').__file__).parent}")

    # Check if dependencies are installed
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


if __name__ == "__main__":
    app()
