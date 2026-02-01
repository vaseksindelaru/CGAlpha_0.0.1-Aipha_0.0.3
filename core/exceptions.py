"""
core/exceptions.py - Excepciones Personalizadas de Aipha

Define la jerarquía de excepciones del sistema para un manejo robusto
de errores y mejor debugging.

Soluciona: P0 #3 - Manejo de errores inconsistente
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ============================================================================
# JERARQUÍA DE EXCEPCIONES
# ============================================================================


class AiphaException(Exception):
    """
    Excepción base para todo el sistema Aipha.
    Todas las excepciones específicas heredan de esta.
    """
    
    def __init__(self, message: str, error_code: str = "UNKNOWN", 
                 details: Optional[dict] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        base = f"[{self.error_code}] {self.message}"
        if self.details:
            details_str = " | ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{base} ({details_str})"
        return base


# ============================================================================
# EXCEPCIONES DE DATOS
# ============================================================================


class DataLoadError(AiphaException):
    """
    Se dispara cuando falla la carga de datos.
    
    Ejemplos:
    - Archivo no encontrado
    - Conexión a DB fallida
    - Formato de datos inválido
    """
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, "DATA_LOAD_ERROR", details)


class DataProcessingError(AiphaException):
    """Se dispara cuando falla el procesamiento de datos."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, "DATA_PROCESSING_ERROR", details)


class DataValidationError(AiphaException):
    """Se dispara cuando los datos no pasan validación."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, "DATA_VALIDATION_ERROR", details)


# ============================================================================
# EXCEPCIONES DE CONFIGURACIÓN
# ============================================================================


class ConfigurationError(AiphaException):
    """
    Se dispara cuando hay un problema de configuración.
    
    Ejemplos:
    - Parámetro fuera de rango
    - Configuración faltante
    - Valores inválidos
    """
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, "CONFIG_ERROR", details)


class ConfigValidationError(AiphaException):
    """Se dispara cuando la validación Pydantic falla."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, "CONFIG_VALIDATION_ERROR", details)


# ============================================================================
# EXCEPCIONES DE TRADING
# ============================================================================


class TradingEngineError(AiphaException):
    """Base para errores del trading engine."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, "TRADING_ENGINE_ERROR", details)


class SignalDetectionError(AiphaException):
    """Se dispara cuando falla la detección de señales."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, "SIGNAL_DETECTION_ERROR", details)


class BarrierError(AiphaException):
    """Se dispara cuando falla el cálculo de barreras."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, "BARRIER_ERROR", details)


# ============================================================================
# EXCEPCIONES DE IA/ML
# ============================================================================


class OracleError(AiphaException):
    """
    Se dispara cuando hay un problema con el Oracle/ML.
    
    Ejemplos:
    - Modelo no encontrado
    - Predicción falla
    - Health check falla
    """
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, "ORACLE_ERROR", details)


class ModelLoadError(OracleError):
    """Se dispara cuando no se puede cargar el modelo."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, details)
        self.error_code = "MODEL_LOAD_ERROR"


class PredictionError(OracleError):
    """Se dispara cuando falla una predicción."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, details)
        self.error_code = "PREDICTION_ERROR"


class HealthCheckError(OracleError):
    """Se dispara cuando el health check falla."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, details)
        self.error_code = "HEALTH_CHECK_ERROR"


# ============================================================================
# EXCEPCIONES DE ORQUESTACIÓN
# ============================================================================


class OrchestrationError(AiphaException):
    """Base para errores de orquestación."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, "ORCHESTRATION_ERROR", details)


class CycleInterruptedError(OrchestrationError):
    """Se dispara cuando un ciclo es interrumpido."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, details)
        self.error_code = "CYCLE_INTERRUPTED"


class ExecutionQueueError(OrchestrationError):
    """Se dispara cuando hay un problema con la queue de ejecución."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, details)
        self.error_code = "EXECUTION_QUEUE_ERROR"


# ============================================================================
# EXCEPCIONES DE MEMORIA
# ============================================================================


class MemoryError(AiphaException):
    """Se dispara cuando hay un problema con la persistencia de memoria."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, "MEMORY_ERROR", details)


class MemoryCorruptionError(MemoryError):
    """Se dispara cuando se detecta corrupción de memoria."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, details)
        self.error_code = "MEMORY_CORRUPTION"


# ============================================================================
# EXCEPCIONES DE LLM/EXTERNOS
# ============================================================================


class LLMError(AiphaException):
    """Se dispara cuando hay un problema con LLM."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, "LLM_ERROR", details)


class LLMConnectionError(LLMError):
    """Se dispara cuando falla la conexión a LLM."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, details)
        self.error_code = "LLM_CONNECTION_ERROR"


class LLMRateLimitError(LLMError):
    """Se dispara cuando se alcanza el rate limit de LLM."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, details)
        self.error_code = "LLM_RATE_LIMIT"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0,
                      backoff_factor: float = 2.0):
    """
    Ejecuta una función con reintentos y backoff exponencial.
    
    Args:
        func: Función a ejecutar
        max_retries: Número máximo de intentos
        base_delay: Delay inicial en segundos
        backoff_factor: Factor de exponencia para backoff
    
    Returns:
        Resultado de la función
    
    Raises:
        AiphaException: Si falla después de todos los reintentos
    """
    import time
    
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return func()
        except AiphaException as e:
            last_exception = e
            if attempt < max_retries - 1:
                delay = base_delay * (backoff_factor ** attempt)
                logger.warning(
                    f"Intento {attempt + 1}/{max_retries} falló. "
                    f"Reintentando en {delay:.1f}s: {e}"
                )
                time.sleep(delay)
            else:
                logger.error(
                    f"Falló después de {max_retries} intentos: {e}"
                )
    
    raise last_exception


# ============================================================================
# CONTEXT MANAGERS
# ============================================================================


class safe_execution:
    """
    Context manager para ejecución segura con manejo de errores.
    
    Ejemplo:
        with safe_execution("Cargando datos"):
            df = load_data()
    """
    
    def __init__(self, operation_name: str, default_return=None):
        self.operation_name = operation_name
        self.default_return = default_return
        self.exception = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            if isinstance(exc_val, AiphaException):
                self.exception = exc_val
                logger.error(f"❌ {self.operation_name} falló: {exc_val}")
            else:
                logger.error(
                    f"❌ {self.operation_name} falló con excepción inesperada: {exc_val}"
                )
            return True  # Suppress exception
        return False
