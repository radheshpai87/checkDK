"""Rich display helpers shared across CLI commands."""

from __future__ import annotations

import re

from rich.console import Console, Group
from rich.markdown import Markdown
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

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
                        console.print(Markdown(fix["explanation"]))
                    if fix.get("root_cause"):
                        console.print("   [bold cyan]Root Cause:[/]")
                        console.print(Markdown(fix["root_cause"]))
                    if fix.get("steps"):
                        console.print("   [bold cyan]Steps:[/]")
                        for step in fix.get("steps", []):
                            console.print(f"   • {escape(step)}")
                else:
                    console.print("\n   [bold green]💡 Fix:[/]")
                    if fix.get("description"):
                        console.print(Markdown(fix["description"]))
                    for step in fix.get("steps", []):
                        console.print(f"   [cyan]→[/] {escape(step)}")

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

    def _recover_sections(a: dict) -> dict:
        """Client-side recovery for when the backend parser falls back to
        dumping the raw LLM text into assessment['assessment'].

        Detects embedded ## / **Label**: section markers and splits them out
        into the correct keys so the display is always structured correctly.
        """
        raw = a.get("assessment", "")
        # Only attempt recovery when root_cause is missing and the assessment
        # text looks like it contains multiple embedded sections.
        section_pattern = re.compile(
            r"(?:^#{1,6}\s+|\*{1,2})?(assessment|root\s*cause|recommendation)",
            re.IGNORECASE | re.MULTILINE,
        )
        if a.get("root_cause") or not section_pattern.search(raw):
            return a  # already structured or no sections embedded — nothing to do

        # Split on ## Header or **Header**: boundaries
        parts = re.split(
            r"\n?\s*(?:#{1,6}\s+|\*{1,2})(Assessment|Root\s*Cause|Recommendations?)"
            r"(?:\*{1,2})?\s*:?\s*\n?",
            raw,
            flags=re.IGNORECASE,
        )

        recovered: dict = {"assessment": "", "root_cause": "", "recommendations": []}
        i = 0
        # parts is [pre-text, label, content, label, content, ...]
        if parts and not re.search(r"assessment|root|recommend", parts[0], re.IGNORECASE):
            i = 0  # skip leading empty / pre-text
        while i < len(parts) - 1:
            label = parts[i].strip().lower() if i < len(parts) else ""
            content = parts[i + 1].strip() if i + 1 < len(parts) else ""
            if "assessment" in label:
                recovered["assessment"] = content
                i += 2
            elif "root" in label:
                recovered["root_cause"] = content
                i += 2
            elif "recommend" in label:
                for line in content.splitlines():
                    line = line.strip()
                    clean = re.sub(r"^[-•*\d.)]+\s*", "", line).strip()
                    if clean:
                        recovered["recommendations"].append(clean)
                i += 2
            else:
                i += 1

        # Preserve original if recovery produced nothing useful
        if not recovered["assessment"] and not recovered["root_cause"]:
            return a
        # Keep any recommendations already parsed by the backend
        if not recovered["recommendations"] and a.get("recommendations"):
            recovered["recommendations"] = a["recommendations"]
        return recovered

    def _clean(text: str) -> str:
        """Strip stray ## headers and leading **Label**: markers from a field."""
        text = re.sub(r"^\s*#{1,6}\s+\S.*$", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*\*{1,2}[^*]+\*{1,2}\s*:\s*", "", text.strip())
        return text.strip()

    a = _recover_sections(assessment)

    parts: list = []

    if a.get("assessment"):
        parts.append(Text("Assessment", style="bold cyan"))
        parts.append(Markdown(_clean(a["assessment"])))
        parts.append(Text(""))

    if a.get("root_cause"):
        parts.append(Text("Root Cause", style="bold cyan"))
        parts.append(Markdown(_clean(a["root_cause"])))
        parts.append(Text(""))

    if a.get("recommendations"):
        parts.append(Text("What You Can Do", style="bold cyan"))
        rec_lines = "\n".join(
            f"{i}. {_clean(rec)}" for i, rec in enumerate(a["recommendations"], 1)
        )
        parts.append(Markdown(rec_lines))

    if parts:
        console.print(
            Panel(
                Group(*parts),
                title="💡 LLM Health Assessment",
                border_style="cyan",
                expand=True,
            )
        )


# ── Playground display ────────────────────────────────────────────────────────

def display_playground_result(result: dict, file_path: str = "") -> None:
    """Render a PlaygroundAnalysisResult dict returned by /analyze/playground."""
    score  = result.get("score", 0)
    status = result.get("status", "unknown")
    issues = result.get("issues", [])
    fixes  = result.get("fixes", [])

    # Score colour
    if score >= 80:
        score_col = "green"
    elif score >= 50:
        score_col = "yellow"
    else:
        score_col = "red"

    status_badge = {
        "healthy":  "[bold green]● HEALTHY[/]",
        "warning":  "[bold yellow]● WARNING[/]",
        "critical": "[bold red]● CRITICAL[/]",
    }.get(status.lower(), f"[white]{status.upper()}[/]")

    provider = result.get("ai_provider", "")
    header_rows = Table.grid(padding=(0, 2))
    header_rows.add_column(style="bold")
    header_rows.add_column()
    if file_path:
        header_rows.add_row("File:", file_path)
    header_rows.add_row("Status:", status_badge)
    header_rows.add_row("Score:", f"[bold {score_col}]{score}/100[/]")
    if provider:
        header_rows.add_row("AI Provider:", f"[dim]{provider}[/]")
    console.print(Panel(header_rows, title="checkDK Playground", border_style=score_col))

    # Issues
    if not issues:
        console.print("[bold green]✓ No issues found![/]")
        return

    issue_pos: dict[int, int] = {id(i): n for n, i in enumerate(issues)}

    for sev, colour, label in [
        ("critical", "red",    "✗ Critical Issues"),
        ("warning",  "yellow", "⚠ Warnings"),
        ("info",     "blue",   "ℹ Info"),
    ]:
        group = [i for i in issues if i.get("severity") == sev]
        if not group:
            continue
        console.print(f"\n[bold {colour}]{label}:[/]")
        for idx, issue in enumerate(group, 1):
            console.print(f"\n[bold {colour}]{idx}.[/] {issue.get('message', '?')}")
            if issue.get("service_name"):
                console.print(f"   [dim]Service: {issue['service_name']}[/]")
            n = issue_pos.get(id(issue), -1)
            fix = fixes[n] if 0 <= n < len(fixes) else None
            if fix:
                steps = fix.get("steps") or []
                if fix.get("explanation"):
                    console.print("   [bold green]💡 Fix:[/]")
                    console.print(Markdown(fix["explanation"]))
                elif steps:
                    console.print("   [bold green]💡 Fix:[/]")
                for step in steps:
                    console.print(f"   [cyan]→[/] {escape(step)}")

    # AI highlights
    highlights = result.get("highlights", [])
    if highlights:
        console.print("\n[bold cyan]💡 AI Highlights:[/]")
        for hl in highlights:
            console.print(Markdown(hl))


# ── Monitor display helper ────────────────────────────────────────────────────

def display_monitor_result(frame: dict, history: list[dict]) -> None:
    """Render a single real-time monitor prediction frame inline (non-Live mode)."""
    label = frame.get("label", "unknown")
    conf  = frame.get("confidence", 0.0)
    col   = {"healthy": "green", "warning": "yellow", "critical": "red"}.get(
        label.lower(), "white"
    )
    console.print(
        f"[dim]{frame.get('ts', '')}[/]  "
        f"CPU: [cyan]{frame.get('cpu', 0):.1f}%[/]  "
        f"MEM: [cyan]{frame.get('mem', 0):.1f}%[/]  "
        f"Risk: [bold {col}]{label}[/] ({conf:.2f})"
    )
