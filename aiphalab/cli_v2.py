#!/usr/bin/env python3
"""
aiphalab/cli_v2.py - CLI Refactorizado (v2.0)

Estructura modularizada del CLI anterior.
Reemplaza aiphalab/cli.py (1,649 líneas) con comandos organizados.

Soluciona: P1 #5 - CLI monolítico sin modularización

Cada comando está en su propio módulo bajo aiphalab/commands/
- status.py   : Estado del sistema
- cycle.py    : Ciclos de mejora
- config.py   : Configuración
- history.py  : Historial
- debug.py    : Debugging
"""

import sys
import os
from pathlib import Path

# Setup path
AIPHA_ROOT = Path(__file__).resolve().parent.parent
if str(AIPHA_ROOT) not in sys.path:
    sys.path.insert(0, str(AIPHA_ROOT))

# Load .env
env_path = AIPHA_ROOT / ".env"
if env_path.exists():
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key] = value.strip()

import click
from aiphalab.commands import (
    status_group,
    cycle_group,
    config_group,
    history_group,
    debug_group,
)

# Rich console (optional)
try:
    from rich.console import Console
    console = Console()
except ImportError:
    console = None


@click.group()
@click.option('--dry-run', is_flag=True, default=False, help='Simulate without changes')
@click.pass_context
def cli(ctx, dry_run):
    """
    🦅 AiphaLab CLI v2.0 - Refactored & Modularized
    
    Aipha v0.0.3 - Self-improving trading system
    CGAlpha v0.0.1 - Collaborative governance layer
    
    Run: aipha --help for commands
    """
    ctx.ensure_object(dict)
    ctx.obj['dry_run'] = dry_run
    
    if dry_run:
        if console:
            console.print("[yellow]⚠️  DRY-RUN MODE - Changes simulated only[/yellow]")
        else:
            click.secho("DRY-RUN MODE - Changes simulated only", fg='yellow')


# Register command groups
cli.add_command(status_group)
cli.add_command(cycle_group)
cli.add_command(config_group)
cli.add_command(history_group)
cli.add_command(debug_group)


@cli.command()
def version():
    """Show version information"""
    version_info = {
        "aipha": "0.0.3",
        "cgalpha": "0.0.1",
        "cli": "2.0 (refactored)",
        "python": f"{sys.version.split()[0]}"
    }
    
    if console:
        from rich.table import Table
        table = Table(title="Version Information", show_header=False)
        table.add_column("Component", style="cyan")
        table.add_column("Version", style="magenta")
        
        for component, ver in version_info.items():
            table.add_row(component, ver)
        
        console.print(table)
    else:
        for component, ver in version_info.items():
            click.echo(f"{component}: {ver}")


@cli.command()
def info():
    """Show system information"""
    if console:
        from rich.panel import Panel
        console.print(Panel("""
[bold]AiphaLab CLI v2.0[/bold]

A modularized, production-ready CLI for Aipha.

[bold blue]Available Commands:[/bold blue]
  • status   - System status and health
  • cycle    - Execute improvement cycles
  • config   - Manage configuration
  • history  - View action history
  • debug    - Debugging tools

[bold blue]Usage:[/bold blue]
  aipha status show          # Show system status
  aipha cycle run            # Run one cycle
  aipha config show          # Show configuration
  aipha history actions      # Show action history
  aipha debug check-deps     # Check dependencies

For more: aipha --help
        """, border_style="blue", title="ℹ️  Information"))
    else:
        click.echo("AiphaLab CLI v2.0")
        click.echo("Run: aipha --help for commands")


if __name__ == "__main__":
    cli()
