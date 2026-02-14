"""
aiphalab/commands/ - Módulos de Comandos CLI

Estructura modularizada del CLI original (1,649 líneas).
Divide responsabilidades: cada comando es un módulo independiente.

Soluciona: P1 #5 - CLI monolítico sin modularización

Comandos disponibles:
  - status.py     : Status del sistema
  - cycle.py      : Ejecutar ciclos de mejora
  - config.py     : Gestión de configuración
  - history.py    : Historial de cambios
  - debug.py      : Herramientas de debug
  - codecraft.py  : Code Craft Sage - AI-Powered Code Improvement
"""

from .base import BaseCommand
from .status import status_group
from .cycle import cycle_group
from .config import config_group
from .history import history_group
from .debug import debug_group
from .codecraft import codecraft_group
from .librarian import ask_command, ask_health_command

__all__ = [
    "BaseCommand",
    "status_group",
    "cycle_group",
    "config_group",
    "history_group",
    "debug_group",
    "codecraft_group",
    "ask_command",
    "ask_health_command",
]
