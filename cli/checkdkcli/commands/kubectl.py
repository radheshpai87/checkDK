"""checkdk kubectl command – analyse Kubernetes manifests via the API."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console

from ..client import analyze_kubernetes, get_api_url
from ..display import display_analysis_result

_console = Console()


@click.command(
    "kubectl",
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.argument("command", nargs=-1, required=True, type=click.UNPROCESSED)
@click.option("--dry-run", is_flag=True, help="Analyse without executing")
@click.option("--force",   is_flag=True, help="Execute even with critical issues")
@click.pass_context
def kubectl_cmd(ctx, command: tuple, dry_run: bool, force: bool) -> None:
    """Wrap kubectl commands with pre-execution analysis (via API).

    \b
    Example:
        checkdk kubectl apply -f deployment.yaml
        checkdk kubectl apply -f k8s/
    """
    if not ("apply" in command and "-f" in command):
        # Non-apply – pass through directly
        _console.print("[dim]Non-apply command detected. Passing through...[/]\n")
        sys.exit(subprocess.call(["kubectl"] + list(command)))

    # ── Locate manifest ──────────────────────────────────────────────────────
    f_index = list(command).index("-f")
    file_path = command[f_index + 1] if f_index + 1 < len(command) else None

    if not file_path:
        _console.print("[bold red]Error:[/] -f flag present but no file path given.")
        sys.exit(1)

    content = Path(file_path).read_text(encoding="utf-8")
    _console.print(f"[bold]Analysing:[/] [cyan]{file_path}[/] via [dim]{get_api_url()}[/]\n")

    try:
        result = analyze_kubernetes(content)
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
        _console.print("\n[bold red]✗ Critical issues found. Use --force to execute anyway.[/]")
        sys.exit(1)

    _console.print(f"\n[bold green]→ Executing:[/] [cyan]kubectl {' '.join(command)}[/]\n")
    sys.exit(subprocess.call(["kubectl"] + list(command)))
