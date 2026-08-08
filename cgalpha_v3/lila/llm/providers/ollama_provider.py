"""
cgalpha_v3/lila/llm/providers/ollama_provider.py - Local Ollama Provider for Lila.

Supports dual-layer architecture:
- Layer 3 (Synthesizer): Reasoning, academic validation (e.g. qwen2.5:7b).
- Layer 2 (Retriever): Fast semantic search, extraction (e.g. qwen2.5:1.5b).
"""

import json
import logging
import os
from typing import Any, Dict, Optional, List
from urllib import request, error

from .base import LLMProvider
from ..exceptions import LilaLLMError, LilaLLMConnectionError

logger = logging.getLogger(__name__)

class OllamaProvider(LLMProvider):
    """
    Proveedor local vía Ollama.
    Implementa la arquitectura de doble capa (Sintetizador y Recuperador).
    """

    def __init__(self, 
                 host: str = "http://127.0.0.1:11434",
                 default_model: str = "qwen2.5:1.5b",
                 layer3_model: str = "qwen2.5:3b"):
        self.host = host.rstrip("/")
        self.default_model = default_model
        self.layer3_model = layer3_model
        self._name = "ollama"

    @property
    def name(self) -> str:
        return self._name

    def generate(self,
                 prompt: str,
                 system_prompt: str = None,
                 temperature: float = 0.2,
                 max_tokens: int = 500,
                 model_override: Optional[str] = None) -> str:
        """
        Genera una respuesta usando el endpoint de Ollama.
        """
        model = model_override or self.default_model
        
        # Combinar prompts si hay un system prompt
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        payload = {
            "model": model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 300,
                "num_ctx": 1024,
                "num_thread": 4
            }
        }
        
        try:
            data = json.dumps(payload).encode("utf-8")
            req = request.Request(
                url=f"{self.host}/api/generate",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            
            with request.urlopen(req, timeout=300) as resp:
                raw = resp.read().decode("utf-8")
                parsed = json.loads(raw)
                return str(parsed.get("response", "")).strip()
                
        except error.URLError as e:
            logger.error(f"Ollama connection failed: {e}")
            raise LilaLLMConnectionError(f"Ollama not reachable at {self.host}")
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise LilaLLMError(f"Local LLM Error: {e}")

    @property
    def model_name(self) -> str:
        return self.default_model

    def validate_api_key(self) -> bool:
        """Verifica si Ollama está respondiendo."""
        try:
            url = f"{self.host}/api/tags"
            with request.urlopen(url, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "provider": "ollama",
            "host": self.host,
            "models": {
                "layer2": self.default_model,
                "layer3": self.layer3_model
            },
            "description": "Local Qwen dual-layer architecture powered by Ollama."
        }

    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """Intenta extraer JSON de la respuesta del modelo local."""
        try:
            # Buscar el bloque JSON si el modelo incluyó texto extra
            if "```json" in response:
                response = response.split("```json")[-1].split("```")[0]
            elif "{" in response:
                response = "{" + response.split("{", 1)[-1].rsplit("}", 1)[0] + "}"
                
            return json.loads(response.strip())
        except Exception:
            raise ValueError(f"No se pudo parsear JSON de la respuesta local: {response[:100]}...")
