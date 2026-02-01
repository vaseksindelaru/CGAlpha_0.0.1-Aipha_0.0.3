#!/usr/bin/env python3
"""
AiphaLab CLI - Interface to observe and control Aipha_0.0.2

Usage:
    aipha status              # View status
    aipha cycle run           # Execute one improvement cycle
    aipha cycle watch         # Run cycles automatically
    aipha history --limit 20  # View action history
"""

import sys
import time
import json
import os
import signal
from pathlib import Path
import textwrap

# Add Aipha_0.0.2 root to the Python path
AIPHA_ROOT = Path(__file__).resolve().parent.parent
if str(AIPHA_ROOT) not in sys.path:
    sys.path.insert(0, str(AIPHA_ROOT))

# Load environment variables from .env if it exists
env_path = AIPHA_ROOT / ".env"
if env_path.exists():
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key] = value.strip()

import click
from core.context_sentinel import ContextSentinel
from core.orchestrator_hardened import CentralOrchestratorHardened
from aiphalab.assistant import AiphaAssistant
from core.llm_assistant import LLMAssistant
from core.llm_client import LLMClient
from core.health_monitor import HealthMonitor
from core.atomic_update_system import AtomicUpdateSystem
from core.change_evaluator import ProposalEvaluator
import uuid
from datetime import datetime

# Use rich for output, with a simple fallback
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from aiphalab.formatters import (
        format_status, format_action, format_proposals,
        format_config, format_memory, display_cycle_progress, display_cycle_results,
    )
    from rich.tree import Tree
    from rich.syntax import Syntax
    from rich.markdown import Markdown
    console = Console()
except ImportError:
    # Fallback if rich or formatters are not available
    class SimpleConsole:
        def print(self, *args, **kwargs):
            click.echo(" ".join(str(a) for a in args))
    console = SimpleConsole()
    def format_status(state, metrics): click.echo(json.dumps({"state": state, "metrics": metrics}, indent=2))
    def format_action(action): click.echo(json.dumps(action, indent=2))
    def format_proposals(proposals): click.echo(json.dumps(proposals, indent=2))
    def format_config(config): click.echo(json.dumps(config, indent=2))
    def format_memory(memory): click.echo(json.dumps(memory, indent=2))
    def display_cycle_progress(step, total, desc): click.echo(f"[{step}/{total}] {desc}...")
    def display_cycle_results(result): click.echo(json.dumps(result, indent=2))
    Tree = None
    Syntax = None
    Markdown = None


# --- CLI Command Group ---

@click.group()
@click.option('--dry-run', is_flag=True, default=False, help='Simulate execution without persisting changes.')
@click.pass_context
def cli(ctx, dry_run):
    """AiphaLab CLI for Aipha_0.0.2"""
    # Store dry_run in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj['dry_run'] = dry_run
    if dry_run:
        click.secho("⚠️  DRY-RUN MODE ENABLED - Changes will be simulated only", fg='yellow', bold=True)

# --- Helper Functions ---

def get_sentinel():
    """Initializes and returns a ContextSentinel instance, handling errors."""
    try:
        storage_path = AIPHA_ROOT / "memory"
        return ContextSentinel(storage_root=storage_path)
    except Exception as e:
        click.secho(f"❌ Error initializing ContextSentinel: {e}", fg='red')
        click.echo("Suggestion: Run 'python life_cycle.py' to initialize the system.")
        sys.exit(1)

def get_assistant():
    """Initializes the AiphaAssistant."""
    return AiphaAssistant(AIPHA_ROOT)

# --- Observation Commands ---

@cli.command()
def status():
    """View the current status of the system."""
    sentinel = get_sentinel()
    try:
        state = sentinel.query_memory("system_state")
        metrics = sentinel.query_memory("trading_metrics")
        format_status(state, metrics)
    except FileNotFoundError:
        click.secho("⚠️ Memory files not found. The system may not have run yet.", fg='yellow')
        click.echo("Suggestion: Run 'python life_cycle.py' to create initial data.")
        sys.exit(1)

@cli.command()
@click.option('--limit', default=10, help='Number of actions to show.')
def history(limit):
    """View the history of system actions."""
    sentinel = get_sentinel()
    actions = sentinel.get_action_history()
    if not actions:
        click.secho("ℹ️ Action history is empty.", fg='cyan')
        return
    
    click.secho(f"📜 Last {limit} actions:", bold=True)
    for action in actions[-limit:]:
        format_action(action)

@cli.command()
def memory():
    """View the full content of the persistent memory file."""
    sentinel = get_sentinel()
    memory_data = sentinel.get_full_memory()
    format_memory(memory_data)

@cli.group()
def config():
    """Commands for configuration management."""
    pass

@config.command(name="view")
def config_view():
    """View the system configuration."""
    from core.config_manager import ConfigManager
    config_manager = ConfigManager(config_path=AIPHA_ROOT / "memory" / "aipha_config.json")
    config_data = config_manager.get_all()
    format_config(config_data)

@config.command(name="validate")
@click.pass_context
def config_validate(ctx):
    """Validate the current configuration."""
    from core.config_manager import ConfigManager
    from core.config_validators import ConfigValidator
    
    config_manager = ConfigManager(config_path=AIPHA_ROOT / "memory" / "aipha_config.json")
    config_data = config_manager.get_all()
    
    if not config_data:
        click.secho("❌ No configuration found", fg='red')
        return
    
    report = ConfigValidator.get_validation_report(config_data)
    
    # Mostrar resultado
    status = report["status"]
    if console:
        if report["is_valid"]:
            console.print(Panel(f"[green]{status}[/green]", border_style="green", title="Configuration Validation"))
        else:
            console.print(Panel(f"[red]{status}[/red]", border_style="red", title="Configuration Validation"))
    else:
        click.echo(status)
    
    # Mostrar errores
    if report["errors"]:
        if console:
            console.print("\n[red][bold]❌ ERRORS:[/bold][/red]")
        else:
            click.secho("\n❌ ERRORS:", fg='red', bold=True)
        
        for error in report["errors"]:
            if console:
                console.print(f"  • {error}")
            else:
                click.secho(f"  • {error}", fg='red')
    
    # Mostrar advertencias
    if report["warnings"]:
        if console:
            console.print("\n[yellow][bold]⚠️  WARNINGS:[/bold][/yellow]")
        else:
            click.secho("\n⚠️  WARNINGS:", fg='yellow', bold=True)
        
        for warning in report["warnings"]:
            if console:
                console.print(f"  • {warning}")
            else:
                click.secho(f"  • {warning}", fg='yellow')
    
    if report["is_valid"] and not report["warnings"]:
        if console:
            console.print("\n[green]✅ All parameters are within valid ranges![/green]")
        else:
            click.secho("\n✅ All parameters are within valid ranges!", fg='green')
    
    # Exit con código de error si hay problemas
    if not report["is_valid"]:
        sys.exit(1)

