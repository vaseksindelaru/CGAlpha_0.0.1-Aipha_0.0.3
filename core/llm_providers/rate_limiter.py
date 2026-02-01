"""
core/llm_providers/rate_limiter.py - Control de Rate Limiting

Implementa circuit breaker y backoff exponencial para respetar rate limits.
"""

import time
import logging
from typing import Callable, TypeVar, Any
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RateLimiter:
    """
    Control de rate limiting con circuit breaker.
    
    Implementa:
    - Throttling: máximo de requests por ventana de tiempo
    - Circuit breaker: detiene requests si hay demasiados errores
    - Backoff exponencial: espera progresivamente más entre intentos
    """
    
    def __init__(self,
                 max_requests_per_minute: int = 60,
                 error_threshold: int = 5,
                 backoff_multiplier: float = 2.0):
        """
        Inicializar rate limiter.
        
        Args:
            max_requests_per_minute: Máximo requests por minuto
            error_threshold: Errores permitidos antes de circuit breaker
            backoff_multiplier: Multiplicador para backoff exponencial
        """
        self.max_requests_per_minute = max_requests_per_minute
        self.error_threshold = error_threshold
        self.backoff_multiplier = backoff_multiplier
        
        # Estado
        self.request_times = []
        self.error_count = 0
        self.circuit_open = False
        self.circuit_open_time = None
        self.min_wait_seconds = 1.0
    
    def is_available(self) -> bool:
        """
        Verificar si se puede hacer un request.
        
        Returns:
            True si se puede hacer un request, False si está limitado
        """
        # Verificar circuit breaker
        if self.circuit_open:
            elapsed = time.time() - self.circuit_open_time
            # Circuit se cierra después de N segundos
            if elapsed > self.min_wait_seconds * 10:
                logger.info("Circuit breaker closing")
                self.circuit_open = False
                self.error_count = 0
                return True
            else:
                logger.warning(f"Circuit breaker open, wait {self.min_wait_seconds * 10 - elapsed:.1f}s")
                return False
        
        # Verificar rate limit
        now = time.time()
        minute_ago = now - 60
        
        # Limpiar requests antiguos
        self.request_times = [t for t in self.request_times if t > minute_ago]
        
        if len(self.request_times) >= self.max_requests_per_minute:
            logger.warning(f"Rate limit reached: {len(self.request_times)}/{self.max_requests_per_minute} requests in last minute")
            return False
        
        return True
    
    def wait_if_needed(self):
        """Esperar si es necesario para respetar rate limit"""
        while not self.is_available():
            time.sleep(self.min_wait_seconds)
    
    def record_request(self):
        """Registrar un request realizado"""
        self.request_times.append(time.time())
        logger.debug(f"Request recorded: {len(self.request_times)} in last minute")
    
    def record_error(self):
        """Registrar un error"""
        self.error_count += 1
        logger.warning(f"Error recorded: {self.error_count}/{self.error_threshold}")
        
        if self.error_count >= self.error_threshold:
            self.circuit_open = True
            self.circuit_open_time = time.time()
            logger.error("Circuit breaker opened due to too many errors")
            # Incrementar espera
            self.min_wait_seconds *= self.backoff_multiplier
    
    def record_success(self):
        """Registrar una operación exitosa"""
        if self.error_count > 0:
            self.error_count -= 1
        # Resetear espera si todo está bien
        if self.error_count == 0:
            self.min_wait_seconds = 1.0
    
    def reset(self):
        """Resetear el rate limiter"""
        self.request_times = []
        self.error_count = 0
        self.circuit_open = False
        self.circuit_open_time = None
        self.min_wait_seconds = 1.0
        logger.info("Rate limiter reset")


def retry_with_rate_limit(rate_limiter: RateLimiter,
                         max_retries: int = 3):
    """
    Decorador para aplicar rate limiting y retries.
    
    Args:
        rate_limiter: Instancia de RateLimiter
        max_retries: Máximo de intentos
    
    Usage:
        @retry_with_rate_limit(limiter)
        def my_api_call():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            for attempt in range(max_retries):
                try:
                    # Esperar si es necesario
                    rate_limiter.wait_if_needed()
                    
                    # Ejecutar
                    result = func(*args, **kwargs)
                    
                    # Registrar éxito
                    rate_limiter.record_request()
                    rate_limiter.record_success()
                    
                    return result
                
                except Exception as e:
                    rate_limiter.record_error()
                    
                    if attempt == max_retries - 1:
                        raise
                    
                    # Esperar antes de reintentar
                    wait_time = rate_limiter.min_wait_seconds * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
        
        return wrapper
    return decorator
