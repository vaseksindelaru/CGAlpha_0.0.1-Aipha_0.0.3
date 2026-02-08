"""
aiphalab/commands/history.py - Comandos de Historial

Ver historial de cambios y propuestas.
"""

import click
import json
from typing import Dict, Any, List
from pathlib import Path
from .base import BaseCommand, get_console

console = get_console()


class HistoryCommand(BaseCommand):
    """Comando para ver historial"""
    
    def get_action_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtener historial de acciones"""
        try:
            memory_path = Path("./memory")
            history_file = memory_path / "operational/action_history.jsonl"
            
            if not history_file.exists():
                return []
            
            actions = []
            with open(history_file, 'r') as f:
                for line in f.readlines()[-limit:]:
                    if line.strip():
                        actions.append(json.loads(line))
            
            return actions
        except Exception as e:
            return []
    
    def get_proposals_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtener historial de propuestas"""
        try:
            memory_path = Path("./memory")
            proposals_file = memory_path / "proposals.jsonl"
            
            if not proposals_file.exists():
                return []
            
            proposals = []
            with open(proposals_file, 'r') as f:
                for line in f.readlines()[-limit:]:
                    if line.strip():
                        proposals.append(json.loads(line))
            
            return proposals
        except Exception as e:
            return []


@click.group(name="history")
def history_group():
    """Ver historial de cambios y propuestas"""
    pass


@history_group.command(name="actions")
@click.option('--limit', default=10, type=int, help='Número de registros a mostrar')
def show_action_history(limit: int):
    """Mostrar historial de acciones"""
    cmd = HistoryCommand()
    actions = cmd.get_action_history(limit)
    
    if not actions:
        cmd.print_info("No action history found")
        return
    
    if console:
        from rich.table import Table
        
        table = Table(title=f"Action History (Last {limit})", show_header=True, header_style="bold blue")
        table.add_column("Timestamp", style="cyan")
        table.add_column("Action", style="magenta")
        table.add_column("Status", style="green")
        
        for action in actions:
            timestamp = action.get('timestamp', 'N/A')[:19]  # Truncate datetime
            action_type = action.get('action', 'N/A')
            status = action.get('status', 'unknown')
            table.add_row(timestamp, action_type, status)
        
        console.print(table)
    else:
        for action in actions:
            click.echo(f"  {action}")


@history_group.command(name="proposals")
@click.option('--limit', default=10, type=int, help='Número de registros a mostrar')
@click.option('--status', default=None, help='Filtrar por estado (accepted, rejected, pending)')
def show_proposals_history(limit: int, status: str):
    """Mostrar historial de propuestas"""
    cmd = HistoryCommand()
    proposals = cmd.get_proposals_history(limit)
    
    if status:
        proposals = [p for p in proposals if p.get('status') == status]
    
    if not proposals:
        cmd.print_info(f"No proposals found{f' with status={status}' if status else ''}")
        return
    
    if console:
        from rich.table import Table
        
        table = Table(title=f"Proposals History (Last {limit})", show_header=True, header_style="bold blue")
        table.add_column("Timestamp", style="cyan")
        table.add_column("Component", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Score", style="yellow")
        
        for proposal in proposals:
            timestamp = proposal.get('timestamp', 'N/A')[:19]
            component = proposal.get('component', 'N/A')
            proposal_status = proposal.get('status', 'N/A')
            score = proposal.get('score', 'N/A')
            table.add_row(timestamp, component, proposal_status, str(score))
        
        console.print(table)
    else:
        for proposal in proposals:
            click.echo(f"  {proposal}")


@history_group.command(name="stats")
def show_history_stats():
    """Mostrar estadísticas del historial"""
    cmd = HistoryCommand()
    
    actions = cmd.get_action_history(1000)  # Get more for stats
    proposals = cmd.get_proposals_history(1000)
    
    if console:
        from rich.panel import Panel
        
        stats_text = f"""
Total Actions: {len(actions)}
Total Proposals: {len(proposals)}
Accepted Proposals: {len([p for p in proposals if p.get('status') == 'accepted'])}
Rejected Proposals: {len([p for p in proposals if p.get('status') == 'rejected'])}
        """
        console.print(Panel(stats_text, title="History Statistics", border_style="blue"))
    else:
        click.echo(f"Total Actions: {len(actions)}")
        click.echo(f"Total Proposals: {len(proposals)}")
