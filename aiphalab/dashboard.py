"""
Real-time Dashboard for Aipha_0.0.2
Displays system metrics, recent proposals, cycle status, and logs using rich.layout
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.live import Live
    from rich.progress import Progress, BarColumn, TextColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

logger = logging.getLogger(__name__)


class DashboardData:
    """Manager for dashboard data - provides current system state."""

    def __init__(self, storage_root: Path = Path("memory")):
        self.storage_root = Path(storage_root)
        from core.context_sentinel import ContextSentinel
        self.sentinel = ContextSentinel(storage_root=self.storage_root)

    def get_system_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas actuales del sistema."""
        state = self.sentinel.query_memory("system_state") or {}
        return {
            "last_cycle": state.get("last_improvement_cycle", "Never"),
            "proposals_generated": state.get("last_cycle_proposals", 0),
            "proposals_approved": state.get("last_cycle_approved", 0),
            "changes_applied": state.get("last_cycle_applied", 0),
            "last_duration": state.get("last_cycle_duration_seconds", 0),
        }

    def get_recent_actions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Obtiene las acciones recientes."""
        history = self.sentinel.get_action_history()
        return history[-limit:] if history else []

    def get_system_info(self) -> Dict[str, Any]:
        """Obtiene información del sistema."""
        info = self.sentinel.query_memory("system_info") or {}
        return {
            "version": info.get("version", "0.0.2"),
            "mode": info.get("mode", "UNKNOWN"),
            "boot_time": info.get("last_boot", "Unknown"),
        }


class AiphaDashboard:
    """Interactive real-time dashboard for Aipha_0.0.2"""

    def __init__(self, storage_root: Path = Path("memory"), auto_refresh: bool = True, refresh_interval: int = 2):
        if not RICH_AVAILABLE:
            raise RuntimeError("Rich library is required for dashboard. Install with: pip install rich")

        self.storage_root = Path(storage_root)
        self.data = DashboardData(storage_root)
        self.console = Console()
        self.auto_refresh = auto_refresh
        self.refresh_interval = refresh_interval

    def create_layout(self) -> Layout:
        """Crea el layout del dashboard."""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=2),
        )

        # Body se divide horizontalmente
        layout["body"].split_row(
            Layout(name="metrics", ratio=1),
            Layout(name="sidebar", ratio=1),
        )

        # Sidebar se divide verticalmente
        layout["sidebar"].split_column(
            Layout(name="proposals", ratio=1),
            Layout(name="logs", ratio=1),
        )

        return layout

    def make_header(self) -> Panel:
        """Crea el panel del header."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        title = Text("🤖 AIPHA Dashboard", style="bold white")
        subtitle = Text(f"Last updated: {timestamp}", style="dim")

        content = f"{title}\n{subtitle}"
        return Panel(content, style="blue", border_style="bold blue")

    def make_metrics_panel(self) -> Panel:
        """Crea el panel de métricas."""
        metrics = self.data.get_system_metrics()
        info = self.data.get_system_info()

        # Crear tabla de métricas
        table = Table(title="📊 System Metrics", show_header=False, box=None)
        table.add_column(style="cyan", no_wrap=False)
        table.add_column(style="white", no_wrap=False)

        table.add_row("Version", info["version"])
        table.add_row("Mode", info["mode"])
        table.add_row("", "")  # Separator
        table.add_row("Last Cycle", metrics["last_cycle"].split("T")[0] if "T" in str(metrics["last_cycle"]) else str(metrics["last_cycle"]))
        table.add_row("Proposals Generated", str(metrics["proposals_generated"]))
        table.add_row("Proposals Approved", str(metrics["proposals_approved"]))
        table.add_row("Changes Applied", str(metrics["changes_applied"]))
        table.add_row("Duration (last)", f"{metrics['last_duration']:.1f}s")

        return Panel(table, title="📊 Metrics", border_style="green")

    def make_proposals_panel(self) -> Panel:
        """Crea el panel de propuestas recientes."""
        actions = self.data.get_recent_actions(limit=5)

        proposals = [a for a in actions if "PROPOSAL" in a.get("action_type", "")]

        if not proposals:
            return Panel("[dim]No recent proposals[/dim]", title="📋 Recent Proposals", border_style="yellow")

        content = ""
        for i, proposal in enumerate(proposals[-3:], 1):  # Show last 3
            title = proposal.get("title", "Unknown")
            status = proposal.get("approved", False)
            icon = "✅" if status else "❌"
            content += f"{i}. {icon} {title[:40]}\n"

        return Panel(content.strip(), title="📋 Recent Proposals", border_style="yellow")

    def make_logs_panel(self) -> Panel:
        """Crea el panel de logs recientes."""
        actions = self.data.get_recent_actions(limit=10)

        if not actions:
            return Panel("[dim]No recent actions[/dim]", title="📜 Recent Actions", border_style="magenta")

        content = ""
        for action in actions[-5:]:  # Show last 5
            timestamp = action.get("timestamp", "")
            action_type = action.get("action_type", "UNKNOWN")
            # Simplify timestamp
            if "T" in timestamp:
                timestamp = timestamp.split("T")[1][:8]
            content += f"[dim]{timestamp}[/dim] {action_type[:30]}\n"

        return Panel(content.strip(), title="📜 Recent Actions", border_style="magenta")

    def make_footer(self) -> Text:
        """Crea el footer."""
        return Text(
            "Press Ctrl+C to exit | 🔄 Auto-refresh enabled",
            style="dim",
            justify="center"
        )

    def update_layout(self, layout: Layout) -> None:
        """Actualiza el contenido del layout."""
        layout["header"].update(self.make_header())
        layout["metrics"].update(self.make_metrics_panel())
        layout["proposals"].update(self.make_proposals_panel())
        layout["logs"].update(self.make_logs_panel())
        layout["footer"].update(self.make_footer())

    def run(self) -> None:
        """Ejecuta el dashboard en modo interactivo."""
        layout = self.create_layout()

        try:
            with Live(
                layout,
                console=self.console,
                screen=True,
                refresh_per_second=1 / self.refresh_interval
            ):
                while True:
                    self.update_layout(layout)
                    time.sleep(self.refresh_interval)
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Dashboard stopped[/yellow]")

    def display_once(self) -> None:
        """Muestra el dashboard una sola vez (sin auto-actualización)."""
        layout = self.create_layout()
        self.update_layout(layout)
        self.console.print(layout)


def create_dashboard(storage_root: Path = Path("memory")) -> AiphaDashboard:
    """Factory function to create a dashboard instance."""
    return AiphaDashboard(storage_root=storage_root)


if __name__ == "__main__":
    dashboard = create_dashboard()
    dashboard.run()

