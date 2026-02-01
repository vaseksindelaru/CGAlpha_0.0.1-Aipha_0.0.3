"""
core/llm_providers/base.py - Interfaz Base para Proveedores LLM

Define la interfaz que deben cumplir todos los proveedores de LLM.
Permite intercambiar entre OpenAI, Anthropic, Qwen, etc. sin cambiar código.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """
    Interfaz abstracta para proveedores de LLM.
    
    Todos los proveedores deben implementar estos métodos
    para ser intercambiables en el sistema.
    """
    
    @abstractmethod
    def generate(self, 
                 prompt: str,
                 system_prompt: Optional[str] = None,
                 temperature: float = 0.7,
                 max_tokens: int = 500,
                 **kwargs) -> str:
        """
        Generar respuesta del LLM.
        
        Args:
            prompt: Texto del usuario
            system_prompt: Instrucciones del sistema (opcional)
            temperature: Creatividad (0.0-2.0)
            max_tokens: Máximo de tokens en respuesta
            **kwargs: Parámetros específicos del proveedor
        
        Returns:
            Respuesta generada
        
        Raises:
            LLMError: Si falla la generación
        """
        pass
    
    @abstractmethod
    def validate_api_key(self) -> bool:
        """
        Validar que la API key es válida.
        
        Returns:
            True si es válida, False si no
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Obtener información del modelo.
        
        Returns:
            Dict con: name, version, max_tokens, cost_per_1k_tokens, etc.
        """
        pass
    
    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parsear respuesta JSON del LLM.
        
        Maneja casos donde el LLM retorna JSON con markdown.
        
        Args:
            response: Respuesta potencialmente JSON
        
        Returns:
            Dict parseado
        
        Raises:
            ValueError: Si no se puede parsear como JSON
        """
        import json
        import re
        
        # Intenta parsear directamente
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Intenta extraer JSON de markdown
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Último intento: buscar { ... }
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        
        raise ValueError(f"Cannot parse JSON from response: {response[:100]}")
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre del proveedor (openai, anthropic, qwen, etc)"""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Nombre del modelo siendo usado"""
        pass


class LLMError(Exception):
    """Excepción base para errores de LLM"""
    pass


class LLMConnectionError(LLMError):
    """Error al conectar con API del LLM"""
    pass


class LLMRateLimitError(LLMError):
    """Se excedió el rate limit del LLM"""
    pass


class LLMParseError(LLMError):
    """Error al parsear respuesta del LLM"""
    pass
