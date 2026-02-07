"""Docker command executor."""

import subprocess
import sys
from typing import List
from rich.console import Console

from ..models import AnalysisResult

console = Console()


class DockerExecutor:
    """Execute Docker commands after analysis."""
    
    def __init__(self, original_command: List[str]):
        self.original_command = original_command
    
    def execute(self, analysis_result: AnalysisResult, force: bool = False) -> int:
        """Execute the Docker command based on analysis results."""
        
        # If critical errors and not forced, block execution
        if analysis_result.has_critical_errors() and not force:
            console.print("\n[bold red]✗ Execution blocked due to critical issues.[/]")
            console.print("[yellow]Fix the issues above or use --force to execute anyway.[/]")
            return 1
        
        # If warnings, prompt user
        if analysis_result.has_warnings() and not force:
            console.print("\n[yellow]⚠ Warnings detected. Proceed with execution?[/]")
            response = console.input("[bold]Continue? (y/N): [/]").strip().lower()
            if response not in ['y', 'yes']:
                console.print("[yellow]Execution cancelled.[/]")
                return 0
        
        # Execute the command
        console.print(f"\n[bold green]→ Executing:[/] [cyan]{' '.join(self.original_command)}[/]\n")
        
        try:
            result = subprocess.run(
                self.original_command,
                stdout=sys.stdout,
                stderr=sys.stderr,
                text=True
            )
            return result.returncode
        except FileNotFoundError:
            console.print(f"[bold red]Error:[/] Command not found: {self.original_command[0]}")
            console.print("[yellow]Make sure Docker is installed and in your PATH.[/]")
            return 127
        except Exception as e:
            console.print(f"[bold red]Error executing command:[/] {str(e)}")
            return 1
