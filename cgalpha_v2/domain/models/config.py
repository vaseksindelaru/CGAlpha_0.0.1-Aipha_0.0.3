"""
cgalpha.domain.models.config — Typed configuration value objects.

This module replaces the untyped dict-based configuration with strongly-typed
immutable value objects.  Each bounded context gets its own config class.

Design notes:
- TradingConfig holds parameters for signal detection and barriers.
- OracleConfig holds ML model parameters.
- SystemConfig bundles all context-specific configs.
- All values have explicit types and ranges documented.
- Defaults match the legacy aipha_config.json baseline.
- Frozen dataclasses — config is read-only once loaded.

Ubiquitous Language:
    TradingConfig → Parameters governing signal detection and trade barriers.
    OracleConfig  → Parameters governing ML prediction filtering.
    SystemConfig  → Top-level container for all configuration sections.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True, slots=True)
class TradingConfig:
    """
    Configuration for the Signal Detection bounded context.

    These parameters control the ATR barrier calculation, volume
    thresholds, and time limits for trade management.

    All defaults match the legacy aipha_config.json baseline.

    Attributes:
        atr_period:                   Period for ATR calculation (candles).
        tp_factor:                    Take-profit distance in ATR multiples.
        sl_factor:                    Stop-loss distance in ATR multiples.
        time_limit:                   Maximum holding time in hours.
        volume_percentile_threshold:  Minimum volume percentile for key candle.
        body_percentile_threshold:    Minimum body percentile for key candle.
    """

    atr_period: int = 14
    tp_factor: float = 2.0
    sl_factor: float = 1.0
    time_limit: int = 24
    volume_percentile_threshold: int = 90
    body_percentile_threshold: int = 25

    def __post_init__(self) -> None:
        if self.atr_period < 1:
            raise ValueError(
                f"TradingConfig atr_period must be ≥ 1, got {self.atr_period}"
            )
        if self.tp_factor <= 0:
            raise ValueError(
                f"TradingConfig tp_factor must be positive, got {self.tp_factor}"
            )
        if self.sl_factor <= 0:
            raise ValueError(
                f"TradingConfig sl_factor must be positive, got {self.sl_factor}"
            )
        if self.time_limit < 1:
            raise ValueError(
                f"TradingConfig time_limit must be ≥ 1, got {self.time_limit}"
            )
        if not (0 <= self.volume_percentile_threshold <= 100):
            raise ValueError(
                f"TradingConfig volume_percentile_threshold must be in [0, 100], "
                f"got {self.volume_percentile_threshold}"
            )
        if not (0 <= self.body_percentile_threshold <= 100):
            raise ValueError(
                f"TradingConfig body_percentile_threshold must be in [0, 100], "
                f"got {self.body_percentile_threshold}"
            )


@dataclass(frozen=True, slots=True)
class OracleConfig:
    """
    Configuration for the Prediction (Oracle) bounded context.

    These parameters control the ML model selection, confidence thresholds,
    and model hyperparameters.

    Attributes:
        confidence_threshold: Minimum probability for Oracle to pass a signal.
        n_estimators:         Number of trees in the RandomForest.
        model_path:           Relative path to the serialized .joblib model.
    """

    confidence_threshold: float = 0.70
    n_estimators: int = 100
    model_path: str = "oracle/models/proof_oracle.joblib"

    def __post_init__(self) -> None:
        if not (0.0 <= self.confidence_threshold <= 1.0):
            raise ValueError(
                f"OracleConfig confidence_threshold must be in [0, 1], "
                f"got {self.confidence_threshold}"
            )
        if self.n_estimators < 1:
            raise ValueError(
                f"OracleConfig n_estimators must be ≥ 1, "
                f"got {self.n_estimators}"
            )


@dataclass(frozen=True, slots=True)
class PostprocessorConfig:
    """
    Configuration for the Data Postprocessor.

    Attributes:
        adaptive_sensitivity: Sensitivity for adaptive feedback (0.0-1.0).
    """

    adaptive_sensitivity: float = 0.1

    def __post_init__(self) -> None:
        if not (0.0 <= self.adaptive_sensitivity <= 1.0):
            raise ValueError(
                f"PostprocessorConfig adaptive_sensitivity must be in [0, 1], "
                f"got {self.adaptive_sensitivity}"
            )


@dataclass(frozen=True, slots=True)
class SystemConfig:
    """
    Top-level configuration container.

    Bundles all context-specific configs into a single immutable object.
    This replaces the legacy dict-based aipha_config.json access pattern.

    Usage:
        config = SystemConfig()  # all defaults
        config = SystemConfig(trading=TradingConfig(tp_factor=2.5))
    """

    trading: TradingConfig = TradingConfig()
    oracle: OracleConfig = OracleConfig()
    postprocessor: PostprocessorConfig = PostprocessorConfig()

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize to a dict matching the legacy aipha_config.json format.

        This ensures backward compatibility with components that still
        read the JSON config directly.
        """
        from dataclasses import asdict

        raw = asdict(self)
        # Map field names to legacy JSON keys
        return {
            "Trading": raw["trading"],
            "Oracle": raw["oracle"],
            "Postprocessor": raw["postprocessor"],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SystemConfig:
        """
        Deserialize from the legacy aipha_config.json format.

        Handles both capitalized (legacy) and lowercase (new) keys.
        """
        trading_data = data.get("Trading", data.get("trading", {}))
        oracle_data = data.get("Oracle", data.get("oracle", {}))
        postprocessor_data = data.get(
            "Postprocessor", data.get("postprocessor", {})
        )
        return cls(
            trading=TradingConfig(**trading_data) if trading_data else TradingConfig(),
            oracle=OracleConfig(**oracle_data) if oracle_data else OracleConfig(),
            postprocessor=(
                PostprocessorConfig(**postprocessor_data)
                if postprocessor_data
                else PostprocessorConfig()
            ),
        )
