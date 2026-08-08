"""
cgAlpha_0.0.1 — Tests for LLM Switcher v4
==========================================
Tests for ACCIÓN 2: task-based provider routing.
"""
from __future__ import annotations

import pytest

from cgalpha_v3.lila.llm.llm_switcher import LLMSwitcher, ProviderConfig


def test_default_routing_has_all_task_types():
    switcher = LLMSwitcher()
    routing = switcher.get_routing_table()
    assert "cat_1" in routing
    assert "cat_2" in routing
    assert "cat_3" in routing
    assert "reflection" in routing
    assert "whitepaper" in routing


def test_cat_1_prefers_ollama():
    switcher = LLMSwitcher()
    config = switcher.select("cat_1")
    assert config.name == "ollama"
    assert config.temperature == 0.3


def test_cat_2_prefers_openai():
    switcher = LLMSwitcher()
    config = switcher.select("cat_2")
    assert config.name == "openai"


def test_cat_3_prefers_openai_high_tokens():
    switcher = LLMSwitcher()
    config = switcher.select("cat_3")
    assert config.name == "openai"
    assert config.max_tokens == 2000


def test_select_invalid_task_type():
    switcher = LLMSwitcher()
    with pytest.raises(ValueError, match="no registrado"):
        switcher.select("invalid_task")


def test_fallback_when_primary_unavailable():
    switcher = LLMSwitcher()
    switcher.mark_unavailable("ollama")
    config = switcher.select("cat_1")
    assert config.name == "openai"


def test_mark_available_restores():
    switcher = LLMSwitcher()
    switcher.mark_unavailable("ollama")
    switcher.mark_available("ollama")
    config = switcher.select("cat_1")
    assert config.name == "ollama"


def test_add_custom_task_type():
    switcher = LLMSwitcher()
    switcher.add_task_type("landscape", [
        ProviderConfig(name="ollama", priority=1, temperature=0.2, max_tokens=300),
    ])
    config = switcher.select("landscape")
    assert config.name == "ollama"
    assert config.temperature == 0.2


def test_routing_table_format():
    switcher = LLMSwitcher()
    table = switcher.get_routing_table()
    for task_type, configs in table.items():
        assert isinstance(configs, list)
        for cfg in configs:
            assert "name" in cfg
            assert "priority" in cfg
            assert "temperature" in cfg
            assert "max_tokens" in cfg
            assert "available" in cfg


def test_all_providers_unavailable_returns_first():
    switcher = LLMSwitcher()
    switcher.mark_unavailable("ollama")
    switcher.mark_unavailable("openai")
    # cat_1 has only ollama and openai
    config = switcher.select("cat_1")
    # Should return first by priority even if unavailable
    assert config.name == "ollama"
