"""
CGAlpha v3 — Change Proposer (Sección E)
========================================
Genera propuestas con fricciones por defecto activas y plan mínimo de validación.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cgalpha_v3.domain.models.signal import ApproachType, Proposal, RiskAssessment


@dataclass(frozen=True)
class FrictionDefaults:
    """
    Fricciones por defecto exigidas por prompt maestro.
    Las métricas y backtests se reportan netas post-fricción.
    """
    fee_taker_pct: float = 0.05
    fee_maker_pct: float = 0.02
    slippage_bps: float = 2.0
    latency_ms: float = 100.0

    def as_dict(self) -> dict[str, float]:
        return {
            "fee_taker_pct": self.fee_taker_pct,
            "fee_maker_pct": self.fee_maker_pct,
            "slippage_bps": self.slippage_bps,
            "latency_ms": self.latency_ms,
        }


class ChangeProposer:
    """
    Generador mínimo de propuestas v3 con:
      - fricciones activas por defecto
      - split temporal train/val/oos
      - walk-forward >=3 ventanas
      - verificación de no-leakage obligatoria
    """

    def __init__(self, friction_defaults: FrictionDefaults | None = None) -> None:
        self.friction_defaults = friction_defaults or FrictionDefaults()

    def create_proposal(
        self,
        *,
        hypothesis: str,
        approach_types_targeted: list[ApproachType],
        symbols: list[str] | None = None,
        source_ids: list[str] | None = None,
        risk_assessment: RiskAssessment | None = None,
        expected_impact: dict[str, Any] | None = None,
    ) -> Proposal:
        """Construye Proposal de dominio lista para ejecutar en ExperimentRunner."""
        if not approach_types_targeted:
            approach_types_targeted = [ApproachType.TOUCH]
        
        symbols = symbols or ["BTCUSDT"]

        risk = risk_assessment or RiskAssessment(
            max_drawdown_impact_pct=1.0,
            position_sizing_impact="none",
            kill_switch_threshold="drawdown_session_pct > max_drawdown_session_pct",
            circuit_breaker_interaction="No bypass. Respeta CB y kill-switch global.",
        )

        return Proposal.new(
            hypothesis=hypothesis.strip() or "Hypothesis pending",
            approach_types_targeted=approach_types_targeted,
            risk_assessment=risk,
            symbols=symbols,
            scientific_justification={
                "source_ids": source_ids or [],
                "evidence_policy": "no_operational_claim_with_only_tertiary",
            },
            backtesting={
                "frictions": self.friction_defaults.as_dict(),
                "splits": {"train_pct": 60, "validation_pct": 20, "oos_pct": 20},
                "walk_forward_windows": 3,
                "oos_leakage_check": True,
            },
            validation_plan={
                "walk_forward_windows_min": 3,
                "report_net_metrics_only": True,
                "require_no_leakage": True,
            },
            expected_impact=expected_impact or {},
            complexity_delta="low",
            reversible=True,
        )
