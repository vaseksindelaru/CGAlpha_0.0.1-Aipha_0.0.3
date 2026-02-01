"""
core/performance_logger.py - Logging de Performance y Observabilidad

Instrumentación del sistema para monitorear performance en tiempo real.
Soluciona: P1#8 - Performance no monitoreada (4 horas)

Características:
- Métricas de ciclo (duración, tamaño queue, etc)
- Performance de funciones críticas (decorador)
- Memory profiling
- CPU/threading analysis
"""

import time
import logging
import functools
import psutil
import json
from pathlib import Path
from typing import Dict, Any, Callable, TypeVar, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class PerformanceMetric:
    """Métrica de performance de una función"""
    function_name: str
    duration_ms: float
    timestamp: float
    success: bool
    error: Optional[str] = None
    memory_before_mb: Optional[float] = None
    memory_after_mb: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PerformanceLogger:
    """
    Logger centralizado de performance del sistema.
    
    Registra:
    - Duración de ciclos
    - Performance de funciones críticas
    - Uso de memoria
    - CPU usage
    """
    
    def __init__(self, memory_path: str = "memory", enabled: bool = True):
        """
        Inicializar performance logger.
        
        Args:
            memory_path: Directorio para guardar métricas
            enabled: Si está deshabilitado, no registra nada (útil para testing)
        """
        self.memory_path = Path(memory_path)
        self.enabled = enabled
        self.metrics_file = self.memory_path / "performance_metrics.jsonl"
        self.cycle_stats_file = self.memory_path / "cycle_stats.jsonl"
        
        # Crear archivos
        self.memory_path.mkdir(parents=True, exist_ok=True)
        self.metrics_file.touch(exist_ok=True)
        self.cycle_stats_file.touch(exist_ok=True)
        
        # Estadísticas en memoria
        self.function_times: Dict[str, list] = {}
        self.cycle_count = 0
        
        if enabled:
            logger.info("✓ Performance logging habilitado")
        else:
            logger.info("⊘ Performance logging deshabilitado (testing mode)")
    
    def log_function_performance(self, 
                                function_name: str,
                                duration_ms: float,
                                success: bool = True,
                                error: Optional[str] = None,
                                memory_before_mb: Optional[float] = None,
                                memory_after_mb: Optional[float] = None) -> None:
        """
        Registrar métrica de performance de función.
        
        Args:
            function_name: Nombre de la función
            duration_ms: Duración en milisegundos
            success: Si fue exitosa
            error: Mensaje de error si falló
            memory_before_mb: Memoria antes (MB)
            memory_after_mb: Memoria después (MB)
        """
        if not self.enabled:
            return
        
        metric = PerformanceMetric(
            function_name=function_name,
            duration_ms=duration_ms,
            timestamp=time.time(),
            success=success,
            error=error,
            memory_before_mb=memory_before_mb,
            memory_after_mb=memory_after_mb
        )
        
        # Guardar en archivo
        with open(self.metrics_file, 'a') as f:
            f.write(json.dumps(metric.to_dict()) + '\n')
        
        # Actualizar estadísticas en memoria
        if function_name not in self.function_times:
            self.function_times[function_name] = []
        self.function_times[function_name].append(duration_ms)
    
    def log_cycle_completion(self,
                            cycle_id: str,
                            cycle_type: str,
                            duration_sec: float,
                            phase_durations: Dict[str, float],
                            queue_size_before: int,
                            queue_size_after: int,
                            proposals_generated: int,
                            proposals_approved: int,
                            success: bool = True,
                            error: Optional[str] = None) -> None:
        """
        Registrar estadísticas de un ciclo completo.
        
        Args:
            cycle_id: ID del ciclo
            cycle_type: Tipo (auto, user, urgent)
            duration_sec: Duración total en segundos
            phase_durations: {fase: duración_sec}
            queue_size_before/after: Tamaño de queue
            proposals_generated/approved: Contadores
            success: Si fue exitoso
            error: Mensaje de error si falló
        """
        if not self.enabled:
            return
        
        stats = {
            'cycle_id': cycle_id,
            'cycle_type': cycle_type,
            'timestamp': datetime.now().isoformat(),
            'duration_sec': duration_sec,
            'phase_durations': phase_durations,
            'queue_size_before': queue_size_before,
            'queue_size_after': queue_size_after,
            'proposals_generated': proposals_generated,
            'proposals_approved': proposals_approved,
            'approval_rate': proposals_approved / max(1, proposals_generated),
            'success': success,
            'error': error,
            'system_metrics': self._get_system_metrics()
        }
        
        # Guardar en archivo
        with open(self.cycle_stats_file, 'a') as f:
            f.write(json.dumps(stats) + '\n')
        
        self.cycle_count += 1
        
        # Log resumen
        logger.info(
            f"📊 Ciclo {self.cycle_count} completado: "
            f"{duration_sec:.1f}s, "
            f"{proposals_generated} proposals → "
            f"{proposals_approved} approved "
            f"({stats['approval_rate']*100:.0f}%)"
        )
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Obtener métricas del sistema actual"""
        try:
            process = psutil.Process()
            return {
                'memory_percent': process.memory_percent(),
                'cpu_percent': process.cpu_percent(interval=0.1),
                'num_threads': process.num_threads()
            }
        except Exception as e:
            logger.warning(f"Could not get system metrics: {e}")
            return {}
    
    def get_function_stats(self, function_name: str) -> Dict[str, Any]:
        """Obtener estadísticas de una función"""
        if function_name not in self.function_times:
            return {}
        
        times = self.function_times[function_name]
        if not times:
            return {}
        
        return {
            'function': function_name,
            'call_count': len(times),
            'avg_ms': sum(times) / len(times),
            'min_ms': min(times),
            'max_ms': max(times),
            'total_ms': sum(times)
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Obtener resumen de performance"""
        return {
            'cycle_count': self.cycle_count,
            'function_stats': [
                self.get_function_stats(fn) 
                for fn in sorted(self.function_times.keys())
            ],
            'timestamp': datetime.now().isoformat()
        }


