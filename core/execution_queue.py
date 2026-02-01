"""
core/execution_queue.py - Cola de Ejecución Thread-Safe

Garantiza que solo 1 AtomicUpdateSystem se ejecuta a la vez,
incluso si llegan múltiples SIGUSR1 simultáneamente.

Prioridad: USER > AUTO
"""

from queue import PriorityQueue
from enum import Enum
from dataclasses import dataclass
import threading
import time
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class ExecutionPriority(Enum):
    """Niveles de prioridad de ejecución"""
    USER_IMMEDIATE = 0      # Usuario: máxima prioridad
    USER_NORMAL = 1
    AUTO_HIGH = 5
    AUTO_NORMAL = 10
    AUTO_LOW = 15


@dataclass
class ExecutionTask:
    """Tarea de ejecución con prioridad y metadata"""
    priority: ExecutionPriority
    proposal_id: str
    cycle_type: str  # 'USER' o 'AUTO'
    timestamp: float
    source: str = "unknown"
    
    def __lt__(self, other):
        """Comparador para PriorityQueue"""
        if self.priority.value == other.priority.value:
            # Mismo nivel: FIFO por timestamp
            return self.timestamp < other.timestamp
        return self.priority.value < other.priority.value


class ExecutionQueue:
    """
    Cola de ejecución thread-safe con prioridad
    
    Características:
    - 1 worker thread ejecuta tareas secuencialmente
    - Múltiples signal handlers pueden encolar sin bloqueo
    - Prioridad garantizada (USER_IMMEDIATE primero)
    - No permite más de max_workers ejecuciones simultáneas
    """
    
    def __init__(self, max_workers: int = 1):
        self.queue = PriorityQueue()
        self.max_workers = max_workers
        self.active_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        
        # Thread del worker
        self.worker_thread = threading.Thread(
            target=self._worker_loop, 
            daemon=True,
            name="ExecutionWorker"
        )
        self.worker_thread.start()
        
        logger.info(
            f"✅ ExecutionQueue iniciada "
            f"({max_workers} max workers)"
        )
    
    def enqueue(self, task: ExecutionTask):
        """
        Encolar tarea de ejecución
        
        Thread-safe: puede ser llamado desde múltiples threads
        sin necesidad de lock externo
        """
        self.queue.put(task)
        
        logger.info(
            f"📋 Tarea encolada: {task.proposal_id} "
            f"(Prioridad: {task.priority.name}, "
            f"Fuente: {task.source})"
        )
        
        # Log a memoria
        self._log_enqueued_task(task)
    
    def _worker_loop(self):
        """
        Loop del worker que procesa tareas
        
        Corre en thread separado para no bloquear signal handlers
        """
        logger.info("▶️ Worker thread iniciado")
        
        while True:
            try:
                # Obtener siguiente tarea (blocking)
                task = self.queue.get(timeout=1)
                
                # Adquirir condición para esperar slot
                with self.condition:
                    # Esperar si hay demasiadas tareas activas
                    while self.active_tasks >= self.max_workers:
                        logger.info(
                            f"⏳ Worker esperando (activas: "
                            f"{self.active_tasks}/{self.max_workers})"
                        )
                        self.condition.wait(timeout=0.5)
                    
                    self.active_tasks += 1
                
                try:
                    logger.info(
                        f"▶️ Ejecutando: {task.proposal_id} "
                        f"(Prioridad: {task.priority.name})"
                    )
                    
                    # EJECUTAR TAREA (puede tardar)
                    result = self._execute_task(task)
                    
                    if result['success']:
                        logger.info(f"✅ Completada: {task.proposal_id}")
                        self.completed_tasks += 1
                    else:
                        logger.error(
                            f"❌ Falló: {task.proposal_id} - "
                            f"{result.get('error', 'Unknown error')}"
                        )
                        self.failed_tasks += 1
                    
                    # Log resultado
                    self._log_completed_task(task, result)
                
                finally:
                    # Actualizar estado
                    with self.condition:
                        self.active_tasks -= 1
                        self.condition.notify_all()
                
                # Marcar como procesado
                self.queue.task_done()
            
            except Exception as e:
                logger.error(f"❌ Error en worker: {e}")
                time.sleep(0.1)  # Evitar busy-loop
    
    def _execute_task(self, task: ExecutionTask) -> dict:
        """
        Ejecutar una tarea de propuesta
        
        Retorna: Dict con {'success': bool, 'error': str (optional)}
        """
        
        # Obtener propuesta desde memoria
        from core.context_sentinel import ContextSentinel
        memory = ContextSentinel()
        
        proposal = memory.get_proposal(task.proposal_id)
        
        if not proposal:
            logger.error(f"Propuesta no encontrada: {task.proposal_id}")
            return {
                'success': False,
                'error': 'Proposal not found'
            }
        
        logger.info(f"📋 Ejecutando propuesta: {proposal.title}")
        
        try:
            # Ejecutar con protocolo atómico
            from core.atomic_update_system import AtomicUpdateSystem
            atomic_system = AtomicUpdateSystem()
            
            result = atomic_system.execute(proposal)
            
            # Actualizar estado en memoria
            if result['success']:
                memory.update_proposal({
                    'id': task.proposal_id,
                    'status': 'COMPLETED',
                    'completed_at': time.time()
                })
            else:
                memory.update_proposal({
                    'id': task.proposal_id,
                    'status': 'FAILED',
                    'error': result.get('error', 'Unknown'),
                    'failed_at': time.time()
                })
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Excepción durante ejecución: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _log_enqueued_task(self, task: ExecutionTask):
        """Registrar tarea encolada en memoria"""
        
        history_file = Path('memory/queue_history.jsonl')
        history_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(history_file, 'a') as f:
            f.write(json.dumps({
                'event': 'task_enqueued',
                'task_id': task.proposal_id,
                'priority': task.priority.name,
                'source': task.source,
                'timestamp': time.time()
            }) + '\n')
    
    def _log_completed_task(self, task: ExecutionTask, result: dict):
        """Registrar tarea completada en memoria"""
        
        history_file = Path('memory/queue_history.jsonl')
        
        with open(history_file, 'a') as f:
            f.write(json.dumps({
                'event': 'task_completed',
                'task_id': task.proposal_id,
                'success': result['success'],
                'error': result.get('error'),
                'timestamp': time.time()
            }) + '\n')
    
    def get_stats(self) -> dict:
        """Obtener estadísticas del queue"""
        
        with self.lock:
            return {
                'queue_size': self.queue.qsize(),
                'active_tasks': self.active_tasks,
                'completed_tasks': self.completed_tasks,
                'failed_tasks': self.failed_tasks,
                'max_workers': self.max_workers
            }
    
    def wait_for_completion(self, timeout: float = None):
        """Esperar a que todas las tareas en cola se completen"""
        
        logger.info("⏳ Esperando completación de todas las tareas...")
        self.queue.join()
        logger.info("✅ Todas las tareas completadas")
