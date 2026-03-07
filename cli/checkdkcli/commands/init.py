"""checkdk init command – configure the backend API URL."""

from __future__ import annotations

import os
from pathlib import Path

import click
from rich.console import Console

console = Console()


@click.command("init")
def init_cmd() -> None:
    """Configure checkDK CLI (set API URL, API keys, etc.)."""
    console.print("[bold]checkDK CLI configuration[/]\n")

    default_url = os.getenv("CHECKDK_API_URL", "https://checkdk.app/api")
    api_url = console.input(
        f"  Backend API URL [[dim]{default_url}[/]]: "
    ).strip() or default_url

    env_path = Path.home() / ".checkdk" / ".env"
    env_path.parent.mkdir(parents=True, exist_ok=True)

    # Read existing entries
    existing: list[str] = []
    if env_path.exists():
        existing = [
            line for line in env_path.read_text().splitlines()
            if not line.startswith("CHECKDK_API_URL=")
        ]

    existing.append(f"CHECKDK_API_URL={api_url}")

    env_path.write_text("\n".join(existing) + "\n")

    console.print(
        f"\n[bold green]✓ Saved to:[/] {env_path}\n"
        f"  [dim]CHECKDK_API_URL={api_url}[/]\n\n"
        "Tip: You can also set this as a shell environment variable."
    )
