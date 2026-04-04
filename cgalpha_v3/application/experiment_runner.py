"""
CGAlpha v3 — Experiment Runner (Sección E)
==========================================
Ejecuta experimentos con:
  - fricciones por defecto
  - walk-forward >=3 ventanas no solapadas
  - chequeo obligatorio de no-leakage OOS
"""
from __future__ import annotations

import math
import statistics
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from cgalpha_v3.application.change_proposer import FrictionDefaults
from cgalpha_v3.data_quality.gates import check_oos_leakage
from cgalpha_v3.domain.models.signal import ApproachType, Proposal
from cgalpha_v3.trading.labelers import classify_approach_type


@dataclass(frozen=True)
class WalkForwardWindow:
    window_id: int
    train_start_ts: float
    train_end_ts: float
    validation_start_ts: float
    validation_end_ts: float
    oos_start_ts: float
    oos_end_ts: float
    train_rows: int
    validation_rows: int
    oos_rows: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "window_id": self.window_id,
            "train_start_ts": self.train_start_ts,
            "train_end_ts": self.train_end_ts,
            "validation_start_ts": self.validation_start_ts,
            "validation_end_ts": self.validation_end_ts,
            "oos_start_ts": self.oos_start_ts,
            "oos_end_ts": self.oos_end_ts,
            "train_rows": self.train_rows,
            "validation_rows": self.validation_rows,
            "oos_rows": self.oos_rows,
        }


@dataclass
class ExperimentResult:
    experiment_id: str
    proposal_id: str
    generated_at: datetime
    friction: FrictionDefaults
    walk_forward_windows: list[WalkForwardWindow]
    metrics: dict[str, float]
    window_metrics: list[dict[str, Any]]
    approach_type_histogram: dict[str, int]
    no_leakage_checked: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "proposal_id": self.proposal_id,
            "generated_at": self.generated_at.isoformat(),
            "friction": self.friction.as_dict(),
            "walk_forward_windows": [w.as_dict() for w in self.walk_forward_windows],
            "metrics": self.metrics,
            "window_metrics": self.window_metrics,
            "approach_type_histogram": self.approach_type_histogram,
            "no_leakage_checked": self.no_leakage_checked,
        }


