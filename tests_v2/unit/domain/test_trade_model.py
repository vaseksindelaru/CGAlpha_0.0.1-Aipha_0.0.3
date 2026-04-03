"""Unit tests for cgalpha_v2.domain.models.trade."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cgalpha_v2.domain.models import (
    SignalDirection,
    TradeOutcome,
    TradeRecord,
    Trajectory,
)


def test_trajectory_capture_efficiency(sample_trajectory: Trajectory) -> None:
    assert sample_trajectory.capture_efficiency == pytest.approx((2.3 - 0.8) / 2.3)


def test_trajectory_zero_mfe_capture_efficiency_is_zero() -> None:
    trajectory = Trajectory(
        mfe=0.0,
        mae=0.0,
        mfe_time_bars=0,
        mae_time_bars=0,
        holding_bars=0,
    )
    assert trajectory.capture_efficiency == 0.0


def test_trajectory_negative_values_raise() -> None:
    with pytest.raises(ValueError, match="MFE"):
        Trajectory(
            mfe=-0.1,
            mae=0.1,
            mfe_time_bars=1,
            mae_time_bars=1,
            holding_bars=1,
        )

    with pytest.raises(ValueError, match="MAE"):
        Trajectory(
            mfe=0.1,
            mae=-0.1,
            mfe_time_bars=1,
            mae_time_bars=1,
            holding_bars=1,
        )


def test_trade_record_is_profitable(sample_trade_record: TradeRecord) -> None:
    assert sample_trade_record.is_profitable is True


def test_trade_record_pnl_atr_for_long(sample_trajectory: Trajectory) -> None:
    trade = TradeRecord(
        trade_id="TRD_LONG",
        signal_id="SIG_1",
        symbol="BTCUSDT",
        timeframe="5m",
        direction=SignalDirection.LONG,
        entry_price=100.0,
        entry_time=datetime.now(timezone.utc),
        atr_at_entry=10.0,
        tp_factor=2.0,
        sl_factor=1.0,
        outcome=TradeOutcome.WIN,
        trajectory=sample_trajectory,
        exit_price=120.0,
    )
    assert trade.pnl_atr == 2.0


def test_trade_record_pnl_atr_for_short(sample_trajectory: Trajectory) -> None:
    trade = TradeRecord(
        trade_id="TRD_SHORT",
        signal_id="SIG_1",
        symbol="BTCUSDT",
        timeframe="5m",
        direction=SignalDirection.SHORT,
        entry_price=100.0,
        entry_time=datetime.now(timezone.utc),
        atr_at_entry=10.0,
        tp_factor=2.0,
        sl_factor=1.0,
        outcome=TradeOutcome.WIN,
        trajectory=sample_trajectory,
        exit_price=90.0,
    )
    assert trade.pnl_atr == 1.0


def test_trade_record_pnl_atr_without_exit_is_zero(sample_trajectory: Trajectory) -> None:
    trade = TradeRecord(
        trade_id="TRD_OPEN",
        signal_id="SIG_1",
        symbol="BTCUSDT",
        timeframe="5m",
        direction=SignalDirection.LONG,
        entry_price=100.0,
        entry_time=datetime.now(timezone.utc),
        atr_at_entry=10.0,
        tp_factor=2.0,
        sl_factor=1.0,
        outcome=TradeOutcome.BREAKEVEN,
        trajectory=sample_trajectory,
    )
    assert trade.pnl_atr == 0.0


def test_trade_record_validation_raises_on_bad_entry_price(
    sample_trajectory: Trajectory,
) -> None:
    with pytest.raises(ValueError, match="entry_price"):
        TradeRecord(
            trade_id="TRD_BAD",
            signal_id="SIG_1",
            symbol="BTCUSDT",
            timeframe="5m",
            direction=SignalDirection.LONG,
            entry_price=0.0,
            entry_time=datetime.now(timezone.utc),
            atr_at_entry=10.0,
            tp_factor=2.0,
            sl_factor=1.0,
            outcome=TradeOutcome.LOSS,
            trajectory=sample_trajectory,
        )


def test_trade_record_validation_raises_on_non_enum_direction(
    sample_trajectory: Trajectory,
) -> None:
    with pytest.raises(TypeError, match="SignalDirection"):
        TradeRecord(
            trade_id="TRD_BAD_DIR",
            signal_id="SIG_1",
            symbol="BTCUSDT",
            timeframe="5m",
            direction="LONG",  # type: ignore[arg-type]
            entry_price=100.0,
            entry_time=datetime.now(timezone.utc),
            atr_at_entry=10.0,
            tp_factor=2.0,
            sl_factor=1.0,
            outcome=TradeOutcome.LOSS,
            trajectory=sample_trajectory,
        )
