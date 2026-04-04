"""
Shared fixtures for CGAlpha v2 tests.

This file provides pytest fixtures aligned with the current v2 domain model
contracts while preserving legacy naming expectations used by the suite.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from cgalpha_v2.config import ProjectPaths, Settings
from cgalpha_v2.domain.models import (
    Candle,
    DetectorVerdict,
    HealthEvent,
    HealthEventType,
    HealthLevel,
    Hypothesis,
    OracleConfig,
    Pattern,
    PatternType,
    Prediction,
    Proposal,
    ProposalSource,
    ProposalStatus,
    Recommendation,
    RecommendationPriority,
    Signal,
    SignalDirection,
    SystemConfig,
    TradeOutcome,
    TradeRecord,
    TradingConfig,
    Trajectory,
    Trend,
    TrendDirection,
    TripleCoincidenceResult,
)


# ============================================================================
# Path Fixtures
# ============================================================================

@pytest.fixture
def temp_project_root(tmp_path: Path) -> Path:
    """Create a temporary project root directory."""
    return tmp_path


@pytest.fixture
def project_paths(temp_project_root: Path) -> ProjectPaths:
    """Create ProjectPaths pointing to temporary directory."""
    return ProjectPaths(root=temp_project_root)


@pytest.fixture
def settings(temp_project_root: Path) -> Settings:
    """Create Settings with temporary paths."""
    return Settings(
        project_root=temp_project_root,
        log_level="DEBUG",
    )


# ============================================================================
# Domain Model Fixtures
# ============================================================================

@pytest.fixture
def sample_candle() -> Candle:
    """Create a sample Candle for testing."""
    return Candle(
        timestamp=datetime.now(timezone.utc),
        open=65000.0,
        high=65200.0,
        low=64800.0,
        close=65100.0,
        volume=1000.0,
        symbol="BTCUSDT",
        timeframe="5m",
    )


@pytest.fixture
def sample_triple_result() -> TripleCoincidenceResult:
    """Create a sample TripleCoincidenceResult for testing."""
    return TripleCoincidenceResult(
        accumulation=DetectorVerdict(
            detector_name="accumulation_zone",
            detected=True,
            confidence=0.92,
        ),
        trend=DetectorVerdict(
            detector_name="trend",
            detected=True,
            confidence=0.86,
        ),
        key_candle=DetectorVerdict(
            detector_name="key_candle",
            detected=True,
            confidence=0.90,
        ),
        timestamp=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_signal(
    sample_candle: Candle,
    sample_triple_result: TripleCoincidenceResult,
) -> Signal:
    """Create a sample Signal for testing."""
    return Signal(
        signal_id="SIG_TEST_001",
        direction=SignalDirection.LONG,
        entry_price=65100.0,
        atr_value=120.0,
        confidence=sample_triple_result.combined_confidence,
        source_candle=sample_candle,
        triple_result=sample_triple_result,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_trend() -> Trend:
    """Create a sample Trend for testing."""
    return Trend(
        direction=TrendDirection.BULLISH,
        r_squared=0.85,
        slope=100.0,
        duration_bars=20,
    )


@pytest.fixture
def sample_trajectory() -> Trajectory:
    """Create a sample trajectory for trade model tests."""
    return Trajectory(
        mfe=2.3,
        mae=0.8,
        mfe_time_bars=8,
        mae_time_bars=3,
        holding_bars=15,
    )


@pytest.fixture
def sample_trade_record(sample_trajectory: Trajectory) -> TradeRecord:
    """Create a sample TradeRecord for testing."""
    return TradeRecord(
        trade_id="TRD_TEST_001",
        signal_id="SIG_TEST_001",
        symbol="BTCUSDT",
        timeframe="5m",
        direction=SignalDirection.LONG,
        entry_price=65000.0,
        entry_time=datetime.now(timezone.utc),
        atr_at_entry=500.0,
        tp_factor=2.0,
        sl_factor=1.0,
        outcome=TradeOutcome.TP,
        trajectory=sample_trajectory,
        exit_price=66000.0,
        exit_time=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_prediction() -> Prediction:
    """Create a sample Prediction for testing."""
    return Prediction(
        signal_id="SIG_TEST_001",
        passed=True,
        probability=0.82,
        threshold=0.70,
        model_id="v2_multiyear",
        features_used=12,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_pattern() -> Pattern:
    """Create a sample Pattern for testing."""
    return Pattern(
        pattern_type=PatternType.CUSTOM,
        name="fakeout_cluster",
        description="Multiple fakeouts detected in recent trades",
        frequency=0.35,
        confidence=0.78,
        affected_trades=35,
        total_trades=100,
    )


@pytest.fixture
def sample_hypothesis() -> Hypothesis:
    """Create a sample Hypothesis for testing."""
    return Hypothesis(
        hypothesis_id="HYP_001",
        pattern_name="fakeout_cluster",
        cause="Order book fakeouts causing premature exits",
        mechanism="Liquidity vacuums around local levels",
        evidence_strength=0.85,
        source="llm",
    )


@pytest.fixture
def sample_recommendation() -> Recommendation:
    """Create a sample Recommendation for testing."""
    return Recommendation(
        title="Increase confidence threshold",
        description="Reduce exposure to low-quality signals",
        target_parameter="Oracle.confidence_threshold",
        current_value="0.70",
        suggested_value="0.75",
        confidence=0.82,
        priority=RecommendationPriority.HIGH,
    )


@pytest.fixture
def sample_proposal() -> Proposal:
    """Create a sample Proposal for testing."""
    return Proposal(
        proposal_id="PROP-2026-001",
        title="Increase confidence threshold",
        description="Increase confidence_threshold from 0.70 to 0.75",
        source=ProposalSource.MANUAL,
        status=ProposalStatus.PENDING,
        confidence=0.82,
    )


@pytest.fixture
def sample_health_event() -> HealthEvent:
    """Create a sample HealthEvent for testing."""
    return HealthEvent(
        event_type=HealthEventType.RESOURCE_WARNING,
        level=HealthLevel.WARNING,
        source="trading_engine",
        message="High latency detected",
        timestamp=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_config() -> SystemConfig:
    """Create a sample SystemConfig for testing."""
    return SystemConfig(
        trading=TradingConfig(
            tp_factor=2.0,
            sl_factor=1.0,
            atr_period=14,
        ),
        oracle=OracleConfig(
            confidence_threshold=0.70,
            n_estimators=100,
        ),
    )


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_market_data_reader():
    """Create a mock MarketDataReader."""

    class MockMarketDataReader:
        def read_ohlcv(self, symbol: str, timeframe: str):
            _ = symbol, timeframe
            return [
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "open": 1.0,
                    "high": 1.1,
                    "low": 0.9,
                    "close": 1.0,
                    "volume": 100.0,
                }
            ]

    return MockMarketDataReader()


@pytest.fixture
def mock_predictor():
    """Create a mock Predictor."""

    class MockPredictor:
        def predict(self, features: dict[str, float], signal_id: str):
            _ = features
            return Prediction(
                signal_id=signal_id,
                passed=True,
                probability=0.8,
                threshold=0.7,
                model_id="dummy",
                features_used=1,
                created_at=datetime.now(timezone.utc),
            )

        def is_available(self) -> bool:
            return True

    return MockPredictor()


# ============================================================================
# Test Utilities
# ============================================================================

def assert_immutable(obj: Any):
    """Assert that an object is immutable (frozen dataclass)."""
    import dataclasses

    cls = obj if isinstance(obj, type) else obj.__class__
    assert dataclasses.is_dataclass(obj), f"{obj} is not a dataclass"
    assert getattr(cls, "__dataclass_params__").frozen, f"{obj} is not frozen/immutable"

