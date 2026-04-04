"""
CGAlpha v3 — Approach Type Labeler
==================================
Implementa schema y clasificación obligatoria de `approach_type` por muestra.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from cgalpha_v3.domain.models.signal import ApproachType


@dataclass(frozen=True)
class ApproachLabel:
    """
    Schema operativo de label para taxonomía de acercamientos (P2.5/P2.6).
    """

    sample_id: str
    generated_at: datetime
    approach_type: ApproachType
    zone_low: float
    zone_high: float
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    prev_close: float | None
    source: str = "v3_labeler"

    def as_dict(self) -> dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "generated_at": self.generated_at.isoformat(),
            "approach_type": self.approach_type.value,
            "zone_low": self.zone_low,
            "zone_high": self.zone_high,
            "open_price": self.open_price,
            "high_price": self.high_price,
            "low_price": self.low_price,
            "close_price": self.close_price,
            "prev_close": self.prev_close,
            "source": self.source,
        }


def classify_approach_type(
    *,
    open_price: float,
    high_price: float,
    low_price: float,
    close_price: float,
    zone_low: float,
    zone_high: float,
    prev_close: float | None = None,
    future_closes: list[float] | None = None,
) -> ApproachType:
    """
    Clasifica una muestra en la taxonomía:
    TOUCH / RETEST / REJECTION / BREAKOUT / OVERSHOOT / FAKE_BREAK.
    """
    if zone_low > zone_high:
        raise ValueError("zone_low must be <= zone_high")
    if high_price < low_price:
        raise ValueError("high_price must be >= low_price")

    future = future_closes or []
    touched_zone = high_price >= zone_low and low_price <= zone_high
    close_above = close_price > zone_high
    close_below = close_price < zone_low
    close_outside = close_above or close_below
    close_inside = zone_low <= close_price <= zone_high
    prev_outside = prev_close is not None and (prev_close > zone_high or prev_close < zone_low)

    # BREAKOUT/OVERSHOOT/FAKE_BREAK
    if close_outside:
        if future:
            returned_into_zone = any(zone_low <= c <= zone_high for c in future)
            if returned_into_zone:
                return ApproachType.FAKE_BREAK
            if close_above and all(c > zone_high for c in future):
                return ApproachType.OVERSHOOT
            if close_below and all(c < zone_low for c in future):
                return ApproachType.OVERSHOOT
        return ApproachType.BREAKOUT

    if not touched_zone:
        # Si no toca zona ni rompe, se considera aproximación suave.
        return ApproachType.TOUCH

    # REJECTION
    candle_range = max(high_price - low_price, 1e-9)
    upper_wick = high_price - max(open_price, close_price)
    lower_wick = min(open_price, close_price) - low_price
    wick_ratio = max(upper_wick, lower_wick) / candle_range
    if wick_ratio >= 0.60:
        return ApproachType.REJECTION

    # RETEST
    if close_inside and prev_outside:
        return ApproachType.RETEST

    return ApproachType.TOUCH


def label_approach_sample(
    sample: dict[str, Any],
    *,
    sample_id: str,
    generated_at: datetime | None = None,
    source: str = "v3_labeler",
) -> ApproachLabel:
    """
    Genera label tipado y trazable para una muestra OHLC + zona.
    """
    label = classify_approach_type(
        open_price=float(sample["open_price"]),
        high_price=float(sample["high_price"]),
        low_price=float(sample["low_price"]),
        close_price=float(sample["close_price"]),
        zone_low=float(sample["zone_low"]),
        zone_high=float(sample["zone_high"]),
        prev_close=float(sample["prev_close"]) if sample.get("prev_close") is not None else None,
        future_closes=[float(x) for x in sample.get("future_closes", [])],
    )
    return ApproachLabel(
        sample_id=sample_id,
        generated_at=generated_at or datetime.now(timezone.utc),
        approach_type=label,
        zone_low=float(sample["zone_low"]),
        zone_high=float(sample["zone_high"]),
        open_price=float(sample["open_price"]),
        high_price=float(sample["high_price"]),
        low_price=float(sample["low_price"]),
        close_price=float(sample["close_price"]),
        prev_close=float(sample["prev_close"]) if sample.get("prev_close") is not None else None,
        source=source,
    )


def label_approach_samples(samples: list[dict[str, Any]]) -> list[ApproachLabel]:
    """
    Clasifica un lote de muestras. `approach_type` obligatorio por muestra.
    """
    labels: list[ApproachLabel] = []
    for idx, sample in enumerate(samples):
        sid = str(sample.get("sample_id") or f"sample-{idx+1:05d}")
        labels.append(label_approach_sample(sample, sample_id=sid))
    return labels

