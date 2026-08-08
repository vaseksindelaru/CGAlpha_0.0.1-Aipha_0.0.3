"""
cgalpha_v3/lila/llm/providers/gemini_provider.py - Proveedor Google Gemini para Lila v3

Implementación específica para la API de Google Gemini (generativeai).
"""

import os
import logging
from typing import Dict, Any, Optional
from .base import LLMProvider, LilaLLMError, LilaLLMConnectionError, LilaLLMRateLimitError

logger = logging.getLogger(__name__)

class GeminiProvider(LLMProvider):
    """Proveedor de Google Gemini de Lila."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash"):
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self._model_name = model
        self._genai = None
        self._model = None
        
        if not self._api_key:
            logger.warning("GEMINI/GOOGLE_API_KEY no configurada. Lila entrará en modo fallback Gemini.")
        
    def _initialize(self):
        """Lazy load del cliente Gemini."""
        if self._genai is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self._api_key)
                self._genai = genai
                self._model = genai.GenerativeModel(self._model_name)
            except ImportError:
                raise LilaLLMError("google-generativeai package no instalado: pip install google-generativeai")
            except Exception as e:
                raise LilaLLMError(f"Error al inicializar Gemini: {e}")
        return self._genai
    
    def generate(self,
                 prompt: str,
                 system_prompt: Optional[str] = None,
                 temperature: float = 0.7,
                 max_tokens: int = 2048,
                 **kwargs) -> str:
        """Generar respuesta con Gemini API."""
        if not self._api_key:
            raise LilaLLMError("GEMINI_API_KEY no configurado en el sistema.")
        
        try:
            self._initialize()
            
            # Gemini maneja el system prompt via instruct o configuración
            # En v0.8.x se recomienda pasarlo en el constructor del modelo o como parte del prompt
            full_prompt = f"{system_prompt}\n\nUser: {prompt}" if system_prompt else prompt
            
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
            
            response = self._model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            if not response.text:
                raise LilaLLMError("Gemini devolvió una respuesta vacía (posible bloqueo de seguridad).")
                
            return response.text
        except Exception as e:
            msg = str(e).lower()
            if "rate limit" in msg or "429" in msg:
                raise LilaLLMRateLimitError(f"Rate limit de Gemini: {e}")
            elif "connection" in msg or "timeout" in msg:
                raise LilaLLMConnectionError(f"Error de conexión con Gemini: {e}")
            raise LilaLLMError(f"Error general de Gemini: {e}")

    def validate_api_key(self) -> bool:
        """Check simple de validación."""
        if not self._api_key or self._api_key == "demo_key_for_testing":
            return False
        return len(self._api_key.strip()) > 30 # Keys reales suelen ser > 30 chars

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "name": self._model_name,
            "provider": "gemini",
            "max_tokens": 32768,
            "description": "Google Gemini Generative Model"
        }

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model_name
