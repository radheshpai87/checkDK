"""checkdk chaos - inject failures into Docker containers or Kubernetes pods."""

from __future__ import annotations

import subprocess
import sys
import time
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

_console = Console()

_EXPERIMENTS = ["cpu", "memory", "disk", "network"]

# stress-ng args per experiment type
_STRESS_ARGS: dict[str, list[str]] = {
    "cpu":     ["stress-ng", "--cpu", "2", "--cpu-load", "80"],
    "memory":  ["stress-ng", "--vm", "1", "--vm-bytes", "256M", "--vm-keep"],
    "disk":    ["stress-ng", "--hdd", "1", "--hdd-bytes", "512M"],
    "network": ["tc", "qdisc", "add", "dev", "eth0", "root", "netem", "delay", "200ms"],
}

_UNDO_ARGS: dict[str, Optional[list[str]]] = {
    "cpu":     None,
    "memory":  None,
    "disk":    None,
    "network": ["tc", "qdisc", "del", "dev", "eth0", "root"],
}


def _docker_exec(container: str, cmd: list[str]) -> bool:
    result = subprocess.run(
        ["docker", "exec", container] + cmd, capture_output=True
    )
    return result.returncode == 0


def _kubectl_exec(pod: str, namespace: str, cmd: list[str]) -> bool:
    result = subprocess.run(
        ["kubectl", "exec", pod, "-n", namespace, "--"] + cmd, capture_output=True
    )
    return result.returncode == 0


@click.group("chaos")
def chaos_cmd() -> None:
    """Inject chaos experiments into containers or pods."""


@chaos_cmd.command("docker")
@click.argument("container")
@click.option("--experiment", "-e", default="cpu",
              type=click.Choice(_EXPERIMENTS), show_default=True,
              help="Chaos experiment type")
@click.option("--duration", "-d", default=30, show_default=True, type=int,
              help="Inject duration in seconds")
@click.option("--yes", "--ci", "auto_yes", is_flag=True,
              help="Skip confirmation prompt (for CI)")
def chaos_docker(container: str, experiment: str, duration: int, auto_yes: bool) -> None:
    """Run a chaos experiment on a Docker container.

    Injects CPU/memory/disk/network stress via stress-ng inside the container.
    The container must have stress-ng (or tc) installed; otherwise Docker exec
    will fail gracefully.

    \b
    Example:
        checkdk chaos docker my-api --experiment cpu --duration 60
        checkdk chaos docker my-db  --experiment memory --duration 30 --yes
    """
    if not auto_yes:
        _console.print(Panel(
            f"[bold yellow]About to inject [red]{experiment}[/] chaos into container [cyan]{container}[/][/]\n"
            f"Duration: {duration}s",
            border_style="yellow",
        ))
        click.confirm("Continue?", abort=True)

    _console.print(f"[bold]Injecting [red]{experiment}[/] into [cyan]{container}[/]...[/]")
    stress_cmd = _STRESS_ARGS[experiment] + ["--timeout", f"{duration}s"]
    ok = _docker_exec(container, stress_cmd)
    if not ok:
        _console.print("[yellow]stress-ng not found in container or exec failed.[/]")
        _console.print("[dim]Install stress-ng in the container image to use chaos testing.[/]")
        sys.exit(1)

    _console.print(f"[green]Experiment running for {duration}s...[/]")
    time.sleep(duration)

    undo = _UNDO_ARGS.get(experiment)
    if undo:
        _docker_exec(container, undo)

    _console.print("[bold green]Chaos experiment complete.[/]")

    _show_summary(container=container, platform="docker", experiment=experiment, duration=duration)


@chaos_cmd.command("k8s")
@click.argument("pod")
@click.option("--namespace", "-n", default="default", show_default=True)
@click.option("--experiment", "-e", default="cpu",
              type=click.Choice(_EXPERIMENTS + ["pod-kill"]), show_default=True)
@click.option("--duration", "-d", default=30, show_default=True, type=int)
@click.option("--yes", "--ci", "auto_yes", is_flag=True)
def chaos_k8s(pod: str, namespace: str, experiment: str, duration: int, auto_yes: bool) -> None:
    """Run a chaos experiment on a Kubernetes pod.

    Supports stress-ng injection (cpu/memory/disk/network) and pod-kill.

    \b
    Example:
        checkdk chaos k8s my-pod -n production --experiment cpu --duration 60
        checkdk chaos k8s api-pod --experiment pod-kill --yes
    """
    if not auto_yes:
        _console.print(Panel(
            f"[bold yellow]About to inject [red]{experiment}[/] chaos into pod [cyan]{pod}[/] "
            f"(ns: {namespace})[/]\n"
            f"Duration: {duration}s",
            border_style="yellow",
        ))
        click.confirm("Continue?", abort=True)

    _console.print(f"[bold]Injecting [red]{experiment}[/] into pod [cyan]{pod}[/]...[/]")

    if experiment == "pod-kill":
        result = subprocess.run(
            ["kubectl", "delete", "pod", pod, "-n", namespace, "--force", "--grace-period=0"],
            capture_output=True,
        )
        if result.returncode == 0:
            _console.print(f"[bold red]Pod {pod} deleted (pod-kill experiment).[/]")
        else:
            _console.print(f"[red]Failed to kill pod:[/] {result.stderr.decode()}")
            sys.exit(1)
    else:
        stress_cmd = _STRESS_ARGS[experiment] + ["--timeout", f"{duration}s"]
        ok = _kubectl_exec(pod, namespace, stress_cmd)
        if not ok:
            _console.print("[yellow]stress-ng exec failed. Install stress-ng in the pod image.[/]")
            sys.exit(1)
        _console.print(f"[green]Experiment running for {duration}s...[/]")
        time.sleep(duration)
        undo = _UNDO_ARGS.get(experiment)
        if undo:
            _kubectl_exec(pod, namespace, undo)

    _console.print("[bold green]Chaos experiment complete.[/]")
    _show_summary(pod=pod, namespace=namespace, platform="kubernetes", experiment=experiment, duration=duration)


def _show_summary(
    platform: str, experiment: str, duration: int,
    container: str = "", pod: str = "", namespace: str = "",
) -> None:
    t = Table.grid(padding=(0, 2))
    t.add_column(style="bold")
    t.add_column()
    target = container if platform == "docker" else f"{pod} (ns: {namespace})"
    t.add_row("Platform:",   platform)
    t.add_row("Target:",     target)
    t.add_row("Experiment:", experiment)
    t.add_row("Duration:",   f"{duration}s")
    _console.print(Panel(t, title="Chaos Summary", border_style="magenta"))
