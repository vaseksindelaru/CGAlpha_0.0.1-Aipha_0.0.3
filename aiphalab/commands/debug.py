"""
aiphalab/commands/debug.py - Comandos de Debug

Herramientas de debugging del sistema.
"""

import click
import sys
from typing import Dict, Any
from .base import BaseCommand, get_console

console = get_console()


class DebugCommand(BaseCommand):
    """Comando para debugging del sistema"""
    
    def check_imports(self) -> Dict[str, bool]:
        """Verificar que todos los imports funcionan"""
        imports_status = {}
        
        modules_to_check = [
            ("Core", "core.orchestrator_hardened"),
            ("Trading", "core.trading_engine"),
            ("Oracle", "trading_manager"),
            ("Health", "core.health_monitor"),
            ("Exceptions", "core.exceptions"),
            ("Config", "core.config_manager"),
        ]
        
        for name, module in modules_to_check:
            try:
                __import__(module)
                imports_status[name] = True
            except ImportError as e:
                imports_status[name] = False
        
        return imports_status
    
    def check_dependencies(self) -> Dict[str, bool]:
        """Verificar dependencias externas"""
        deps_status = {}
        
        dependencies = [
            ("pandas", "pandas"),
            ("numpy", "numpy"),
            ("duckdb", "duckdb"),
            ("click", "click"),
            ("pydantic", "pydantic"),
            ("rich", "rich"),
            ("openai", "openai"),
            ("requests", "requests"),
        ]
        
        for name, module in dependencies:
            try:
                __import__(module)
                deps_status[name] = True
            except ImportError:
                deps_status[name] = False
        
        return deps_status


@click.group(name="debug")
def debug_group():
    """Herramientas de debugging"""
    pass


@debug_group.command(name="check-imports")
def check_imports():
    """Verificar que todos los imports funcionan"""
    cmd = DebugCommand()
    status = cmd.check_imports()
    
    if console:
        from rich.table import Table
        
        table = Table(title="Import Status", show_header=True, header_style="bold blue")
        table.add_column("Module", style="cyan")
        table.add_column("Status", style="magenta")
        
        for module, ok in status.items():
            status_str = "✓" if ok else "✗"
            color = "green" if ok else "red"
            table.add_row(module, f"[{color}]{status_str}[/{color}]")
        
        console.print(table)
    else:
        for module, ok in status.items():
            symbol = "✓" if ok else "✗"
            click.echo(f"  {symbol} {module}")


@debug_group.command(name="check-deps")
def check_dependencies():
    """Verificar dependencias externas"""
    cmd = DebugCommand()
    status = cmd.check_dependencies()
    
    missing = [dep for dep, ok in status.items() if not ok]
    
    if missing:
        cmd.print_warning(f"Missing dependencies: {', '.join(missing)}")
        cmd.print_info("Install with: pip install -r requirements.txt")
    else:
        cmd.print_success("All dependencies installed")
    
    if console:
        from rich.table import Table
        
        table = Table(title="Dependency Status", show_header=True, header_style="bold blue")
        table.add_column("Package", style="cyan")
        table.add_column("Status", style="magenta")
        
        for dep, ok in status.items():
            status_str = "✓" if ok else "✗"
            color = "green" if ok else "red"
            table.add_row(dep, f"[{color}]{status_str}[/{color}]")
        
        console.print(table)


@debug_group.command(name="system-info")
def system_info():
    """Mostrar información del sistema"""
    cmd = DebugCommand()
    
    try:
        import sys
        import platform
        from pathlib import Path
        
        info = {
            "Python": f"{sys.version.split()[0]}",
            "Platform": platform.system(),
            "Architecture": platform.machine(),
            "Root": str(Path.cwd()),
        }
        
        if console:
            from rich.table import Table
            
            table = Table(title="System Information", show_header=False)
            table.add_column("Key", style="cyan")
            table.add_column("Value", style="magenta")
            
            for key, value in info.items():
                table.add_row(key, value)
            
            console.print(table)
        else:
            for key, value in info.items():
                click.echo(f"  {key}: {value}")
        
        cmd.print_success("System info retrieved")
    except Exception as e:
        cmd.print_error(f"Error getting system info: {e}")


@debug_group.command(name="validate-config")
def validate_config():
    """Validar configuración del sistema"""
    cmd = DebugCommand()
    
    try:
        from core.config_validators import validate_config, get_default_config
        
        # Obtener config actual
        default_config = get_default_config()
        config_dict = default_config.to_dict()
        
        # Validar
        is_valid, error = validate_config(config_dict)
        
        if is_valid:
            cmd.print_success("Configuration is valid")
        else:
            cmd.print_error(f"Configuration error: {error}")
            sys.exit(1)
    except Exception as e:
        cmd.print_error(f"Cannot validate config: {e}")
        sys.exit(1)
