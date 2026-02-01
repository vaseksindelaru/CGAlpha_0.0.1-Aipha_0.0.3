"""
core/llm_providers/openai_provider.py - Proveedor de OpenAI

Implementación específica para OpenAI API (GPT-3.5-turbo, GPT-4, etc).
"""

import os
import logging
from typing import Dict, Any, Optional
from .base import LLMProvider, LLMConnectionError, LLMRateLimitError, LLMError

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """
    Proveedor de OpenAI.
    
    Implementa la interfaz LLMProvider para OpenAI API.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        Inicializar OpenAI provider.
        
        Args:
            api_key: API key de OpenAI (si no, usa env var OPENAI_API_KEY)
            model: Modelo a usar (gpt-3.5-turbo, gpt-4, etc)
        """
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._model = model
        self._client = None
        
        if not self._api_key:
            logger.warning("OPENAI_API_KEY not set, will fail on generate()")
        
        logger.info(f"✓ OpenAI Provider initialized (model={model})")
    
    def _get_client(self):
        """Lazy load del cliente OpenAI"""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self._api_key)
            except ImportError:
                raise LLMError("openai package not installed: pip install openai")
        return self._client
    
    def generate(self,
                 prompt: str,
                 system_prompt: Optional[str] = None,
                 temperature: float = 0.7,
                 max_tokens: int = 500,
                 **kwargs) -> str:
        """
        Generar respuesta usando OpenAI API.
        
        Args:
            prompt: Texto del usuario
            system_prompt: Instrucciones del sistema
            temperature: Creatividad (0-2)
            max_tokens: Máximo tokens
            **kwargs: Parámetros adicionales (top_p, frequency_penalty, etc)
        
        Returns:
            Respuesta generada
        
        Raises:
            LLMConnectionError: Si falla la conexión
            LLMRateLimitError: Si se excede rate limit
            LLMError: Si hay otro error
        """
        if not self._api_key:
            raise LLMError("OPENAI_API_KEY not configured")
        
        try:
            client = self._get_client()
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            error_msg = str(e)
            
            if "rate_limit" in error_msg.lower():
                raise LLMRateLimitError(f"Rate limited by OpenAI: {e}") from e
            elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                raise LLMConnectionError(f"Connection error: {e}") from e
            else:
                raise LLMError(f"OpenAI API error: {e}") from e
    
    def validate_api_key(self) -> bool:
        """
        Validar que la API key funciona.
        
        Returns:
            True si es válida, False si no
        """
        if not self._api_key:
            return False
        
        try:
            client = self._get_client()
            # Intenta listar modelos para validar key
            client.models.list()
            return True
        except Exception as e:
            logger.warning(f"API key validation failed: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Obtener información del modelo.
        
        Returns:
            Info sobre el modelo
        """
        model_info = {
            "gpt-3.5-turbo": {
                "name": "GPT-3.5 Turbo",
                "max_tokens": 4096,
                "cost_per_1k_tokens": 0.0015,  # Input tokens
                "training_data": "April 2023"
            },
            "gpt-4": {
                "name": "GPT-4",
                "max_tokens": 8192,
                "cost_per_1k_tokens": 0.03,  # Input tokens
                "training_data": "April 2023"
            },
            "gpt-4-turbo": {
                "name": "GPT-4 Turbo",
                "max_tokens": 128000,
                "cost_per_1k_tokens": 0.01,  # Input tokens
                "training_data": "April 2024"
            }
        }
        
        return model_info.get(self._model, {
            "name": self._model,
            "max_tokens": 4096,
            "cost_per_1k_tokens": 0.0015
        })
    
    @property
    def name(self) -> str:
        """Nombre del proveedor"""
        return "openai"
    
    @property
    def model_name(self) -> str:
        """Nombre del modelo"""
        return self._model