def profile_function(logger_instance: PerformanceLogger) -> Callable:
    """
    Decorador para perfilar funciones automáticamente.
    
    Registra duración, memoria, y errores.
    
    Usage:
        @profile_function(perf_logger)
        def my_function(x, y):
            return x + y
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Obtener memoria inicial
            process = psutil.Process()
            mem_before = process.memory_info().rss / 1024 / 1024  # MB
            
            # Ejecutar función
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                mem_after = process.memory_info().rss / 1024 / 1024  # MB
                
                logger_instance.log_function_performance(
                    function_name=func.__name__,
                    duration_ms=duration_ms,
                    success=True,
                    memory_before_mb=mem_before,
                    memory_after_mb=mem_after
                )
                
                return result
            
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                mem_after = process.memory_info().rss / 1024 / 1024  # MB
                
                logger_instance.log_function_performance(
                    function_name=func.__name__,
                    duration_ms=duration_ms,
                    success=False,
                    error=str(e),
                    memory_before_mb=mem_before,
                    memory_after_mb=mem_after
                )
                
                raise
        
        return wrapper
    return decorator


# Instancia global
_perf_logger_instance: Optional[PerformanceLogger] = None


def get_performance_logger() -> PerformanceLogger:
    """Obtener instancia global del performance logger"""
    global _perf_logger_instance
    if _perf_logger_instance is None:
        _perf_logger_instance = PerformanceLogger()
    return _perf_logger_instance


def set_performance_logging_enabled(enabled: bool) -> None:
    """Habilitar/deshabilitar logging de performance"""
    global _perf_logger_instance
    if _perf_logger_instance:
        _perf_logger_instance.enabled = enabled
