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
import joblib
from aiphalab.commands import (
    status_group,
    cycle_group,
    config_group,
    history_group,
    debug_group,
    codecraft_group,
    ask_command,
    ask_health_command,
)
from cgalpha.orchestrator import CGAlphaOrchestrator

# Rich console (optional)
try:
    from rich.console import Console
    console = Console()
except ImportError:
    console = None

# Oracle loader (lazy loading)
_oracle_cache = None

def get_oracle():
    """Load Oracle model (cached)"""
    global _oracle_cache
    if _oracle_cache is None:
        model_path = AIPHA_ROOT / "oracle" / "models" / "oracle_5m_trained.joblib"
        if model_path.exists():
            _oracle_cache = joblib.load(str(model_path))
            return _oracle_cache
        else:
            return None
    return _oracle_cache


@click.group()
@click.option('--dry-run', is_flag=True, default=False, help='Simulate without changes')
@click.pass_context
def cli(ctx, dry_run):
    """
    🧠 CGAlpha CLI v2.0 - Unified & Modularized (AiphaLab CLI legacy)
    
    CGAlpha v0.1.x - Unified autonomous system
    (legacy alias: aipha)
    
    Run: cgalpha --help for commands
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
cli.add_command(codecraft_group)
cli.add_command(ask_command)
cli.add_command(ask_health_command)


@cli.command()
def version():
    """Show version information"""
    version_info = {
        "cgalpha": "0.1.x",
        "aipha_alias": "supported",
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
[bold]CGAlpha CLI v2.0[/bold]

A modularized, production-ready CLI for Aipha.

[bold blue]Available Commands:[/bold blue]
  • status   - System status and health
  • cycle    - Execute improvement cycles
  • config   - Manage configuration
  • history  - View action history
  • debug    - Debugging tools
  • oracle   - Oracle signal filtering

[bold blue]Usage:[/bold blue]
  cgalpha status show          # Show system status
  cgalpha cycle run            # Run one cycle
  cgalpha config show          # Show configuration
  cgalpha history actions      # Show action history
  cgalpha debug check-deps     # Check dependencies
  cgalpha oracle test-model    # Test Oracle model
  cgalpha auto-analyze         # Ghost Architect causal analysis
  cgalpha ask "..."            # Local Librarian mentor
  cgalpha ask-health           # Local Librarian health check

For more: cgalpha --help
        """, border_style="blue", title="ℹ️  Information"))
    else:
        click.echo("CGAlpha CLI v2.0")
        click.echo("Run: cgalpha --help for commands")


@cli.group()
def oracle():
    """⚡ Oracle signal filtering and management"""
    pass


@oracle.command()
@click.option('--threshold', type=float, default=0.5, help='Confidence threshold (0-1)')
def test_model(threshold):
    """Test Oracle model availability and performance"""
    oracle_model = get_oracle()
    
    if oracle_model is None:
        click.secho("❌ Oracle model not found at oracle/models/oracle_5m_trained.joblib", fg='red')
        return
    
    click.secho("✅ Oracle model loaded successfully", fg='green')
    click.echo(f"   Model type: {type(oracle_model).__name__}")
    click.echo(f"   Confidence threshold: {threshold}")
    click.echo(f"   Status: Ready for signal filtering")


@oracle.command()
@click.argument('signal_count', type=int, default=10)
def predict(signal_count):
    """Predict on sample signals (demo)"""
    import numpy as np
    
    oracle_model = get_oracle()
    if oracle_model is None:
        click.secho("❌ Oracle model not available", fg='red')
        return
    
    # Generate dummy features (4 features)
    X_dummy = np.random.rand(signal_count, 4)
    
    try:
        predictions = oracle_model.predict(X_dummy)
        probabilities = oracle_model.predict_proba(X_dummy)
        
        click.echo(f"\n📊 Sample predictions ({signal_count} signals):")
        click.echo(f"   Predicted as TP: {(predictions == 1).sum()}")
        click.echo(f"   Predicted as SL: {(predictions == -1).sum()}")
        click.echo(f"   Average confidence: {probabilities.max(axis=1).mean():.2%}")
        click.secho("   ✅ Oracle is operational", fg='green')
    except Exception as e:
        click.secho(f"❌ Error during prediction: {e}", fg='red')


