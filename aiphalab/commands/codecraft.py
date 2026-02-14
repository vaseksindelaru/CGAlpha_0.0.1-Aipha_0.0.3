"""
aiphalab/commands/codecraft.py - Code Craft Sage CLI Integration

Este módulo proporciona comandos CLI para Code Craft Sage:
- apply: Ejecutar el pipeline completo de 4 fases
- status: Mostrar estado del sistema Code Craft Sage

Ejemplo de uso:
    cgalpha codecraft apply --text "Cambiar threshold de 0.3 a 0.65"
    cgalpha codecraft status
"""

import sys
import time
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cgalpha.codecraft.orchestrator import CodeCraftOrchestrator, CodeCraftError


# Rich console
console = Console()


@click.group()
def codecraft_group():
    """
    🎨 Code Craft Sage - AI-Powered Code Improvement
    
    Ejecuta el pipeline completo de 4 fases:
    1. Parsear propuesta
    2. Modificar código
    3. Generar tests
    4. Crear commit Git
    
    ¡Nunca modifica main/master - siempre usa ramas de feature!
    """
    pass


@codecraft_group.command()
@click.option('--text', 'proposal_text', type=str, help='Texto de la propuesta')
@click.option('--id', 'proposal_id', type=str, help='ID de la propuesta (opcional)')
@click.option('--working-dir', 'working_dir', type=str, default='.', 
              help='Directorio de trabajo (raíz del proyecto)')
@click.option('--no-rollback', 'no_rollback', is_flag=True, default=False,
              help='No hacer rollback automático si los tests fallan')
@click.option('--verbose', 'verbose', is_flag=True, default=False,
              help='Mostrar output detallado')
