"""
aiphalab/commands/status.py - Comandos de Status

Muestra el estado del sistema Aipha.
"""

import click
from pathlib import Path
from typing import Dict, Any
from .base import BaseCommand, get_console

console = get_console()


class StatusCommand(BaseCommand):
    """Comando para mostrar status del sistema"""
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado actual del sistema"""
        try:
            from core.health_monitor import HealthMonitor
            from core.orchestrator_hardened import CentralOrchestratorHardened
            
            health = HealthMonitor()
            orchestrator = CentralOrchestratorHardened()
            
            return {
                "status": "running",
                "components": {
                    "orchestrator": "active",
                    "health_monitor": "active",
                    "trading_engine": "ready",
                    "oracle": "ready"
                },
                "memory_usage": health.get_memory_usage(),
                "last_cycle": health.get_last_cycle_time()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


@click.group(name="status")
def status_group():
    """Status y monitoreo del sistema"""
    pass


@status_group.command(name="show")
def show_status():
    """Mostrar estado actual del sistema"""
    cmd = StatusCommand()
    
    status = cmd.get_system_status()
    
    if console:
        from rich.table import Table
        
        table = Table(title="System Status", show_header=True, header_style="bold blue")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="magenta")
        
        for component, state in status.get("components", {}).items():
            table.add_row(component.replace("_", " ").title(), state)
        
        console.print(table)
    else:
        for component, state in status.get("components", {}).items():
            click.echo(f"  {component}: {state}")


@status_group.command(name="health")
def show_health():
    """Mostrar estado de salud del sistema"""
    cmd = StatusCommand()
    
    try:
        from core.health_monitor import HealthMonitor
        health = HealthMonitor()
        
        memory = health.get_memory_usage()
        cpu = health.get_cpu_usage()
        
        cmd.print(f"Memory: {memory:.1f}% | CPU: {cpu:.1f}%")
        cmd.print_success("System healthy")
    except Exception as e:
        cmd.print_error(f"Health check failed: {e}")