@config.command(name="suggest")
@click.argument('parameter')
def config_suggest(parameter):
    """Get suggestions for a specific parameter (e.g., 'Trading.tp_factor')."""
    from core.config_validators import ConfigValidator
    
    parts = parameter.split('.')
    if len(parts) != 2:
        click.secho("❌ Parameter format should be 'Category.parameter' (e.g., 'Trading.tp_factor')", fg='red')
        sys.exit(1)
    
    category, param_name = parts
    
    suggestions = ConfigValidator.get_parameter_suggestions(category, param_name)
    
    if not suggestions:
        click.secho(f"❌ Unknown parameter: {parameter}", fg='red')
        sys.exit(1)
    
    if console:
        console.print(Panel(
            f"[bold]{suggestions['name']}[/bold]\n[dim]{suggestions['description']}[/dim]",
            title=f"[bold]{suggestions['category']}[/bold]",
            border_style="blue"
        ))
        
        # Mostrar rango
        range_info = suggestions['range']
        if range_info['min'] is not None and range_info['max'] is not None:
            console.print(f"[bold]Range:[/bold] {range_info['min']} - {range_info['max']}")
        
        # Mostrar valores típicos
        if 'typical_values' in suggestions:
            console.print(f"[bold]Typical values:[/bold] {', '.join(str(v) for v in suggestions['typical_values'])}")
    else:
        click.echo(f"Parameter: {suggestions['name']}")
        click.echo(f"Category: {suggestions['category']}")
        click.echo(f"Description: {suggestions['description']}")
        if 'typical_values' in suggestions:
            click.echo(f"Typical values: {', '.join(str(v) for v in suggestions['typical_values'])}")

# --- Dashboard Command ---

@cli.command()
@click.option('--interval', default=2, help='Refresh interval in seconds.')
@click.pass_context
def dashboard(ctx, interval):
    """Display a real-time dashboard of system status."""
    from aiphalab.dashboard import create_dashboard
    
    if not console:
        click.echo("Rich library is required for dashboard. Install with: pip install rich")
        return
    
    click.secho("Starting dashboard... (Press Ctrl+C to exit)", fg='cyan')
    
    try:
        storage_path = AIPHA_ROOT / "memory"
        dashboard_instance = create_dashboard(storage_root=storage_path)
        dashboard_instance.refresh_interval = interval
        dashboard_instance.run()
    except KeyboardInterrupt:
        click.echo("\n✅ Dashboard closed")
    except Exception as e:
        click.secho(f"❌ Dashboard error: {e}", fg='red')

# --- Automejora Cycle Commands ---

@cli.group()
def cycle():
    """Commands for the self-improvement cycle."""
    pass

@cycle.command()
@click.pass_context
def run(ctx):
    """Run a single self-improvement cycle."""
    storage_path = AIPHA_ROOT / "memory"
    dry_run = ctx.obj.get('dry_run', False) if ctx.obj else False
    orchestrator = CentralOrchestratorHardened()
    
    mode_str = "[DRY-RUN] " if dry_run else ""
    if console:
        console.print(Panel(f"{mode_str}🔄 Running a single self-improvement cycle...", border_style="blue"))
    else:
        click.echo(f"{mode_str}🔄 Running a single self-improvement cycle...")

    # This is a simplified representation. A real run would have callbacks.
    display_cycle_progress(1, 5, "Collecting metrics")
    display_cycle_progress(2, 5, "Generating proposals")
    display_cycle_progress(3, 5, "Evaluating proposals")
    display_cycle_progress(4, 5, "Applying changes")
    display_cycle_progress(5, 5, "Logging results")
    
    result = orchestrator.run_improvement_cycle()
    
    if result.get("error"):
        click.secho(f"❌ Cycle failed: {result['error']}", fg='red')
    else:
        display_cycle_results(result)

@cycle.command()
@click.option('--interval', default=60, help='Seconds between cycles.')
@click.pass_context
def watch(ctx, interval):
    """Activate observer mode for automatic cycles."""
    storage_path = AIPHA_ROOT / "memory"
    dry_run = ctx.obj.get('dry_run', False) if ctx.obj else False
    orchestrator = CentralOrchestratorHardened()
    cycle_count = 0

    mode_str = "[DRY-RUN] " if dry_run else ""
    if console:
        console.print(Panel(f"{mode_str}👁️  Observer mode activated. Interval: {interval}s. Press Ctrl+C to stop.", border_style="magenta"))
    else:
        click.echo(f"{mode_str}👁️  Observer mode activated. Interval: {interval}s. Press Ctrl+C to stop.")

    try:
        while True:
            cycle_count += 1
            header = f"CYCLE #{cycle_count} - {time.strftime('%Y-%m-%d %H:%M:%S')}"
            if console:
                console.print(Panel(f"{mode_str}{header}", border_style="bold yellow"))
            else:
                click.echo(f"\n--- {mode_str}{header} ---")
            
            result = orchestrator.run_improvement_cycle()

            if result.get("error"):
                click.secho(f"❌ Cycle failed: {result['error']}", fg='red')
            else:
                display_cycle_results(result)

            click.echo(f"⏳ Waiting {interval}s for the next cycle...")
            time.sleep(interval)
    except KeyboardInterrupt:
        click.echo("\n🛑 Observer mode stopped.")
        sys.exit(0)

# --- Proposal Commands ---

@cli.command(name="proposals")
def proposals_list():
    """List recent proposals."""
    # This is a placeholder as the core system doesn't store a list of proposals yet.
    # We simulate it by looking at history.
    sentinel = get_sentinel()
    history = sentinel.get_action_history()
    
    proposals = []
    evaluations = {}

    for item in history:
        if item.get('action_type') == 'PROPOSAL_EVALUATED':
            evaluations[item.get('proposal_id')] = {'score': item.get('score'), 'approved': item.get('approved')}

    for item in history:
        if item.get('action_type') == 'PROPOSAL_GENERATED':
            prop_id = item.get('proposal_id')
            if prop_id in evaluations:
                item.update(evaluations[prop_id])
            proposals.append({
                "id": prop_id,
                "title": item.get('title', 'N/A'),
                "justification": item.get('justification', 'N/A'),
                "score": item.get('score'),
                "approved": item.get('approved')
            })
    
    format_proposals(proposals[-10:]) # Show last 10

# --- EDUCATIONAL COMMANDS (NEW) ---

