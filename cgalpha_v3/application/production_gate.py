"""
CGAlpha v3 — Production Gate (Sección P3.6)
===========================================
Garantiza que ninguna estrategia entre en producción sin validación formal.
"""
from __future__ import annotations

from typing import Any
from cgalpha_v3.application.promotion_validator import PromotionValidator, PromotionStatus
from cgalpha_v3.application.experiment_runner import ExperimentResult
from cgalpha_v3.domain.models.signal import MemoryLevel


class ProductionGateError(Exception):
    """Excepción alzada cuando un criterio de producción es violado."""
    pass


class ProductionGate:
    def __init__(self, validator: PromotionValidator) -> None:
        self.validator = validator

    def verify_promotion_eligibility(
        self, 
        target_level: MemoryLevel, 
        experiment_result: ExperimentResult | None,
        health_snapshot: dict[str, Any]
    ) -> None:
        """
        Verifica si una entrada de memoria es elegible para el nivel destino.
        Si el nivel es STRATEGY (4), exige un experimento aprobado.
        """
        if target_level != MemoryLevel.STRATEGY:
            return  # No hay restricciones para niveles inferiores (0a-3) en este Gate

        if not experiment_result:
            raise ProductionGateError(
                "Promoción a PRODUCCIÓN rechazada: Se requiere un ExperimentResult vinculado."
            )

        report = self.validator.validate_experiment(experiment_result, health_snapshot)
        
        if report.status != PromotionStatus.APPROVED:
            reasons_str = "; ".join(report.reasons)
            raise ProductionGateError(
                f"Promoción a PRODUCCIÓN rechazada: El experimento {experiment_result.experiment_id} "
                f"no cumple los criterios. Motivos: {reasons_str}"
            )
        
        # Si llegamos aquí, el gate se abre
        return
