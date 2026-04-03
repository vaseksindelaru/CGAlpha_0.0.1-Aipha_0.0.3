"""Unit tests for cgalpha_v2.domain.models.config."""

from __future__ import annotations

import pytest

from cgalpha_v2.domain.models import OracleConfig, SystemConfig, TradingConfig
from cgalpha_v2.domain.models.config import PostprocessorConfig


def test_trading_config_validation_raises() -> None:
    with pytest.raises(ValueError, match="atr_period"):
        TradingConfig(atr_period=0)

    with pytest.raises(ValueError, match="tp_factor"):
        TradingConfig(tp_factor=0.0)

    with pytest.raises(ValueError, match="volume_percentile_threshold"):
        TradingConfig(volume_percentile_threshold=101)


def test_oracle_config_validation_raises() -> None:
    with pytest.raises(ValueError, match="confidence_threshold"):
        OracleConfig(confidence_threshold=1.1)

    with pytest.raises(ValueError, match="n_estimators"):
        OracleConfig(n_estimators=0)


def test_postprocessor_config_validation_raises() -> None:
    with pytest.raises(ValueError, match="adaptive_sensitivity"):
        PostprocessorConfig(adaptive_sensitivity=-0.1)


def test_system_config_to_dict_uses_legacy_keys() -> None:
    config = SystemConfig()
    raw = config.to_dict()
    assert set(raw.keys()) == {"Trading", "Oracle", "Postprocessor"}


def test_system_config_from_dict_accepts_legacy_and_new_keys() -> None:
    legacy = {
        "Trading": {"tp_factor": 2.5},
        "Oracle": {"confidence_threshold": 0.75},
        "Postprocessor": {"adaptive_sensitivity": 0.3},
    }
    cfg_legacy = SystemConfig.from_dict(legacy)
    assert cfg_legacy.trading.tp_factor == 2.5
    assert cfg_legacy.oracle.confidence_threshold == 0.75
    assert cfg_legacy.postprocessor.adaptive_sensitivity == 0.3

    modern = {
        "trading": {"tp_factor": 3.0},
        "oracle": {"confidence_threshold": 0.8},
        "postprocessor": {"adaptive_sensitivity": 0.25},
    }
    cfg_modern = SystemConfig.from_dict(modern)
    assert cfg_modern.trading.tp_factor == 3.0
    assert cfg_modern.oracle.confidence_threshold == 0.8
    assert cfg_modern.postprocessor.adaptive_sensitivity == 0.25