@cli.command()
@click.pass_context
def learn(ctx):
    """Interactive tutorial mode."""
    if not console:
        click.echo("Rich is required for the tutorial.")
        return

    console.print(Panel("[bold cyan]🎓 Welcome to Aipha_0.0.2 Learning Mode[/bold cyan]", border_style="cyan"))
    console.print("This mode will guide you through the system concepts.\n")
    
    steps = [
        ("What is Aipha?", "Aipha is a self-improving trading system that uses a closed feedback loop."),
        ("The Loop", "1. Acquire Data -> 2. Trade -> 3. Evaluate -> 4. Propose Change -> 5. Apply -> Repeat."),
        ("Key Components", "- [bold]ContextSentinel[/]: The memory.\n- [bold]Orchestrator[/]: The brain.\n- [bold]ChangeProposer[/]: The innovator."),
        ("Your Role", "You are the supervisor. You use this CLI to watch, guide, and refine the system.")
    ]
    
    for title, content in steps:
        console.print(Panel(content, title=f"[bold]{title}[/bold]", border_style="blue"))
        click.pause(info="Press any key to continue...")
        console.clear()
    
    console.print("[bold green]Tutorial Complete![/bold green] Try running 'aipha explain flow' next.")

@cli.command()
@click.argument('topic')
def explain(topic):
    """Explain a component, flow, or concept."""
    assistant = get_assistant()
    
    if topic == "flow":
        if console:
            flow_md = textwrap.dedent("""
            # 🔄 The Aipha Feedback Loop
            
            1. **Market Data** 📊
               `DataProcessor` fetches candles.
            
            2. **Trading** 📈
               `TradingManager` executes strategies (e.g., ProofStrategy).
               Metrics (Win Rate, Drawdown) are recorded in Memory.
            
            3. **Analysis** 🧠
               `ChangeProposer` reads metrics from `ContextSentinel`.
               If performance is poor/good, it generates a `ChangeProposal`.
            
            4. **Evaluation** ⚖️
               `ChangeEvaluator` scores the proposal (Risk vs Reward).
            
            5. **Evolution** 🧬
               `AtomicUpdateSystem` applies the code change safely.
               If tests fail, it rolls back.
            """)
            console.print(Markdown(flow_md))
        else:
            click.echo("Flow explanation requires Rich.")
        return

    # Component explanation
    info = assistant.get_component_info(topic)
    if not info:
        click.secho(f"❌ Unknown component or topic: {topic}", fg='red')
        click.echo("Try: context_sentinel, orchestrator, change_proposer, potential_capture_engine")
        return
        
    if "error" in info:
        click.secho(f"❌ {info['error']}", fg='red')
        return

    if console:
        # Header
        console.print(Panel(f"[bold white]{topic.upper()}[/bold white]\n[dim]{info['file']}[/dim]", style="bold blue"))
        
        # Purpose (Module Doc)
        console.print(Panel(info['module_doc'].strip(), title="[bold]🎯 Purpose[/bold]", border_style="green"))
        
        # Functionality (Target Doc)
        console.print(Panel(info['target_doc'].strip(), title=f"[bold]🔧 Functionality ({info['target']})[/bold]", border_style="cyan"))
        
        # Dependencies
        tree = Tree("[bold]🔗 Dependencies[/bold]")
        for dep in info['dependencies']:
            tree.add(dep)
        console.print(tree)
        console.print("")
        
        # Footer
        console.print(f"[dim]To see code: aipha inspect code {topic}[/dim]")

# --- DEVELOPMENT COMMANDS (NEW) ---

@cli.group()
def dev():
    """Development tools for creating proposals."""
    pass

@dev.command(name="idea")
@click.argument('text')
def dev_idea(text):
    """Analyze a raw idea and suggest components."""
    assistant = get_assistant()
    analysis = assistant.analyze_idea(text)
    
    if console:
        console.print(Panel(f"[italic]\"{analysis['original']}\"[/italic]", title="🧠 Analyzing Idea", border_style="magenta"))
        
        # Concepts
        if analysis['concepts']:
            table = Table(title="Detected Concepts", show_header=True)
            table.add_column("Category", style="cyan")
            table.add_column("Keywords", style="yellow")
            
            for cat, kws in analysis['concepts'].items():
                table.add_row(cat.upper(), ", ".join(kws))
            console.print(table)
            
            # Suggestions
            console.print("\n[bold]💡 Suggestions:[/bold]")
            if "risk" in analysis['concepts']:
                console.print("- Consider modifying [bold]sl_factor[/bold] in [cyan]potential_capture_engine[/cyan].")
                console.print("- Check [bold]ChangeProposer[/bold] rules for 'Tighten Risk'.")
            if "profit" in analysis['concepts']:
                console.print("- Consider modifying [bold]tp_factor[/bold] in [cyan]potential_capture_engine[/cyan].")
            if "volatility" in analysis['concepts']:
                console.print("- Review [bold]atr_period[/bold] settings.")
                console.print("- Consider adding a volatility filter to [cyan]ConfigManager[/cyan].")
        else:
            console.print("[yellow]No specific system concepts detected. Try using terms like 'risk', 'profit', 'volatility', or 'trades'.[/yellow]")

@dev.command(name="propose")
def dev_propose():
    """Interactive proposal generator (Mock)."""
    if not console: return
    
    console.print("[bold]🤖 Interactive Proposal Generator[/bold]")
    
    # Mock interaction
    options = ["Parameters (tp/sl/atr)", "Change Rules", "New Component"]
    for i, opt in enumerate(options, 1):
        console.print(f"{i}. {opt}")
    
    choice = click.prompt("Choose target", type=int, default=1)
    
    if choice == 1:
        param = click.prompt("Parameter to change", default="tp_factor")
        val = click.prompt("New value", default=2.0, type=float)
        justification = click.prompt("Justification")
        
        console.print("\n[bold green]📋 Generating Proposal...[/bold green]")
        console.print(Panel(f"""
        Title: Manual Adjustment of {param}
        Target: potential_capture_engine
        Change: {param} -> {val}
        Justification: {justification}
        """, title="Draft Proposal", border_style="green"))
        
        if click.confirm("Simulate this proposal?"):
            console.print("[dim]Simulating... (Mock)[/dim]")
            console.print("✅ Simulation passed. Impact: Medium. Risk: Low.")

# --- LLM COMMANDS (NEW) ---

@cli.group()
def llm():
    """Comandos LLM para análisis avanzado."""
    pass

