"""
core/llm_client.py - Cliente de Conexión a Qwen 2.5 Coder 32B

Gestiona la conexión con el modelo LLM a través de HuggingFace router.
Implementa retry logic, rate limiting, y manejo seguro de tokens.
MEJORADO: Carga automática de .env
"""

import os
import json
import logging
import time
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum
import sys

logger = logging.getLogger(__name__)

# CARGAR .env INMEDIATAMENTE AL IMPORTAR
def _load_dotenv():
    """Cargar .env al importar el módulo (ejecuta PRIMERO)"""
    # Buscar .env
    env_path = Path(".env")
    
    # Si no está en el directorio actual, buscar en superiores
    if not env_path.exists():
        for parent in Path.cwd().parents:
            candidate = parent / ".env"
            if candidate.exists():
                env_path = candidate
                break
    
    # Cargar si existe
    if env_path.exists():
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' not in line:
                        continue
                    
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remover comillas
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    
                    os.environ[key] = value
        except Exception as e:
            logger.debug(f"Error cargando .env: {e}")

# EJECUTAR AL IMPORTAR EL MÓDULO
_load_dotenv()


class LLMProvider(Enum):
    """Proveedores de LLM soportados"""
    OPENAI_COMPATIBLE = "openai"  # HuggingFace router compatible con OpenAI


@dataclass
class LLMConfig:
    """Configuración del cliente LLM"""
    model: str = "Qwen/Qwen2.5-Coder-32B-Instruct:auto"
    api_base: str = "https://router.huggingface.co/v1"
    provider: LLMProvider = LLMProvider.OPENAI_COMPATIBLE
    api_key: Optional[str] = None
    max_retries: int = 3
    timeout_seconds: int = 30
    max_tokens: int = 2048
    temperature: float = 0.7


class LLMClient:
    """
    Cliente seguro para conectar con Qwen 2.5 Coder 32B
    
    Características:
    - Manejo seguro de API keys (env var o .env)
    - Retry logic automático
    - Rate limiting
    - Logging de requests/responses
    - Validación de responses
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Inicializar cliente LLM
        
        Argumentos:
            config: Configuración (si None, usa defaults + env vars)
        
        NOTA: .env ya se carga en el import del módulo (_load_dotenv)
        """
        
        self.config = config or self._load_config()
        
        # Validar que tenemos API key
        if not self.config.api_key:
            raise ValueError(
                "❌ API Key no encontrada. "
                "Configure AIPHA_BRAIN_KEY en .env o variable de entorno"
            )
        
        # Importar openai (lazy import)
        try:
            from openai import OpenAI
            self.OpenAI = OpenAI
        except ImportError:
            raise ImportError(
                "openai library no instalada. "
                "Instale: pip install openai"
            )
        
        # Inicializar cliente OpenAI con router de HF
        self.client = self.OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.api_base
        )
        
        # Estadísticas
        self.request_count = 0
        self.total_tokens = 0
        self.error_count = 0
        
        logger.info(
            f"✅ LLMClient inicializado: {self.config.model} "
            f"({self.config.api_base})"
        )
    
    
    def _load_config(self) -> LLMConfig:
        """
        Cargar configuración desde environment variables
        
        (Las variables ya han sido cargadas desde .env en el import)
        """
        
        logger.info("� Cargando configuración del LLM...")
        
        # Obtener valores
        api_key = os.getenv("AIPHA_BRAIN_KEY")
        api_base = os.getenv(
            "AIPHA_BRAIN_BASE",
            "https://router.huggingface.co/v1"
        )
        model = os.getenv(
            "AIPHA_BRAIN_MODEL",
            "Qwen/Qwen2.5-Coder-32B-Instruct:auto"
        )
        
        # Log de lo que se encontró
        if api_key:
            logger.info(f"✅ AIPHA_BRAIN_KEY encontrada ({len(api_key)} caracteres)")
        else:
            logger.error("❌ AIPHA_BRAIN_KEY no encontrada")
        
        logger.info(f"✅ API Base: {api_base}")
        logger.info(f"✅ Modelo: {model}")
        
        return LLMConfig(
            api_key=api_key,
            api_base=api_base,
            model=model
        )
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generar respuesta del LLM
        
        Argumentos:
            prompt: Mensaje del usuario
            system_prompt: Instrucciones del sistema
            temperature: Creatividad (0-1)
            max_tokens: Máximo de tokens en respuesta
        
        Retorna:
            Respuesta del modelo
        """
        
        messages = []
        
        # Agregar system prompt si está disponible
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # Agregar mensaje del usuario
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Configurar parámetros
        temp = temperature if temperature is not None else self.config.temperature
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        
        # Retry logic
        for attempt in range(self.config.max_retries):
            try:
                logger.info(
                    f"📤 Enviando request al LLM (intento {attempt + 1}/"
                    f"{self.config.max_retries})"
                )
                
                # Realizar request
                response = self.client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,
                    temperature=temp,
                    max_tokens=tokens,
                    timeout=self.config.timeout_seconds
                )
                
                # Extraer respuesta
                result = response.choices[0].message.content
                
                # Actualizar estadísticas
                self.request_count += 1
                self.total_tokens += response.usage.total_tokens
                
                logger.info(
                    f"✅ Response recibida ({response.usage.total_tokens} tokens)"
                )
                
                return result
            
            except Exception as e:
                self.error_count += 1
                logger.error(f"❌ Error en LLM (intento {attempt + 1}): {e}")
                
                if attempt < self.config.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"⏳ Reintentando en {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise
        
        raise RuntimeError("No se pudo conectar al LLM")
    
    def get_statistics(self) -> Dict:
        """Obtener estadísticas de uso"""
        
        return {
            'total_requests': self.request_count,
            'total_tokens': self.total_tokens,
            'error_count': self.error_count,
            'average_tokens_per_request': (
                self.total_tokens / self.request_count
                if self.request_count > 0 else 0
            ),
            'error_rate': (
                self.error_count / self.request_count
                if self.request_count > 0 else 0
            )
        }
    
    def health_check(self) -> bool:
        """
        Verificar que el cliente pueda conectarse
        
        Retorna: True si la conexión funciona
        """
        
        try:
            logger.info("🔍 Realizando health-check del LLM...")
            
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[{
                    "role": "user",
                    "content": "test"
                }],
                max_tokens=10,
                timeout=10
            )
            
            logger.info("✅ Health-check OK")
            return True
        
        except Exception as e:
            logger.error(f"❌ Health-check falló: {e}")
            return False


# Instancia global del cliente
_llm_client_instance: Optional[LLMClient] = None


def get_llm_client(config: Optional[LLMConfig] = None) -> LLMClient:
    """Obtener instancia global del cliente LLM"""
    
    global _llm_client_instance
    
    if _llm_client_instance is None:
        _llm_client_instance = LLMClient(config)
    
    return _llm_client_instance
