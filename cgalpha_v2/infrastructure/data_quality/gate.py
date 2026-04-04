"""
CGAlpha v3 — Data Quality Gate
Módulo de validación de klines antes de alimentar el pipeline de señales.

Política: datos no validados NO pueden entrar al pipeline.
Cualquier fallo lanza DataQualityError con evidencia del error.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class DataQualityError(Exception):
    """Excepción lanzada cuando un kline no supera el Data Quality Gate."""

    def __init__(self, message: str, evidence: dict[str, Any]) -> None:
        super().__init__(message)
        self.evidence = evidence


@dataclass
class KlineValidationResult:
    """Resultado de validación de un conjunto de klines."""

    passed: int = 0
    failed: int = 0
    errors: list[dict[str, Any]] = field(default_factory=list)
    status: str = "unknown"  # "ok" | "failed" | "empty"

    @property
    def is_clean(self) -> bool:
        return self.failed == 0 and self.passed > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "status": self.status,
            "is_clean": self.is_clean,
        }


class DataQualityGate:
    """
    Gate de calidad de datos para klines OHLCV.

    Validaciones implementadas:
    - high >= low
    - open in [low, high]
    - close in [low, high]
    - volume > 0
    - timestamp monotónico creciente
    - sin timestamps duplicados
    - sin gaps temporales mayores al umbral configurado

    Usage:
        gate = DataQualityGate(max_gap_candles=3)
        result = gate.validate_batch(klines)
        if not result.is_clean:
            raise DataQualityError("Batch failed", result.to_dict())
    """

    def __init__(
        self,
        max_gap_candles: int = 5,
        allow_zero_volume: bool = False,
        strict_ohlcv: bool = True,
    ) -> None:
        self.max_gap_candles = max_gap_candles
        self.allow_zero_volume = allow_zero_volume
        self.strict_ohlcv = strict_ohlcv
        self._last_validation: KlineValidationResult | None = None

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def validate_single(self, kline: dict[str, Any]) -> None:
        """
        Valida un único kline. Lanza DataQualityError si falla alguna regla.

        Args:
            kline: dict con keys: open, high, low, close, volume, timestamp

        Raises:
            DataQualityError: si el kline no pasa alguna validación
        """
        errors = self._check_single(kline)
        if errors:
            raise DataQualityError(
                f"Kline failed data quality gate: {errors[0]['rule']}",
                evidence={"kline": kline, "errors": errors},
            )

    def validate_batch(self, klines: list[dict[str, Any]]) -> KlineValidationResult:
        """
        Valida una lista de klines y devuelve un resultado agregado.
        No lanza excepción; el caller decide si es bloqueante.

        Args:
            klines: lista de dicts OHLCV

        Returns:
            KlineValidationResult con estadísticas y errores
        """
        result = KlineValidationResult()

        if not klines:
            result.status = "empty"
            self._last_validation = result
            return result

        timestamps: list[Any] = []
        prev_ts: Any = None

        for i, kline in enumerate(klines):
            errors = self._check_single(kline)

            # Validación de temporalidad
            ts = kline.get("timestamp")
            if ts is not None:
                if prev_ts is not None and ts <= prev_ts:
                    errors.append({
                        "rule": "timestamp_monotonic",
                        "detail": f"Kline[{i}] ts={ts} <= prev ts={prev_ts}",
                    })
                if ts in timestamps:
                    errors.append({
                        "rule": "timestamp_duplicate",
                        "detail": f"Kline[{i}] ts={ts} ya existe en el batch",
                    })
                timestamps.append(ts)
                prev_ts = ts

            if errors:
                result.failed += 1
                result.errors.append({"index": i, "kline_ts": ts, "errors": errors})
            else:
                result.passed += 1

        # Check gaps
        gap_errors = self._check_gaps(klines)
        if gap_errors:
            result.errors.extend(gap_errors)

        result.status = "ok" if result.is_clean else "failed"
        self._last_validation = result

        if result.is_clean:
            logger.debug(
                "Data Quality Gate PASSED — %d klines validados", result.passed
            )
        else:
            logger.warning(
                "Data Quality Gate FAILED — %d/%d klines con errores",
                result.failed,
                result.passed + result.failed,
            )

        return result

    def validate_or_raise(self, klines: list[dict[str, Any]]) -> KlineValidationResult:
        """
        Valida un batch; lanza DataQualityError si algún kline falla.

        Returns:
            KlineValidationResult si todo es correcto

        Raises:
            DataQualityError: si algún kline no pasa
        """
        result = self.validate_batch(klines)
        if not result.is_clean:
            raise DataQualityError(
                f"Batch de {result.failed} klines falló el Data Quality Gate",
                evidence=result.to_dict(),
            )
        return result

    def get_gui_status(self) -> dict[str, Any]:
        """Retorna estado para el panel Market Live de la GUI."""
        if self._last_validation is None:
            return {"status": "no_data", "label": "⚪ Sin validación", "details": {}}

        v = self._last_validation
        if v.is_clean:
            label = "✅ valid"
        elif v.status == "empty":
            label = "⚪ Sin datos"
        else:
            label = "❌ corrupted"

        return {
            "status": v.status,
            "label": label,
            "passed": v.passed,
            "failed": v.failed,
            "error_count": len(v.errors),
            "details": v.errors[:5],  # máximo 5 para GUI
        }

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    def _check_single(self, kline: dict[str, Any]) -> list[dict[str, Any]]:
        errors: list[dict[str, Any]] = []
        o = kline.get("open")
        h = kline.get("high")
        lo = kline.get("low")
        c = kline.get("close")
        v = kline.get("volume")

        # Todos los campos requeridos presentes
        for name, val in [("open", o), ("high", h), ("low", lo), ("close", c), ("volume", v)]:
            if val is None:
                errors.append({"rule": "missing_field", "detail": f"Campo '{name}' ausente"})

        if errors:
            return errors  # sin datos no podemos validar el resto

        # high >= low
        if h < lo:  # type: ignore[operator]
            errors.append({
                "rule": "high_lt_low",
                "detail": f"high={h} < low={lo}",
            })

        # open in [low, high]
        if self.strict_ohlcv and not (lo <= o <= h):  # type: ignore[operator]
            errors.append({
                "rule": "open_out_of_range",
                "detail": f"open={o} fuera de [{lo}, {h}]",
            })

        # close in [low, high]
        if self.strict_ohlcv and not (lo <= c <= h):  # type: ignore[operator]
            errors.append({
                "rule": "close_out_of_range",
                "detail": f"close={c} fuera de [{lo}, {h}]",
            })

        # volume >= 0 (o > 0 si strict)
        if not self.allow_zero_volume and v <= 0:  # type: ignore[operator]
            errors.append({
                "rule": "zero_or_negative_volume",
                "detail": f"volume={v}",
            })

        return errors

    def _check_gaps(self, klines: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Detecta gaps temporales mayores a max_gap_candles intervalos."""
        errors: list[dict[str, Any]] = []
        timestamps = [k.get("timestamp") for k in klines if k.get("timestamp") is not None]

        if len(timestamps) < 2:
            return errors

        # Estimar intervalo modal (el más frecuente)
        diffs = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]
        if not diffs:
            return errors

        from collections import Counter
        modal_interval = Counter(diffs).most_common(1)[0][0]

        for i, diff in enumerate(diffs):
            if diff > modal_interval * self.max_gap_candles:
                errors.append({
                    "rule": "temporal_gap",
                    "detail": (
                        f"Gap de {diff} entre ts[{i}]={timestamps[i]} y "
                        f"ts[{i+1}]={timestamps[i+1]}. "
                        f"Esperado ≤{modal_interval * self.max_gap_candles}"
                    ),
                    "index": i,
                })

        return errors