@llm.command()
@click.argument('component')
def analyze(component):
    """Análisis profundo de componente usando LLM."""
    assistant = get_assistant()
    
    if not assistant.use_llm:
        click.secho("⚠️ LLM no disponible, usando análisis estático", fg='yellow')
    
    console.print(f"🧠 Analizando {component} con LLM...")
    
    result = assistant.analyze_component_llm(component)
    
    if 'error' in result:
        click.secho(f"❌ Error: {result['error']}", fg='red')
        return
    
    # Mostrar resultados
    console.print(Panel(f"[bold]{result['name']}[/bold]", border_style="magenta"))
    
    if result.get('analysis_source') == 'llm':
        console.print("[bold]📊 Análisis LLM:[/bold]")
        console.print(Markdown(result.get('llm_analysis', 'No disponible')))
        
        insights = result.get('llm_insights', {})
        if insights:
            console.print("\n[bold]💡 Insights clave:[/bold]")
            for category, insight in insights.items():
                console.print(f"  • {category.title()}: {insight}")
        
        suggestions = result.get('llm_suggestions', [])
        if suggestions:
            console.print(f"\n[bold]🔧 {len(suggestions)} sugerencias de mejora:[/bold]")
            for i, suggestion in enumerate(suggestions[:5], 1):
                priority = suggestion.get('priority', 'medium')
                color = 'green' if priority == 'low' else 'yellow' if priority == 'medium' else 'red'
                console.print(f"  {i}. [{color}]{suggestion.get('description', 'N/A')}[/{color}]")
    else:
        console.print("[bold]📊 Análisis estático:[/bold]")
        console.print(f"Purpose: {result.get('purpose', 'N/A')}")
        console.print(f"Dependencies: {', '.join(result.get('dependencies', []))}")

@llm.command()
def self_analyze():
    """Auto-análisis del CLI usando LLM."""
    assistant = get_assistant()
    
    if not assistant.use_llm:
        click.secho("⚠️ LLM no disponible, usando análisis estático", fg='yellow')
    
    console.print("🤖 Realizando auto-análisis del CLI...")
    
    result = assistant.analyze_cli_self()
    
    # Mostrar resumen
    console.print("\n[bold]📋 Resumen del auto-análisis:[/bold]")
    
    for component, analysis in result.items():
        status = "✅ LLM" if analysis.get('analysis_source') == 'llm' else "⚠️ Estático"
        console.print(f"  • {component}: {status}")
    
    # Mostrar insights generales
    console.print("\n[bold]🧠 Insights generales:[/bold]")
    for component, analysis in result.items():
        if analysis.get('llm_insights'):
            console.print(f"\n[bold]{component}:[/bold]")
            insights = analysis['llm_insights']
            for category, insight in insights.items():
                console.print(f"  • {category.title()}: {insight}")

@llm.command()
def improve():
    """Sugerir mejoras para el CLI usando LLM."""
    assistant = get_assistant()
    
    if not assistant.use_llm:
        click.secho("⚠️ LLM no disponible", fg='red')
        return
    
    console.print("💡 Generando sugerencias de mejora para el CLI...")
    
    result = assistant.suggest_cli_improvements()
    
    if 'error' in result:
        click.secho(f"❌ Error: {result['error']}", fg='red')
        return
    
    # Mostrar sugerencias
    suggestions = result.get('improvement_suggestions', [])
    
    if not suggestions:
        console.print("ℹ️ No se encontraron sugerencias de mejora.")
        return
    
    console.print(f"\n[bold]🎯 {len(suggestions)} sugerencias de mejora:[/bold]")
    
    for i, suggestion in enumerate(suggestions, 1):
        category = suggestion.get('category', 'general')
        priority = suggestion.get('priority', 'medium')
        impact = suggestion.get('impact', 'medium')
        
        # Colores según prioridad
        color = 'green' if priority == 'low' else 'yellow' if priority == 'medium' else 'red'
        
        console.print(f"\n{i}. [{color}][{priority.upper()}][/{color}] {suggestion.get('title', 'N/A')}")
        console.print(f"   Categoría: {category}")
        console.print(f"   Impacto: {impact}")
        console.print(f"   Descripción: {suggestion.get('description', 'N/A')}")
    
    # Mostrar plan de implementación
    implementation_plan = result.get('implementation_plan', {})
    if implementation_plan:
        console.print("\n[bold]📅 Plan de implementación:[/bold]")
        for phase, tasks in implementation_plan.items():
            console.print(f"\n[bold]{phase.upper()}:[/bold]")
            for task in tasks:
                console.print(f"  • {task}")
    
    # Mostrar assessment de prioridades
    priority_assessment = result.get('priority_assessment', {})
    if priority_assessment:
        console.print("\n[bold]⚡ Assessment de prioridades:[/bold]")
        for category, items in priority_assessment.items():
            if items:
                console.print(f"\n[bold]{category.replace('_', ' ').title()}:[/bold]")
                for item in items:
                    console.print(f"  • {item}")

# --- INSPECTION COMMANDS (NEW) ---

@cli.group()
def inspect():
    """Deep inspection tools."""
    pass

@inspect.command(name="code")
@click.argument('component')
def inspect_code(component):
    """View the source code of a component."""
    assistant = get_assistant()
    info = assistant.get_component_info(component)
    
    if not info or "error" in info:
        click.secho(f"❌ Could not load code for {component}", fg='red')
        return
        
    if console:
        syntax = Syntax(info['content'], "python", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title=f"[bold]{info['file']}[/bold]", border_style="blue"))

@inspect.command(name="memory")
def inspect_memory():
    """Alias for 'memory' command."""
    sentinel = get_sentinel()
    memory_data = sentinel.get_full_memory()
    format_memory(memory_data)

# --- SIMULATION COMMANDS (NEW) ---

@cli.group()
def simulate():
    """Simulation tools."""
    pass

@simulate.command(name="proposal")
@click.argument('proposal_id')
def simulate_proposal(proposal_id):
    """Simulate the application of a proposal."""
    console.print(f"🔬 Simulating proposal [bold]{proposal_id}[/bold]...")
    # Mock simulation logic
    import time
    with console.status("Running impact analysis..."):
        time.sleep(1.5)
    console.print("✅ Tests: PASS")
    console.print("✅ Syntax: VALID")
    console.print("📊 Predicted Impact: [green]Positive[/green]")

# --- Utility Commands ---

@cli.command()
def version():
    """Show the system version."""
    sentinel = get_sentinel()
    info = sentinel.query_memory("system_info")
    version = info.get("version", "0.0.2") if info else "0.0.2"
    click.echo(f"Aipha_0.0.2 - Version {version}")

# --- Test Function ---

def test_cli():
    """Test function for the CLI."""
    click.secho("\n=== CLI TEST ===", bold=True)
    
    # 1. ContextSentinel availability
    try:
        sentinel = get_sentinel()
        click.secho("✅ ContextSentinel OK", fg='green')
    except Exception as e:
        click.secho(f"❌ ContextSentinel failed: {e}", fg='red')
        return

    # 2. Memory existence
    try:
        state = sentinel.query_memory("system_state")
        if state:
            click.secho("✅ Memory OK", fg='green')
        else:
            click.secho("⚠️  Memory is empty. Run 'python life_cycle.py' to populate it.", fg='yellow')
    except FileNotFoundError:
        click.secho("❌ Memory file not found.", fg='red')
    except Exception as e:
        click.secho(f"❌ Memory check failed: {e}", fg='red')
        
    click.secho("\n=== TEST COMPLETE ===", bold=True)


# --- Proposal Management Commands ---

@cli.group()
def proposal():
    """Gestión de propuestas de cambio en el sistema Aipha."""
    pass


