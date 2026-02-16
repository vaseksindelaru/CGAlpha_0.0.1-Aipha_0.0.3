"""
cgalpha.config.settings — Environment-based application settings.

Uses pydantic's BaseSettings to load configuration from:
1. Environment variables (CGALPHA_* prefix)
2. .env file (optional)
3. Hardcoded defaults

This is for *application-level* settings (paths, feature flags, logging).
Trading/Oracle *parameters* live in SystemConfig (domain/models/config.py).

Usage:
    from cgalpha_v2.config.settings import Settings

    settings = Settings()                          # loads from env
    settings = Settings(project_root="/tmp/test")  # override for testing
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application-level settings loaded from environment variables.

    All environment variables use the CGALPHA_ prefix:
        CGALPHA_PROJECT_ROOT=/home/user/cgalpha
        CGALPHA_LOG_LEVEL=DEBUG
        CGALPHA_REDIS_URL=redis://localhost:6379/0
    """

    # ── Project root ─────────────────────────────────────────────────────

    project_root: Path = Field(
        default=Path("."),
        description="Absolute path to the project root directory.",
    )

    # ── Logging ──────────────────────────────────────────────────────────

    log_level: str = Field(
        default="INFO",
        description="Python logging level (DEBUG, INFO, WARNING, ERROR).",
    )

    # ── Redis ────────────────────────────────────────────────────────────

    redis_url: Optional[str] = Field(
        default=None,
        description="Redis connection URL. None = Redis disabled.",
    )

    redis_enabled: bool = Field(
        default=False,
        description="Whether Redis integration is active.",
    )

    # ── LLM ──────────────────────────────────────────────────────────────

    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key. None = LLM features disabled.",
    )

    llm_enabled: bool = Field(
        default=False,
        description="Whether LLM features are active.",
    )

    llm_model: str = Field(
        default="gpt-4o-mini",
        description="LLM model identifier.",
    )

    # ── Feature flags ────────────────────────────────────────────────────

    code_craft_enabled: bool = Field(
        default=True,
        description="Whether Code Craft Sage auto-modification is enabled.",
    )

    deep_causal_enabled: bool = Field(
        default=False,
        description="Whether Deep Causal v0.3 features are enabled.",
    )

    # ── Resource thresholds ──────────────────────────────────────────────

    cpu_warning_threshold: float = Field(
        default=70.0,
        description="CPU usage percentage that triggers YELLOW state.",
    )

    cpu_critical_threshold: float = Field(
        default=90.0,
        description="CPU usage percentage that triggers RED state.",
    )

    memory_warning_threshold: float = Field(
        default=75.0,
        description="Memory usage percentage that triggers YELLOW state.",
    )

    memory_critical_threshold: float = Field(
        default=90.0,
        description="Memory usage percentage that triggers RED state.",
    )

    model_config = {
        "env_prefix": "CGALPHA_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }
