"""checkdk playground command - hybrid AI + rules analysis via the API."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from rich.console import Console

from ..client import analyze_playground, get_api_url
from ..display import console, display_playground_result

_console = Console()


def _detect_filename(path: str) -> str:
    return Path(path).name


@click.command("playground")
@click.option("-f", "--file", "file_path", required=True,
              type=click.Path(exists=True, readable=True),
              help="Path to a Docker Compose or Kubernetes YAML file")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON")
@click.option("--timeout", default=90, show_default=True, type=int,
              help="API request timeout in seconds (LLM calls can be slow)")
def playground_cmd(file_path: str, output_json: bool, timeout: int) -> None:
    """Run a full AI + rule-based analysis on a config file.

    Like the web playground at checkdk.app, but in your terminal.
    Returns a score (0-100), status badge, issue list, and AI-generated fixes.

    \b
    Example:
        checkdk playground -f docker-compose.yml
        checkdk playground -f k8s/deployment.yaml
        checkdk playground -f docker-compose.yml --json | jq .score
    """
    content = Path(file_path).read_text(encoding="utf-8")
    filename = _detect_filename(file_path)

    if not output_json:
        _console.print(f"[bold]Analysing:[/] [cyan]{file_path}[/] via [dim]{get_api_url()}[/]\n")
        _console.print("[dim]Running AI + rule-based analysis (this may take a moment)...[/]\n")

    try:
        result = analyze_playground(content, filename=filename, timeout=timeout)
    except Exception as exc:
        if output_json:
            print(json.dumps({"error": str(exc)}))
        else:
            _console.print(f"[bold red]API error:[/] {exc}")
            _console.print("[yellow]Is the backend running? Check CHECKDK_API_URL.[/]")
        sys.exit(1)

    if output_json:
        print(json.dumps(result, indent=2))
    else:
        display_playground_result(result, file_path)
