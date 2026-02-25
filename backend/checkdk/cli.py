"""Main CLI entry point for checkDK."""

import sys
import yaml
from pathlib import Path
from typing import List, Optional
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .config import CheckDKConfig, get_config
from .models import AnalysisResult, Issue, IssueType, Severity, Fix
from .parsers import DockerComposeParser
from .validators import PortValidator
from .executors import DockerExecutor
from .ai import get_ai_provider

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


def analyze_docker_compose(file_path: Path, use_ai: bool = True) -> AnalysisResult:
    """Analyze a Docker Compose file."""
    console.print(f"[bold]Analyzing:[/] [cyan]{file_path}[/]\n")
    
    # Parse configuration
    parser = DockerComposeParser(str(file_path))
    config = parser.parse()
    
    # Collect all issues
    all_issues = parser.issues.copy()
    
    # Run all validators
    from .validators.compose_validator import DockerComposeValidator
    
    validators = [
        PortValidator(),
    ]
    
    for validator in validators:
        issues = validator.validate(config)
        all_issues.extend(issues)
    
    # Run comprehensive Docker Compose validators on raw config dict
    compose_dict = {'services': config.services, 'volumes': config.volumes, 'networks': config.networks}
    all_issues.extend(DockerComposeValidator.validate_images(compose_dict))
    all_issues.extend(DockerComposeValidator.validate_environment_variables(compose_dict))
    all_issues.extend(DockerComposeValidator.validate_dependencies(compose_dict))
    all_issues.extend(DockerComposeValidator.validate_volumes(compose_dict))
    all_issues.extend(DockerComposeValidator.validate_networks(compose_dict))
    all_issues.extend(DockerComposeValidator.validate_resource_limits(compose_dict))
    
    # Generate fixes
    fixes = []
    
    # Try AI-powered analysis if enabled
    ai_provider = None
    if use_ai:
        try:
            cfg = get_config()
            if cfg.ai.enabled:
                ai_provider = get_ai_provider(cfg)
                if ai_provider:
                    console.print("[dim]🤖 AI analysis enabled[/]")
        except Exception:
            pass
    
    for issue in all_issues:
        # Try AI analysis for critical issues
        if issue.severity == Severity.CRITICAL and ai_provider:
            try:
                # Get config snippet for context
                service_config = config.services.get(issue.service_name, {})
                
                if issue.type == IssueType.PORT_CONFLICT:
                    config_snippet = str(service_config.get('ports', []))
                elif issue.type == IssueType.SERVICE_DEPENDENCY:
                    config_snippet = str(service_config.get('depends_on', []))
                else:
                    config_snippet = str(service_config)[:500]  # Limit size
                
                ai_result = ai_provider.analyze_error(
                    error_message=issue.message,
                    config_snippet=config_snippet,
                    context={
                        'service_name': issue.service_name,
                        'issue_type': issue.type.value,
                        'platform': 'docker-compose'
                    }
                )
                
                if 'error' not in ai_result and ai_result.get('fix_steps'):
                    fix = Fix(
                        description=ai_result.get('explanation', 'AI-generated fix'),
                        steps=ai_result.get('fix_steps', []),
                        auto_applicable=False,
                        explanation=ai_result.get('explanation', ''),
                        root_cause=ai_result.get('root_cause', '')
                    )
                    fixes.append(fix)
                    continue
            except Exception:
                pass  # Silently fall back to rule-based
        
        # Fallback to rule-based fixes
        if issue.type == IssueType.PORT_CONFLICT:
            fix = PortValidator.generate_fix(issue)
        else:
            fix = DockerComposeValidator.generate_fix(issue)
        
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
            
            # Show fix if available - match by index or service name
            if idx <= len(result.fixes):
                fix = result.fixes[idx - 1]
                
                # Check if this is an AI-enhanced fix
                is_ai_fix = fix.explanation or fix.root_cause
                
                if is_ai_fix:
                    console.print(f"\n   [bold green]💡 AI-Enhanced Fix:[/]")
                    
                    # Show explanation if available
                    if fix.explanation:
                        console.print(f"   [yellow]{fix.explanation}[/]")
                        console.print()
                    
                    # Show root cause if available
                    if fix.root_cause:
                        console.print(f"   [bold cyan]Root Cause:[/] {fix.root_cause}")
                        console.print()
                    
                    # Show fix steps
                    console.print(f"   [bold cyan]Steps:[/]")
                    for step in fix.steps:
                        console.print(f"   • {step}")
                else:
                    # Rule-based fix
                    console.print(f"\n   [bold green]💡 Fix:[/]")
                    if fix.description:
                        console.print(f"   [dim]{fix.description}[/]")
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


