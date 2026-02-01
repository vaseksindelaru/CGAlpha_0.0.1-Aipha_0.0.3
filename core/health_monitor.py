"""
core/health_monitor.py - Monitor Centralizado de Salud

Hub que centraliza alertas de salud del sistema.
Emite broadcasts cuando hay problemas críticos.
Integra quarantine, ML health, y ciclo info.
"""

import json
import time
import logging
import threading
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Callable, Dict, Optional
from queue import Queue

logger = logging.getLogger(__name__)


class HealthLevel(Enum):
    """Niveles de salud del sistema"""
    CRITICAL = "critical"      # 🔴 Crítico
    WARNING = "warning"        # 🟡 Advertencia
    DEGRADED = "degraded"      # 🟠 Degradado
    HEALTHY = "healthy"        # 🟢 Sano


class HealthEventType(Enum):
    """Tipos de eventos de salud"""
    MODEL_FAILURE = "model_failure"
    MODEL_RECOVERY = "model_recovery"
    MODEL_DEGRADATION = "model_degradation"
    PARAMETER_QUARANTINED = "parameter_quarantined"
    CYCLE_FAILED = "cycle_failed"
    CYCLE_INTERRUPTED = "cycle_interrupted"
    HEALTH_CHECK_PASSED = "health_check_passed"
    AUTO_REMEDIATION = "auto_remediation"


@dataclass
class HealthEvent:
    """Evento de salud del sistema"""
    event_type: HealthEventType
    level: HealthLevel
    message: str
    timestamp: float
    parameter: Optional[str] = None
    value: Optional[any] = None
    details: Optional[Dict] = None
    resolution: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'event_type': self.event_type.value,
            'level': self.level.value,
            'message': self.message,
            'timestamp': self.timestamp,
            'parameter': self.parameter,
            'value': self.value,
            'details': self.details,
            'resolution': self.resolution
        }


