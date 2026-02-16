"""
Shared fixtures for CGAlpha v2 tests.

This file provides pytest fixtures for testing the v2 codebase.
"""

import pytest
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

# Import v2 domain models
from cgalpha_v2.domain.models import (
    Signal,
    SignalDirection,
    Candle,
    Trend,
    TrendDirection,
    TradeRecord,
    TradeOutcome,
    Prediction,
    Pattern,
    Hypothesis,
    Recommendation,
    Proposal,
    ProposalStatus,
    HealthEvent,
    HealthLevel,
    SystemConfig,
)
from cgalpha_v2.config import ProjectPaths, Settings


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
        project_root=str(temp_project_root),
        debug=True,
        log_level="DEBUG",
    )


# ============================================================================
# Domain Model Fixtures
# ============================================================================

@pytest.fixture
def sample_signal() -> Signal:
    """Create a sample Signal for testing."""
    return Signal(
        symbol="BTCUSDT",
        direction=SignalDirection.LONG,
        confidence=0.85,
        timestamp=datetime.now(timezone.utc),
        detectors=["accumulation_zone", "trend", "key_candle"],
        price=65000.0,
        timeframe="5m",
    )


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
def sample_trend() -> Trend:
    """Create a sample Trend for testing."""
    return Trend(
        direction=TrendDirection.BULLISH,
        r_squared=0.85,
        slope=100.0,
        duration_bars=20,
    )


@pytest.fixture
def sample_trade_record() -> TradeRecord:
    """Create a sample TradeRecord for testing."""
    return TradeRecord(
        trade_id="TEST-001",
        symbol="BTCUSDT",
        direction=SignalDirection.LONG,
        entry_price=65000.0,
        exit_price=66000.0,
        entry_time=datetime.now(timezone.utc),
        exit_time=datetime.now(timezone.utc),
        outcome=TradeOutcome.TP,
        mfe_atr=2.5,
        mae_atr=0.5,
        config_snapshot={"threshold": 0.7},
    )


@pytest.fixture
def sample_prediction() -> Prediction:
    """Create a sample Prediction for testing."""
    return Prediction(
        probability=0.82,
        direction=SignalDirection.LONG,
        features={"body_percentage": 0.25, "volume_ratio": 1.5},
        model_version="v2_multiyear",
    )


@pytest.fixture
def sample_pattern() -> Pattern:
    """Create a sample Pattern for testing."""
    return Pattern(
        pattern_type="fakeout_cluster",
        severity="high",
        evidence_count=5,
        description="Multiple fakeouts detected in recent trades",
    )


@pytest.fixture
def sample_hypothesis() -> Hypothesis:
    """Create a sample Hypothesis for testing."""
    return Hypothesis(
        cause="Order book fakeouts causing premature exits",
        effect="Win rate degraded from 50% to 35%",
        confidence=0.85,
        signal="fakeout",
    )


@pytest.fixture
def sample_recommendation() -> Recommendation:
    """Create a sample Recommendation for testing."""
    return Recommendation(
        action="Increase confidence_threshold from 0.70 to 0.75",
        reason="Reduce exposure to low-quality signals",
        confidence=0.82,
        priority=1,
    )


@pytest.fixture
def sample_proposal() -> Proposal:
    """Create a sample Proposal for testing."""
    return Proposal(
        proposal_id="PROP-2026-001",
        title="Increase confidence threshold",
        description="Increase confidence_threshold from 0.70 to 0.75",
        status=ProposalStatus.PENDING,
        score=0.82,
    )


@pytest.fixture
def sample_health_event() -> HealthEvent:
    """Create a sample HealthEvent for testing."""
    return HealthEvent(
        level=HealthLevel.WARNING,
        component="trading_engine",
        message="High latency detected",
        timestamp=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_config() -> SystemConfig:
    """Create a sample SystemConfig for testing."""
    return SystemConfig(
        confidence_threshold=0.70,
        tp_factor=2.0,
        sl_factor=1.0,
        atr_period=14,
    )


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_market_data_reader():
    """Create a mock MarketDataReader."""
    from typing import Protocol
    from cgalpha_v2.domain.ports.data_port import MarketDataReader
    
    class MockMarketDataReader:
        def read_ohlcv(self, symbol: str, timeframe: str):
            return [sample_candle()]
    
    return MockMarketDataReader()


@pytest.fixture
def mock_predictor():
    """Create a mock Predictor."""
    from cgalpha_v2.domain.ports.prediction_port import Predictor
    
    class MockPredictor:
        def predict(self, features: dict[str, float]):
            return sample_prediction()
        
        def is_available(self) -> bool:
            return True
    
    return MockPredictor()


# ============================================================================
# Test Utilities
# ============================================================================

def assert_immutable(obj: Any):
    """Assert that an object is immutable (frozen dataclass)."""
    import dataclasses
    assert dataclasses.is_dataclass(obj), f"{obj} is not a dataclass"
    assert obj.__dataclass_fields__.get('__frozen__', False) or hasattr(obj, '__hash__'), \
        f"{obj} is not frozen/immutable"
