"""
cgalpha.domain.models.trade — Trade record entity and trajectory value objects.

The trade module links Signal Detection (input) to Causal Analysis (output).
A TradeRecord is the *entity* written to the evolutionary bridge — it has
identity (trade_id) and a lifecycle (signal → outcome).

Design notes:
- Trajectory captures the full MFE/MAE path for causal analysis.
- TradeOutcome is the final result (ordinal ATR label).
- TradeRecord is the only entity (vs. value object) in this module
  because it has a lifecycle: created → filled → closed.
- Despite being an entity, it is still a frozen dataclass.
  Identity is determined by trade_id, not field equality.

Ubiquitous Language:
    Trajectory   → The full MFE/MAE price path over a trade's lifetime.
    TradeOutcome  → Final classification of a trade (ATR-ordinal label).
    TradeRecord   → Complete record of one trade, written to the bridge.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class TradeOutcome(Enum):
    """
    Ordinal classification of a trade result in ATR multiples.

    This replaces the legacy binary (win/loss) labeling with a more
    nuanced ordinal scale, as implemented in the Potential Capture Engine.

    Values:
        STRONG_LOSS:   MAE exceeded 2× ATR before any TP hit.
        LOSS:          MAE exceeded 1× ATR, closed at loss.
        BREAKEVEN:     Closed within ±0.25 ATR of entry.
        WIN:           MFE reached 1× ATR take-profit.
        STRONG_WIN:    MFE reached 2× ATR or more.
    """

    STRONG_LOSS = "strong_loss"
    LOSS = "loss"
    BREAKEVEN = "breakeven"
    WIN = "win"
    STRONG_WIN = "strong_win"


@dataclass(frozen=True, slots=True)
class Trajectory:
    """
    The MFE/MAE trajectory of a trade over its lifetime.

    Trajectories are the primary evidence used by the Ghost Architect
    for causal analysis.  They capture *how* a trade evolved, not just
    its final outcome.

    Attributes:
        mfe:            Maximum Favorable Excursion (best unrealized profit, ATR multiples).
        mae:            Maximum Adverse Excursion (worst unrealized drawdown, ATR multiples).
        mfe_time_bars:  Number of bars until MFE was reached.
        mae_time_bars:  Number of bars until MAE was reached.
        holding_bars:   Total bars the trade was held.
        price_path:     Optional tuple of (bar_offset, price) for full path replay.
    """

    mfe: float
    mae: float
    mfe_time_bars: int
    mae_time_bars: int
    holding_bars: int
    price_path: tuple[tuple[int, float], ...] = ()

    def __post_init__(self) -> None:
        if self.mfe < 0:
            raise ValueError(f"Trajectory MFE must be ≥ 0, got {self.mfe}")
        if self.mae < 0:
            raise ValueError(f"Trajectory MAE must be ≥ 0, got {self.mae}")
        if self.holding_bars < 0:
            raise ValueError(
                f"Trajectory holding_bars must be ≥ 0, "
                f"got {self.holding_bars}"
            )

    @property
    def capture_efficiency(self) -> float:
        """
        Ratio of realized profit to maximum available (MFE).

        Returns 0.0 if MFE is zero (no favorable excursion).
        A value of 1.0 means perfect capture (exited at MFE).
        """
        if self.mfe == 0:
            return 0.0
        return min(1.0, (self.mfe - self.mae) / self.mfe)


@dataclass(frozen=True, slots=True)
class TradeRecord:
    """
    Complete record of one trade — the unit written to the evolutionary bridge.

    TradeRecord is the primary *entity* in this module.  It is identified by
    trade_id and represents the full lifecycle of a trade from signal
    detection through outcome classification.

    Attributes:
        trade_id:       Unique identifier (format: TRD_<timestamp>_<hash>).
        signal_id:      ID of the signal that triggered this trade.
        symbol:         Trading pair (e.g. 'BTCUSDT').
        timeframe:      Candle timeframe (e.g. '1h').
        direction:      'long' or 'short'.
        entry_price:    Price at entry.
        entry_time:     Timestamp of entry.
        exit_price:     Price at exit (None if still open).
        exit_time:      Timestamp of exit (None if still open).
        atr_at_entry:   ATR value at entry for barrier calculation.
        tp_factor:      Take-profit factor in ATR multiples.
        sl_factor:      Stop-loss factor in ATR multiples.
        outcome:        Ordinal classification of the result.
        trajectory:     Full MFE/MAE trajectory.
        oracle_probability: Oracle's predicted probability (if available).
        features:       Feature values used for this trade (for reproducibility).
        created_at:     When this record was created.
    """

    trade_id: str
    signal_id: str
    symbol: str
    timeframe: str
    direction: str
    entry_price: float
    entry_time: datetime
    atr_at_entry: float
    tp_factor: float
    sl_factor: float
    outcome: TradeOutcome
    trajectory: Trajectory
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    oracle_probability: Optional[float] = None
    features: tuple[tuple[str, float], ...] = ()
    created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.entry_price <= 0:
            raise ValueError(
                f"TradeRecord entry_price must be positive, "
                f"got {self.entry_price}"
            )
        if self.atr_at_entry <= 0:
            raise ValueError(
                f"TradeRecord atr_at_entry must be positive, "
                f"got {self.atr_at_entry}"
            )
        if self.tp_factor <= 0:
            raise ValueError(
                f"TradeRecord tp_factor must be positive, "
                f"got {self.tp_factor}"
            )
        if self.sl_factor <= 0:
            raise ValueError(
                f"TradeRecord sl_factor must be positive, "
                f"got {self.sl_factor}"
            )

    @property
    def is_profitable(self) -> bool:
        """True if outcome is WIN or STRONG_WIN."""
        return self.outcome in (TradeOutcome.WIN, TradeOutcome.STRONG_WIN)

    @property
    def pnl_atr(self) -> float:
        """
        Profit/loss expressed in ATR multiples.

        Positive = profit, negative = loss.  Uses exit-entry delta
        normalized by ATR.  Returns 0.0 if exit_price is not set.
        """
        if self.exit_price is None:
            return 0.0
        delta = self.exit_price - self.entry_price
        if self.direction == "short":
            delta = -delta
        return delta / self.atr_at_entry