@cli.command(context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument('command', nargs=-1, required=True, type=click.UNPROCESSED)
@click.option('--dry-run', is_flag=True, help='Analyze only, do not execute')
@click.option('--force', is_flag=True, help='Execute even if critical issues are found')
@click.pass_context
def docker(ctx, command: tuple, dry_run: bool, force: bool):
    """Wrap Docker commands with pre-execution analysis.
    
    Example: checkdk docker compose up -d
    """
    print_banner()
    
    # Reconstruct the full command
    full_command = ['docker'] + list(command)
    
    # Check if this is a compose command
    if len(command) >= 2 and command[0] == 'compose':
        # Find docker-compose.yml (check for -f flag first)
        compose_file = None
        
        # Check if -f or --file is specified
        command_list = list(command)
        for i, arg in enumerate(command_list):
            if arg in ['-f', '--file'] and i + 1 < len(command_list):
                compose_file = command_list[i + 1]
                break
        
        # If not specified, find default
        if not compose_file:
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


@cli.command(context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument('command', nargs=-1, required=True, type=click.UNPROCESSED)
@click.option('--dry-run', is_flag=True, help='Analyze without executing')
@click.option('--force', is_flag=True, help='Execute even with critical issues')
@click.pass_context
def kubectl(ctx, command: tuple, dry_run: bool, force: bool):
    """Wrap kubectl commands with pre-execution analysis.
    
    Example: checkdk kubectl apply -f deployment.yaml
    """
    print_banner()
    
    full_command = ' '.join(command)
    
    # Check if this is an apply command with a file
    if 'apply' in command and '-f' in command:
        # Find the file path
        f_index = command.index('-f')
        if f_index + 1 < len(command):
            file_path = command[f_index + 1]
            
            console.print(f"Analyzing: [cyan]{file_path}[/]\n")
            
            # Analyze the Kubernetes manifest
            result = analyze_kubernetes_manifest(file_path)
            
            # Display results
            display_analysis_result(result)
            
            if dry_run:
                console.print("\n[bold cyan]--dry-run:[/] Analysis complete. Skipping execution.")
                sys.exit(0 if not result.has_critical_errors() else 1)
            
            # Check if we should execute
            if result.has_critical_errors() and not force:
                console.print("\n[bold red]Critical issues found. Use --force to execute anyway.[/]")
                sys.exit(1)
            
            # Execute kubectl command
            import subprocess
            exit_code = subprocess.call(['kubectl'] + list(command))
            sys.exit(exit_code)
    
    # For other kubectl commands, just pass through
    console.print("[dim]Non-apply command detected. Passing through...[/]\n")
    import subprocess
    exit_code = subprocess.call(['kubectl'] + list(command))
    sys.exit(exit_code)


def analyze_kubernetes_manifest(file_path: str) -> AnalysisResult:
    """Analyze a Kubernetes manifest file."""
    from .parsers.kubernetes_parser import KubernetesParser
    from .validators.k8s_validator import KubernetesValidator
    from .config import get_config
    from .ai import get_ai_provider
    
    try:
        # Parse the Kubernetes manifest
        resources = KubernetesParser.parse(file_path)
        
        if not resources:
            return AnalysisResult(
                success=False,
                issues=[Issue(
                    type=IssueType.INVALID_YAML,
                    severity=Severity.CRITICAL,
                    message="No valid Kubernetes resources found in file",
                    file_path=file_path
                )]
            )
        
        # Run all validators
        all_issues = []
        all_issues.extend(KubernetesValidator.validate_services(resources))
        all_issues.extend(KubernetesValidator.validate_deployments(resources))
        all_issues.extend(KubernetesValidator.validate_security(resources))
        all_issues.extend(KubernetesValidator.validate_probes(resources))
        all_issues.extend(KubernetesValidator.validate_labels(resources))
        
        # Initialize AI provider if enabled
        ai_provider = None
        try:
            cfg = get_config()
            if cfg.ai.enabled:
                ai_provider = get_ai_provider(cfg)
                if ai_provider:
                    console.print("[dim]🤖 AI analysis enabled[/]")
        except Exception:
            pass
        
        # Generate fixes
        fixes = []
        for issue in all_issues:
            # Try AI analysis for critical issues
            if issue.severity == Severity.CRITICAL and ai_provider:
                try:
                    # Build better context snippet for AI
                    if issue.type == IssueType.PORT_CONFLICT:
                        port = issue.details.get('port')
                        namespace = issue.details.get('namespace', 'default')
                        context_snippet = f"""
apiVersion: v1
kind: Service
metadata:
  name: {issue.service_name}
  namespace: {namespace}
spec:
  type: NodePort
  ports:
  - nodePort: {port}
    port: 8080
    targetPort: 80
"""
                    else:
                        context_snippet = f"Service: {issue.service_name}, Details: {issue.details}"
                    
                    ai_result = ai_provider.analyze_error(
                        error_message=issue.message,
                        config_snippet=context_snippet,
                        context={
                            'service_name': issue.service_name,
                            'issue_type': issue.type.value,
                            'platform': 'kubernetes',
                            'namespace': issue.details.get('namespace', 'default')
                        }
                    )
                    
                    if 'error' not in ai_result and ai_result.get('fix_steps'):
                        fix = Fix(
                            description=ai_result.get('explanation', 'AI-generated fix'),
                            steps=ai_result.get('fix_steps', []),
                            auto_applicable=False,
                            explanation=ai_result.get('explanation', ''),
                            root_cause=ai_result.get('root_cause', '')
                        )
                        fixes.append(fix)
                        continue
                except Exception:
                    pass  # Fall back to rule-based
            
            # Fallback to rule-based fix
            fix = KubernetesValidator.generate_fix(issue)
            fixes.append(fix)
        
        return AnalysisResult(
            success=len([i for i in all_issues if i.severity == Severity.CRITICAL]) == 0,
            issues=all_issues,
            fixes=fixes
        )
        
    except FileNotFoundError:
        return AnalysisResult(
            success=False,
            issues=[Issue(
                type=IssueType.INVALID_YAML,
                severity=Severity.CRITICAL,
                message=f"File not found: {file_path}",
                file_path=file_path
            )]
        )
    except yaml.YAMLError as e:
        return AnalysisResult(
            success=False,
            issues=[Issue(
                type=IssueType.INVALID_YAML,
                severity=Severity.CRITICAL,
                message=f"Invalid YAML: {str(e)}",
                file_path=file_path
            )]
        )
    except Exception as e:
        return AnalysisResult(
            success=False,
            issues=[Issue(
                type=IssueType.INVALID_YAML,
                severity=Severity.CRITICAL,
                message=f"Analysis failed: {str(e)}",
                file_path=file_path
            )]
        )


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
