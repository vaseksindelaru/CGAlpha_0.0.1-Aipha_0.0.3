"""
aiphalab/commands/base.py - Clase Base para Comandos

Proporciona funcionalidad común para todos los comandos.
"""

import click
from typing import Optional, Any, Dict
from core.config_manager import ConfigManager
from rich.console import Console

# Instancia global de console
console: Optional[Console] = None

try:
    console = Console()
except Exception:
    console = None


class BaseCommand:
    """Base class para todos los comandos CLI"""
    
    def __init__(self):
        """Inicializar comando base"""
        self.config = ConfigManager()
        self.console = console
        self.dry_run = False
    
    def print(self, message: str, **kwargs):
        """Print message compatible con Rich"""
        if self.console:
            self.console.print(message, **kwargs)
        else:
            click.echo(message)
    
    def print_error(self, message: str):
        """Print error message"""
        if self.console:
            self.console.print(f"[bold red]❌ {message}[/bold red]")
        else:
            click.secho(f"✗ {message}", fg='red')
    
    def print_success(self, message: str):
        """Print success message"""
        if self.console:
            self.console.print(f"[bold green]✅ {message}[/bold green]")
        else:
            click.secho(f"✓ {message}", fg='green')
    
    def print_warning(self, message: str):
        """Print warning message"""
        if self.console:
            self.console.print(f"[bold yellow]⚠️  {message}[/bold yellow]")
        else:
            click.secho(f"! {message}", fg='yellow')
    
    def print_info(self, message: str):
        """Print info message"""
        if self.console:
            self.console.print(f"[dim]{message}[/dim]")
        else:
            click.echo(message)


def get_console() -> Optional[Console]:
    """Obtener instancia de console global"""
    return console
