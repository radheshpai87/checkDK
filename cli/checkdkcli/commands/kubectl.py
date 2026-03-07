"""checkdk kubectl command - analyse Kubernetes manifests via the API."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console

from ..client import analyze_kubernetes, get_api_url
from ..display import display_analysis_result

_console = Console()


def _read_manifest(path_str: str) -> tuple:
    """Read a manifest file or directory. Returns (content, display_name).

    For directories, all *.yml and *.yaml files are concatenated with --- separators.
    """
    p = Path(path_str)
    if p.is_dir():
        files = sorted(p.glob("*.yml")) + sorted(p.glob("*.yaml"))
        if not files:
            raise click.ClickException(f"No YAML files found in directory: {path_str}")
        parts = [f.read_text(encoding="utf-8") for f in files]
        return "\n---\n".join(parts), f"{path_str}/ ({len(files)} files)"
    return p.read_text(encoding="utf-8"), str(p)


@click.command(
    "kubectl",
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.argument("command", nargs=-1, required=True, type=click.UNPROCESSED)
@click.option("--dry-run", is_flag=True, help="Analyse without executing")
@click.option("--force",   is_flag=True, help="Execute even with critical issues")
@click.option("--yes", "--ci", "yes", is_flag=True, help="Auto-confirm warnings (non-TTY/CI safe)")
@click.option("--timeout", default=60, show_default=True, type=int, help="API request timeout in seconds")
@click.pass_context
def kubectl_cmd(ctx, command: tuple, dry_run: bool, force: bool, yes: bool, timeout: int) -> None:
    """Wrap kubectl commands with pre-execution analysis (via API).

    \b
    Example:
        checkdk kubectl apply -f deployment.yaml
        checkdk kubectl apply -f k8s/
    """
    args = list(command)
    if not ("apply" in args and "-f" in args):
        _console.print("[dim]Non-apply command detected. Passing through...[/]\n")
        sys.exit(subprocess.call(["kubectl"] + args))

    f_index = args.index("-f")
    file_path = args[f_index + 1] if f_index + 1 < len(args) else None

    if not file_path:
        _console.print("[bold red]Error:[/] -f flag present but no file path given.")
        sys.exit(1)

    try:
        content, display_name = _read_manifest(file_path)
    except Exception as exc:
        _console.print(f"[bold red]Error reading manifest:[/] {exc}")
        sys.exit(1)

    _console.print(f"[bold]Analysing:[/] [cyan]{display_name}[/] via [dim]{get_api_url()}[/]\n")

    try:
        result = analyze_kubernetes(content, filename=file_path, timeout=timeout)
    except Exception as exc:
        _console.print(f"[bold red]API error:[/] {exc}")
        _console.print("[yellow]Is the backend running? Check CHECKDK_API_URL.[/]")
        sys.exit(1)

    display_analysis_result(result)

    if dry_run:
        _console.print("\n[bold cyan]--dry-run:[/] Analysis complete. Skipping execution.")
        sys.exit(0 if result.get("success", True) else 1)

    has_critical = any(i.get("severity") == "critical" for i in result.get("issues", []))
    if has_critical and not force:
        _console.print("\n[bold red]Critical issues found. Use --force to execute anyway.[/]")
        sys.exit(1)

    if result.get("issues") and not force:
        if yes or not sys.stdin.isatty():
            _console.print("\n[yellow]Warnings detected. Auto-confirming (--yes/--ci).[/]")
        else:
            response = _console.input("\n[yellow]Warnings detected. Continue? (y/N):[/] ").strip().lower()
            if response not in ("y", "yes"):
                _console.print("[yellow]Execution cancelled.[/]")
                sys.exit(0)

    _console.print(f"\n[bold green]Executing:[/] [cyan]kubectl {' '.join(args)}[/]\n")
    sys.exit(subprocess.call(["kubectl"] + args))
