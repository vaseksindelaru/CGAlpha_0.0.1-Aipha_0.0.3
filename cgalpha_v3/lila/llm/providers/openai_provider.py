"""
cgalpha_v3/lila/llm/providers/openai_provider.py - Proveedor OpenAI para Lila v3

Implementación específica para la API de OpenAI (GPT-3.5-turbo, GPT-4).
"""

import os
import logging
from typing import Dict, Any, Optional
from .base import LLMProvider, LilaLLMError, LilaLLMConnectionError, LilaLLMRateLimitError

logger = logging.getLogger(__name__)

class OpenAIProvider(LLMProvider):
    """Proveedor de OpenAI de Lila."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._model = model
        self._client = None
        
        if not self._api_key:
            logger.warning("OPENAI_API_KEY no configurada. Lila entrará en modo fallback OpenAI.")
        
    def _get_client(self):
        """Lazy load del cliente OpenAI."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self._api_key)
            except ImportError:
                raise LilaLLMError("openai package no instalado: pip install openai")
        return self._client
    
    def generate(self,
                 prompt: str,
                 system_prompt: Optional[str] = None,
                 temperature: float = 0.7,
                 max_tokens: int = 500,
                 **kwargs) -> str:
        """Generar respuesta con completion API."""
        if not self._api_key:
            raise LilaLLMError("OPENAI_API_KEY no configurado en el sistema.")
        
        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt or "Eres Lila, el asistente de CGAlpha v3."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            msg = str(e).lower()
            if "rate_limit" in msg:
                raise LilaLLMRateLimitError(f"Rate limit de OpenAI: {e}")
            elif "connection" in msg or "timeout" in msg:
                raise LilaLLMConnectionError(f"Error de conexión con OpenAI: {e}")
            raise LilaLLMError(f"Error general de OpenAI: {e}")

    def validate_api_key(self) -> bool:
        """Check simple de validación."""
        return bool(self._api_key and len(self._api_key.strip()) > 30)

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "name": self._model,
            "provider": "openai",
            "max_tokens": 4096,
            "description": "OpenAI GPT-based model"
        }

    @property
    def name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model
