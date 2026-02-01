"""
core/llm_providers/__init__.py - Proveedores de LLM Modularizados

Arquitectura modular para diferentes proveedores de LLM (OpenAI, Anthropic, etc).
Soluciona: P1 #6 - LLM Assistant acoplado (895 líneas)

Estructura:
  - base.py: Interfaz abstracta LLMProvider
  - openai_provider.py: Implementación para OpenAI
  - rate_limiter.py: Control de rate limiting
  - cache.py: Cache de respuestas LLM
"""

from .base import LLMProvider
from .openai_provider import OpenAIProvider
from .rate_limiter import RateLimiter, retry_with_rate_limit

__all__ = [
    "LLMProvider",
    "OpenAIProvider",
    "RateLimiter",
    "retry_with_rate_limit",
]
