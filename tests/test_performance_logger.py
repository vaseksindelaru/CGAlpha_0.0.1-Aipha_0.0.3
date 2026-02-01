"""
tests/test_performance_logger.py - Tests para performance logging

Validar:
- Logging de funciones
- Logging de ciclos
- Decorador @profile_function
- Estadísticas en memoria
- Archivos de métricas creados
"""

import pytest
import time
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile

from core.performance_logger import (
    PerformanceLogger,
    PerformanceMetric,
    profile_function,
    get_performance_logger,
    set_performance_logging_enabled
)


@pytest.fixture
def temp_memory_dir() -> Path:
    """Directorio temporal para archivos de performance"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def perf_logger(temp_memory_dir) -> PerformanceLogger:
    """PerformanceLogger para testing"""
    return PerformanceLogger(memory_path=str(temp_memory_dir), enabled=True)


class TestPerformanceMetric:
    """Tests para PerformanceMetric dataclass"""
    
    def test_create_metric(self):
        """Crear métrica básica"""
        metric = PerformanceMetric(
            function_name="test_func",
            duration_ms=123.45,
            timestamp=time.time(),
            success=True
        )
        assert metric.function_name == "test_func"
        assert metric.duration_ms == 123.45
        assert metric.success is True
        assert metric.error is None
    
    def test_metric_with_error(self):
        """Métrica con error"""
        metric = PerformanceMetric(
            function_name="test_func",
            duration_ms=50.0,
            timestamp=time.time(),
            success=False,
            error="ValueError: invalid value"
        )
        assert metric.success is False
        assert metric.error == "ValueError: invalid value"
    
    def test_metric_to_dict(self):
        """Convertir métrica a dict"""
        metric = PerformanceMetric(
            function_name="test_func",
            duration_ms=100.0,
            timestamp=1000.0,
            success=True,
            memory_before_mb=50.0,
            memory_after_mb=55.0
        )
        d = metric.to_dict()
        assert d['function_name'] == "test_func"
        assert d['duration_ms'] == 100.0
        assert d['success'] is True
        assert d['memory_before_mb'] == 50.0


class TestPerformanceLogger:
    """Tests para PerformanceLogger"""
    
    def test_init_creates_files(self, temp_memory_dir):
        """Inicialización crea archivos necesarios"""
        logger = PerformanceLogger(memory_path=str(temp_memory_dir))
        
        assert logger.memory_path.exists()
        assert logger.metrics_file.exists()
        assert logger.cycle_stats_file.exists()
    
    def test_init_disabled_mode(self, temp_memory_dir):
        """Modo deshabilitado no registra nada"""
        logger = PerformanceLogger(
            memory_path=str(temp_memory_dir),
            enabled=False
        )
        assert logger.enabled is False
    
    def test_log_function_performance(self, perf_logger, temp_memory_dir):
        """Registrar performance de función"""
        perf_logger.log_function_performance(
            function_name="process_data",
            duration_ms=123.45,
            success=True
        )
        
        # Verificar que se registró en memoria
        assert "process_data" in perf_logger.function_times
        assert perf_logger.function_times["process_data"][0] == 123.45
        
        # Verificar que se escribió en archivo
        lines = (temp_memory_dir / "performance_metrics.jsonl").read_text().strip().split('\n')
        assert len(lines) > 0
        metric = json.loads(lines[0])
        assert metric['function_name'] == "process_data"
        assert metric['duration_ms'] == 123.45
    
    def test_log_function_performance_with_error(self, perf_logger, temp_memory_dir):
        """Registrar performance con error"""
        perf_logger.log_function_performance(
            function_name="failing_func",
            duration_ms=50.0,
            success=False,
            error="IndexError: list index out of range"
        )
        
        lines = (temp_memory_dir / "performance_metrics.jsonl").read_text().strip().split('\n')
        metric = json.loads(lines[0])
        assert metric['success'] is False
        assert "IndexError" in metric['error']
    
    def test_log_cycle_completion(self, perf_logger, temp_memory_dir):
        """Registrar ciclo completo"""
        perf_logger.log_cycle_completion(
            cycle_id="cycle_001",
            cycle_type="auto",
            duration_sec=5.5,
            phase_durations={
                "data_collection": 1.5,
                "proposal_generation": 2.0,
                "evaluation": 1.0,
                "execution": 1.0
            },
            queue_size_before=10,
            queue_size_after=5,
            proposals_generated=3,
            proposals_approved=2
        )
        
        # Verificar ciclo_count
        assert perf_logger.cycle_count == 1
        
        # Verificar archivo
        lines = (temp_memory_dir / "cycle_stats.jsonl").read_text().strip().split('\n')
        stats = json.loads(lines[0])
        assert stats['cycle_id'] == "cycle_001"
        assert stats['cycle_type'] == "auto"
        assert stats['duration_sec'] == 5.5
        assert stats['proposals_generated'] == 3
        assert stats['approval_rate'] == 2/3
    
    def test_multiple_function_calls(self, perf_logger):
        """Múltiples llamadas a la misma función"""
        perf_logger.log_function_performance("calc", 10.0, True)
        perf_logger.log_function_performance("calc", 12.0, True)
        perf_logger.log_function_performance("calc", 11.0, True)
        
        stats = perf_logger.get_function_stats("calc")
        assert stats['call_count'] == 3
        assert stats['avg_ms'] == 11.0
        assert stats['min_ms'] == 10.0
        assert stats['max_ms'] == 12.0
        assert stats['total_ms'] == 33.0
    
    def test_get_performance_summary(self, perf_logger):
        """Obtener resumen de performance"""
        perf_logger.log_function_performance("func_a", 100.0, True)
        perf_logger.log_function_performance("func_b", 50.0, True)
        perf_logger.log_cycle_completion(
            cycle_id="c1", cycle_type="auto", duration_sec=5.0,
            phase_durations={}, queue_size_before=0, queue_size_after=0,
            proposals_generated=0, proposals_approved=0
        )
        
        summary = perf_logger.get_performance_summary()
        assert summary['cycle_count'] == 1
        assert len(summary['function_stats']) == 2
        assert 'timestamp' in summary
    
    def test_logging_disabled_doesnt_write(self, temp_memory_dir):
        """Logging deshabilitado no escribe"""
        logger = PerformanceLogger(
            memory_path=str(temp_memory_dir),
            enabled=False
        )
        
        logger.log_function_performance("test", 100.0, True)
        logger.log_cycle_completion(
            cycle_id="c1", cycle_type="auto", duration_sec=5.0,
            phase_durations={}, queue_size_before=0, queue_size_after=0,
            proposals_generated=0, proposals_approved=0
        )
        
        metrics_content = (temp_memory_dir / "performance_metrics.jsonl").read_text()
        stats_content = (temp_memory_dir / "cycle_stats.jsonl").read_text()
        
        assert metrics_content == ""
        assert stats_content == ""


class TestProfileFunctionDecorator:
    """Tests para decorador @profile_function"""
    
    def test_decorator_measures_time(self, perf_logger):
        """Decorador mide tiempo de ejecución"""
        @profile_function(perf_logger)
        def slow_function():
            time.sleep(0.1)  # 100ms
        
        slow_function()
        
        stats = perf_logger.get_function_stats("slow_function")
        assert stats['call_count'] == 1
        assert stats['avg_ms'] >= 100  # Al menos 100ms
    
    def test_decorator_preserves_return_value(self, perf_logger):
        """Decorador preserva return value"""
        @profile_function(perf_logger)
        def add(a, b):
            return a + b
        
        result = add(5, 3)
        assert result == 8
    
    def test_decorator_records_error(self, perf_logger):
        """Decorador registra errores"""
        @profile_function(perf_logger)
        def failing_func():
            raise ValueError("test error")
        
        with pytest.raises(ValueError):
            failing_func()
        
        stats = perf_logger.get_function_stats("failing_func")
        assert stats['call_count'] == 1
    
    def test_decorator_tracks_memory(self, perf_logger, temp_memory_dir):
        """Decorador mide memoria"""
        @profile_function(perf_logger)
        def allocate_memory():
            x = [i for i in range(100000)]
            return len(x)
        
        allocate_memory()
        
        lines = (temp_memory_dir / "performance_metrics.jsonl").read_text().strip().split('\n')
        metric = json.loads(lines[0])
        
        assert metric['memory_before_mb'] is not None
        assert metric['memory_after_mb'] is not None
    
    def test_decorator_multiple_calls(self, perf_logger):
        """Decorador cuenta múltiples llamadas"""
        @profile_function(perf_logger)
        def fast_func():
            return 42
        
        for _ in range(5):
            fast_func()
        
        stats = perf_logger.get_function_stats("fast_func")
        assert stats['call_count'] == 5


class TestGlobalLogger:
    """Tests para instancia global"""
    
    def test_get_performance_logger_returns_same_instance(self):
        """get_performance_logger retorna la misma instancia"""
        logger1 = get_performance_logger()
        logger2 = get_performance_logger()
        assert logger1 is logger2
    
    def test_set_performance_logging_enabled(self):
        """Habilitar/deshabilitar logging globalmente"""
        logger = get_performance_logger()
        original_state = logger.enabled
        
        set_performance_logging_enabled(False)
        assert logger.enabled is False
        
        set_performance_logging_enabled(True)
        assert logger.enabled is True
        
        # Restaurar
        set_performance_logging_enabled(original_state)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
