"""
cgalpha_v3/lila/llm/exceptions.py - Excepciones para el componente LLM de Lila

Define los errores específicos del asistente inteligente.
"""

class LilaLLMError(Exception):
    """Excepción base para errores de LLM en Lila."""
    def __init__(self, message: str, error_code: str = "LLM_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class LilaLLMConnectionError(LilaLLMError):
    """Error al conectar con la API del LLM."""
    def __init__(self, message: str):
        super().__init__(message, "LLM_CONNECTION_ERROR")

class LilaLLMRateLimitError(LilaLLMError):
    """Se alcanzó el límite de peticiones del LLM."""
    def __init__(self, message: str):
        super().__init__(message, "LLM_RATE_LIMIT")
