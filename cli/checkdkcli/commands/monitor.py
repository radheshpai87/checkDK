"""checkdk monitor - real-time container/pod health monitoring over WebSocket."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from typing import Optional

import click
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.text import Text

_console = Console()


def _risk_color(label: str) -> str:
    return {"healthy": "green", "warning": "yellow", "critical": "red"}.get(
        label.lower(), "white"
    )


def _docker_stats(container: str) -> Optional[dict]:
    """Return one snapshot from docker stats --no-stream."""
    try:
        out = subprocess.check_output(
            ["docker", "stats", "--no-stream", "--format",
             "{{.CPUPerc}},{{.MemPerc}},{{.BlockIO}},{{.NetIO}}", container],
            stderr=subprocess.DEVNULL, timeout=5,
        ).decode().strip()
    except Exception:
        return None
    parts = out.split(",")
    if len(parts) < 2:
        return None
    def _pct(s: str) -> float:
        try: return float(s.strip().rstrip("%"))
        except: return 0.0
    return {"cpu": _pct(parts[0]), "memory": _pct(parts[1])}


def _k8s_stats(pod: str, namespace: str) -> Optional[dict]:
    """Return one snapshot via kubectl top pod."""
    try:
        out = subprocess.check_output(
            ["kubectl", "top", "pod", pod, "-n", namespace,
             "--no-headers", "--use-protocol-buffers=false"],
            stderr=subprocess.DEVNULL, timeout=5,
        ).decode().strip()
    except Exception:
        return None
    parts = out.split()
    if len(parts) < 3:
        return None
    def _pct(s: str) -> float:
        try: return float(s.rstrip("m").rstrip("%").rstrip("Mi").rstrip("Gi"))
        except: return 0.0
    return {"cpu": _pct(parts[1]), "memory": _pct(parts[2])}


def _build_table(history: list[dict]) -> Table:
    t = Table(title="checkDK Real-Time Monitor", expand=True)
    t.add_column("#",          style="dim",    width=4)
    t.add_column("CPU %",      style="cyan",   width=8)
    t.add_column("MEM %",      style="cyan",   width=8)
    t.add_column("Risk Label", width=12)
    t.add_column("Confidence", width=12)
    t.add_column("Time",       style="dim")
    for i, row in enumerate(history[-20:], 1):
        label = row.get("label", "unknown")
        conf  = row.get("confidence", 0.0)
        col   = _risk_color(label)
        t.add_row(
            str(i),
            f"{row.get('cpu', 0):.1f}",
            f"{row.get('mem', 0):.1f}",
            Text(label, style=f"bold {col}"),
            f"{conf:.2f}",
            row.get("ts", ""),
        )
    return t


@click.group("monitor")
def monitor_cmd() -> None:
    """Real-time container/pod health monitoring."""


@monitor_cmd.command("docker")
@click.argument("container")
@click.option("--duration", default=0, type=int, show_default=True,
              help="Stop after N seconds (0 = run until Ctrl-C)")
@click.option("--interval", default=5, show_default=True, type=int,
              help="Polling interval in seconds")
@click.option("--api-url", envvar="CHECKDK_API_URL", default="http://localhost:8000",
              help="Backend base URL")
def monitor_docker(container: str, duration: int, interval: int, api_url: str) -> None:
    """Stream live Docker container metrics and predict failure risk.

    \b
    Example:
        checkdk monitor docker my-container
        checkdk monitor docker api --duration 120 --interval 3
    """
    try:
        import websocket  # noqa: F401
    except ImportError:
        _console.print("[bold red]Missing dependency:[/] install websocket-client")
        _console.print("  pip install websocket-client")
        sys.exit(1)

    import websocket as ws_lib

    ws_url = api_url.replace("http://", "ws://").replace("https://", "wss://") + "/ws/monitor"
    history: list[dict] = []
    start = time.time()

    _console.print(f"[bold]Monitoring container:[/] [cyan]{container}[/]  [dim]{ws_url}[/]")
    _console.print("[dim]Press Ctrl-C to stop.[/]\n")

    try:
        sock = ws_lib.create_connection(ws_url, timeout=10)
    except Exception as exc:
        _console.print(f"[bold red]Cannot connect to WebSocket:[/] {exc}")
        _console.print("[yellow]Is the backend running with WebSocket support?[/]")
        sys.exit(1)

    try:
        with Live(_build_table(history), refresh_per_second=1) as live:
            while True:
                if duration and (time.time() - start) >= duration:
                    break
                stats = _docker_stats(container)
                if stats is None:
                    time.sleep(interval)
                    continue
                payload = {
                    "cpu_usage": stats["cpu"], "memory_usage": stats["memory"],
                    "disk_usage": 50.0, "network_latency": 0.0,
                    "restart_count": 0, "probe_failures": 0,
                    "cpu_pressure": 0, "memory_pressure": 0,
                    "pod_age_minutes": 60,
                }
                sock.send(json.dumps(payload))
                raw = sock.recv()
                resp = json.loads(raw)
                history.append({
                    "cpu": stats["cpu"], "mem": stats["memory"],
                    "label": resp.get("label", "?"),
                    "confidence": resp.get("confidence", 0.0),
                    "ts": time.strftime("%H:%M:%S"),
                })
                live.update(_build_table(history))
                time.sleep(interval)
    except KeyboardInterrupt:
        pass
    finally:
        try: sock.close()
        except: pass
    _console.print("\n[bold green]Monitor stopped.[/]")


@monitor_cmd.command("k8s")
@click.argument("pod")
@click.option("--namespace", "-n", default="default", show_default=True)
@click.option("--duration", default=0, type=int, help="Stop after N seconds (0 = Ctrl-C)")
@click.option("--interval", default=5, show_default=True, type=int)
@click.option("--api-url", envvar="CHECKDK_API_URL", default="http://localhost:8000")
def monitor_k8s(pod: str, namespace: str, duration: int, interval: int, api_url: str) -> None:
    """Stream live Kubernetes pod metrics and predict failure risk.

    \b
    Example:
        checkdk monitor k8s my-pod -n production
        checkdk monitor k8s api-pod --duration 120
    """
    try:
        import websocket  # noqa: F401
    except ImportError:
        _console.print("[bold red]Missing dependency:[/] install websocket-client")
        sys.exit(1)

    import websocket as ws_lib

    ws_url = api_url.replace("http://", "ws://").replace("https://", "wss://") + "/ws/monitor"
    history: list[dict] = []
    start = time.time()

    _console.print(f"[bold]Monitoring pod:[/] [cyan]{pod}[/] (ns: {namespace})  [dim]{ws_url}[/]")
    _console.print("[dim]Press Ctrl-C to stop.[/]\n")

    try:
        sock = ws_lib.create_connection(ws_url, timeout=10)
    except Exception as exc:
        _console.print(f"[bold red]Cannot connect to WebSocket:[/] {exc}")
        sys.exit(1)

    try:
        with Live(_build_table(history), refresh_per_second=1) as live:
            while True:
                if duration and (time.time() - start) >= duration:
                    break
                stats = _k8s_stats(pod, namespace)
                if stats is None:
                    time.sleep(interval)
                    continue
                payload = {
                    "cpu_usage": stats["cpu"], "memory_usage": stats["memory"],
                    "disk_usage": 50.0, "network_latency": 0.0,
                    "restart_count": 0, "probe_failures": 0,
                    "cpu_pressure": 0, "memory_pressure": 0,
                    "pod_age_minutes": 60,
                }
                sock.send(json.dumps(payload))
                raw = sock.recv()
                resp = json.loads(raw)
                history.append({
                    "cpu": stats["cpu"], "mem": stats["memory"],
                    "label": resp.get("label", "?"),
                    "confidence": resp.get("confidence", 0.0),
                    "ts": time.strftime("%H:%M:%S"),
                })
                live.update(_build_table(history))
                time.sleep(interval)
    except KeyboardInterrupt:
        pass
    finally:
        try: sock.close()
        except: pass
    _console.print("\n[bold green]Monitor stopped.[/]")
