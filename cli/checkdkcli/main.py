"""checkDK CLI entry point."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console

from . import __version__
from .commands.init    import init_cmd
from .commands.docker  import docker_cmd
from .commands.kubectl import kubectl_cmd
from .commands.predict import predict_cmd

console = Console()

# ── Load ~/.checkdk/.env automatically (if it exists) ────────────────────────

def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore[import]
        candidates = [
            Path.home() / ".checkdk" / ".env",
            Path.cwd() / ".env",
        ]
        for p in candidates:
            if p.exists():
                load_dotenv(p, override=False)  # env vars already set take priority
    except ImportError:
        pass


# ── CLI group ─────────────────────────────────────────────────────────────────

@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="checkDK")
@click.option("--debug", is_flag=True, hidden=True, help="Show full tracebacks")
@click.pass_context
def cli(ctx: click.Context, debug: bool = False) -> None:
    """checkDK – AI-powered Docker/Kubernetes issue detector and fixer.

    Delegates all analysis and prediction to the checkDK backend API.
    Set CHECKDK_API_URL to point to your running backend instance.

    \b
    Quick start:
        export CHECKDK_API_URL=http://localhost:8000
        checkdk docker compose up -d
        checkdk kubectl apply -f deployment.yaml
        checkdk predict --cpu 93 --memory 91
    """
    _load_dotenv()
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug
    if ctx.invoked_subcommand is None:
        console.print(
            f"\n[bold cyan]checkDK[/] v{__version__}\n"
            "[dim]Predict. Diagnose. Fix – Before You Waste Time.[/]\n"
        )
        console.print("Run [bold cyan]checkdk --help[/] for usage.\n")


# ── Register commands ─────────────────────────────────────────────────────────

cli.add_command(init_cmd)
cli.add_command(docker_cmd)
cli.add_command(kubectl_cmd)
cli.add_command(predict_cmd)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    try:
        cli(standalone_mode=True)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled.[/]")
        sys.exit(130)
    except Exception as exc:
        console.print(f"\n[bold red]Error:[/] {exc}")
        if "--debug" in sys.argv or getattr(getattr(cli, 'ctx', None), 'obj', {}).get('debug'):
            raise
        sys.exit(1)


if __name__ == "__main__":
    main()
