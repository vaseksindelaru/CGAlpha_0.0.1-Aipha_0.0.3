"""
cgalpha_v3/lila/llm/providers/zhipu_provider.py - Proveedor Zhipu AI para Lila v3

Implementación específica para la API de Zhipu AI (GLM-4) compatible OpenAI.
"""

import os
import logging
from typing import Dict, Any, Optional
from .openai_provider import OpenAIProvider
from ..exceptions import LilaLLMError

logger = logging.getLogger(__name__)

class ZhipuProvider(OpenAIProvider):
    """Proveedor de Zhipu AI de Lila."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._zhipu_key = api_key or os.environ.get("ZHIPU_API_KEY")
        # Priorizar ZHIPU_MODEL si se pasa
        self._model_name = model or os.environ.get("ZHIPU_MODEL", "glm-4")
        # Inicializamos con la clave de Zhipu
        super().__init__(api_key=self._zhipu_key, model=self._model_name)
        
        if not self._zhipu_key:
            logger.warning("ZHIPU_API_KEY no configurada. Lila entrará en modo fallback Zhipu.")
        
    def _get_client(self):
        """Lazy load del cliente OpenAI configurado para Zhipu."""
        if self._client is None:
            try:
                from openai import OpenAI
                # Zhipu AI v4 compatible endpoint
                self._client = OpenAI(
                    api_key=self._api_key,
                    base_url="https://open.bigmodel.cn/api/paas/v4/"
                )
            except ImportError:
                raise LilaLLMError("openai package no instalado: pip install openai")
        return self._client
    
    def generate(self, *args, **kwargs) -> str:
        try:
            return super().generate(*args, **kwargs)
        except Exception as e:
            raise LilaLLMError(f"Error de Zhipu AI (GLM): {e}")
        return {
            "name": self._model,
            "provider": "zhipu",
            "max_tokens": 4096,
            "description": "Zhipu AI GLM-4 family (Chat)"
        }

    @property
    def name(self) -> str:
        return "zhipu"

    @property
    def model_name(self) -> str:
        return self._model
