"""
cgalpha_v3/lila/llm/assistant.py - Asistente LLM para Lila v3 (Migrado)

Controlador central para las capacidades de IA de Lila.
"""

import logging
import os
from typing import Dict, Any, Optional
from .providers.base import LLMProvider
from .providers.openai_provider import OpenAIProvider
from .providers.zhipu_provider import ZhipuProvider
from .providers.ollama_provider import OllamaProvider
from .providers.gemini_provider import GeminiProvider
from .providers.rate_limiter import RateLimiter, retry_with_rate_limit
from .exceptions import LilaLLMError
from .context import ContextBuilder
from pathlib import Path

logger = logging.getLogger(__name__)


class LLMAssistant:
    """
    Controlador LLM de Lila.
    
    Gestiona la selección de proveedores, límites de tasa y generación de respuestas con contexto.
    """
    
    def __init__(self,
                 provider: Optional[Any] = None,
                 system_prompt: str = None):
        """
        Inicializar asistente LLM v3.
        """
        self._available_providers = {
            "openai": OpenAIProvider,
            "zhipu": ZhipuProvider,
            "ollama": OllamaProvider,
            "gemini": GeminiProvider
        }
        
        if provider:
            self.provider = provider
        else:
            # Estrategia de selección automática inicial
            self.provider = self._select_best_provider()
        
        # Rate limiter
        self.rate_limiter = RateLimiter(
            max_requests_per_minute=60,
            error_threshold=5
        )
        
        # System prompt por defecto (Sección A)
        self.system_prompt = system_prompt or self._get_default_system_prompt()
        
        # Context Builder (raíz del proyecto)
        root = Path(__file__).resolve().parent.parent.parent.parent
        self.context_builder = ContextBuilder(root)
        
        logger.info(f"✓ LLMAssistant V3 inicializado (provider={self.provider.name})")

    def _select_best_provider(self) -> LLMProvider:
        """Selecciona el mejor proveedor basado en credenciales disponibles."""
        # Permitir forzar local via env
        if os.environ.get("FORCE_LOCAL_LLM", "false").lower() == "true":
            ollama = OllamaProvider()
            if ollama.validate_api_key():
                return ollama

        if (os.environ.get("GEMINI_API_KEY") and os.environ.get("GEMINI_API_KEY") != "demo_key_for_testing") or os.environ.get("GOOGLE_API_KEY"):
            return GeminiProvider()

        if os.environ.get("OPENAI_API_KEY"):
            return OpenAIProvider()
        if os.environ.get("ZHIPU_API_KEY"):
            return ZhipuProvider()
        
        # Fallback a Ollama si el servicio está vivo
        ollama = OllamaProvider()
        if ollama.validate_api_key():
            return ollama
            
        # Fallback final (Gemini si hay key, sino OpenAI mostrará error de API key)
        return OpenAIProvider()

    def switch_provider(self, name: str) -> bool:
        """Cambia el proveedor activo dinámicamente."""
        if name not in self._available_providers:
            logger.error(f"Proveedor no reconocido: {name}")
            return False
            
        try:
            # Crear nueva instancia del proveedor
            new_provider = self._available_providers[name]()
            
            # Verificar si es Ollama y si está vivo (opcional pero recomendado)
            if name == "ollama" and not new_provider.validate_api_key():
                logger.warning("Ollama seleccionado pero no responde en http://127.0.0.1:11434")
                # Aún así permitimos el switch para que el usuario vea el error real al generar
            
            self.provider = new_provider
            logger.info(f"✅ LILA_ASSISTANT: Proveedor cambiado MANUALMENTE a {name.upper()}")
            return True
        except Exception as e:
            logger.error(f"Error al cambiar a {name}: {e}")
            return False

    def generate_layer2(self, prompt: str) -> str:
        """Capa 2: Recuperador (Alta velocidad, modelo pequeño)."""
        if isinstance(self.provider, OllamaProvider):
            return self.generate(prompt, temperature=0.1, max_tokens=200, model_override=self.provider.default_model)
        return self.generate(prompt, temperature=0.1, max_tokens=200)

    def generate_layer3(self, prompt: str) -> str:
        """Capa 3: Sintetizador (Razonamiento, modelo grande)."""
        if isinstance(self.provider, OllamaProvider):
            return self.generate(prompt, temperature=0.3, max_tokens=1000, model_override=self.provider.layer3_model)
        return self.generate(prompt, temperature=0.3, max_tokens=1000)

    def ask_technical(self, query: str, role: str = "mentor") -> str:
        """
        Consulta técnica integral (Librarian v3).
        Sintetiza contexto y usa la capa 3 para responder.
        """
        # 1. Recuperar contexto (Capa 2 implicitamente en el builder)
        context = self.context_builder.build_technical_context(query)
        
        # 2. Elegir prompt según el rol
        if role == "requirements":
            prompt = self.context_builder.get_requirements_prompt(query, context)
        else:
            prompt = self.context_builder.get_mentor_prompt(query, context)
            
        # 3. Generar respuesta con la capa 3 (Sintetizador)
        return self.generate_layer3(prompt)
    
    def _get_default_system_prompt(self) -> str:
        """System prompt oficial para Lila v3."""
        return """Eres Lila, el asistente inteligente incorporado en el sistema CGAlpha v3.
Tu rol es asistir al usuario en la auditoría técnica y gestión de riesgo del trading system.

Reglas:
- Brindas respuestas basadas en la integridad temporal de los datos.
- Eres estricto con los circuit breakers y el risk manager.
- Cuando analizas experimentos, verificas que no exista leakage temporal.
- Explicas siempre el razonamiento técnico detrás de tus recomendaciones."""
    
    def generate(self,
                 prompt: str,
                 temperature: float = 0.7,
                 max_tokens: int = 600,
                 **kwargs) -> str:
        """
        Generar respuesta usando el proveedor configurado.
        Incluye gestión de errores y reintentos.
        """
        @retry_with_rate_limit(self.rate_limiter, max_retries=2)
        def _exec():
            return self.provider.generate(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        
        try:
            return _exec()
        except Exception as e:
            logger.error(f"Error generativo en Lila: {e}")
            raise LilaLLMError(f"Error generativo: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Retorna el estado actual para la GUI."""
        info = self.provider.get_model_info()
        return {
            "provider_name": self.provider.name,
            "model_name": self.provider.model_name,
            "info": info,
            "circuit_breaker": {
                "status": "Open" if self.rate_limiter.circuit_open else "Closed",
                "available": self.rate_limiter.is_available()
            }
        }
