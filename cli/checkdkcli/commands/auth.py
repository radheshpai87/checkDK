"""checkdk auth commands - login, logout, whoami."""

from __future__ import annotations

import os
import sys
import webbrowser
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..client import get_api_url, get_current_user, validate_token

_console = Console()
_ENV_FILE = Path.home() / ".checkdk" / ".env"


def _save_token(token: str) -> None:
    _ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    lines = _ENV_FILE.read_text().splitlines() if _ENV_FILE.exists() else []
    lines = [l for l in lines if not l.startswith("CHECKDK_TOKEN=")]
    lines.append(f"CHECKDK_TOKEN={token}")
    _ENV_FILE.write_text("\n".join(lines) + "\n")


def _remove_token() -> None:
    if not _ENV_FILE.exists():
        return
    lines = [l for l in _ENV_FILE.read_text().splitlines()
             if not l.startswith("CHECKDK_TOKEN=")]
    _ENV_FILE.write_text("\n".join(lines) + "\n")


@click.group("auth")
def auth_cmd() -> None:
    """Authentication - log in, log out, or check who you are."""


@auth_cmd.command("login")
def login_cmd() -> None:
    """Log in to checkDK via GitHub or Google OAuth.

    Opens the sign-in page in your browser, then prompts you to paste
    the JWT token shown after a successful login.
    """
    login_url = f"{get_api_url().replace('/api', '')}/login" if "/api" in get_api_url() else "https://checkdk.app/login"
    _console.print(f"\n[bold]Opening sign-in page:[/] [cyan]{login_url}[/]")
    _console.print("[dim]Sign in with GitHub or Google, then copy the token from the page.[/]\n")

    try:
        webbrowser.open(login_url)
    except Exception:
        _console.print("[yellow]Could not open browser automatically.[/]")
        _console.print(f"Please visit: [cyan]{login_url}[/]\n")

    token = _console.input("[bold]Paste your JWT token here:[/] ").strip()
    if not token:
        _console.print("[red]No token provided. Login cancelled.[/]")
        sys.exit(1)

    try:
        user = validate_token(token)
    except Exception as exc:
        _console.print(f"[bold red]Token validation failed:[/] {exc}")
        _console.print("[yellow]Make sure CHECKDK_API_URL points to a running backend.[/]")
        sys.exit(1)

    _save_token(token)
    os.environ["CHECKDK_TOKEN"] = token

    _console.print(Panel(
        f"[bold green]Logged in successfully![/]\n\n"
        f"  Name:     {user.get('name', '?')}\n"
        f"  Email:    {user.get('email', '?')}\n"
        f"  Provider: {user.get('provider', '?')}\n\n"
        f"[dim]Token saved to {_ENV_FILE}[/]",
        border_style="green",
    ))


@auth_cmd.command("logout")
def logout_cmd() -> None:
    """Remove the stored JWT token."""
    _remove_token()
    if "CHECKDK_TOKEN" in os.environ:
        del os.environ["CHECKDK_TOKEN"]
    _console.print("[bold green]Logged out.[/] Token removed from local config.")


@auth_cmd.command("whoami")
def whoami_cmd() -> None:
    """Show the currently logged-in user."""
    try:
        user = get_current_user()
    except Exception as exc:
        _console.print(f"[bold red]Not logged in or API unreachable:[/] {exc}")
        _console.print("[dim]Run [bold]checkdk auth login[/] first.[/]")
        sys.exit(1)

    t = Table.grid(padding=(0, 2))
    t.add_column(style="bold cyan")
    t.add_column()
    t.add_row("Name:",     user.get("name", "?"))
    t.add_row("Email:",    user.get("email", "?"))
    t.add_row("Provider:", user.get("provider", "?"))
    t.add_row("User ID:",  user.get("userId", "?"))
    _console.print(Panel(t, title="Current User", border_style="cyan"))
