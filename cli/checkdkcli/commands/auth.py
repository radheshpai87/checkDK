"""checkdk auth commands - login, logout, whoami."""

from __future__ import annotations

import os
import socket
import sys
import threading
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
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


def _find_free_port() -> int:
    """Return an available localhost port."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_token(port: int, timeout: int = 120) -> "str | None":
    """Start a temporary HTTP server on localhost and wait for the OAuth callback."""
    received: dict = {"token": None}
    server_ready = threading.Event()

    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            token = (params.get("token") or [None])[0]
            received["token"] = token

            if token:
                body = (
                    b"<html><body style=\"font-family:sans-serif;text-align:center;"
                    b"margin-top:10vh;background:#0f172a;color:#e2e8f0\">"
                    b"<h2 style=\"color:#818cf8\">checkDK CLI</h2>"
                    b"<p style=\"font-size:1.2rem\">You\'re logged in!"
                    b" You can close this tab.</p></body></html>"
                )
            else:
                body = b"<html><body>Authentication failed. Please try again.</body></html>"

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_) -> None:
            pass  # silence access logs

    httpd = HTTPServer(("127.0.0.1", port), _Handler)
    httpd.timeout = 1  # poll interval

    def _serve() -> None:
        server_ready.set()
        deadline = time.time() + timeout
        while received["token"] is None and time.time() < deadline:
            httpd.handle_request()
        httpd.server_close()

    t = threading.Thread(target=_serve, daemon=True)
    t.start()
    server_ready.wait()
    t.join(timeout + 2)
    return received["token"]


@click.group("auth")
def auth_cmd() -> None:
    """Authentication - log in, log out, or check who you are."""


@auth_cmd.command("login")
def login_cmd() -> None:
    """Log in to checkDK via GitHub or Google OAuth.

    Starts a local callback server, opens the sign-in page in your browser,
    and receives the token automatically - no copy-pasting required.
    """
    port = _find_free_port()
    callback_url = f"http://127.0.0.1:{port}/callback"

    api = get_api_url()
    base = api[: api.rindex("/api")] if "/api" in api else "https://checkdk.app"
    encoded_cb = urllib.parse.quote(callback_url, safe="")
    login_url = f"{base}/login?cli_callback={encoded_cb}"

    _console.print("\n[bold]Opening browser for sign-in...[/]")
    _console.print(
        "  [dim]If the browser did not open, visit:[/]\n"
        f"  [cyan]{login_url}[/]\n"
    )

    try:
        webbrowser.open(login_url)
    except Exception:
        _console.print(f"[yellow]Open this URL in your browser:[/] [cyan]{login_url}[/]\n")

    with _console.status("[bold cyan]Waiting for authentication (2-min timeout)...[/]"):
        token = _wait_for_token(port, timeout=120)

    if not token:
        _console.print("[bold red]Login timed out or was cancelled.[/]")
        sys.exit(1)

    try:
        user = validate_token(token)
    except Exception as exc:
        _console.print(f"[bold red]Token validation failed:[/] {exc}")
        sys.exit(1)

    _save_token(token)
    os.environ["CHECKDK_TOKEN"] = token

    _console.print(Panel(
        f"[bold green]Logged in successfully![/]\n\n"
        f"  Name:     {user.get('name', '?\')}\n"
        f"  Email:    {user.get('email', '?\')}\n"
        f"  Provider: {user.get('provider', '?\')}\n\n"
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
