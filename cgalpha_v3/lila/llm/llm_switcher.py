"""
cgAlpha_0.0.1 — LLM Switcher v4
================================
Selección de proveedor LLM por tipo de tarea.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger("llm_switcher")

@dataclass
class ProviderConfig:
    """Configuración de un proveedor para un tipo de tarea."""
    name: str
    priority: int  # menor = mayor prioridad
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 600
    available: bool = True

@dataclass
class LLMSwitcher:
    """
    Selección inteligente de proveedor LLM por tipo de tarea.
    """
    assistant: Any = None  # LLMAssistant instance
    _task_routing: dict[str, list[ProviderConfig]] = field(default_factory=dict)
    _fallback_order: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self._task_routing:
            self._task_routing = self._default_routing()
        if not self._fallback_order:
            self._fallback_order = ["ollama", "openai", "zhipu", "gemini"]

    @staticmethod
    def _default_routing() -> dict[str, list[ProviderConfig]]:
        """Routing por defecto basado en las reglas del Prompt Fundacional §4."""
        return {
            "cat_1": [
                ProviderConfig(name="ollama", priority=1, temperature=0.3, max_tokens=400),
                ProviderConfig(name="openai", priority=2, temperature=0.3, max_tokens=400),
            ],
            "cat_2": [
                ProviderConfig(name="openai", priority=1, temperature=0.5, max_tokens=1000),
                ProviderConfig(name="ollama", priority=2, temperature=0.5, max_tokens=1000),
                ProviderConfig(name="gemini", priority=3, temperature=0.5, max_tokens=1000),
                ProviderConfig(name="zhipu", priority=4, temperature=0.5, max_tokens=1000),
            ],
            "cat_3": [
                ProviderConfig(name="openai", priority=1, temperature=0.7, max_tokens=2000),
                ProviderConfig(name="gemini", priority=2, temperature=0.7, max_tokens=2000),
                ProviderConfig(name="ollama", priority=3, temperature=0.7, max_tokens=2000),
                ProviderConfig(name="zhipu", priority=4, temperature=0.7, max_tokens=2000),
            ],
            "reflection": [
                ProviderConfig(name="openai", priority=1, temperature=0.4, max_tokens=1000),
                ProviderConfig(name="ollama", priority=2, temperature=0.4, max_tokens=1000),
                ProviderConfig(name="gemini", priority=3, temperature=0.4, max_tokens=1000),
            ],
            "whitepaper": [
                ProviderConfig(name="openai", priority=1, temperature=0.6, max_tokens=4000),
                ProviderConfig(name="gemini", priority=2, temperature=0.6, max_tokens=4000),
                ProviderConfig(name="zhipu", priority=3, temperature=0.6, max_tokens=4000),
            ],
        }

    def select(self, task_type: str) -> ProviderConfig:
        if task_type not in self._task_routing:
            raise ValueError(f"Tipo de tarea '{task_type}' no registrado.")

        candidates = sorted(self._task_routing[task_type], key=lambda c: c.priority)
        for config in candidates:
            if config.available:
                return config
        return candidates[0]

    def generate(self, task_type: str, prompt: str, **kwargs) -> str:
        if not self.assistant:
            raise RuntimeError("LLMSwitcher requiere un LLMAssistant configurado")
        if task_type not in self._task_routing:
            raise ValueError(f"Tipo de tarea '{task_type}' no registrado.")

        candidates = sorted(self._task_routing[task_type], key=lambda c: c.priority)
        for cfg in candidates:
            if not cfg.available:
                continue
            try:
                if self.assistant.provider.name != cfg.name:
                    switched = self.assistant.switch_provider(cfg.name)
                    if not switched:
                        continue

                return self.assistant.generate(
                    prompt,
                    temperature=kwargs.get("temperature", cfg.temperature),
                    max_tokens=kwargs.get("max_tokens", cfg.max_tokens),
                )
            except Exception as e:
                logger.warning(f"⚠️ LLM_SWITCHER: {cfg.name} falló para {task_type}: {e}")
                cfg.available = False
                continue

        raise RuntimeError(f"Todos los proveedores fallaron para '{task_type}'")

    def mark_unavailable(self, provider_name: str) -> None:
        for configs in self._task_routing.values():
            for cfg in configs:
                if cfg.name == provider_name:
                    cfg.available = False

    def mark_available(self, provider_name: str) -> None:
        for configs in self._task_routing.values():
            for cfg in configs:
                if cfg.name == provider_name:
                    cfg.available = True

    def add_task_type(self, task_type: str, configs: list[ProviderConfig]) -> None:
        if not task_type or not task_type.strip():
            raise ValueError("task_type no puede estar vacio")
        if not configs:
            raise ValueError("configs no puede estar vacio")
        self._task_routing[task_type] = list(configs)

    def get_routing_table(self) -> dict[str, list[dict]]:
        result = {}
        for task_type, configs in self._task_routing.items():
            result[task_type] = [
                {
                    "name": c.name,
                    "priority": c.priority,
                    "temperature": c.temperature,
                    "max_tokens": c.max_tokens,
                    "available": c.available,
                }
                for c in sorted(configs, key=lambda c: c.priority)
            ]
        return result
