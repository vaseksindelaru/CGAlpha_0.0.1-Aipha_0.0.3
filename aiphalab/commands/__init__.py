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
"""

from .status import status_group
from .cycle import cycle_group
from .config import config_group
from .history import history_group
from .debug import debug_group

__all__ = [
    "status_group",
    "cycle_group",
    "config_group",
    "history_group",
    "debug_group",
]
