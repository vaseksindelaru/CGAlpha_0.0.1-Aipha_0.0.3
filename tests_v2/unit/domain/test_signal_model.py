"""Unit tests for cgalpha_v2.domain.models.signal."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cgalpha_v2.domain.models import (
    Candle,
    DetectorVerdict,
    Signal,
    SignalDirection,
    TripleCoincidenceResult,
)


def test_candle_properties(sample_candle: Candle) -> None:
    assert sample_candle.body_size == 100.0
    assert sample_candle.range_size == 400.0
    assert sample_candle.is_bullish is True
    assert sample_candle.body_ratio == 0.25


def test_candle_zero_range_body_ratio_is_zero() -> None:
    candle = Candle(
        timestamp=datetime.now(timezone.utc),
        open=100.0,
        high=100.0,
        low=100.0,
        close=100.0,
        volume=1.0,
    )
    assert candle.range_size == 0.0
    assert candle.body_ratio == 0.0


def test_candle_invalid_high_low_raises() -> None:
    with pytest.raises(ValueError, match="high"):
        Candle(
            timestamp=datetime.now(timezone.utc),
            open=10.0,
            high=9.0,
            low=10.0,
            close=9.5,
            volume=100.0,
        )


def test_candle_negative_volume_raises() -> None:
    with pytest.raises(ValueError, match="volume"):
        Candle(
            timestamp=datetime.now(timezone.utc),
            open=10.0,
            high=11.0,
            low=9.0,
            close=10.5,
            volume=-1.0,
        )


def test_detector_verdict_confidence_validation() -> None:
    with pytest.raises(ValueError, match="confidence"):
        DetectorVerdict(detector_name="trend", detected=True, confidence=1.2)


def test_triple_coincidence_properties(sample_triple_result: TripleCoincidenceResult) -> None:
    assert sample_triple_result.is_triple_match is True
    assert sample_triple_result.combined_confidence == 0.86


def test_triple_coincidence_not_all_detected() -> None:
    result = TripleCoincidenceResult(
        accumulation=DetectorVerdict(
            detector_name="accumulation_zone",
            detected=True,
            confidence=0.8,
        ),
        trend=DetectorVerdict(
            detector_name="trend",
            detected=False,
            confidence=0.9,
        ),
        key_candle=DetectorVerdict(
            detector_name="key_candle",
            detected=True,
            confidence=0.7,
        ),
        timestamp=datetime.now(timezone.utc),
    )
    assert result.is_triple_match is False
    assert result.combined_confidence == 0.7


def test_signal_validation_raises_on_bad_confidence(
    sample_candle: Candle,
    sample_triple_result: TripleCoincidenceResult,
) -> None:
    with pytest.raises(ValueError, match="confidence"):
        Signal(
            signal_id="SIG_BAD_CONF",
            direction=SignalDirection.LONG,
            entry_price=100.0,
            atr_value=2.0,
            confidence=2.0,
            source_candle=sample_candle,
            triple_result=sample_triple_result,
            created_at=datetime.now(timezone.utc),
        )


def test_signal_validation_raises_on_non_positive_atr(
    sample_candle: Candle,
    sample_triple_result: TripleCoincidenceResult,
) -> None:
    with pytest.raises(ValueError, match="ATR"):
        Signal(
            signal_id="SIG_BAD_ATR",
            direction=SignalDirection.SHORT,
            entry_price=100.0,
            atr_value=0.0,
            confidence=0.5,
            source_candle=sample_candle,
            triple_result=sample_triple_result,
            created_at=datetime.now(timezone.utc),
        )