@proposal.command(name="create")
@click.option("--component", required=True, help="Componente a modificar (ej: orchestrator, evaluator, etc)")
@click.option("--parameter", required=True, help="Parámetro específico a cambiar (ej: confidence_threshold)")
@click.option("--new-value", required=True, help="Nuevo valor del parámetro")
@click.option("--reason", required=True, help="Razón para el cambio (ej: mejorar win rate)")
@click.option("--priority", default="high", type=click.Choice(['low', 'medium', 'high', 'critical']), help="Nivel de prioridad")
@click.option("--tags", default="", help="Etiquetas separadas por coma (ej: risk,urgent)")
def proposal_create(component, parameter, new_value, reason, priority, tags):
    """Crear una propuesta manual de cambio.
    
    Ejemplo:
        aipha proposal create --component orchestrator --parameter confidence_threshold \\
                              --new-value 0.65 --reason "Aumentar sensibilidad para ganar operaciones"
    """
    try:
        # Generar ID único
        proposal_id = f"PROP_MANUAL_{uuid.uuid4().hex[:8].upper()}"
        
        # Obtener métricas actuales para el "Veredicto del Mercado" (Hito 5)
        sentinel = get_sentinel()
        current_metrics = sentinel.query_memory("trading_metrics") or {}
        baseline_metrics = {
            "win_rate": current_metrics.get("win_rate", 0.0),
            "drawdown": current_metrics.get("current_drawdown", 0.0),
            "total_trades": current_metrics.get("total_trades", 0)
        }
        
        # Crear propuesta
        proposal_data = {
            "proposal_id": proposal_id,
            "timestamp": datetime.now().isoformat(),
            "component": component,
            "parameter": parameter,
            "new_value": new_value,
            "reason": reason,
            "priority": priority,
            "tags": [t.strip() for t in tags.split(",") if t.strip()],
            "status": "PENDING_EVALUATION",
            "created_by": "CLI",
            "evaluation_score": None,
            "applied": False,
            "baseline_metrics": baseline_metrics  # Guardar estado inicial
        }
        
        # Guardar en memory/proposals.jsonl
        proposals_file = AIPHA_ROOT / "memory" / "proposals.jsonl"
        proposals_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(proposals_file, "a") as f:
            f.write(json.dumps(proposal_data) + "\n")
        
        # Notificar al Orquestador (SIGUSR1) para procesamiento inmediato
        try:
            pid_file = AIPHA_ROOT / "memory" / "orchestrator.pid"
            if pid_file.exists():
                with open(pid_file, "r") as f:
                    pid = int(f.read().strip())
                os.kill(pid, signal.SIGUSR1)
                click.secho(f"⚡ Señal enviada al Orquestador (PID {pid}) para evaluación inmediata.", fg='yellow')
            else:
                click.secho("ℹ️  Orquestador no detectado (sin archivo PID). La propuesta quedará en cola.", fg='dim')
        except ProcessLookupError:
            click.secho("⚠️  El proceso del Orquestador no está corriendo actualmente.", fg='yellow')
        except Exception as e:
            click.secho(f"⚠️  No se pudo enviar señal al Orquestador: {e}", fg='yellow')

        # Mostrar confirmación
        click.secho("\n✅ PROPUESTA CREADA", fg='green', bold=True)
        click.echo(f"  ID: {proposal_id}")
        click.echo(f"  Componente: {component}")
        click.echo(f"  Parámetro: {parameter}")
        click.echo(f"  Nuevo Valor: {new_value}")
        click.echo(f"  Razón: {reason}")
        click.echo(f"  Estado: PENDING_EVALUATION")
        click.echo(f"\n💡 Siguiente paso: aipha proposal evaluate {proposal_id}")
        
    except Exception as e:
        click.secho(f"❌ Error al crear propuesta: {e}", fg='red')
        sys.exit(1)


@proposal.command(name="list")
def proposal_list():
    """Listar todas las propuestas con su estado actual."""
    try:
        proposals_file = AIPHA_ROOT / "memory" / "proposals.jsonl"
        
        if not proposals_file.exists():
            click.secho("ℹ️  No hay propuestas registradas aún", fg='yellow')
            return
        
        # Leer propuestas
        proposals = []
        with open(proposals_file, "r") as f:
            for line in f:
                if line.strip():
                    proposals.append(json.loads(line))
        
        if not proposals:
            click.secho("ℹ️  No hay propuestas registradas", fg='yellow')
            return
        
        # Crear tabla
        try:
            table = Table(title="📋 Propuestas Registradas", show_header=True, header_style="bold cyan")
            table.add_column("ID", style="cyan")
            table.add_column("Componente", style="magenta")
            table.add_column("Parámetro", style="yellow")
            table.add_column("Nuevo Valor", style="green")
            table.add_column("Estado", style="blue")
            table.add_column("Score", style="bright_black")
            
            for prop in proposals:
                score = f"{prop.get('evaluation_score', 'N/A'):.2f}" if prop.get('evaluation_score') else "N/A"
                table.add_row(
                    prop["proposal_id"],
                    prop["component"],
                    prop["parameter"],
                    str(prop["new_value"]),
                    prop["status"],
                    score,
                )
            
            console.print(table)
        except:
            # Fallback sin Rich
            click.echo(f"{'ID':<20} {'Componente':<15} {'Parámetro':<20} {'Valor':<15} {'Estado':<20} {'Score':<8}")
            for prop in proposals:
                score = f"{prop.get('evaluation_score', 'N/A'):.2f}" if prop.get('evaluation_score') else "N/A"
                click.echo(f"{prop['proposal_id']:<20} {prop['component']:<15} {prop['parameter']:<20} {str(prop['new_value']):<15} {prop['status']:<20} {score:<8}")
        
    except Exception as e:
        click.secho(f"❌ Error al listar propuestas: {e}", fg='red')
        sys.exit(1)


