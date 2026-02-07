"""Main CLI entry point for checkDK."""

import sys
from pathlib import Path
from typing import List, Optional
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .config import CheckDKConfig, get_config
from .models import AnalysisResult, Issue, Severity
from .parsers import DockerComposeParser
from .validators import PortValidator
from .executors import DockerExecutor

console = Console()


def print_banner():
    """Print the checkDK banner."""
    banner = """
[bold cyan]checkDK[/] v{version}
[dim]Predict. Diagnose. Fix – Before You Waste Time.[/]
    """.format(version=__version__)
    console.print(banner)


def find_compose_file() -> Optional[Path]:
    """Find docker-compose.yml in current directory."""
    current_dir = Path.cwd()
    
    # Check common filenames
    for filename in ['docker-compose.yml', 'docker-compose.yaml', 'compose.yml', 'compose.yaml']:
        file_path = current_dir / filename
        if file_path.exists():
            return file_path
    
    return None


def analyze_docker_compose(file_path: Path) -> AnalysisResult:
    """Analyze a Docker Compose file."""
    console.print(f"[bold]Analyzing:[/] [cyan]{file_path}[/]\n")
    
    # Parse configuration
    parser = DockerComposeParser(str(file_path))
    config = parser.parse()
    
    # Collect all issues
    all_issues = parser.issues.copy()
    
    # Run validators
    validators = [
        PortValidator(),
    ]
    
    for validator in validators:
        issues = validator.validate(config)
        all_issues.extend(issues)
    
    # Generate fixes
    fixes = []
    for issue in all_issues:
        if issue.type == issue.type.PORT_CONFLICT:
            fix = PortValidator.generate_fix(issue)
            fixes.append(fix)
    
    # Create result
    result = AnalysisResult(
        success=len([i for i in all_issues if i.severity == Severity.CRITICAL]) == 0,
        issues=all_issues,
        fixes=fixes
    )
    
    return result


def display_analysis_result(result: AnalysisResult):
    """Display the analysis result in a formatted way."""
    
    if not result.issues:
        console.print(Panel(
            "[bold green]✓ No issues found![/]\n[dim]Your configuration looks good.[/]",
            border_style="green"
        ))
        return
    
    # Group issues by severity
    critical = [i for i in result.issues if i.severity == Severity.CRITICAL]
    warnings = [i for i in result.issues if i.severity == Severity.WARNING]
    info = [i for i in result.issues if i.severity == Severity.INFO]
    
    # Display critical issues
    if critical:
        console.print("\n[bold red]✗ Critical Issues:[/]")
        for idx, issue in enumerate(critical, 1):
            console.print(f"\n[bold red]{idx}.[/] {issue.message}")
            if issue.service_name:
                console.print(f"   [dim]Service: {issue.service_name}[/]")
            
            # Show fix if available
            matching_fixes = [f for f in result.fixes if f.description and str(issue.details.get('port', '')) in f.description]
            
            if matching_fixes:
                fix = matching_fixes[0]
                console.print(f"\n   [bold green]💡 Suggested Fix:[/]")
                for step in fix.steps:
                    console.print(f"   [cyan]{step}[/]")
    
    # Display warnings
    if warnings:
        console.print("\n[bold yellow]⚠ Warnings:[/]")
        for idx, issue in enumerate(warnings, 1):
            console.print(f"\n[bold yellow]{idx}.[/] {issue.message}")
            if issue.service_name:
                console.print(f"   [dim]Service: {issue.service_name}[/]")
    
    # Display info
    if info:
        console.print("\n[bold blue]ℹ Info:[/]")
        for idx, issue in enumerate(info, 1):
            console.print(f"[blue]{idx}.[/] {issue.message}")
    
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


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version=__version__, prog_name="checkDK")
def cli(ctx):
    """checkDK - AI-powered Docker/Kubernetes issue detector and fixer."""
    if ctx.invoked_subcommand is None:
        print_banner()
        console.print("Run [bold cyan]checkdk --help[/] for usage information.\n")


@cli.command()
def init():
    """Initialize checkDK configuration."""
    print_banner()
    console.print("[bold]Initializing checkDK configuration...[/]\n")
    
    config = CheckDKConfig()
    config_path = Path.home() / ".checkdk" / "config.yaml"
    
    # Interactive setup
    console.print("[cyan]AI Provider Configuration:[/]")
    provider = console.input("  Provider (aws-bedrock/openai) [aws-bedrock]: ").strip() or "aws-bedrock"
    model = console.input("  Model [claude-3-sonnet]: ").strip() or "claude-3-sonnet"
    
    config.ai.provider = provider
    config.ai.model = model
    
    config.save(config_path)
    
    console.print(f"\n[bold green]✓ Configuration saved to:[/] {config_path}\n")


@cli.command()
@click.argument('command', nargs=-1, required=True)
@click.option('--dry-run', is_flag=True, help='Analyze only, do not execute')
@click.option('--force', is_flag=True, help='Execute even if critical issues are found')
def docker(command: tuple, dry_run: bool, force: bool):
    """Wrap Docker commands with pre-execution analysis.
    
    Example: checkdk docker compose up -d
    """
    print_banner()
    
    # Reconstruct the full command
    full_command = ['docker'] + list(command)
    
    # Check if this is a compose command
    if len(command) >= 2 and command[0] == 'compose':
        # Find docker-compose.yml
        compose_file = find_compose_file()
        
        if not compose_file:
            console.print("[bold yellow]⚠ Warning:[/] No docker-compose.yml found in current directory")
            console.print("[dim]Skipping analysis...[/]\n")
        else:
            # Analyze the configuration
            result = analyze_docker_compose(compose_file)
            display_analysis_result(result)
            
            # If dry-run, stop here
            if dry_run:
                console.print("\n[bold cyan]--dry-run:[/] Analysis complete. Skipping execution.")
                sys.exit(0 if not result.has_critical_errors() else 1)
            
            # Execute the command
            executor = DockerExecutor(full_command)
            exit_code = executor.execute(result, force=force)
            sys.exit(exit_code)
    
    # For non-compose commands, just pass through
    console.print("[dim]Non-compose command detected. Passing through...[/]\n")
    executor = DockerExecutor(full_command)
    exit_code = executor.execute(AnalysisResult(success=True))
    sys.exit(exit_code)


@cli.command()
@click.argument('command', nargs=-1, required=True)
def kubectl(command: tuple):
    """Wrap kubectl commands with pre-execution analysis.
    
    Example: checkdk kubectl apply -f deployment.yaml
    """
    print_banner()
    console.print("[bold yellow]Kubernetes support coming soon![/]")
    console.print(f"[dim]Command:[/] kubectl {' '.join(command)}\n")
    sys.exit(1)


def main():
    """Main entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user.[/]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[bold red]Error:[/] {str(e)}")
        if '--debug' in sys.argv:
            raise
        sys.exit(1)


if __name__ == '__main__':
    main()