class HealthMonitor:
    """
    Monitor centralizado de salud del sistema
    
    Características:
    - Centraliza alertas de todos los componentes
    - Emite broadcasts de eventos
    - Historial de eventos
    - Alertas en tiempo real
    - Integración con quarantine
    """
    
    def __init__(self, memory_path: str = "memory"):
        self.memory_path = Path(memory_path)
        self.health_log_file = self.memory_path / "health_events.jsonl"
        self.health_broadcasts_file = self.memory_path / "health_broadcasts.jsonl"
        
        # Crear archivos
        self.health_log_file.parent.mkdir(parents=True, exist_ok=True)
        self.health_log_file.touch(exist_ok=True)
        self.health_broadcasts_file.touch(exist_ok=True)
        
        # Cola de eventos (para async processing)
        self.event_queue = Queue()
        
        # Subscribers para broadcasts en tiempo real
        self.subscribers: List[Callable[[HealthEvent], None]] = []
        
        # Estado actual del sistema
        self.current_health_level = HealthLevel.HEALTHY
        self.last_event = None
        
        # Thread para procesar eventos
        self.processor_thread = threading.Thread(
            target=self._event_processor_loop,
            daemon=True,
            name="HealthEventProcessor"
        )
        self.processor_thread.start()
        
        # Estadísticas
        self.event_count = 0
        self.events_by_type: Dict[str, int] = {}
        
        logger.info("✅ HealthMonitor inicializado")
    
    def subscribe(self, callback: Callable[[HealthEvent], None]):
        """
        Suscribirse a eventos de salud
        
        Callback se ejecuta cuando hay nuevo evento
        """
        self.subscribers.append(callback)
        logger.info(f"📢 Subscriber registrado: {callback.__name__}")
    
    def emit_event(
        self,
        event_type: HealthEventType,
        level: HealthLevel,
        message: str,
        parameter: str = None,
        value: any = None,
        details: Dict = None,
        resolution: str = None
    ) -> HealthEvent:
        """
        Emitir evento de salud
        
        Este es el punto de entrada principal para todos los componentes
        """
        
        event = HealthEvent(
            event_type=event_type,
            level=level,
            message=message,
            timestamp=time.time(),
            parameter=parameter,
            value=value,
            details=details,
            resolution=resolution
        )
        
        # Encolar para procesamiento
        self.event_queue.put(event)
        
        logger.info(
            f"📊 Evento de salud emitido: {event_type.value} "
            f"({level.value}) - {message}"
        )
        
        return event
    
    def _event_processor_loop(self):
        """
        Loop que procesa eventos de la cola
        
        Corre en thread separado para no bloquear callers
        """
        
        logger.info("▶️ Event processor thread iniciado")
        
        import queue
        while True:
            try:
                # Obtener evento (blocking)
                event = self.event_queue.get(timeout=1)
                
                # Procesar
                self._process_event(event)
                
            except queue.Empty:
                # Es normal que la cola esté vacía, no es un error
                continue
            except Exception as e:
                logger.error(f"❌ Error en event processor: {e}")
                time.sleep(0.1)
    
    def _process_event(self, event: HealthEvent):
        """Procesar evento internamente"""
        
        # PASO 1: Actualizar estado de salud
        if event.level == HealthLevel.CRITICAL:
            self.current_health_level = HealthLevel.CRITICAL
        elif event.level == HealthLevel.WARNING and \
             self.current_health_level != HealthLevel.CRITICAL:
            self.current_health_level = HealthLevel.WARNING
        elif event.level == HealthLevel.DEGRADED and \
             self.current_health_level == HealthLevel.HEALTHY:
            self.current_health_level = HealthLevel.DEGRADED
        
        # PASO 2: Persistir evento
        self._save_event(event)
        
        # PASO 3: Emitir broadcast
        self._broadcast_event(event)
        
        # PASO 4: Actualizar estadísticas
        self.event_count += 1
        event_type_str = event.event_type.value
        self.events_by_type[event_type_str] = self.events_by_type.get(event_type_str, 0) + 1
        self.last_event = event
    
    def _save_event(self, event: HealthEvent):
        """Guardar evento en archivo"""
        
        with open(self.health_log_file, 'a') as f:
            f.write(json.dumps(event.to_dict()) + '\n')
            f.flush()
    
    def _broadcast_event(self, event: HealthEvent):
        """
        Emitir broadcast a todos los subscribers
        
        Esto permite que CLI, dashboard, etc. se enteren
        """
        
        # Guardar también como broadcast
        with open(self.health_broadcasts_file, 'a') as f:
            f.write(json.dumps(event.to_dict()) + '\n')
            f.flush()
        
        # Notificar subscribers
        for subscriber in self.subscribers:
            try:
                subscriber(event)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")
    
    def get_current_health(self) -> Dict:
        """Obtener estado actual de salud"""
        
        return {
            'level': self.current_health_level.value,
            'last_event': self.last_event.to_dict() if self.last_event else None,
            'event_count': self.event_count,
            'events_by_type': self.events_by_type,
            'timestamp': time.time()
        }
    
    def get_recent_events(self, count: int = 10) -> List[Dict]:
        """Obtener últimos N eventos con robustez"""
        
        events = []
        
        try:
            if not self.health_log_file.exists():
                return []
                
            with open(self.health_log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                valid_lines = [l.strip() for l in lines if l.strip()]
                for line in valid_lines[-count:]:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.debug(f"Error discreto leyendo health events: {e}")
        
        return events
    
    def get_critical_events(self) -> List[Dict]:
        """Obtener eventos críticos con robustez"""
        
        events = []
        
        try:
            if not self.health_log_file.exists():
                return []
                
            with open(self.health_log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    clean_line = line.strip()
                    if not clean_line:
                        continue
                    try:
                        event = json.loads(clean_line)
                        if event.get('level') == HealthLevel.CRITICAL.value:
                            events.append(event)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.debug(f"Error discreto leyendo eventos críticos: {e}")
        
        return events
    
    def get_statistics(self) -> Dict:
        """Obtener estadísticas de salud"""
        
        return {
            'current_level': self.current_health_level.value,
            'total_events': self.event_count,
            'events_by_type': self.events_by_type,
            'events_by_level': self._count_by_level(),
            'timestamp': time.time()
        }
    
    def _count_by_level(self) -> Dict[str, int]:
        """Contar eventos por nivel con robustez"""
        
        counts = {level.value: 0 for level in HealthLevel}
        
        try:
            if not self.health_log_file.exists():
                return counts
                
            with open(self.health_log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    clean_line = line.strip()
                    if not clean_line:
                        continue
                    try:
                        event = json.loads(clean_line)
                        level = event.get('level', 'unknown')
                        counts[level] = counts.get(level, 0) + 1
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.debug(f"Error discreto contando niveles: {e}")
        
        return counts


# Instancia global
_health_monitor_instance: Optional[HealthMonitor] = None


def get_health_monitor() -> HealthMonitor:
    """Obtener instancia del health monitor"""
    
    global _health_monitor_instance
    
    if _health_monitor_instance is None:
        _health_monitor_instance = HealthMonitor()
    
    return _health_monitor_instance