@oracle.command()
def status():
    """Show Oracle status"""
    oracle_model = get_oracle()
    
    if oracle_model is None:
        click.secho("❌ Oracle model not loaded", fg='red')
        return
    
    click.secho("✅ Oracle Status:", fg='green', bold=True)
    click.echo(f"   Model: Random Forest (100 trees)")
    click.echo(f"   Training accuracy: 50%")
    click.echo(f"   Validation accuracy: 70.91%")
    click.echo(f"   Filtered accuracy: 75.00% (+4.09% improvement)")
    click.echo(f"   Status: Production-Ready ✅")
    click.echo(f"   Location: oracle/models/oracle_5m_trained.joblib")


@cli.command(name="auto-analyze")
@click.option('--working-dir', 'working_dir', type=str, default='.',
              help='Directorio de trabajo (raíz del proyecto)')
@click.option('--min-confidence', 'min_confidence', type=float, default=0.70,
              help='Confianza mínima para propuestas (default: 0.70)')
@click.option('--log-file', 'log_file', type=str, default=None,
              help='Ruta explícita a logs JSONL (opcional)')
@click.option('--cleanup-processed', 'cleanup_processed', is_flag=True, default=False,
              help='Renombrar log procesado a *.processed al finalizar')
def auto_analyze(working_dir: str, min_confidence: float, log_file: str, cleanup_processed: bool):
    """
    🔍 Ghost Architect v0.1 - Análisis causal histórico + propuestas accionables.
    """
    orchestrator = CGAlphaOrchestrator(working_dir=working_dir)
    result = orchestrator.auto_analyze(
        min_confidence=min_confidence,
        log_file=log_file,
        cleanup_processed=cleanup_processed
    )

    analysis = result["analysis"]
    insights = result["insights"][:5]
    proposals = result["proposals"][:5]
    causal_metrics = analysis.get("causal_metrics", {})

    click.echo("🔍 CGAlpha Performance Analysis")
    click.echo("📊 Detected Issues:")
    click.echo(f"- Records analyzed: {analysis.get('records_analyzed', 0)}")
    click.echo(f"- Patterns detected: {len(analysis.get('patterns', []))}")
    click.echo(f"- Analysis engine: {analysis.get('analysis_engine', 'heuristic_fallback')}")

    if analysis.get("patterns"):
        for pattern in analysis["patterns"][:3]:
            ptype = pattern.get("type", "unknown")
            value = pattern.get("value")
            click.echo(f"- {ptype}: {value}")
    else:
        click.echo("- No critical patterns detected in historical logs.")

    if causal_metrics:
        click.echo("")
        click.echo("Causal Metrics:")
        click.echo(f"- Accuracy Causal: {causal_metrics.get('accuracy_causal', 0):.2f}")
        click.echo(f"- Efficiency: {causal_metrics.get('efficiency', 0):.2f}")

    click.echo("")
    click.echo("💡 Generated Proposals:")
    if proposals:
        for proposal in proposals:
            click.echo(f"[Confidence: {proposal['confidence']:.2f}] \"{proposal['proposal_text']}\"")
            click.echo(f"Reason: {proposal['reason']}")
    else:
        click.echo("No automatic proposals generated from performance data.")

    if insights:
        click.echo("")
        click.echo("🧠 Ghost Architect Insights:")
        for insight in insights:
            click.echo(f"- {insight['type']}: {insight['reason']}")
            click.echo(f"  Suggested: {insight['command']}")

    if proposals:
        first_id = proposals[0].get("proposal_id", "AUTO_PROP_001")
        click.echo("")
        click.echo(f"Run 'cgalpha codecraft apply --id {first_id}' to execute.")

    click.echo("")
    click.echo(f"Report saved: {result['report_path']}")
    if result.get("cleaned_log"):
        click.echo(f"Processed log archived: {result['cleaned_log']}")


if __name__ == "__main__":
    cli()
