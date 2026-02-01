"""
Change Evaluator - Puntúa propuestas antes de aplicarlas.
Usa criterios de factibilidad, impacto y riesgo.
"""
import logging
from typing import Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class EvaluationResult:
    """Resultado de evaluación (Study Plan V5)"""
    score: float
    reasoning: str
    approved: bool

class ProposalEvaluator:
    """
    Evalúa propuestas basado en:
    1. Impacto (30%)
    2. Dificultad (20%)
    3. Riesgo (30%)
    4. Complejidad (20%)
    """
    APPROVAL_THRESHOLD = 0.70

    def __init__(self, sentinel):
        """
        Args:
            sentinel: Instancia de ContextSentinel para persistencia
        """
        self.sentinel = sentinel
        logger.info("ProposalEvaluator (Fase 2) inicializado")

    def evaluate(self, proposal, metrics: Dict[str, Any] = None) -> EvaluationResult:
        """
        Evalúa una propuesta de cambio usando lógica matemática del Hito 3.
        
        Criterios:
        1. Impacto (35%): Basado en prioridad y Win Rate actual.
        2. Riesgo (25%): Basado en prioridad y Drawdown.
        3. Dificultad (20%): Basado en complejidad estimada.
        4. Complejidad (20%): Basado en el tamaño del cambio.
        
        Multiplicador de Crisis:
        - Prioridad 'high': x1.10
        - Prioridad 'critical': x1.25
        """
        metrics = metrics or {}
        win_rate = metrics.get("win_rate", 0.5)
        drawdown = metrics.get("current_drawdown", 0.0)
        priority = getattr(proposal, 'priority', 'normal').lower()
        
        # 1. Cálculo de Impacto (0.0 - 1.0)
        # Si el Win Rate es bajo (< 40%), las propuestas de alta prioridad tienen más impacto
        if win_rate < 0.4:
            impact_base = 0.85 if priority in ['high', 'critical'] else 0.5
        else:
            impact_base = 0.70
        impact = impact_base
        
        # 2. Cálculo de Riesgo (0.0 - 1.0, donde 1.0 es bajo riesgo)
        # Propuestas críticas en momentos de alto drawdown son riesgosas pero necesarias
        risk_base = 0.90 # Por defecto bajo riesgo
        if drawdown > 0.15 and priority == 'critical':
            risk_base = 0.75 # Riesgo moderado por urgencia
        elif priority == 'critical':
            risk_base = 0.80
        risk = risk_base
        
        # 3. Dificultad (0.0 - 1.0, donde 1.0 es fácil)
        difficulty_map = {"baja": 0.9, "media": 0.7, "alta": 0.4}
        difficulty = difficulty_map.get(getattr(proposal, 'estimated_difficulty', 'media').lower(), 0.7)
        
        # 4. Complejidad (0.0 - 1.0, donde 1.0 es simple)
        complexity_map = {"trivial": 1.0, "simple": 0.9, "moderate": 0.7, "complex": 0.4}
        complexity = complexity_map.get(getattr(proposal, 'estimated_complexity', 'moderate').lower(), 0.7)
        
        # Fórmula Final Ponderada (Hito 3)
        base_score = (impact * 0.35) + (risk * 0.25) + (difficulty * 0.20) + (complexity * 0.20)
        
        # Multiplicador de Crisis
        multiplier = 1.0
        if priority == 'high':
            multiplier = 1.10
        elif priority == 'critical':
            multiplier = 1.25
            
        score = min(base_score * multiplier, 1.0)
        approved = score >= self.APPROVAL_THRESHOLD
        
        reasoning = (
            f"Evaluación Hito 3 para {proposal.proposal_id} (Prioridad: {priority.upper()}):\n"
            f"- Impacto (35%): {impact:.2f} (WR: {win_rate:.2f})\n"
            f"- Riesgo (25%): {risk:.2f} (DD: {drawdown:.2f})\n"
            f"- Dificultad (20%): {difficulty:.2f}\n"
            f"- Complejidad (20%): {complexity:.2f}\n"
            f"- Multiplicador Crisis: x{multiplier:.2f}\n"
            f"Score Final: {score:.2f} -> {'APROBADO' if approved else 'RECHAZADO'}"
        )
        
        # Registrar la evaluación en la memoria
        self.sentinel.add_action(
            agent="ProposalEvaluator",
            action_type="PROPOSAL_EVALUATED",
            proposal_id=proposal.proposal_id,
            details={
                "score": score, 
                "approved": approved, 
                "priority": priority,
                "multiplier": multiplier,
                "win_rate": win_rate
            }
        )
        
        return EvaluationResult(
            score=score,
            reasoning=reasoning,
            approved=approved
        )
