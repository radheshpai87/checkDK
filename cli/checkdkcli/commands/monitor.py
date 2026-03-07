"""checkdk monitor - real-time container/pod health monitoring via REST polling.

Polls the /predict endpoint on each interval instead of using a WebSocket
connection, which is blocked by the App Runner infrastructure layer.
"""

from __future__ import annotations

import subprocess
import sys
import time
from typing import Optional

import click
import requests
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.text import Text

from ..client import get_api_url

_console = Console()


def _risk_color(label: str) -> str:
    return {"healthy": "green", "warning": "yellow", "critical": "red"}.get(
        label.lower(), "white"
    )


def _level_color(level: str) -> str:
    return {"low": "green", "medium": "yellow", "high": "red", "critical": "bold red"}.get(
        level.lower(), "white"
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


def _predict(api_url: str, stats: dict, platform: str, service: str, no_ai: bool) -> Optional[dict]:
    """POST to /predict and return the prediction dict, or None on error."""
    try:
        resp = requests.post(
            f"{api_url}/predict",
            json={
                "cpu": stats["cpu"],
                "memory": stats["memory"],
                "disk": 50.0,
                "latency": 10.0,
                "restarts": 0,
                "probe_failures": 0,
                "cpu_pressure": 0,
                "mem_pressure": 0,
                "age": 60,
                "service": service,
                "platform": platform,
                "no_ai": no_ai,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        pred = data.get("prediction", {})
        return {
            "label":      pred.get("label", "unknown"),
            "confidence": pred.get("confidence", 0.0),
            "risk_level": pred.get("risk_level", "unknown"),
        }
    except Exception as exc:
        _console.log(f"[dim red]Predict error: {exc}[/]")
        return None


def _build_table(history: list[dict]) -> Table:
    t = Table(title="checkDK Real-Time Monitor", expand=True)
    t.add_column("#",          style="dim",    width=4)
    t.add_column("CPU %",      style="cyan",   width=8)
    t.add_column("MEM %",      style="cyan",   width=8)
    t.add_column("Risk Label", width=12)
    t.add_column("Risk Level", width=12)
    t.add_column("Confidence", width=12)
    t.add_column("Time",       style="dim")
    for i, row in enumerate(history[-20:], 1):
        label = row.get("label", "unknown")
        level = row.get("risk_level", "unknown")
        conf  = row.get("confidence", 0.0)
        t.add_row(
            str(i),
            f"{row.get('cpu', 0):.1f}",
            f"{row.get('mem', 0):.1f}",
            Text(label, style=f"bold {_risk_color(label)}"),
            Text(level, style=_level_color(level)),
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
@click.option("--no-ai", is_flag=True, default=False,
              help="Skip LLM analysis (faster, ML prediction only)")
def monitor_docker(container: str, duration: int, interval: int, no_ai: bool) -> None:
    """Stream live Docker container metrics and predict failure risk.

    \b
    Example:
        checkdk monitor docker my-container
        checkdk monitor docker api --duration 120 --interval 3
        checkdk monitor docker api --no-ai
    """
    api_url = get_api_url()
    history: list[dict] = []
    start = time.time()

    _console.print(f"[bold]Monitoring container:[/] [cyan]{container}[/]  [dim]{api_url}/predict[/]")
    _console.print("[dim]Press Ctrl-C to stop.[/]\n")

    try:
        with Live(_build_table(history), refresh_per_second=1) as live:
            while True:
                if duration and (time.time() - start) >= duration:
                    break
                stats = _docker_stats(container)
                if stats is None:
                    time.sleep(interval)
                    continue
                pred = _predict(api_url, stats, platform="docker", service=container, no_ai=no_ai)
                if pred:
                    history.append({
                        "cpu":        stats["cpu"],
                        "mem":        stats["memory"],
                        "label":      pred["label"],
                        "risk_level": pred["risk_level"],
                        "confidence": pred["confidence"],
                        "ts":         time.strftime("%H:%M:%S"),
                    })
                    live.update(_build_table(history))
                time.sleep(interval)
    except KeyboardInterrupt:
        pass
    _console.print("\n[bold green]Monitor stopped.[/]")


@monitor_cmd.command("k8s")
@click.argument("pod")
@click.option("--namespace", "-n", default="default", show_default=True)
@click.option("--duration", default=0, type=int, help="Stop after N seconds (0 = Ctrl-C)")
@click.option("--interval", default=5, show_default=True, type=int)
@click.option("--no-ai", is_flag=True, default=False,
              help="Skip LLM analysis (faster, ML prediction only)")
def monitor_k8s(pod: str, namespace: str, duration: int, interval: int, no_ai: bool) -> None:
    """Stream live Kubernetes pod metrics and predict failure risk.

    \b
    Example:
        checkdk monitor k8s my-pod -n production
        checkdk monitor k8s api-pod --duration 120
        checkdk monitor k8s api-pod --no-ai
    """
    api_url = get_api_url()
    history: list[dict] = []
    start = time.time()

    _console.print(f"[bold]Monitoring pod:[/] [cyan]{pod}[/] (ns: {namespace})  [dim]{api_url}/predict[/]")
    _console.print("[dim]Press Ctrl-C to stop.[/]\n")

    try:
        with Live(_build_table(history), refresh_per_second=1) as live:
            while True:
                if duration and (time.time() - start) >= duration:
                    break
                stats = _k8s_stats(pod, namespace)
                if stats is None:
                    time.sleep(interval)
                    continue
                pred = _predict(api_url, stats, platform="kubernetes", service=pod, no_ai=no_ai)
                if pred:
                    history.append({
                        "cpu":        stats["cpu"],
                        "mem":        stats["memory"],
                        "label":      pred["label"],
                        "risk_level": pred["risk_level"],
                        "confidence": pred["confidence"],
                        "ts":         time.strftime("%H:%M:%S"),
                    })
                    live.update(_build_table(history))
                time.sleep(interval)
    except KeyboardInterrupt:
        pass
    _console.print("\n[bold green]Monitor stopped.[/]")