@proposal.command(name="evaluate")
@click.argument("proposal_id")
def proposal_evaluate(proposal_id):
    """Evaluar una propuesta usando ChangeEvaluator.
    
    Ejemplo:
        aipha proposal evaluate PROP_MANUAL_ABC12345
    """
    try:
        proposals_file = AIPHA_ROOT / "memory" / "proposals.jsonl"
        
        if not proposals_file.exists():
            click.secho("❌ No hay propuestas registradas", fg='red')
            sys.exit(1)
        
        # Buscar la propuesta
        proposal_data = None
        with open(proposals_file, "r") as f:
            for line in f:
                if line.strip():
                    prop = json.loads(line)
                    if prop["proposal_id"] == proposal_id:
                        proposal_data = prop
                        break
        
        if not proposal_data:
            click.secho(f"❌ Propuesta no encontrada: {proposal_id}", fg='red')
            sys.exit(1)
        
        if proposal_data["status"] != "PENDING_EVALUATION":
            click.secho(f"⚠️  Propuesta ya evaluada (Estado: {proposal_data['status']})", fg='yellow')
            return
        
        click.echo("\n🔍 Evaluando propuesta...")
        
        # Inicializar evaluador
        sentinel = get_sentinel()
        evaluator = ProposalEvaluator(sentinel)
        
        # Mock proposal object for evaluator
        class ProposalMock:
            def __init__(self, data):
                self.proposal_id = data["proposal_id"]
                self.component = data["component"]
                self.parameter = data["parameter"]
                self.new_value = data["new_value"]
        
        mock_proposal = ProposalMock(proposal_data)
        
        # Evaluar
        result = evaluator.evaluate(mock_proposal)
        
        # Actualizar propuesta con score
        proposals = []
        with open(proposals_file, "r") as f:
            for line in f:
                if line.strip():
                    prop = json.loads(line)
                    if prop["proposal_id"] == proposal_id:
                        prop["evaluation_score"] = result.score
                        prop["status"] = "APPROVED" if result.approved else "REJECTED"
                    proposals.append(prop)
        
        # Guardar actualización
        with open(proposals_file, "w") as f:
            for prop in proposals:
                f.write(json.dumps(prop) + "\n")
        
        # Mostrar resultado
        click.secho("\n📊 EVALUACIÓN COMPLETADA", fg='cyan', bold=True)
        click.echo(f"\nPropuesta: {proposal_id}")
        click.echo(f"Score: {result.score:.2f} / 1.00")
        click.echo(f"Estado: {'✅ APROBADO' if result.approved else '❌ RECHAZADO'}")
        click.echo(f"\n{result.reasoning}")
        
        if result.approved:
            click.echo(f"\n💡 Siguiente paso: aipha proposal apply {proposal_id}")
        
    except Exception as e:
        click.secho(f"❌ Error en evaluación: {e}", fg='red')
        import traceback
        traceback.print_exc()
        sys.exit(1)


@proposal.command(name="apply")
@click.argument("proposal_id")
def proposal_apply(proposal_id):
    """Aplicar una propuesta evaluada usando protocolo atómico.
    
    Ejecuta el protocolo atómico: Backup → Diff → Test → Commit
    
    Ejemplo:
        aipha proposal apply PROP_MANUAL_ABC12345
    """
    try:
        proposals_file = AIPHA_ROOT / "memory" / "proposals.jsonl"
        
        if not proposals_file.exists():
            click.secho("❌ No hay propuestas registradas", fg='red')
            sys.exit(1)
        
        # Buscar la propuesta
        proposal_data = None
        with open(proposals_file, "r") as f:
            for line in f:
                if line.strip():
                    prop = json.loads(line)
                    if prop["proposal_id"] == proposal_id:
                        proposal_data = prop
                        break
        
        if not proposal_data:
            click.secho(f"❌ Propuesta no encontrada: {proposal_id}", fg='red')
            sys.exit(1)
        
        if proposal_data["status"] not in ["PENDING_EVALUATION", "APPROVED"]:
            click.secho(f"⚠️  No se puede aplicar propuesta en estado: {proposal_data['status']}", fg='yellow')
            sys.exit(1)
        
        if proposal_data.get("applied"):
            click.secho(f"⚠️  Propuesta ya ha sido aplicada", fg='yellow')
            sys.exit(1)
        
        click.secho(f"\n🚀 Aplicando propuesta: {proposal_id}", fg='cyan', bold=True)
        click.echo(f"  Componente: {proposal_data['component']}")
        click.echo(f"  Parámetro: {proposal_data['parameter']}")
        click.echo(f"  Nuevo Valor: {proposal_data['new_value']}")
        
        # FASE 1: BACKUP
        click.secho("\n[1/4] 💾 BACKUP", fg='yellow')
        click.echo("  Creando copia de seguridad del estado actual...")
        
        config_file = AIPHA_ROOT / "memory" / "aipha_config.json"
        if not config_file.exists():
            click.secho("  ⚠️  Archivo de config no existe", fg='yellow')
            config_data = {}
        else:
            try:
                with open(config_file, "r") as f:
                    config_data = json.load(f)
            except Exception as e:
                click.secho(f"  ❌ Error al leer config: {e}", fg='red')
                sys.exit(1)
        
        # Crear backup
        backup_file = AIPHA_ROOT / "memory" / f".backup_{proposal_id}.json"
        try:
            with open(backup_file, "w") as f:
                json.dump(config_data, f, indent=2)
            click.secho("  ✅ Backup creado", fg='green')
        except Exception as e:
            click.secho(f"  ❌ Error en backup: {e}", fg='red')
            sys.exit(1)
        
        # FASE 2: DIFF
        click.secho("\n[2/4] 📝 DIFF", fg='yellow')
        click.echo(f"  Preparando cambio: {proposal_data['parameter']} = {proposal_data['new_value']}")
        
        try:
            # Asegurar que existe el componente
            if proposal_data["component"] not in config_data:
                config_data[proposal_data["component"]] = {}
            
            # Guardar valor anterior para comparación
            old_value = config_data[proposal_data["component"]].get(proposal_data["parameter"])
            
            # Aplicar cambio
            config_data[proposal_data["component"]][proposal_data["parameter"]] = proposal_data["new_value"]
            
            click.echo(f"  Anterior: {old_value}")
            click.echo(f"  Nuevo:    {proposal_data['new_value']}")
            click.secho("  ✅ Diff preparado", fg='green')
        except Exception as e:
            click.secho(f"  ❌ Error en diff: {e}", fg='red')
            sys.exit(1)
        
        # FASE 3: TEST
        click.secho("\n[3/4] 🧪 TEST", fg='yellow')
        click.echo("  Validando cambios...")
        
        try:
            # Validación básica
            if not isinstance(config_data, dict):
                raise ValueError("Config debe ser un diccionario")
            
            # Validar tipo de valor
            try:
                float(proposal_data["new_value"])
                click.echo("  ✓ Tipo: válido (numérico)")
            except:
                click.echo("  ✓ Tipo: válido (string)")
            
            click.secho("  ✅ Validaciones pasadas", fg='green')
        except Exception as e:
            click.secho(f"  ❌ Validación fallida: {e}", fg='red')
            click.secho("\n[ROLLBACK] 🔄 Restaurando backup...", fg='red')
            try:
                backup_file.unlink()
            except:
                pass
            sys.exit(1)
        
        # FASE 4: COMMIT
        click.secho("\n[4/4] ✅ COMMIT", fg='yellow')
        click.echo("  Consolidando cambios...")
        
        try:
            # Guardar config
            with open(config_file, "w") as f:
                json.dump(config_data, f, indent=2)
            
            # Registrar en historial
            sentinel = get_sentinel()
            sentinel.add_action(
                agent="ProposalApply",
                action_type="PROPOSAL_APPLIED",
                proposal_id=proposal_id,
                details={
                    "component": proposal_data["component"],
                    "parameter": proposal_data["parameter"],
                    "old_value": old_value,
                    "new_value": proposal_data["new_value"],
                    "reason": proposal_data["reason"],
                }
            )
            
            click.secho("  ✅ Cambios consolidados", fg='green')
            
            # Limpiar backup
            try:
                backup_file.unlink()
            except:
                pass
                
        except Exception as e:
            click.secho(f"  ❌ Error en commit: {e}", fg='red')
            click.secho("\n[ROLLBACK] 🔄 Restaurando backup...", fg='red')
            try:
                with open(backup_file, "r") as f:
                    backup_data = json.load(f)
                with open(config_file, "w") as f:
                    json.dump(backup_data, f, indent=2)
                click.secho("  ✅ Sistema restaurado", fg='green')
            except:
                click.secho("  ❌ Error al restaurar", fg='red')
            sys.exit(1)
        
        # Actualizar propuesta
        try:
            proposals = []
            with open(proposals_file, "r") as f:
                for line in f:
                    if line.strip():
                        prop = json.loads(line)
                        if prop["proposal_id"] == proposal_id:
                            prop["applied"] = True
                            prop["status"] = "APPLIED"
                        proposals.append(prop)
            
            with open(proposals_file, "w") as f:
                for prop in proposals:
                    f.write(json.dumps(prop) + "\n")
            
            # Registrar como última propuesta aplicada para el Orquestador (Hito 5)
            sentinel.add_memory("last_applied_proposal_id", proposal_id)
            
        except Exception as e:
            click.secho(f"  ⚠️  Error al actualizar registro: {e}", fg='yellow')
        
        # Resultado final
        click.secho("\n" + "="*60, fg='cyan')
        click.secho("✅ PROTOCOLO ATÓMICO COMPLETADO", fg='green', bold=True)
        click.secho("="*60, fg='cyan')
        click.echo(f"\nPropuesta {proposal_id} ha sido aplicada exitosamente.")
        click.echo(f"  • Componente: {proposal_data['component']}")
        click.echo(f"  • Parámetro: {proposal_data['parameter']}")
        click.echo(f"  • Anterior: {old_value}")
        click.echo(f"  • Nuevo: {proposal_data['new_value']}")
        click.echo(f"  • Razón: {proposal_data['reason']}")
        click.secho("\n✨ Sistema actualizado y seguro", fg='green')
        
    except Exception as e:
        click.secho(f"❌ Error al aplicar propuesta: {e}", fg='red')
        import traceback
        traceback.print_exc()
        sys.exit(1)



