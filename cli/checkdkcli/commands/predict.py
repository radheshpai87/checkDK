"""checkdk predict command - pod failure risk prediction via the API."""

from __future__ import annotations

import json
import sys
from typing import Optional

import click

from ..client import get_api_url, predict_pod_health
from ..display import console, display_predict_result


@click.command("predict")
@click.option("--cpu",            required=True,  type=float, help="CPU usage % (0-100)")
@click.option("--memory",         required=True,  type=float, help="Memory usage % (0-100)")
@click.option("--disk",           default=50.0,   type=float, show_default=True, help="Disk usage %")
@click.option("--latency",        default=10.0,   type=float, show_default=True, help="Network latency ms")
@click.option("--restarts",       default=0,      type=int,   show_default=True, help="Container restart count")
@click.option("--probe-failures", default=0,      type=int,   show_default=True, help="Probe failure count")
@click.option("--cpu-pressure",   default=0,      type=int,   show_default=True, help="Node CPU pressure (0/1)")
@click.option("--mem-pressure",   default=0,      type=int,   show_default=True, help="Node memory pressure (0/1)")
@click.option("--age",            default=60,     type=int,   show_default=True, help="Pod age in minutes")
@click.option("--service",        default=None,   type=str,   help="Service/pod name")
@click.option("--platform", default="docker", type=click.Choice(["docker", "kubernetes"]), show_default=True)
@click.option("--no-ai",    is_flag=True, help="Skip LLM analysis, ML result only")
@click.option("--json", "output_json", is_flag=True, help="Output raw JSON (for scripting/CI)")
@click.option("--timeout", default=30, show_default=True, type=int, help="API request timeout in seconds")
def predict_cmd(
    cpu: float, memory: float, disk: float, latency: float,
    restarts: int, probe_failures: int, cpu_pressure: int, mem_pressure: int,
    age: int, service: Optional[str], platform: str, no_ai: bool,
    output_json: bool, timeout: int,
) -> None:
    """Predict pod/container failure risk from runtime metrics.

    \b
    Example - healthy pod:
        checkdk predict --cpu 22 --memory 35

    \b
    Example - high-risk pod:
        checkdk predict --cpu 93 --memory 91 --restarts 5 \\
                        --cpu-pressure 1 --mem-pressure 1 \\
                        --service my-api --platform kubernetes

    \b
    CI/scripting:
        checkdk predict --cpu 85 --memory 70 --json | jq .prediction.label
    """
    if not output_json:
        console.print(f"[dim]Sending metrics to API: {get_api_url()}[/]")

    try:
        resp = predict_pod_health(
            cpu=cpu, memory=memory, disk=disk, latency=latency,
            restarts=restarts, probe_failures=probe_failures,
            cpu_pressure=cpu_pressure, mem_pressure=mem_pressure,
            age=age, service=service, platform=platform, no_ai=no_ai,
            timeout=timeout,
        )
    except Exception as exc:
        if output_json:
            print(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[bold red]API error:[/] {exc}")
            console.print("[yellow]Is the backend running? Check CHECKDK_API_URL.[/]")
        sys.exit(1)

    if output_json:
        print(json.dumps(resp, indent=2))
    else:
        display_predict_result(resp, service, platform)