class ExperimentRunner:
    """Orquesta split temporal, validación no-leakage y métricas netas."""

    def __init__(self, friction_defaults: FrictionDefaults | None = None) -> None:
        self.friction_defaults = friction_defaults or FrictionDefaults()

    def build_walk_forward_windows(
        self,
        rows: list[dict[str, Any]],
        windows: int = 3,
    ) -> list[WalkForwardWindow]:
        if windows < 3:
            raise ValueError("walk-forward requiere al menos 3 ventanas")
        if len(rows) < windows * 10:
            raise ValueError("insufficient_rows_for_walk_forward")

        rows_sorted = sorted(rows, key=lambda r: float(r["open_time"]))
        segment_size = len(rows_sorted) // windows
        if segment_size < 10:
            raise ValueError("insufficient_segment_size")

        wf: list[WalkForwardWindow] = []
        for idx in range(windows):
            start = idx * segment_size
            end = len(rows_sorted) if idx == windows - 1 else (idx + 1) * segment_size
            segment = rows_sorted[start:end]
            seg_n = len(segment)
            if seg_n < 10:
                raise ValueError("insufficient_rows_in_window")

            train_n = max(int(seg_n * 0.6), 1)
            val_n = max(int(seg_n * 0.2), 1)
            oos_n = seg_n - train_n - val_n
            if oos_n < 1:
                oos_n = 1
                if val_n > 1:
                    val_n -= 1
                else:
                    train_n = max(train_n - 1, 1)

            train = segment[:train_n]
            val = segment[train_n : train_n + val_n]
            oos = segment[train_n + val_n :]
            if not (train and val and oos):
                raise ValueError("invalid_temporal_split")

            wf.append(
                WalkForwardWindow(
                    window_id=idx + 1,
                    train_start_ts=float(train[0]["open_time"]),
                    train_end_ts=float(train[-1]["close_time"]),
                    validation_start_ts=float(val[0]["open_time"]),
                    validation_end_ts=float(val[-1]["close_time"]),
                    oos_start_ts=float(oos[0]["open_time"]),
                    oos_end_ts=float(oos[-1]["close_time"]),
                    train_rows=len(train),
                    validation_rows=len(val),
                    oos_rows=len(oos),
                )
            )
        return wf

    def run_experiment(
        self,
        proposal: Proposal,
        rows: list[dict[str, Any]],
        feature_timestamps: list[float] | None = None,
    ) -> ExperimentResult:
        """
        Ejecuta experimento con fricción y no-leakage.
        - feature_timestamps opcional: para simulaciones o tests de leakage.
        """
        windows = self.build_walk_forward_windows(rows, windows=3)
        rows_sorted = sorted(rows, key=lambda r: float(r["open_time"]))
        segment_size = len(rows_sorted) // len(windows)

        metrics_by_window: list[dict[str, Any]] = []
        aggregated_gross = 0.0
        aggregated_cost = 0.0
        aggregated_net = 0.0
        aggregated_sharpe = 0.0
        aggregated_mdd = 0.0
        aggregated_trades = 0
        aggregated_hist = self._empty_histogram()

        for wf in windows:
            idx = wf.window_id - 1
            start = idx * segment_size
            end = len(rows_sorted) if idx == len(windows) - 1 else (idx + 1) * segment_size
            segment = rows_sorted[start:end]
            train = segment[: wf.train_rows]
            val = segment[wf.train_rows : wf.train_rows + wf.validation_rows]
            oos = segment[wf.train_rows + wf.validation_rows :]

            if feature_timestamps is None:
                window_feature_ts = [float(r["open_time"]) for r in (train + val)]
            else:
                window_feature_ts = feature_timestamps

            # Integración E2E obligatoria de no-leakage
            check_oos_leakage(
                train_end_ts=wf.train_end_ts,
                oos_start_ts=wf.oos_start_ts,
                feature_timestamps=window_feature_ts,
            )

            oos_prices = [float(r["close"]) for r in oos]
            gross_return_pct = self._gross_return_pct(oos_prices)
            window_returns = self._returns_pct(oos_prices)
            trades = max(len(window_returns), 1)
            friction_cost_pct = trades * self._cost_per_trade_pct(self.friction_defaults)
            net_return_pct = gross_return_pct - friction_cost_pct
            sharpe_like = self._sharpe_like(net_return_pct, window_returns)
            max_dd_pct = self._max_drawdown_pct(oos_prices)
            window_hist = self._approach_type_histogram(oos)
            self._merge_hist(aggregated_hist, window_hist)

            metrics_by_window.append(
                {
                    "window_id": wf.window_id,
                    "gross_return_pct": round(gross_return_pct, 4),
                    "friction_cost_pct": round(friction_cost_pct, 4),
                    "net_return_pct": round(net_return_pct, 4),
                    "sharpe_like": round(sharpe_like, 4),
                    "max_drawdown_pct": round(max_dd_pct, 4),
                    "trades": trades,
                    "oos_rows": len(oos_prices),
                    "approach_type_histogram": window_hist,
                }
            )

            aggregated_gross += gross_return_pct
            aggregated_cost += friction_cost_pct
            aggregated_net += net_return_pct
            aggregated_sharpe += sharpe_like
            aggregated_mdd += max_dd_pct
            aggregated_trades += trades

        total_windows = len(windows)
        final_metrics = {
            "gross_return_pct": round(aggregated_gross / total_windows, 4),
            "friction_cost_pct": round(aggregated_cost / total_windows, 4),
            "net_return_pct": round(aggregated_net / total_windows, 4),
            "sharpe_like": round(aggregated_sharpe / total_windows, 4),
            "max_drawdown_pct": round(aggregated_mdd / total_windows, 4),
            "trades": float(aggregated_trades),
            "walk_forward_windows": float(total_windows),
        }

        return ExperimentResult(
            experiment_id=f"exp-{uuid.uuid4().hex[:8]}",
            proposal_id=proposal.proposal_id,
            generated_at=datetime.now(timezone.utc),
            friction=self.friction_defaults,
            walk_forward_windows=windows,
            metrics=final_metrics,
            window_metrics=metrics_by_window,
            approach_type_histogram=aggregated_hist,
            no_leakage_checked=True,
        )

    @staticmethod
    def _returns_pct(prices: list[float]) -> list[float]:
        if len(prices) < 2:
            return []
        returns: list[float] = []
        for idx in range(1, len(prices)):
            prev = prices[idx - 1]
            curr = prices[idx]
            if prev == 0:
                continue
            returns.append(((curr - prev) / prev) * 100.0)
        return returns

    def _cost_per_trade_pct(self, friction: FrictionDefaults) -> float:
        # slippage_bps a porcentaje: 2 bps => 0.02%
        slippage_pct = friction.slippage_bps / 100.0
        latency_pct = friction.latency_ms / 100000.0
        return friction.fee_taker_pct + friction.fee_maker_pct + slippage_pct + latency_pct

    @staticmethod
    def _gross_return_pct(prices: list[float]) -> float:
        if len(prices) < 2 or prices[0] == 0:
            return 0.0
        return ((prices[-1] - prices[0]) / prices[0]) * 100.0

    @staticmethod
    def _sharpe_like(net_return_pct: float, returns_pct: list[float]) -> float:
        if not returns_pct:
            return 0.0
        std = statistics.pstdev(returns_pct)
        if std == 0:
            return 0.0
        # Ajuste simple por longitud para mantener escala estable.
        return (net_return_pct / std) / math.sqrt(len(returns_pct))

    @staticmethod
    def _max_drawdown_pct(prices: list[float]) -> float:
        if not prices:
            return 0.0
        peak = prices[0]
        max_dd = 0.0
        for price in prices:
            if price > peak:
                peak = price
            if peak == 0:
                continue
            dd = ((peak - price) / peak) * 100.0
            if dd > max_dd:
                max_dd = dd
        return max_dd

    @staticmethod
    def _empty_histogram() -> dict[str, int]:
        return {a.value: 0 for a in ApproachType}

    def _approach_type_histogram(self, rows: list[dict[str, Any]]) -> dict[str, int]:
        hist = self._empty_histogram()
        if len(rows) < 2:
            return hist

        for idx, row in enumerate(rows):
            prev_close = None
            if idx > 0:
                prev_close = float(rows[idx - 1].get("close", rows[idx - 1].get("open", 0.0)))
            close_price = float(row.get("close", row.get("open", 0.0)))
            open_price = float(row.get("open", close_price))
            high_price = float(row.get("high", max(open_price, close_price)))
            low_price = float(row.get("low", min(open_price, close_price)))
            zone_low = close_price * 0.999
            zone_high = close_price * 1.001
            future = [float(x.get("close", close_price)) for x in rows[idx + 1 : idx + 4]]

            approach = classify_approach_type(
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=close_price,
                zone_low=zone_low,
                zone_high=zone_high,
                prev_close=prev_close,
                future_closes=future,
            )
            hist[approach.value] += 1
        return hist

    @staticmethod
    def _merge_hist(target: dict[str, int], source: dict[str, int]) -> None:
        for key, value in source.items():
            target[key] = target.get(key, 0) + value
