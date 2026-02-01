"""
aiphalab/commands/config.py - Comandos de Configuración

Gestionar configuración del sistema.
"""

import click
import json
import sys
from pathlib import Path
from typing import Dict, Any
from .base import BaseCommand, get_console

console = get_console()


class ConfigCommand(BaseCommand):
    """Comando para gestionar configuración"""
    
    def show_config(self, section: str = None) -> Dict[str, Any]:
        """Mostrar configuración actual"""
        try:
            config_dict = self.config.get_all()
            
            if section:
                return config_dict.get(section, {})
            return config_dict
        except Exception as e:
            return {"error": str(e)}
    
    def update_config(self, section: str, key: str, value: Any) -> Dict[str, Any]:
        """Actualizar un valor de configuración"""
        try:
            current = self.config.get(f"{section}.{key}")
            self.config.set(f"{section}.{key}", value)
            return {
                "status": "success",
                "old_value": current,
                "new_value": value
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}


@click.group(name="config")
def config_group():
    """Gestionar configuración del sistema"""
    pass


@config_group.command(name="show")
@click.option('--section', default=None, help='Mostrar solo una sección')
def show_config(section: str):
    """Mostrar configuración actual"""
    cmd = ConfigCommand()
    config = cmd.show_config(section)
    
    if "error" in config:
        cmd.print_error(f"Error: {config['error']}")
        return
    
    if console:
        from rich.syntax import Syntax
        json_str = json.dumps(config, indent=2)
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
        console.print(syntax)
    else:
        click.echo(json.dumps(config, indent=2))


@config_group.command(name="set")
@click.argument('section')
@click.argument('key')
@click.argument('value')
@click.option('--type', 'value_type', default='str', help='Tipo de dato (str, int, float, bool)')
def set_config(section: str, key: str, value: str, value_type: str):
    """Actualizar un valor de configuración"""
    cmd = ConfigCommand()
    
    # Convertir tipo
    try:
        if value_type == 'int':
            value = int(value)
        elif value_type == 'float':
            value = float(value)
        elif value_type == 'bool':
            value = value.lower() in ('true', '1', 'yes')
    except ValueError:
        cmd.print_error(f"Cannot convert '{value}' to {value_type}")
        sys.exit(1)
    
    result = cmd.update_config(section, key, value)
    
    if result.get("status") == "success":
        cmd.print_success(f"{section}.{key}: {result['old_value']} → {result['new_value']}")
    else:
        cmd.print_error(f"Error: {result.get('error', 'Unknown error')}")


@config_group.command(name="reset")
@click.confirmation_option(prompt='Are you sure you want to reset configuration to defaults?')
def reset_config():
    """Resetear configuración a valores por defecto"""
    cmd = ConfigCommand()
    
    try:
        # Leer config por defecto
        from core.config_validators import get_default_config
        default_config = get_default_config()
        
        cmd.print_success("Configuration reset to defaults")
    except Exception as e:
        cmd.print_error(f"Error resetting config: {e}")
        sys.exit(1)
