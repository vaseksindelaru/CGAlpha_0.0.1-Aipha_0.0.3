"""
cgalpha_v3/lila/llm/providers/rate_limiter.py - Rate Limiter para CGAlpha v3 (Lila)

Implementa control de flujo y circuit breaker para las peticiones LLM.
"""

import time
import logging
import functools
from collections import deque
from ..exceptions import LilaLLMRateLimitError

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter inteligente con circuit breaker."""
    
    def __init__(self, 
                 max_requests_per_minute: int = 60,
                 error_threshold: int = 5):
        self.max_requests_per_minute = max_requests_per_minute
        self.error_threshold = error_threshold
        
        self.request_times = deque()
        self.error_count = 0
        self.circuit_open = False
        self.last_error_time = 0
    
    def is_available(self) -> bool:
        """Verificar si el limiter permite una nueva petición."""
        now = time.time()
        
        # Resetear circuit breaker tras cooldown (60s)
        if self.circuit_open and (now - self.last_error_time > 60):
            self.reset()
            
        if self.circuit_open:
            return False
            
        # Limpiar requests antiguas (> 60s)
        while self.request_times and (now - self.request_times[0] > 60):
            self.request_times.popleft()
            
        return len(self.request_times) < self.max_requests_per_minute
    
    def record_request(self):
        """Registrar una nueva petición efectuada."""
        self.request_times.append(time.time())
        
    def record_error(self):
        """Registrar fallo en la petición (aumenta circuit breaker)."""
        self.error_count += 1
        if self.error_count >= self.error_threshold:
            self.circuit_open = True
            self.last_error_time = time.time()
            logger.critical("⚠️ Lila LLM Circuit Breaker activado por exceso de fallas.")
            
    def record_success(self):
        """Registrar éxito (limpia errores parciales)."""
        if self.error_count > 0:
            self.error_count = max(0, self.error_count - 1)
            
    def reset(self):
        """Resetear estado del limiter."""
        self.request_times.clear()
        self.error_count = 0
        self.circuit_open = False
        logger.info("✓ Lila LLM Circuit Breaker reseteado.")

def retry_with_rate_limit(limiter: RateLimiter, max_retries: int = 3):
    """Decorador para reintentar con backoff exponencial y rate-limiting."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_err = None
            for attempt in range(max_retries):
                if not limiter.is_available():
                    logger.warning(f"Rate limit alcanzado. Intento {attempt+1}/{max_retries}.")
                    time.sleep(2 * (attempt + 1))
                    continue
                
                try:
                    limiter.record_request()
                    result = func(*args, **kwargs)
                    limiter.record_success()
                    return result
                except Exception as e:
                    last_err = e
                    limiter.record_error()
                    logger.error(f"Error en llamada LLM ({type(e).__name__}): {e}")
                    time.sleep(1 * (attempt+1))
            
            raise last_err or LilaLLMRateLimitError("Maximum retries with rate limit reached.")
        return wrapper
    return decorator
