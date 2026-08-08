"""
CGAlpha v3 — Data Quality Gates (Sección F / K P0.3)
======================================================
Valida klines de Binance antes de usarlos en señales o entrenamiento.

Gates activos:
  DQ-1: frescura del dato (stale si > N segundos sin actualizar)
  DQ-2: integridad del schema (campos requeridos presentes y con tipos correctos)
  DQ-3: consistencia temporal (sin gaps, sin orden invertido)
  DQ-4: valores outlier (precio/volumen fuera de rango razonable)
  DQ-5: no-leakage (OOS no contaminado por datos de entrenamiento)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

log = logging.getLogger(__name__)

# Campos obligatorios en un kline de Binance
REQUIRED_KLINE_FIELDS = {
    "open_time", "open", "high", "low", "close", "volume", "close_time",
}


@dataclass
class DQResult:
    """Resultado de un Data Quality Gate."""
    gate:     str
    passed:   bool
    message:  str
    severity: str = "error"   # "error" | "warning"


@dataclass
class DQReport:
    """Reporte completo de Data Quality para un lote de klines."""
    checked_at:  datetime
    symbol:      str
    interval:    str
    total_rows:  int
    results:     list[DQResult] = field(default_factory=list)
    status:      str = "valid"   # "valid" | "stale" | "corrupted"

    def add(self, result: DQResult) -> None:
        self.results.append(result)
        if not result.passed:
            if result.severity == "error":
                self.status = "corrupted"
            elif self.status == "valid":
                self.status = "stale"

    @property
    def passed(self) -> bool:
        return all(r.passed or r.severity == "warning" for r in self.results)

    @property
    def errors(self) -> list[DQResult]:
        return [r for r in self.results if not r.passed and r.severity == "error"]

    @property
    def warnings(self) -> list[DQResult]:
        return [r for r in self.results if not r.passed and r.severity == "warning"]


class DataQualityGate:
    """
    Ejecuta todos los DQ gates sobre un lote de klines.
    Uso:
        gate = DataQualityGate(stale_threshold_s=60)
        report = gate.run(klines, symbol="BTCUSDT", interval="5m")
        if not report.passed:
            # suspender señales → alerta P1
    """

    def __init__(
        self,
        stale_threshold_s: float = 60.0,
        max_gap_multiplier: float = 3.0,
        outlier_sigma: float = 5.0,
    ) -> None:
        self.stale_threshold_s  = stale_threshold_s
        self.max_gap_multiplier = max_gap_multiplier
        self.outlier_sigma      = outlier_sigma

    def run(
        self,
        klines: list[dict[str, Any]],
        symbol: str,
        interval: str,
        last_update_ts: datetime | None = None,
    ) -> DQReport:
        report = DQReport(
            checked_at=datetime.now(timezone.utc),
            symbol=symbol,
            interval=interval,
            total_rows=len(klines),
        )

        report.add(self._gate_schema(klines))
        report.add(self._gate_freshness(last_update_ts))
        report.add(self._gate_temporal_order(klines))

        if klines:
            report.add(self._gate_gaps(klines))
            report.add(self._gate_outliers(klines))

        status_icon = "✅" if report.passed else ("⚠️" if report.status == "stale" else "❌")
        log.info(
            f"[DQ] {status_icon} {symbol}/{interval} "
            f"rows={len(klines)} status={report.status} "
            f"errors={len(report.errors)} warnings={len(report.warnings)}"
        )
        return report

    # ── GATE 1: Schema ────────────────────────────
    def _gate_schema(self, klines: list[dict[str, Any]]) -> DQResult:
        if not klines:
            return DQResult("DQ-1-schema", False, "Dataset vacío", severity="error")
        missing_overall: set[str] = set()
        for row in klines:
            missing = REQUIRED_KLINE_FIELDS - set(row.keys())
            missing_overall |= missing
        if missing_overall:
            return DQResult(
                "DQ-1-schema", False,
                f"Campos faltantes en klines: {missing_overall}", severity="error",
            )
        return DQResult("DQ-1-schema", True, "Schema OK")

    # ── GATE 2: Freshness ─────────────────────────
    def _gate_freshness(self, last_update_ts: datetime | None) -> DQResult:
        if last_update_ts is None:
            return DQResult(
                "DQ-2-freshness", False,
                "Sin timestamp de última actualización", severity="warning",
            )
        age_s = (datetime.now(timezone.utc) - last_update_ts).total_seconds()
        if age_s > self.stale_threshold_s:
            return DQResult(
                "DQ-2-freshness", False,
                f"Dato stale: {age_s:.0f}s > threshold {self.stale_threshold_s}s",
                severity="warning",
            )
        return DQResult("DQ-2-freshness", True, f"Fresco: {age_s:.1f}s")

    # ── GATE 3: Temporal order ────────────────────
    def _gate_temporal_order(self, klines: list[dict[str, Any]]) -> DQResult:
        if len(klines) < 2:
            return DQResult("DQ-3-order", True, "Orden OK (1 fila)")
        times = [float(k["open_time"]) for k in klines]
        for i in range(1, len(times)):
            if times[i] <= times[i - 1]:
                return DQResult(
                    "DQ-3-order", False,
                    f"Orden temporal invertido en índice {i}: {times[i]} <= {times[i-1]}",
                    severity="error",
                )
        return DQResult("DQ-3-order", True, "Orden temporal correcto")

    # ── GATE 4: Gaps ──────────────────────────────
    def _gate_gaps(self, klines: list[dict[str, Any]]) -> DQResult:
        if len(klines) < 2:
            return DQResult("DQ-4-gaps", True, "Sin gaps (1 fila)")
        times   = [float(k["open_time"]) for k in klines]
        diffs   = [times[i + 1] - times[i] for i in range(len(times) - 1)]
        expected = min(diffs)
        max_gap  = self.max_gap_multiplier * expected
        gaps = [(i, d) for i, d in enumerate(diffs) if d > max_gap]
        if gaps:
            return DQResult(
                "DQ-4-gaps", False,
                f"{len(gaps)} gap(s) detectado(s) (max: {max(d for _, d in gaps):.0f}ms, threshold: {max_gap:.0f}ms)",
                severity="warning",
            )
        return DQResult("DQ-4-gaps", True, "Sin gaps temporales")

    # ── GATE 5: Outliers ──────────────────────────
    def _gate_outliers(self, klines: list[dict[str, Any]]) -> DQResult:
        try:
            closes = [float(k["close"]) for k in klines]
            if len(closes) < 4:
                return DQResult("DQ-5-outliers", True, "Insuficientes datos para outlier check")
            mean = sum(closes) / len(closes)
            variance = sum((c - mean) ** 2 for c in closes) / len(closes)
            std  = variance ** 0.5
            if std == 0:
                return DQResult("DQ-5-outliers", True, "Sin varianza — no se aplica outlier check")
            outliers = [c for c in closes if abs(c - mean) > self.outlier_sigma * std]
            if outliers:
                return DQResult(
                    "DQ-5-outliers", False,
                    f"{len(outliers)} outlier(s) detectado(s) en close (>{self.outlier_sigma}σ)",
                    severity="warning",
                )
        except (KeyError, ValueError, TypeError) as exc:
            return DQResult("DQ-5-outliers", False, f"Error en outlier check: {exc}", severity="warning")
        return DQResult("DQ-5-outliers", True, "Sin outliers")


class TemporalLeakageError(Exception):
    """
    Violación del protocolo de no-leakage (Sección E).
    Se lanza cuando datos OOS son detectados en el pipeline de entrenamiento.
    """
    pass


def check_oos_leakage(
    train_end_ts: float,
    oos_start_ts: float,
    feature_timestamps: list[float],
) -> None:
    """
    Verifica que ningún timestamp de feature engineering caiga en zona OOS.
    Lanza TemporalLeakageError si detecta contaminación.

    Args:
        train_end_ts: timestamp de fin del split de entrenamiento
        oos_start_ts: timestamp de inicio del split OOS
        feature_timestamps: timestamps de los features generados
    """
    contaminated = [t for t in feature_timestamps if t >= oos_start_ts]
    if contaminated:
        raise TemporalLeakageError(
            f"[DQ] TemporalLeakageError: {len(contaminated)} feature(s) con timestamp "
            f">= OOS start ({oos_start_ts}). Violación del protocolo OOS (Sección E)."
        )
    log.info(f"[DQ] No-leakage: {len(feature_timestamps)} features verificados — 0 en zona OOS")
