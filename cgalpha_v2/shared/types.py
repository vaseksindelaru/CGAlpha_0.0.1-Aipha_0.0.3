"""
cgalpha.shared.types — Domain type aliases.

Centralizes type aliases used throughout the CGAlpha domain.
These are intentionally simple wrappers (NewType) that:
- Provide semantic meaning to primitive types
- Enable static analysis (mypy) to catch mix-ups
- Serve as living documentation of the domain vocabulary

Usage:
    from cgalpha_v2.shared.types import SignalId, TradeId, Timeframe

    def process_signal(signal_id: SignalId) -> None:
        ...
"""

from __future__ import annotations

from typing import NewType

# ─── Identifiers ──────────────────────────────────────────────────────────────

SignalId = NewType("SignalId", str)
"""Unique identifier for a detected trading signal."""

TradeId = NewType("TradeId", str)
"""Unique identifier for a trade record in the bridge."""

ProposalId = NewType("ProposalId", str)
"""Unique identifier for a change proposal."""

CycleId = NewType("CycleId", str)
"""Unique identifier for an orchestration cycle."""

ModelId = NewType("ModelId", str)
"""Unique identifier for a serialized ML model."""


# ─── Domain scalars ───────────────────────────────────────────────────────────

Timeframe = NewType("Timeframe", str)
"""
Candle timeframe string following exchange convention.

Examples: '1m', '5m', '15m', '1h', '4h', '1d'
"""

Symbol = NewType("Symbol", str)
"""
Trading pair symbol.

Examples: 'BTCUSDT', 'ETHUSDT'
"""

Confidence = NewType("Confidence", float)
"""
A probability score in [0.0, 1.0].

Used for ML predictions and parser confidence.
"""

ATRMultiple = NewType("ATRMultiple", float)
"""
A price distance expressed as a multiple of the Average True Range.

Positive values = favorable excursion, negative = adverse.
"""
