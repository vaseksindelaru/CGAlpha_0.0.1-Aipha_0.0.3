"""
cgalpha.domain.models.signal — Signal Detection value objects.

This module defines the core value objects for the Signal Detection bounded
context: the individual candle, detector verdicts, and the combined signal.

Design notes:
- All classes are frozen dataclasses (immutable after creation).
- Candle is the fundamental unit of market data throughout the system.
- Signal represents a *detected* trading opportunity, not a raw candle.
- TripleCoincidenceResult captures the fusion of 3 independent detectors.
- No I/O, no side effects, no external dependencies.

Ubiquitous Language:
    Candle               → One OHLCV bar at a specific timeframe.
    Signal               → A detected trading opportunity with direction and strength.
    DetectorVerdict      → The output of a single detector (detected + confidence).
    TripleCoincidenceResult → The fused output of all 3 detectors.
    SignalDirection      → LONG or SHORT.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class SignalDirection(Enum):
    """Direction of a detected trading signal."""

    LONG = "long"
    SHORT = "short"


@dataclass(frozen=True, slots=True)
class Candle:
    """
    A single OHLCV candlestick.

    This is the fundamental unit of market data used by every detector
    and the trading engine.  Candles are immutable value objects —
    two candles with the same fields are considered equal.

    Attributes:
        timestamp:  UTC datetime of the candle open.
        open:       Opening price.
        high:       Highest price during the period.
        low:        Lowest price during the period.
        close:      Closing price.
        volume:     Traded volume during the period.
        symbol:     Trading pair (e.g. 'BTCUSDT').
        timeframe:  Candle period (e.g. '1h', '5m').
    """

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str = "BTCUSDT"
    timeframe: str = "1h"

    def __post_init__(self) -> None:
        if self.high < self.low:
            raise ValueError(
                f"Candle invariant violated: high ({self.high}) < low ({self.low})"
            )
        if self.volume < 0:
            raise ValueError(
                f"Candle invariant violated: volume ({self.volume}) is negative"
            )

    @property
    def body_size(self) -> float:
        """Absolute size of the candle body (|close − open|)."""
        return abs(self.close - self.open)

    @property
    def range_size(self) -> float:
        """Full range of the candle (high − low)."""
        return self.high - self.low

    @property
    def is_bullish(self) -> bool:
        """True if close > open."""
        return self.close > self.open

    @property
    def body_ratio(self) -> float:
        """Ratio of body to full range. 0.0 if range is zero (doji)."""
        if self.range_size == 0:
            return 0.0
        return self.body_size / self.range_size


@dataclass(frozen=True, slots=True)
class DetectorVerdict:
    """
    The output of a single detector in the Triple Coincidence system.

    Each detector (AccumulationZone, Trend, KeyCandle) produces a verdict
    with a boolean detection flag and a confidence score.

    Attributes:
        detector_name:  Canonical name of the detector.
        detected:       Whether the detector found its pattern.
        confidence:     Confidence score in [0.0, 1.0].
        metadata:       Optional detector-specific context (e.g. R² for trend).
    """

    detector_name: str
    detected: bool
    confidence: float
    metadata: Optional[dict[str, Any]] = None

    def __post_init__(self) -> None:
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"DetectorVerdict confidence must be in [0, 1], "
                f"got {self.confidence}"
            )


@dataclass(frozen=True, slots=True)
class TripleCoincidenceResult:
    """
    The fused result of all 3 detectors.

    A signal is emitted only when all three detectors agree (all detected=True).
    The combined confidence is the minimum of individual confidences —
    the chain is only as strong as its weakest link.

    Attributes:
        accumulation: Verdict from the AccumulationZoneDetector.
        trend:        Verdict from the TrendDetector.
        key_candle:   Verdict from the KeyCandleDetector.
        timestamp:    When the fusion was computed.
    """

    accumulation: DetectorVerdict
    trend: DetectorVerdict
    key_candle: DetectorVerdict
    timestamp: datetime

    @property
    def is_triple_match(self) -> bool:
        """True if all three detectors fired."""
        return (
            self.accumulation.detected
            and self.trend.detected
            and self.key_candle.detected
        )

    @property
    def combined_confidence(self) -> float:
        """Minimum confidence across detectors (weakest link)."""
        return min(
            self.accumulation.confidence,
            self.trend.confidence,
            self.key_candle.confidence,
        )


@dataclass(frozen=True, slots=True)
class Signal:
    """
    A detected trading signal — the output of the Signal Detection context.

    A Signal is only created when TripleCoincidenceResult.is_triple_match is
    True.  It enriches the raw detection with direction, price context,
    and a unique identifier.

    Attributes:
        signal_id:    Unique identifier (format: SIG_<timestamp>_<hash>).
        direction:    LONG or SHORT.
        entry_price:  Suggested entry price (typically candle close).
        atr_value:    Current ATR value for barrier calculation.
        confidence:   Combined confidence from Triple Coincidence.
        source_candle: The candle that triggered the signal.
        triple_result: Full Triple Coincidence breakdown.
        created_at:   When the signal was created.
    """

    signal_id: str
    direction: SignalDirection
    entry_price: float
    atr_value: float
    confidence: float
    source_candle: Candle
    triple_result: TripleCoincidenceResult
    created_at: datetime

    def __post_init__(self) -> None:
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"Signal confidence must be in [0, 1], got {self.confidence}"
            )
        if self.atr_value <= 0:
            raise ValueError(
                f"Signal ATR must be positive, got {self.atr_value}"
            )
        if self.entry_price <= 0:
            raise ValueError(
                f"Signal entry_price must be positive, got {self.entry_price}"
            )
