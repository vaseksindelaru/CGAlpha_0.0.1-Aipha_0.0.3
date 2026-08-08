"""
CGAlpha v3 — Health Monitor & SLOs (Sección P3.5)
================================================
Monitoriza objetivos de nivel de servicio (SLOs) y emite alertas runtime.
"""
from __future__ import annotations

import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"


@dataclass
class SLOEntry:
    slo_id: str
    description: str
    target: float
    unit: str
    condition: str  # "<", ">", "<=", ">="
    values: list[float] = field(default_factory=list)

    def current_value(self) -> float:
        if not self.values:
            return 0.0
        return statistics.mean(self.values)

    def is_breached(self) -> bool:
        curr = self.current_value()
        if self.condition == "<":
            return curr >= self.target
        if self.condition == ">":
            return curr <= self.target
        if self.condition == "<=":
            return curr > self.target
        if self.condition == ">=":
            return curr < self.target
        return False


class HealthMonitor:
    def __init__(self) -> None:
        self.slos: dict[str, SLOEntry] = {
            "exp_latency": SLOEntry("exp_latency", "Latencia de experimento (s)", 60.0, "s", "<"),
            "leakage_rate": SLOEntry("leakage_rate", "Tasa de leakage temporal", 0.05, "ratio", "<"),
            "dq_freshness": SLOEntry("dq_freshness", "Freshness de datos (m)", 15.0, "m", "<"),
            "rollback_sla": SLOEntry("rollback_sla", "Tiempo de rollback", 60.0, "s", "<"),
        }
        self.alerts: list[dict[str, Any]] = []

    @property
    def total_samples(self) -> int:
        """Devuelve el conteo total de muestras registradas en todos los SLOs."""
        return sum(len(slo.values) for slo in self.slos.values())

    def record_metric(self, slo_id: str, value: float) -> None:
        if slo_id in self.slos:
            self.slos[slo_id].values.append(value)
            if len(self.slos[slo_id].values) > 100:
                self.slos[slo_id].values.pop(0)

    def status_snapshot(self) -> dict[str, Any]:
        snapshot = {}
        overall_status = HealthStatus.HEALTHY
        breaches = 0

        for slo_id, slo in self.slos.items():
            breached = slo.is_breached()
            if breached:
                breaches += 1
            snapshot[slo_id] = {
                "description": slo.description,
                "current": round(slo.current_value(), 4),
                "target": slo.target,
                "unit": slo.unit,
                "breached": breached,
            }

        if breaches > 0:
            overall_status = HealthStatus.DEGRADED
        if breaches >= 3:
            overall_status = HealthStatus.CRITICAL

        return {
            "status": overall_status.value,
            "breaches": breaches,
            "slos": snapshot,
            "ts": datetime.now(timezone.utc).isoformat(),
        }

    def check_for_alerts(self) -> list[str]:
        new_alerts = []
        for slo_id, slo in self.slos.items():
            if slo.is_breached():
                new_alerts.append(f"SLO_BREACH: {slo.description} excedido ({slo.current_value():.2f} {slo.unit})")
        return new_alerts
