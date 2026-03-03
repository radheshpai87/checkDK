"""checkdk docker command – analyse Docker Compose configs via the API."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from ..client import analyze_docker_compose, get_api_url
from ..display import display_analysis_result

_console = Console()


def _find_compose_file() -> Optional[Path]:
    for name in ["docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"]:
        p = Path.cwd() / name
        if p.exists():
            return p
    return None


@click.command(
    "docker",
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.argument("command", nargs=-1, required=True, type=click.UNPROCESSED)
@click.option("--dry-run", is_flag=True, help="Analyse only, do not execute")
@click.option("--force",   is_flag=True, help="Execute even if critical issues are found")
@click.pass_context
def docker_cmd(ctx, command: tuple, dry_run: bool, force: bool) -> None:
    """Wrap Docker commands with pre-execution analysis (via API).

    \b
    Example:
        checkdk docker compose up -d
        checkdk docker compose up -f my-compose.yml
    """
    full_command = ["docker"] + list(command)

    if not (len(command) >= 2 and command[0] == "compose"):
        # Non-compose – pass through directly
        _console.print("[dim]Non-compose command detected. Passing through...[/]\n")
        sys.exit(subprocess.call(full_command))

    # ── Locate compose file ──────────────────────────────────────────────────
    compose_file: str | Path | None = None
    command_list = list(command)
    for i, arg in enumerate(command_list):
        if arg in ["-f", "--file"] and i + 1 < len(command_list):
            compose_file = command_list[i + 1]
            break
    if not compose_file:
        compose_file = _find_compose_file()

    if not compose_file:
        _console.print("[bold yellow]⚠ Warning:[/] No docker-compose.yml found in current directory")
        _console.print("[dim]Skipping analysis...[/]\n")
        sys.exit(subprocess.call(full_command))

    # ── Send to API ──────────────────────────────────────────────────────────
    content = Path(compose_file).read_text(encoding="utf-8")
    _console.print(f"[bold]Analysing:[/] [cyan]{compose_file}[/] via [dim]{get_api_url()}[/]\n")

    try:
        result = analyze_docker_compose(content)
    except Exception as exc:
        _console.print(f"[bold red]API error:[/] {exc}")
        _console.print("[yellow]Is the backend running? Check CHECKDK_API_URL.[/]")
        sys.exit(1)

    display_analysis_result(result)

    if dry_run:
        _console.print("\n[bold cyan]--dry-run:[/] Analysis complete. Skipping execution.")
        sys.exit(0 if result.get("success") else 1)

    has_critical = any(i.get("severity") == "critical" for i in result.get("issues", []))
    if has_critical and not force:
        _console.print("\n[bold red]✗ Critical issues found. Fix them or use --force to proceed.[/]")
        sys.exit(1)

    if result.get("issues") and not force:
        response = _console.input("\n[yellow]⚠ Warnings detected. Continue? (y/N):[/] ").strip().lower()
        if response not in ("y", "yes"):
            _console.print("[yellow]Execution cancelled.[/]")
            sys.exit(0)

    _console.print(f"\n[bold green]→ Executing:[/] [cyan]{' '.join(full_command)}[/]\n")
    sys.exit(subprocess.call(full_command))
