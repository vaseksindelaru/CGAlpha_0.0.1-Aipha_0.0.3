"""
AiphaLab Formatters - Helpers for beautiful CLI output using rich.
"""

import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.progress import Progress
from rich.style import Style
from rich.text import Text

console = Console()

# Define styles for different action types
ACTION_STYLES = {
    "ATOMIC_COMMIT": "bold green",
    "ATOMIC_ROLLBACK": "bold red",
    "PROPOSAL_EVALUATED": "cyan",
    "PROPOSAL_GENERATED": "magenta",
    "DEFAULT": "white",
}

def format_status(state, metrics):
    """Formats the system status into a rich Panel."""
    if not state and not metrics:
        console.print(Panel("[yellow]⚠️ System has no data. Run a cycle first.[/yellow]", title="Status", border_style="yellow"))
        return

    table = Table.grid(expand=True, padding=(0, 1))
    table.add_column(style="bold cyan")
    table.add_column()

    if state:
        table.add_row("Last Cycle:", state.get('last_improvement_cycle', 'N/A').split('.')[0])
        table.add_row("Proposals (last):", str(state.get('last_cycle_proposals', 0)))
        table.add_row("Approved (last):", str(state.get('last_cycle_approved', 0)))
        table.add_row("Applied (last):", str(state.get('last_cycle_applied', 0)))
        duration = state.get('last_cycle_duration_seconds')
        if duration:
            table.add_row("Duration:", f"{duration:.2f}s")

    if metrics:
        table.add_row() # Spacer
        table.add_row("[bold magenta]Trading Metrics[/bold magenta]")
        
        wr = metrics.get('win_rate', 0)
        if wr > 0.5:
            wr_style = "green"
            wr_icon = "✅"
        elif wr > 0.4:
            wr_style = "yellow"
            wr_icon = "⚠️"
        else:
            wr_style = "red"
            wr_icon = "❌"
        table.add_row("Win Rate:", Text(f"{wr:.2%} [{wr_icon}]", style=wr_style))

        table.add_row("Total Trades:", str(metrics.get('total_trades', 0)))

        dd = metrics.get('current_drawdown', 0)
        dd_style = "red" if dd > 0.15 else "yellow" if dd > 0.10 else "green"
        table.add_row("Drawdown:", Text(f"{dd:.2%}", style=dd_style))
        table.add_row("Status:", metrics.get('status', 'N/A'))

    console.print(Panel(table, title="[bold]AIPHA_0.0.2 STATUS[/bold]", border_style="blue"))


def format_action(action):
    """Formats a single action from the history."""
    timestamp = action.get('timestamp', '').split('.')[0]
    agent = action.get('agent', 'Unknown')
    action_type = action.get('action_type', 'UNKNOWN')
    
    style = ACTION_STYLES.get(action_type, ACTION_STYLES["DEFAULT"])
    
    header = f"[{style}][{timestamp}] {agent}: {action_type}[/{style}]"
    
    details = []
    if 'proposal_id' in action:
        details.append(f"  → Proposal: {action['proposal_id']}")
    if 'score' in action:
        approved = action.get('approved', False)
        icon = "✅" if approved else "❌"
        details.append(f"  → Score: {action['score']:.2f} | Approved: {approved} {icon}")
    if 'details' in action and isinstance(action['details'], dict):
        if 'msg' in action['details']:
            details.append(f"  → {action['details']['msg']}")
        if 'changes' in action['details']:
             for key, value in action['details']['changes'].items():
                details.append(f"  → {key}: {value['old']} → {value['new']}")

    console.print(header)
    if details:
        for line in details:
            console.print(line)

def format_proposals(proposals):
    """Formats a list of proposals into a table."""
    if not proposals:
        console.print("[yellow]No proposals found.[/yellow]")
        return

    table = Table(title="[bold]Recent Proposals[/bold]", border_style="magenta")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title")
    table.add_column("Justification")
    table.add_column("Score", justify="right")
    table.add_column("Status")

    for prop in proposals:
        status = "Approved" if prop.get('approved') else "Rejected"
        status_color = "green" if prop.get('approved') else "red"
        score = prop.get('score', 'N/A')
        if isinstance(score, float):
            score = f"{score:.2f}"
        
        table.add_row(
            prop.get('id', 'N/A'),
            prop.get('title', 'N/A'),
            prop.get('justification', 'N/A'),
            score,
            f"[{status_color}]{status}[/{status_color}]"
        )
    console.print(table)

def format_config(config_data):
    """Formats configuration data using rich Syntax."""
    config_str = json.dumps(config_data, indent=2)
    syntax = Syntax(config_str, "json", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title="[bold]Aipha Configuration[/bold]", border_style="green"))

def format_memory(memory_data):
    """Formats memory data using rich Syntax."""
    memory_str = json.dumps(memory_data, indent=2)
    syntax = Syntax(memory_str, "json", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title="[bold]Aipha Memory[/bold]", border_style="yellow"))

def display_cycle_progress(step, total, description):
    """Displays a simple progress indicator for a cycle step."""
    console.print(f"🔄 [bold][{step}/{total}][/bold] {description}...")

def display_cycle_results(result):
    """Displays the results of a completed cycle."""
    duration = result.get('duration_seconds', 0)
    
    table = Table.grid(expand=True)
    table.add_column(style="bold green")
    table.add_column()
    
    table.add_row("Proposals Generated:", str(result.get('proposals_generated', 0)))
    table.add_row("Proposals Approved:", str(result.get('proposals_approved', 0)))
    table.add_row("Changes Applied:", str(result.get('changes_applied', 0)))
    table.add_row("Duration:", f"{duration:.2f}s")

    console.print(Panel(table, title="[bold green]✅ Cycle Completed[/bold green]", border_style="green"))
