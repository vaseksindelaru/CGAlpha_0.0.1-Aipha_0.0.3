"""
CGAlpha v3 — Promotion Validator (Sección P3.3)
===============================================
Valida formalmente los criterios de promoción de Labs a Producción.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from cgalpha_v3.application.experiment_runner import ExperimentResult
from cgalpha_v3.risk.health_monitor import HealthMonitor, HealthStatus


class PromotionStatus(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING = "pending"


@dataclass
class PromotionReport:
    status: PromotionStatus
    experiment_id: str
    overall_score: float
    checks: dict[str, bool] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)


class PromotionValidator:
    def __init__(self, thresholds: dict[str, float] | None = None) -> None:
        self.thresholds = thresholds or {
            "min_sharpe_oos": 0.8,
            "max_drawdown_oos": 15.0,
            "min_calmar_oos": 1.5,
            "min_profit_factor_oos": 1.3,
        }

    def validate_experiment(self, result: ExperimentResult, health: dict[str, Any]) -> PromotionReport:
        """
        Realiza el check formal de P3.3 sobre un experimento completado.
        """
        metrics = result.metrics
        checks = {}
        reasons = []

        # 1. Sharpe OOS Check
        sharpe = metrics.get("sharpe_ratio_oos", 0.0)
        checks["sharpe_oos"] = sharpe >= self.thresholds["min_sharpe_oos"]
        if not checks["sharpe_oos"]:
            reasons.append(f"Sharpe Ratio OOS insuficiente: {sharpe:.2f} (requerido >= {self.thresholds['min_sharpe_oos']})")

        # 2. Drawdown OOS Check
        dd = metrics.get("max_drawdown_oos", 100.0)
        checks["drawdown_oos"] = dd <= self.thresholds["max_drawdown_oos"]
        if not checks["drawdown_oos"]:
            reasons.append(f"Max Drawdown OOS excesivo: {dd:.2f}% (requerido <= {self.thresholds['max_drawdown_oos']}%)")

        # 3. Profit Factor OOS Check
        pf = metrics.get("profit_factor_oos", 0.0)
        checks["profit_factor_oos"] = pf >= self.thresholds["min_profit_factor_oos"]
        if not checks["profit_factor_oos"]:
            reasons.append(f"Profit Factor OOS insuficiente: {pf:.2f} (requerido >= {self.thresholds['min_profit_factor_oos']})")

        # 4. Leakage Verification
        checks["no_leakage"] = result.no_leakage_checked
        if not checks["no_leakage"]:
            reasons.append("El experimento no pasó la verificación obligatoria de no-leakage.")

        # 5. System Health Check (vía HealthMonitor snapshot)
        is_healthy = health.get("status") == HealthStatus.HEALTHY.value
        checks["system_healthy"] = is_healthy
        if not is_healthy:
            reasons.append(f"Estado del sistema no apto para deploy: {health.get('status')}")

        # Decisión final
        passed_all = all(checks.values())
        status = PromotionStatus.APPROVED if passed_all else PromotionStatus.REJECTED
        
        # Scoring simple
        score = sum(1 for v in checks.values() if v) / len(checks)

        return PromotionReport(
            status=status,
            experiment_id=result.experiment_id,
            overall_score=round(score, 4),
            checks=checks,
            reasons=reasons
        )
