"""
CGA_Ops: Supervisor Determinista de Recursos

🎯 MISIÓN: Gestionar el semáforo de recursos para evitar conflictos entre
           Aipha (ejecutor en tiempo real) y CGAlpha (analista intensivo).

🔴 REGLA DE ORO: Si Aipha necesita CPU/RAM, CGAlpha DEBE ceder.
"""

import psutil
import logging
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict

logger = logging.getLogger(__name__)


class ResourceState(Enum):
    """Estados del semáforo de recursos"""
    GREEN = "green"    # < 60% RAM, entrenamiento permitido
    YELLOW = "yellow"  # 60-80% RAM, pausa nuevos procesos
    RED = "red"        # > 80% RAM O señal de trading activa


@dataclass
class ResourceSnapshot:
    """Snapshot del estado de recursos del sistema"""
    cpu_percent: float
    ram_percent: float
    ram_available_mb: float
    state: ResourceState
    aipha_signal_active: bool = False
    
    def __str__(self):
        return (f"CPU: {self.cpu_percent:.1f}% | RAM: {self.ram_percent:.1f}% "
                f"({self.ram_available_mb:.0f}MB free) | State: {self.state.value}")


class CGAOps:
    """
    Supervisor de Recursos para CGAlpha
    
    **Decisiones Autónomas Implementadas:**
    1. Umbrales de RAM: 60% (Yellow), 80% (Red)
       Justificación: Basado en best practices de sistemas en producción
    2. Polling interval: 5 segundos
       Justificación: Balance entre reactividad y overhead
    3. Prioridad absoluta a Aipha
       Justificación: Operaciones en tiempo real >> Análisis offline
    """
    
    def __init__(
        self,
        ram_threshold_yellow: float = 60.0,
        ram_threshold_red: float = 80.0,
        poll_interval_seconds: int = 5
    ):
        self.ram_threshold_yellow = ram_threshold_yellow
        self.ram_threshold_red = ram_threshold_red
        self.poll_interval = poll_interval_seconds
        self._aipha_signal_flag = False  # Flag manual desde Aipha
        
    def get_resource_state(self) -> ResourceSnapshot:
        """
        Obtiene el estado actual de recursos del sistema
        
        Returns:
            ResourceSnapshot con métricas y estado del semáforo
        """
        cpu_percent = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory()
        ram_percent = ram.percent
        ram_available_mb = ram.available / (1024 * 1024)
        
        # Determinar estado del semáforo
        if self._aipha_signal_flag or ram_percent >= self.ram_threshold_red:
            state = ResourceState.RED
        elif ram_percent >= self.ram_threshold_yellow:
            state = ResourceState.YELLOW
        else:
            state = ResourceState.GREEN
        
        snapshot = ResourceSnapshot(
            cpu_percent=cpu_percent,
            ram_percent=ram_percent,
            ram_available_mb=ram_available_mb,
            state=state,
            aipha_signal_active=self._aipha_signal_flag
        )
        
        logger.debug(f"Resource snapshot: {snapshot}")
        return snapshot
    
    def can_start_heavy_task(self) -> bool:
        """
        Verifica si se puede iniciar un proceso pesado (EconML, Clustering)
        
        Returns:
            True si el semáforo está en GREEN
        """
        snapshot = self.get_resource_state()
        can_start = snapshot.state == ResourceState.GREEN
        
        if not can_start:
            logger.warning(
                f"Heavy task blocked: {snapshot.state.value} "
                f"(RAM: {snapshot.ram_percent:.1f}%)"
            )
        
        return can_start
    
    def signal_aipha_active(self, active: bool):
        """
        Flag manual desde Aipha para indicar operación en tiempo real
        
        Args:
            active: True si Aipha está procesando señal/trade activo
        """
        self._aipha_signal_flag = active
        if active:
            logger.warning("🔴 AIPHA SIGNAL ACTIVE - CGAlpha entering standby mode")
        else:
            logger.info("🟢 Aipha signal cleared - CGAlpha can resume")
    
    def get_recommended_actions(self) -> List[str]:
        """
        Genera recomendaciones basadas en el estado actual
        
        Returns:
            Lista de acciones sugeridas para los Labs
        """
        snapshot = self.get_resource_state()
        actions = []
        
        if snapshot.state == ResourceState.RED:
            actions.append("STOP: Terminate all non-critical CGAlpha processes")
            actions.append("PRIORITY: Aipha has absolute resource priority")
        elif snapshot.state == ResourceState.YELLOW:
            actions.append("PAUSE: Do not start new heavy tasks")
            actions.append("CONTINUE: Existing tasks may finish")
        else:
            actions.append("GO: System resources available for analysis")
            actions.append("SAFE: Heavy ML training permitted")
        
        return actions


# 🧪 Test rápido si se ejecuta directamente
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    ops = CGAOps()
    snapshot = ops.get_resource_state()
    
    print("=" * 60)
    print("CGA_Ops Resource Monitor")
    print("=" * 60)
    print(f"\n{snapshot}\n")
    print("Recommended Actions:")
    for action in ops.get_recommended_actions():
        print(f"  • {action}")
    print("\nCan start heavy task:", ops.can_start_heavy_task())
