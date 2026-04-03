"""Unit tests for cgalpha_v2.config.settings."""

from __future__ import annotations

from pathlib import Path

import pytest

from cgalpha_v2.config import Settings


def test_settings_defaults_have_expected_types() -> None:
    settings = Settings()
    assert isinstance(settings.project_root, Path)
    assert isinstance(settings.log_level, str)
    assert isinstance(settings.redis_enabled, bool)
    assert isinstance(settings.llm_enabled, bool)


def test_settings_reads_env_vars(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CGALPHA_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("CGALPHA_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("CGALPHA_REDIS_ENABLED", "true")
    monkeypatch.setenv("CGALPHA_LLM_ENABLED", "true")
    monkeypatch.setenv("CGALPHA_LLM_MODEL", "gpt-4o-mini")

    settings = Settings()
    assert settings.project_root == tmp_path
    assert settings.log_level == "DEBUG"
    assert settings.redis_enabled is True
    assert settings.llm_enabled is True
    assert settings.llm_model == "gpt-4o-mini"


def test_settings_ignores_unknown_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CGALPHA_UNKNOWN_OPTION", "something")
    settings = Settings()
    assert settings.log_level in {"DEBUG", "INFO", "WARNING", "ERROR"}
