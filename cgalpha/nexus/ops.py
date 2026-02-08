"""
CGA_Ops: Supervisor Determinista de Recursos con Integración Redis

🎯 MISIÓN: Gestionar el semáforo de recursos Y la cola de tareas distribuidas.
           Actúa como puente entre la infraestructura física (CPU/RAM) y 
           la lógica distribuida (Redis).

🔴 REGLA DE ORO: Si Aipha necesita CPU/RAM, CGAlpha DEBE ceder.
"""

import psutil
import logging
import json
import time
from enum import Enum
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any

# Integración Redis
try:
    from cgalpha.nexus.redis_client import RedisClient
except ImportError:
    RedisClient = None # Fallback si no está instalado

from cgalpha.nexus.task_buffer import TaskBufferManager

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
    timestamp: float = 0.0
    
    def __str__(self):
        return (f"CPU: {self.cpu_percent:.1f}% | RAM: {self.ram_percent:.1f}% "
                f"({self.ram_available_mb:.0f}MB free) | State: {self.state.value}")
    
    def to_dict(self):
        return {
            "cpu_percent": self.cpu_percent,
            "ram_percent": self.ram_percent,
            "ram_available_mb": self.ram_available_mb,
            "state": self.state.value,
            "aipha_signal_active": self.aipha_signal_active,
            "timestamp": self.timestamp
        }

from cgalpha.nexus.task_buffer import TaskBufferManager

class CGAOps:
    """
    Supervisor de Recursos para CGAlpha con soporte Redis.
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
        self._aipha_signal_flag = False  # Flag manual local
        
        # Buffer Persistente Local
        self.task_buffer = TaskBufferManager()
        
        # Inicializar Redis Cliente
        self.redis = None
        if RedisClient:
            try:
                self.redis = RedisClient()
                if not self.redis.is_connected():
                   logger.warning("Redis not connected initially.") 
            except Exception as e:
                logger.error(f"Failed to initialize RedisClient: {e}")
                self.redis = None
        
        # Auto-recovery check (si Redis vuelve, intentar vaciar buffer)
        self._try_recover_buffer()

    def _try_recover_buffer(self):
        """Intenta enviar tareas pendientes del buffer a Redis."""
        if self.redis and self.redis.is_connected():
            pending = self.task_buffer.get_pending_tasks(limit=50)
            recovered_ids = []
            for task in pending:
                # task['payload'] es el dict que guardamos
                # task['task_type'] es "lab_analysis"
                if self.redis.push_analysis_task(task['task_type'], task['payload']):
                    recovered_ids.append(task['id'])
            
            if recovered_ids:
                self.task_buffer.mark_as_recovered(recovered_ids)
                logger.info(f"♻️ Recovered {len(recovered_ids)} tasks from local buffer to Redis")

    def get_resource_state(self) -> ResourceSnapshot:
        """
        Obtiene el estado actual. 
        """
        # Intentar recovery periódico
        self._try_recover_buffer()
        
        # 1. Medición Local (Siempre es la verdad "física")
        cpu_percent = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory()
        ram_percent = ram.percent
        ram_available_mb = ram.available / (1024 * 1024)
        
        # 2. Lógica de Semáforo Local
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
            aipha_signal_active=self._aipha_signal_flag,
            timestamp=time.time()
        )
        
        # 3. Sincronización con Redis (Fire-and-forget)
        if self.redis:
            self.redis.cache_system_state("global_resources", snapshot.to_dict(), ttl_seconds=10)
        
        logger.debug(f"Resource snapshot: {snapshot}")
        return snapshot
    
    def push_lab_task(self, lab_name: str, task_data: Dict[str, Any]) -> bool:
        """
        Encola una tarea de análisis para un Lab específico.
        Si Redis falla, guarda en buffer persistente local.
        """
        # Decorar data con metadata de enrutamiento
        task_payload = {
            "target_lab": lab_name,
            "payload": task_data,
            "created_at": time.time()
        }
        
        # 1. Intentar Redis
        if self.redis:
            try:
                if self.redis.push_analysis_task("lab_analysis", task_payload):
                    return True
            except Exception as e:
                logger.warning(f"Failed to push task to Redis: {e}")
        
        # 2. Fallback: Buffer Persistente (SQLite)
        logger.warning(f"⚠️ Redis unavailable. Buffering task for {lab_name} locally.")
        return self.task_buffer.save_task("lab_analysis", task_payload)

    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """
        Recupera tareas pendientes (simulado como pop único por ahora).
        En un sistema real, esto sería un loop en un worker separado.
        """
        if self.redis:
            tasks = []
            # Intentar sacar 1 tarea
            item = self.redis.pop_analysis_task(timeout=1) # No bloquear mucho
            if item:
                task_type, data = item
                if task_type == "lab_analysis":
                    tasks.append(data)
            return tasks
        return []

    def acquire_resource_lock(self, resource: str, timeout: int = 30) -> bool:
        """
        Intenta adquirir un lock distribuido para un recurso crítico.
        """
        if self.redis:
            return self.redis.acquire_lock(resource, timeout)
        return True # Si no hay Redis, asumimos local = owner (single instance mode)

    def release_resource_lock(self, resource: str):
        if self.redis:
            self.redis.release_lock(resource)

    # ... (métodos existentes can_start_heavy_task, signal_aipha_active, etc. se mantienen igual)
    
    def can_start_heavy_task(self) -> bool:
        snapshot = self.get_resource_state()
        return snapshot.state == ResourceState.GREEN
    
    def signal_aipha_active(self, active: bool):
        self._aipha_signal_flag = active
        # Publicar evento crítico en Redis
        if self.redis:
            self.redis.publish_event("system_alerts", {
                "type": "AIPHA_SIGNAL",
                "active": active,
                "timestamp": time.time()
            })
            
        if active:
            logger.warning("🔴 AIPHA SIGNAL ACTIVE - CGAlpha entering standby mode")
        else:
            logger.info("🟢 Aipha signal cleared - CGAlpha can resume")

    def get_recommended_actions(self) -> List[str]:
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

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ops = CGAOps()
    snapshot = ops.get_resource_state()
    print(f"Snapshot: {snapshot}")
    
    # Test Redis Queue
    if ops.redis:
        print("Testing Redis Queue...")
        ops.push_lab_task("risk_barrier", {"test": "data"})
        time.sleep(0.1)
        tasks = ops.get_pending_tasks()
        print(f"Retrieved tasks: {tasks}")
