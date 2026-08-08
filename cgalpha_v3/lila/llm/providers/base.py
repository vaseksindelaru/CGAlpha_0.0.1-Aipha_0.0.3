"""
cgalpha_v3/lila/llm/providers/base.py - Interfaz Base para Proveedores LLM (Lila v3)

Define la interfaz que todos los proveedores de LLM deben cumplir.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from ..exceptions import LilaLLMError, LilaLLMConnectionError, LilaLLMRateLimitError

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Interfaz abstracta para proveedores de LLM en Lila."""
    
    @abstractmethod
    def generate(self, 
                 prompt: str,
                 system_prompt: Optional[str] = None,
                 temperature: float = 0.7,
                 max_tokens: int = 500,
                 **kwargs) -> str:
        """Generar respuesta del LLM."""
        pass
    
    @abstractmethod
    def validate_api_key(self) -> bool:
        """Validar que la API key es válida."""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Obtener información del modelo."""
        pass
    
    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parsear respuesta JSON del LLM (soporta markdown)."""
        import json
        import re
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        
        raise ValueError(f"No se pudo parsear JSON de la respuesta: {response[:100]}")
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre del proveedor (openai, zhipu, etc)"""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Nombre del modelo que se está usando."""
        pass