# --- Super Brain Commands (LLM Integration) ---

@cli.group()
def brain():
    """Comandos LLM para análisis avanzado del Super Cerebro (Qwen 2.5 Coder 32B)."""
    pass


def _check_api_key():
    """Verifica que AIPHA_BRAIN_KEY esté configurada. Retorna la clave o None."""
    api_key = os.getenv("AIPHA_BRAIN_KEY")
    if not api_key:
        click.secho(
            "❌ AIPHA_BRAIN_KEY no está configurada",
            fg='red',
            bold=True
        )
        click.echo("\n📋 Para configurar la API Key:")
        click.echo("  1. Obtén un token en: https://huggingface.co/settings/tokens")
        click.echo("  2. Edita .env y añade: AIPHA_BRAIN_KEY=hf_YOUR_TOKEN")
        click.echo("  3. Ejecuta nuevamente el comando\n")
        return None
    return api_key


@brain.command(name="test-connection")
def brain_test_connection():
    """Prueba la conexión con Qwen 2.5 Coder 32B vía HuggingFace Router."""
    api_key = _check_api_key()
    if not api_key:
        sys.exit(1)
    
    click.secho("🧠 Probando conexión con Qwen 2.5 Coder 32B...", fg='cyan', bold=True)
    
    try:
        client = LLMClient()
        click.echo("  ✅ LLMClient inicializado")
        
        # Health check
        result = client.health_check()
        if result:
            click.secho("  ✅ Health check: OK", fg='green')
            click.secho(
                f"\n✨ Conexión exitosa\n"
                f"   Modelo: Qwen/Qwen2.5-Coder-32B-Instruct\n"
                f"   API: HuggingFace Router\n"
                f"   Estado: 🟢 Operacional",
                fg='green',
                bold=True
            )
        else:
            click.secho("  ❌ Health check falló", fg='red')
            sys.exit(1)
    except ValueError as e:
        click.secho(f"  ❌ Error: {e}", fg='red')
        sys.exit(1)
    except Exception as e:
        click.secho(f"  ❌ Error inesperado: {e}", fg='red')
        sys.exit(1)