def apply(proposal_text: str, proposal_id: str, working_dir: str, no_rollback: bool, verbose: bool):
    """
    🎨 Ejecutar el pipeline completo de Code Craft Sage
    
    \b
    Ejemplos:
        cgalpha codecraft apply --text "Cambiar threshold de 0.3 a 0.65"
        cgalpha codecraft apply --id prop_001 --working-dir /path/to/project
    
    \b
    El pipeline ejecutará:
        1. Parsear propuesta (ProposalParser)
        2. Modificar código (ASTModifier)
        3. Generar tests (TestGenerator)
        4. Crear commit Git (GitAutomator)
    """
    if not proposal_text:
        console.print("[bold red]❌ Error: Se requiere --text o --id[/bold red]")
        console.print("Usa: cgalpha codecraft apply --text 'TU PROPUESTA'")
        return
    
    # Inicializar orchestrator
    try:
        orchestrator = CodeCraftOrchestrator(
            working_dir=working_dir,
            auto_rollback=not no_rollback
        )
    except Exception as e:
        console.print(f"[bold red]❌ Error inicializando orchestrator: {e}[/bold red]")
        return
    
    # Mostrar header
    console.print("\n")
    console.print(Panel(
        Text("CODE CRAFT SAGE - PIPELINE EXECUTION", justify="center", style="bold cyan"),
        border_style="cyan",
        subtitle="🎨 AI-Powered Code Improvement"
    ))
    
    try:
        # Ejecutar pipeline
        start_time = time.time()
        result = orchestrator.execute_pipeline(proposal_text, proposal_id)
        total_time = time.time() - start_time
        
        # Mostrar progreso de cada fase
        _display_pipeline_progress(result, verbose)
        
        # Mostrar resultado final
        _display_final_result(result, total_time)
        
    except CodeCraftError as e:
        console.print(f"[bold red]❌ Error en el pipeline: {e}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]❌ Error inesperado: {e}[/bold red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())


def _display_pipeline_progress(result: dict, verbose: bool = False):
    """
    Muestra el progreso de cada fase del pipeline.
    """
    pipeline_history = result.get('pipeline_history', [])
    
    # Mostrar cada fase
    for phase_info in pipeline_history:
        phase = phase_info.get('phase', 0)
        name = phase_info.get('name', '')
        status = phase_info.get('status', 'unknown')
        duration = phase_info.get('duration', 0)
        
        if phase == "rollback":
            emoji = "🔄"
            status_text = "ROLLED BACK"
            style = "yellow"
        elif status == "success":
            emoji = "✅"
            status_text = "Done"
            style = "green"
        elif status == "failed":
            emoji = "❌"
            status_text = "FAILED"
            style = "red"
        else:
            emoji = "⏳"
            status_text = "RUNNING"
            style = "blue"
        
        # Formato de la línea de fase
        phase_str = f"[{phase}/4]" if isinstance(phase, int) else "    "
        console.print(f"{phase_str} {emoji} {name:<20} {status_text:<10} ({duration:.2f}s)")
        
        # Mostrar detalles si verbose
        if verbose and 'details' in phase_info:
            details = phase_info['details']
            if isinstance(details, dict):
                for key, value in details.items():
                    console.print(f"     ├─ {key}: {value}")
    
    console.print("")


def _display_final_result(result: dict, total_time: float):
    """
    Muestra el resultado final del pipeline.
    """
    status = result.get('status', 'unknown')
    proposal_id = result.get('proposal_id', 'unknown')
    
    # Separador
    console.print("━" * 50)
    
    if status == "success":
        # Panel de éxito
        branch_name = result.get('branch_name', 'unknown')
        commit_hash = result.get('commit_hash', 'unknown')[:8]
        test_results = result.get('test_results', {})
        
        # Resumen de tests
        console.print("[bold green]✅ SUCCESS: Change Applied Successfully![/bold green]\n")
        
        console.print(f"Branch:    [cyan]{branch_name}[/cyan]")
        console.print(f"Commit:    [cyan]{commit_hash}[/cyan]")
        console.print(f"Proposal:  [cyan]{proposal_id}[/cyan]\n")
        
        # Resumen de tests
        if test_results:
            console.print("[bold]Test Results:[/bold]")
            console.print(f"  ├─ Unit Test:       {test_results.get('new_test_status', 'N/A').upper()}  ✅")
            console.print(f"  ├─ Regression:      {test_results.get('regression_status', 'N/A').upper()}  ✅")
            console.print(f"  └─ Coverage:        {test_results.get('coverage_percentage', 0):.1f}%  ✅")
        
        console.print("")
        
        # Próximos pasos
        console.print(Panel(
            "[bold]Next Steps:[/bold]\n"
            f"1. Review changes: git diff main {branch_name}\n"
            "2. Run full tests: pytest\n"
            f"3. Merge when ready: git merge {branch_name}",
            title="📋 Next Steps",
            border_style="green"
        ))
        
    else:
        # Panel de fallo
        console.print("[bold red]❌ FAILED: Pipeline Execution Failed[/bold red]\n")
        
        errors = result.get('errors', [])
        if errors:
            console.print("[bold]Errors:[/bold]")
            for i, error in enumerate(errors, 1):
                console.print(f"  {i}. {error.get('message', 'Unknown error')}")
        
        # Mostrar si se hizo rollback
        changes = result.get('changes_summary', {})
        if changes.get('rollback_performed'):
            console.print("\n[yellow]🔄 Rollback performed - Original code restored[/yellow]")
        
        # Sugerencias
        console.print(Panel(
            "[bold]Suggestions:[/bold]\n"
            "- Check your proposal text for errors\n"
            "- Ensure the target file exists\n"
            "- Verify the class/attribute names are correct\n"
            "- Run with --verbose for more details",
            title="💡 Troubleshooting",
            border_style="yellow"
        ))
    
    # Tiempo total
    console.print(f"\n[dim]Total time: {total_time:.2f}s[/dim]")


@codecraft_group.command()
@click.option('--working-dir', 'working_dir', type=str, default='.',
              help='Directorio de trabajo (raíz del proyecto)')
def status(working_dir: str):
    """
    📊 Mostrar estado de Code Craft Sage
    
    Muestra:
    - Estado del sistema (disponible, ocupado, error)
    - Última propuesta procesada
    - Estado del repositorio Git
    """
    try:
        orchestrator = CodeCraftOrchestrator(working_dir=working_dir)
        status_info = orchestrator.get_status()
    except Exception as e:
        console.print(f"[bold red]❌ Error obteniendo estado: {e}[/bold red]")
        return
    
    # Panel de estado
    console.print("\n")
    console.print(Panel(
        f"""
[bold cyan]Code Craft Sage Status[/bold cyan]

[bold]State:[/bold]       {status_info.get('status', 'unknown').upper()}
[bold]Working Dir:[/bold] {status_info.get('working_dir', 'unknown')}
[bold]Auto-Rollback:[/bold] {'Yes' if status_info.get('auto_rollback') else 'No'}
[bold]Current Proposal:[/bold] {status_info.get('current_proposal_id', 'None')}

[bold]Components:[/bold]
  ├─ ProposalParser:  {status_info.get('components', {}).get('parser', 'unknown')}
  ├─ ASTModifier:      {status_info.get('components', {}).get('modifier', 'unknown')}
  ├─ TestGenerator:    {status_info.get('components', {}).get('test_generator', 'unknown')}
  └─ GitAutomator:     {status_info.get('components', {}).get('git_automator', 'unknown')}
        """,
        title="🎨 Code Craft Sage",
        border_style="cyan"
    ))
    
    # Estado de Git
    git_status = status_info.get('git_status', {})
    if 'error' not in git_status:
        console.print(Panel(
            f"""
[bold]Git Status[/bold]

[bold]Current Branch:[/bold] {git_status.get('current_branch', 'unknown')}
[bold]Repo Clean:[/bold]   {'Yes ✅' if git_status.get('is_clean') else 'No ❌'}
[bold]Uncommitted:[/bold]  {'Yes ❌' if git_status.get('has_uncommitted_changes') else 'No ✅'}
            """,
            title="📝 Git",
            border_style="blue"
        ))
    else:
        console.print(f"[yellow]⚠️  Git: {git_status.get('error')}[/yellow]")


@codecraft_group.command()
@click.option('--working-dir', 'working_dir', type=str, default='.',
              help='Directorio de trabajo (raíz del proyecto)')
@click.option('--min-confidence', 'min_confidence', type=float, default=0.70,
              help='Confianza mínima para propuestas (default: 0.70)')
def auto_analyze(working_dir: str, min_confidence: float):
    """
    🔍 Analizar métricas y generar propuestas de mejora automáticas
    
    Analiza datos de rendimiento y genera propuestas de mejora basadas en:
    - Win Rate bajo
    - Drawdown excesivo
    - Rachas de pérdidas
    - Cobertura de tests baja
    
    Ejemplo:
        cgalpha codecraft auto-analyze
        cgalpha codecraft auto-analyze --min-confidence 0.80
    """
    # Importar aquí para evitar circular imports
    from cgalpha.codecraft.proposal_generator import ProposalGenerator
    
    console.print("\n")
    console.print(Panel(
        Text("CGAlpha Performance Analysis", justify="center", style="bold cyan"),
        border_style="cyan",
        subtitle="🔍 Automatic Proposal Generator"
    ))
    
    try:
        # Crear generator
        memory_dir = str(Path(working_dir).resolve() / "aipha_memory")
        generator = ProposalGenerator(
            data_dir=memory_dir,
            min_confidence=min_confidence
        )
        
        # Analizar
        proposals = generator.analyze_performance()
        
        if proposals:
            # Mostrar métricas detectadas
            console.print(f"\n📊 Detected Issues: {len(proposals)}")
            
            # Tabla de propuestas
            table = Table(title="💡 Generated Proposals")
            table.add_column("#", style="dim")
            table.add_column("Confidence", style="green")
            table.add_column("Proposal", style="cyan")
            table.add_column("Reason", style="yellow")
            table.add_column("Severity", style="red")
            
            for i, prop in enumerate(proposals, 1):
                severity_emoji = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(prop.get("severity", "low"), "⚪")
                
                table.add_row(
                    str(i),
                    f"{prop['confidence']:.0%}",
                    prop['proposal_text'],
                    prop['reason'],
                    f"{severity_emoji} {prop.get('severity', 'low')}"
                )
            
            console.print(table)
            
            # Mostrar comando para aplicar
            console.print("\n")
            console.print(Panel(
                "[bold]Commands to Execute:[/bold]\n"
                f"cgalpha codecraft apply --text \"{proposals[0]['proposal_text']}\" --id {proposals[0]['proposal_id']}\n"
                "\n[dim]Note: Proposals are generated but NOT applied automatically.[/dim]",
                title="🚀 Next Steps",
                border_style="green"
            ))
            
        else:
            console.print(Panel(
                "[bold green]✅ No issues detected - System is performing well![/bold green]\n"
                "Your trading system is operating within acceptable parameters.",
                title="🎉 All Good!",
                border_style="green"
            ))
            
    except Exception as e:
        console.print(f"[bold red]❌ Error during analysis: {e}[/bold red]")


# Registrar en el CLI principal
# Este código se ejecuta cuando el módulo es importado por cli_v2.py
if __name__ == "__main__":
    # Si se ejecuta directamente, mostrar ayuda
    codecraft_group()
