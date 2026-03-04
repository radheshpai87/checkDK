"""Rich display helpers shared across CLI commands."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


# ── Banners / helpers ─────────────────────────────────────────────────────────

def print_banner(version: str = "0.1.0") -> None:
    console.print(
        f"\n[bold cyan]checkDK[/] v{version}\n"
        "[dim]Predict. Diagnose. Fix – Before You Waste Time.[/]\n"
    )


# ── Analysis result display ───────────────────────────────────────────────────

def display_analysis_result(result: dict) -> None:
    """Render an AnalysisResult dict returned by the API."""
    issues = result.get("issues", [])
    fixes  = result.get("fixes",  [])

    if not issues:
        console.print(
            Panel(
                "[bold green]✓ No issues found![/]\n[dim]Your configuration looks good.[/]",
                border_style="green",
            )
        )
        return

    critical = [i for i in issues if i.get("severity") == "critical"]
    warnings = [i for i in issues if i.get("severity") == "warning"]
    info     = [i for i in issues if i.get("severity") == "info"]

    # Build a map from Python object identity → original index in `issues`.
    # This is safe even when two issues have identical field values (which would
    # cause list.index() to always return the first match).
    issue_pos: dict[int, int] = {id(i): n for n, i in enumerate(issues)}

    if critical:
        console.print("\n[bold red]✗ Critical Issues:[/]")
        for idx, issue in enumerate(critical, 1):
            console.print(f"\n[bold red]{idx}.[/] {issue['message']}")
            if issue.get("service_name"):
                console.print(f"   [dim]Service: {issue['service_name']}[/]")

            issue_idx = issue_pos.get(id(issue), -1)
            fix = fixes[issue_idx] if 0 <= issue_idx < len(fixes) else None
            if fix:
                is_ai = fix.get("explanation") or fix.get("root_cause")
                if is_ai:
                    console.print("\n   [bold green]💡 AI-Enhanced Fix:[/]")
                    if fix.get("explanation"):
                        console.print(f"   [yellow]{fix['explanation']}[/]\n")
                    if fix.get("root_cause"):
                        console.print(f"   [bold cyan]Root Cause:[/] {fix['root_cause']}\n")
                    console.print("   [bold cyan]Steps:[/]")
                    for step in fix.get("steps", []):
                        console.print(f"   • {step}")
                else:
                    console.print("\n   [bold green]💡 Fix:[/]")
                    if fix.get("description"):
                        console.print(f"   [dim]{fix['description']}[/]")
                    for step in fix.get("steps", []):
                        console.print(f"   [cyan]{step}[/]")

    if warnings:
        console.print("\n[bold yellow]⚠ Warnings:[/]")
        for idx, issue in enumerate(warnings, 1):
            console.print(f"\n[bold yellow]{idx}.[/] {issue['message']}")
            if issue.get("service_name"):
                console.print(f"   [dim]Service: {issue['service_name']}[/]")

    if info:
        console.print("\n[bold blue]ℹ Info:[/]")
        for idx, issue in enumerate(info, 1):
            console.print(f"[blue]{idx}.[/] {issue['message']}")

    # Summary
    console.print()
    summary = Table.grid(padding=(0, 2))
    summary.add_column(style="bold")
    summary.add_column()
    if critical:
        summary.add_row("[red]Critical:[/]", str(len(critical)))
    if warnings:
        summary.add_row("[yellow]Warnings:[/]", str(len(warnings)))
    if info:
        summary.add_row("[blue]Info:[/]", str(len(info)))
    console.print(Panel(summary, title="Summary", border_style="cyan"))


# ── Prediction display ────────────────────────────────────────────────────────

def display_predict_result(resp: dict, service: str | None, platform: str) -> None:
    """Render a PredictResponse dict returned by the API."""
    pred = resp.get("prediction", {})
    risk_colour = {
        "low":      "green",
        "medium":   "yellow",
        "high":     "dark_orange",
        "critical": "red",
    }.get(pred.get("risk_level", ""), "white")

    ml_table = Table.grid(padding=(0, 2))
    ml_table.add_column(style="bold")
    ml_table.add_column()
    if service:
        ml_table.add_row("Service:", service)
    ml_table.add_row("Platform:",    platform.capitalize())
    ml_table.add_row("Prediction:",  f"[bold {risk_colour}]{pred.get('label', '?').upper()}[/]")
    ml_table.add_row(
        "Failure Prob.:",
        f"[{risk_colour}]{round(pred.get('confidence', 0) * 100, 1)}%[/]",
    )
    ml_table.add_row("Risk Level:", f"[bold {risk_colour}]{pred.get('risk_level', '?').upper()}[/]")

    border = "red" if pred.get("is_failure") else "green"
    console.print(Panel(ml_table, title="🤖 ML Prediction (Random Forest)", border_style=border))

    assessment = resp.get("assessment")
    if not assessment:
        return

    ai_table = Table.grid(padding=(0, 1))
    ai_table.add_column(style="bold cyan", no_wrap=True)
    ai_table.add_column()

    if assessment.get("assessment"):
        ai_table.add_row("Assessment:", assessment["assessment"])
        ai_table.add_row("", "")
    if assessment.get("root_cause"):
        ai_table.add_row("Root Cause:", assessment["root_cause"])
        ai_table.add_row("", "")
    if assessment.get("recommendations"):
        ai_table.add_row("Actions:", "")
        for i, rec in enumerate(assessment["recommendations"], 1):
            ai_table.add_row(f"  {i}.", rec)

    console.print(Panel(ai_table, title="💡 LLM Health Assessment", border_style="cyan"))