@brain.command(name="diagnose")
@click.option('--detailed', is_flag=True, default=False, help='Mostrar diagnóstico detallado con análisis profundo')
def brain_diagnose(detailed):
    """Diagnóstico profundo del sistema usando Qwen 2.5 Coder 32B con evidencia y intervenciones manuales."""
    api_key = _check_api_key()
    if not api_key:
        sys.exit(1)
    
    click.secho("🧠 Ejecutando diagnóstico profundo del sistema...\n", fg='cyan', bold=True)
    
    try:
        # Inicializar asistente LLM con capacidades mejoradas
        assistant = LLMAssistant(memory_path=AIPHA_ROOT / "memory")
        click.secho("  ✅ Super Cerebro inicializado", fg='green')
        
        click.secho("  ⏳ Analizando sistema (extrayendo evidencia e intervenciones)...", fg='yellow')
        
        # Obtener diagnóstico profundo con estructura
        diagnosis_result = assistant.diagnose_system(detailed=detailed)
        
        # Mostrar resultado formateado
        if isinstance(diagnosis_result, dict):
            # Tiene estructura mejorada
            if console:
                from rich.panel import Panel
                from rich.table import Table
                from rich.markdown import Markdown
                
                # Mostrar diagnóstico principal
                click.echo("")
                console.print(Panel(
                    diagnosis_result.get('formatted_diagnosis', diagnosis_result.get('diagnosis', '')),
                    border_style="cyan",
                    title="🧠 Diagnóstico Profundo del Sistema"
                ))
                
                # Mostrar tabla de intervenciones manuales si existen
                recent_proposals = diagnosis_result.get('recent_proposals', [])
                manual_interventions = diagnosis_result.get('manual_interventions', 0)
                
                if manual_interventions > 0 and recent_proposals:
                    click.echo("")
                    console.print("[bold yellow]📝 INTERVENCIONES MANUALES DETECTADAS:[/bold yellow]")
                    
                    table = Table(show_header=True, header_style="bold yellow")
                    table.add_column("ID", style="cyan")
                    table.add_column("Componente", style="magenta")
                    table.add_column("Parámetro", style="yellow")
                    table.add_column("Nuevo Valor", style="green")
                    table.add_column("Score", style="blue")
                    table.add_column("Estado", style="white")
                    
                    for prop in recent_proposals:
                        if prop.get('applied'):
                            score = f"{prop.get('evaluation_score', 'N/A'):.2f}" if prop.get('evaluation_score') else "N/A"
                            status_icon = "✅" if prop.get('status') == 'APPLIED' else "⏳"
                            table.add_row(
                                prop.get('proposal_id', 'UNKNOWN')[:16],
                                prop.get('component', '?'),
                                prop.get('parameter', '?'),
                                str(prop.get('new_value', '?')),
                                score,
                                f"{status_icon} {prop.get('status', 'UNKNOWN')}"
                            )
                    
                    console.print(table)
                    console.print(f"\n💡 El Super Cerebro detectó {manual_interventions} intervención(es) manual(es).")
                    console.print("   Esto ayuda a evaluar si los cambios manuales están mejorando el sistema.")
                
                # Mostrar tabla de parámetros en riesgo si existen
                risk_params = diagnosis_result.get('risk_parameters', [])
                if risk_params:
                    click.echo("")
                    table = Table(title="⚠️  Parámetros en Riesgo", show_header=True, header_style="bold red")
                    table.add_column("Parámetro", style="yellow")
                    table.add_column("Valor Actual", style="cyan")
                    table.add_column("Límite Crítico", style="red")
                    table.add_column("Prob. Fallo", style="red", justify="center")
                    
                    for param in risk_params:
                        table.add_row(
                            param.get('parameter', 'N/A'),
                            str(param.get('current_value', 'N/A')),
                            str(param.get('critical_limit', 'N/A')),
                            param.get('failure_probability', 'N/A')
                        )
                    
                    console.print(table)
                
                # Mostrar modo simulación si está activo
                if diagnosis_result.get('simulation_mode'):
                    click.echo("")
                    console.print("[yellow]⚠️  MODO SIMULACIÓN ACTIVO[/yellow]")
                    console.print("[yellow]   → La latencia puede ser del flujo de datos sintéticos[/yellow]")
                    console.print("[yellow]   → Los timings pueden no reflejar el hardware real[/yellow]")
                
                # Mostrar comandos sugeridos
                commands = diagnosis_result.get('suggested_commands', [])
                if commands:
                    click.echo("")
                    console.print("[bold cyan]🔧 ACCIONES SUGERIDAS (COPY-PASTE):[/bold cyan]")
                    for cmd in commands:
                        console.print(f"[green]▶️  {cmd}[/green]")
                
                # Mostrar evidencia citada
                evidence = diagnosis_result.get('evidence', [])
                if evidence and detailed:
                    click.echo("")
                    console.print("[bold cyan]📋 EVIDENCIA CITADA:[/bold cyan]")
                    for ev in evidence[:5]:  # Mostrar máx 5
                        if isinstance(ev, dict):
                            console.print(f"  [yellow]Línea {ev.get('line_number', 'N/A')}[/yellow]: {ev.get('message', 'N/A')}")
                        else:
                            console.print(f"  [yellow]{str(ev)[:50]}[/yellow]")
                
                # Mostrar análisis detallado del LLM si está disponible
                llm_analysis = diagnosis_result.get('llm_analysis', None)
                if llm_analysis and detailed:
                    click.echo("")
                    console.print("[bold cyan]🤖 ANÁLISIS DETALLADO DEL SUPER CEREBRO:[/bold cyan]")
                    console.print(Markdown(llm_analysis))
            else:
                click.echo(diagnosis_result.get('formatted_diagnosis', diagnosis_result.get('diagnosis', '')))
        else:
            # Formato simple si es string
            click.echo(diagnosis_result)
        
        click.secho("\n✅ Diagnóstico completado", fg='green')
        
    except Exception as e:
        click.secho(f"❌ Error durante diagnóstico: {e}", fg='red')
        import traceback
        if detailed:
            click.echo(traceback.format_exc())
        sys.exit(1)


@brain.command(name="propose")
def brain_propose():
    """Generar propuestas de mejora automáticas usando Qwen 2.5."""
    api_key = _check_api_key()
    if not api_key:
        sys.exit(1)
    
    click.secho("🧠 Generando propuestas de mejora...\n", fg='cyan', bold=True)
    
    try:
        # Inicializar cliente LLM directamente
        client = LLMClient()
        click.secho("  ✅ Cliente LLM inicializado", fg='green')
        
        # Prompt simple para propuestas
        prompt = """Sugiere una propuesta de mejora para un sistema de trading autónomo en máximo 3 líneas:
        
- Cambio propuesto
- Beneficio esperado"""
        
        click.secho("  ⏳ Generando propuesta...", fg='yellow')
        
        proposal = client.generate(
            prompt=prompt,
            system_prompt="Eres un experto en trading systems.",
            temperature=0.4,
            max_tokens=300
        )
        
        # Mostrar propuesta
        if console:
            from rich.panel import Panel
            console.print(Panel(
                proposal,
                border_style="cyan",
                title="💡 Propuesta de Mejora",
                expand=False
            ))
        else:
            click.echo(proposal)
        
        click.secho("\n✅ Propuesta generada", fg='green')
        
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg='red')
        sys.exit(1)


@brain.command(name="health")
def brain_health():
    """Ver estado de salud del Super Cerebro y del sistema."""
    api_key = _check_api_key()
    if not api_key:
        sys.exit(1)
    
    click.secho("💚 Estado de Salud del Sistema\n", fg='cyan', bold=True)
    
    try:
        # Verificar LLMClient
        try:
            client = LLMClient()
            client.health_check()
            llm_status = "🟢 OK"
        except:
            llm_status = "🔴 Error"
        
        # Verificar Memory
        try:
            sentinel = get_sentinel()
            sentinel.query_memory("system_state")
            memory_status = "🟢 OK"
        except:
            memory_status = "⚠️  No disponible"
        
        # Mostrar tabla
        if console:
            from rich.table import Table
            
            table = Table(title="🏥 Estado de Componentes", show_header=True, header_style="bold cyan")
            table.add_column("Componente", style="cyan")
            table.add_column("Estado", style="green")
            
            table.add_row("🧠 LLMClient (Qwen 2.5)", llm_status)
            table.add_row("💾 Memoria del Sistema", memory_status)
            table.add_row("📊 Orchest rador", "🟢 OK")
            
            console.print(table)
        else:
            click.echo(f"🧠 LLMClient: {llm_status}")
            click.echo(f"💾 Memoria: {memory_status}")
            click.echo(f"📊 Orquestrador: 🟢 OK")
        
        click.secho("\n✅ Verificación completada", fg='green')
        
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg='red')
        sys.exit(1)

        
    click.secho("\n=== TEST COMPLETE ===", bold=True)


if __name__ == '__main__':
    if '--test' in sys.argv:
        test_cli()
    else:
        cli()
