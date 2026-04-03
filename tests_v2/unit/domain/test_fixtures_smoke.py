"""Smoke tests for v2 shared fixtures."""

from __future__ import annotations

from cgalpha_v2.domain.models import HealthEvent, Prediction, Signal, TradeRecord


def test_sample_signal_fixture(sample_signal: Signal) -> None:
    assert sample_signal.signal_id.startswith("SIG_")


def test_sample_trade_record_fixture(sample_trade_record: TradeRecord) -> None:
    assert sample_trade_record.trade_id.startswith("TRD_")


def test_sample_prediction_fixture(sample_prediction: Prediction) -> None:
    assert 0.0 <= sample_prediction.probability <= 1.0


def test_sample_health_event_fixture(sample_health_event: HealthEvent) -> None:
    assert sample_health_event.source == "trading_engine"
