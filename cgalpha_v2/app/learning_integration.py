"""
Learning Integration Layer: Conecta Knowledge Base ↔ Trading Engine ↔ Learning App
Orquestación de flujos de aprendizaje y recomendación
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import json
import logging

from cgalpha_v2.knowledge_base import IntelligentCurator, KnowledgeRetriever
from cgalpha_v2.core.trading_engine import CGAlphaScalpingEngine


logger = logging.getLogger(__name__)


@dataclass
class TradingDecisionContext:
    """Contexto completo de una decisión de trading con justificación"""
    
    timestamp: datetime
    decision_type: str  # 'ENTRY', 'EXIT', 'REJECTION'
    decision: Dict  # {'valid': True, 'entry_price': 1.0850, ...}
    
    # Principios aplicados
    principles_applied: List[str] = field(default_factory=list)  # [rs_001, rs_003, cur_001]
    
    # Papers de referencia
    papers_referenced: List[Dict] = field(default_factory=list)  # [{'id': 'vwap_002', 'relevance': 0.92}, ...]
    
    # Explicación legible
    explanation: str = ""
    
    # Métricas
    signal_strength: float = 0.0  # 0-1
    confidence: float = 0.0  # 0-1
    
    # Resultado post-hoc
    outcome: Optional[str] = None  # 'WIN', 'LOSS', 'PARTIAL'
    outcome_pnl: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """Serializar para logging/análisis"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'decision_type': self.decision_type,
            'decision': self.decision,
            'principles': self.principles_applied,
            'papers': self.papers_referenced,
            'explanation': self.explanation,
            'signal_strength': self.signal_strength,
            'confidence': self.confidence,
            'outcome': self.outcome,
            'pnl': self.outcome_pnl
        }


@dataclass
class LearningSession:
    """Sesión de trading con aprendizaje asociado"""
    
    session_id: str
    symbol: str
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Decisiones de trading
    decisions: List[TradingDecisionContext] = field(default_factory=list)
    
    # Estadísticas
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    
    # Aprendizaje
    learned_principles: List[str] = field(default_factory=list)  # Principios más usados
    best_performing_papers: List[str] = field(default_factory=list)  # Papers con mejor result
    gaps_identified: List[str] = field(default_factory=list)  # Áreas de mejora
    
    def add_decision(self, decision_context: TradingDecisionContext) -> None:
        """Agrega decisión a la sesión"""
        self.decisions.append(decision_context)
        
        if decision_context.decision_type == 'ENTRY':
            self.total_trades += 1
        
        if decision_context.outcome == 'WIN':
            self.winning_trades += 1
        elif decision_context.outcome == 'LOSS':
            self.losing_trades += 1
        
        if decision_context.outcome_pnl:
            self.total_pnl += decision_context.outcome_pnl
    
    def get_winrate(self) -> float:
        """Retorna winrate de la sesión"""
        if self.total_trades == 0:
            return 0.0
        return self.winning_trades / self.total_trades
    
    def to_dict(self) -> Dict:
        """Serializar sesión"""
        return {
            'session_id': self.session_id,
            'symbol': self.symbol,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'winrate': self.get_winrate(),
            'total_pnl': self.total_pnl,
            'learned_principles': self.learned_principles,
            'best_papers': self.best_performing_papers,
            'gaps': self.gaps_identified,
            'decisions': [d.to_dict() for d in self.decisions]
        }


class LearningIntegrationEngine:
    """
    Motor de integración: Knowledge Base ↔ Trading Engine ↔ Learning
    
    Responsabilidades:
    1. Sincronizar decisiones de trading con contexto de knowledge
    2. Explicar decisiones usando principios + papers
    3. Registrar aprendizaje
    4. Generar recomendaciones de mejora
    """
    
    def __init__(self, symbol: str = 'EURUSD'):
        self.symbol = symbol
        self.logger = logging.getLogger(f'{__name__}.{symbol}')
        
        # Componentes
        self.curator = IntelligentCurator()
        self.retriever = self.curator.retriever
        self.trading_engine: Optional[CGAlphaScalpingEngine] = None
        
        # Sesión de aprendizaje actual
        self.current_session: Optional[LearningSession] = None
        self.session_history: List[LearningSession] = []
        
        # Estadísticas acumuladas
        self.total_decisions = 0
        self.decision_history: List[TradingDecisionContext] = []
    
    def start_learning_session(self, session_id: str) -> LearningSession:
        """Inicia nueva sesión de aprendizaje"""
        
        self.current_session = LearningSession(
            session_id=session_id,
            symbol=self.symbol,
            start_time=datetime.now()
        )
        
        self.logger.info(f"Learning session started: {session_id}")
        
        return self.current_session
    
    def end_learning_session(self) -> Optional[LearningSession]:
        """Finaliza sesión y analiza aprendizaje"""
        
        if not self.current_session:
            return None
        
        self.current_session.end_time = datetime.now()
        
        # Analizar aprendizaje
        self._analyze_session_learning()
        
        # Guardar en histórico
        self.session_history.append(self.current_session)
        
        self.logger.info(
            f"Learning session ended: {self.current_session.session_id} | "
            f"Trades: {self.current_session.total_trades} | "
            f"Winrate: {self.current_session.get_winrate():.1%}"
        )
        
        return self.current_session
    
    def record_trading_decision(
        self,
        decision_type: str,  # 'ENTRY', 'EXIT', 'REJECTION'
        decision: Dict,
        principles: List[str],
        papers: List[Dict],
        signal_strength: float = 0.0,
        confidence: float = 0.0
    ) -> TradingDecisionContext:
        """
        Registra decisión de trading con contexto de knowledge
        
        Args:
            decision_type: Tipo de decisión
            decision: Dict con detalles (entry_price, etc.)
            principles: Lista de principios aplicados
            papers: Lista de papers referenciados
            signal_strength: Fuerza de la señal (0-1)
            confidence: Confianza en la decisión (0-1)
        
        Returns:
            TradingDecisionContext registrado
        """
        
        # Generar explicación
        explanation = self._generate_decision_explanation(
            decision_type=decision_type,
            principles=principles,
            papers=papers,
            decision=decision
        )
        
        # Crear contexto
        context = TradingDecisionContext(
            timestamp=datetime.now(),
            decision_type=decision_type,
            decision=decision,
            principles_applied=principles,
            papers_referenced=papers,
            explanation=explanation,
            signal_strength=signal_strength,
            confidence=confidence
        )
        
        # Registrar en sesión actual
        if self.current_session:
            self.current_session.add_decision(context)
        
        # Registrar en histórico global
        self.decision_history.append(context)
        self.total_decisions += 1
        
        self.logger.debug(
            f"Decision recorded: {decision_type} | "
            f"Principles: {len(principles)} | "
            f"Papers: {len(papers)} | "
            f"Confidence: {confidence:.0%}"
        )
        
        return context
    
    def record_decision_outcome(
        self,
        decision_context: TradingDecisionContext,
        outcome: str,  # 'WIN', 'LOSS', 'PARTIAL'
        pnl: float
    ) -> None:
        """
        Registra resultado post-hoc de decisión
        Usado para aprendizaje y validación de papers
        
        Args:
            decision_context: Contexto de decisión original
            outcome: Resultado ('WIN', 'LOSS', 'PARTIAL')
            pnl: PnL generado
        """
        
        decision_context.outcome = outcome
        decision_context.outcome_pnl = pnl
        
        self.logger.info(
            f"Decision outcome: {outcome} | PnL: ${pnl:.2f} | "
            f"Decision type: {decision_context.decision_type}"
        )
    
    def get_entry_context(self, position_side: str) -> str:
        """
        Obtiene contexto principiado para decisión de entrada
        
        Retorna: Síntesis de principios + papers para usar en decisión
        """
        
        return self.retriever.synthesize_context('trading_entry_validation')
    
    def get_exit_context(self, position_side: str) -> str:
        """
        Obtiene contexto principiado para decisión de salida
        """
        
        return self.retriever.synthesize_context('trading_exit_strategy')
    
    def _generate_decision_explanation(
        self,
        decision_type: str,
        principles: List[str],
        papers: List[Dict],
        decision: Dict
    ) -> str:
        """
        Genera explicación legible de decisión
        """
        
        principle_objects = [self.retriever.principles_lib.get_principle(pid) for pid in principles if self.retriever.principles_lib.get_principle(pid)]
        
        explanation = f"**{decision_type} Decision**\n\n"
        
        explanation += "**Principles Applied:**\n"
        for p in principle_objects:
            explanation += f"- {p.title}\n"
        
        explanation += f"\n**Papers Referenced:** ({len(papers)})\n"
        for paper_ref in papers[:3]:  # Top 3 papers
            explanation += f"- {paper_ref.get('title', 'Unknown')} (relevance: {paper_ref.get('relevance', 0):.0%})\n"
        
        explanation += f"\n**Decision Details:**\n"
        for key, value in decision.items():
            if key not in ['metrics', 'details']:
                explanation += f"- {key}: {value}\n"
        
        return explanation
    
    def _analyze_session_learning(self) -> None:
        """
        Analiza sesión completada para extraer aprendizaje
        """
        
        if not self.current_session or len(self.current_session.decisions) == 0:
            return
        
        # Analizar principios más usados en trades ganadores
        winning_decisions = [d for d in self.current_session.decisions if d.outcome == 'WIN']
        
        if winning_decisions:
            # Contar principios en trades ganadores
            principle_counts = {}
            for decision in winning_decisions:
                for principle in decision.principles_applied:
                    principle_counts[principle] = principle_counts.get(principle, 0) + 1
            
            # Top principios
            self.current_session.learned_principles = sorted(
                principle_counts.keys(),
                key=lambda x: principle_counts[x],
                reverse=True
            )[:5]
        
        # Analizar papers en trades ganadores
        if winning_decisions:
            paper_performance = {}
            for decision in winning_decisions:
                for paper_ref in decision.papers_referenced:
                    paper_id = paper_ref.get('id', 'unknown')
                    paper_performance[paper_id] = paper_performance.get(paper_id, 0) + 1
            
            self.current_session.best_performing_papers = sorted(
                paper_performance.keys(),
                key=lambda x: paper_performance[x],
                reverse=True
            )[:5]
        
        # Identificar gaps
        gaps = self._identify_learning_gaps()
        self.current_session.gaps_identified = gaps
        
        self.logger.info(
            f"Session analysis: Learned {len(self.current_session.learned_principles)} principles | "
            f"Best papers: {self.current_session.best_performing_papers[:3]} | "
            f"Gaps: {len(gaps)}"
        )
    
    def _identify_learning_gaps(self) -> List[str]:
        """
        Identifica áreas donde el sistema falló
        Sugerencias para mejorar
        """
        
        if not self.current_session:
            return []
        
        gaps = []
        
        # Gap 1: Muchos rechazos (falta coverage)
        total_decisions = len(self.current_session.decisions)
        entries = sum(1 for d in self.current_session.decisions if d.decision_type == 'ENTRY')
        rejections = sum(1 for d in self.current_session.decisions if d.decision_type == 'REJECTION')
        
        if rejections > entries * 2:
            gaps.append(
                "HIGH_REJECTION_RATE: Demasiadas señales rechazadas. "
                "Revisar thresholds de OBI o VWAP."
            )
        
        # Gap 2: Baja winrate
        if self.current_session.get_winrate() < 0.5:
            gaps.append(
                "LOW_WINRATE: <50%. Revisar principios de curaduría (cur_001, cur_002). "
                "Falta validación empírica en papers referenciados."
            )
        
        # Gap 3: Papers no recomendados
        papers_used = set()
        for decision in self.current_session.decisions:
            for paper_ref in decision.papers_referenced:
                papers_used.add(paper_ref.get('id'))
        
        all_papers = set(p.id for p in self.retriever.trading_lib.get_all_papers())
        unused_papers = all_papers - papers_used
        
        if len(unused_papers) > len(papers_used):
            gaps.append(
                f"UNUSED_PAPERS: {len(unused_papers)} papers no se usaron. "
                "Considerar revisar rango de búsqueda de contexto."
            )
        
        # Gap 4: Baja confianza en decisiones
        avg_confidence = sum(d.confidence for d in self.current_session.decisions) / len(self.current_session.decisions) if self.current_session.decisions else 0
        
        if avg_confidence < 0.6:
            gaps.append(
                f"LOW_CONFIDENCE: Promedio {avg_confidence:.0%}. "
                "Agregar más principios o papers de validación."
            )
        
        return gaps
    
    def get_improvement_recommendations(self) -> Dict:
        """
        Genera recomendaciones de mejora basadas en sesiones anteriores
        """
        
        if not self.session_history:
            return {'message': 'No sessions completed yet'}
        
        # Analizar tendencias
        avg_winrate = sum(s.get_winrate() for s in self.session_history) / len(self.session_history)
        avg_trades_per_session = sum(s.total_trades for s in self.session_history) / len(self.session_history)
        
        recommendations = {
            'avg_winrate': avg_winrate,
            'avg_trades_per_session': avg_trades_per_session,
            'improvements': []
        }
        
        # Recomendar basado en tendencias
        if avg_winrate < 0.55:
            recommendations['improvements'].append({
                'category': 'VALIDATION',
                'action': 'Aumentar rigor en cur_001 (validación empírica)',
                'reason': f'Winrate ({avg_winrate:.0%}) < 55% target'
            })
        
        if avg_trades_per_session < 3:
            recommendations['improvements'].append({
                'category': 'COVERAGE',
                'action': 'Revisar rs_002 (diversidad) - aumentar range de búsqueda',
                'reason': f'Demasiadas sesiones sin trades ({avg_trades_per_session:.1f}/sesión)'
            })
        
        # Recomendar papers según gaps
        all_gaps = []
        for session in self.session_history:
            all_gaps.extend(session.gaps_identified)
        
        if 'LOW_WINRATE' in all_gaps:
            recommendations['improvements'].append({
                'category': 'PAPERS',
                'action': 'Buscar papers con mejor validación empírica',
                'papers_to_review': self.retriever.trading_lib.get_live_tested()[:5]
            })
        
        return recommendations
    
    def export_session_report(self, session: Optional[LearningSession] = None) -> str:
        """
        Exporta reporte de sesión o sesión actual
        """
        
        target_session = session or self.current_session
        
        if not target_session:
            return "No session available"
        
        report = f"""
# Learning Session Report: {target_session.session_id}

## Overview
- **Symbol:** {target_session.symbol}
- **Duration:** {(target_session.end_time - target_session.start_time).total_seconds():.1f}s
- **Completed:** {target_session.end_time is not None}

## Performance
- **Total Trades:** {target_session.total_trades}
- **Winning Trades:** {target_session.winning_trades}
- **Losing Trades:** {target_session.losing_trades}
- **Winrate:** {target_session.get_winrate():.1%}
- **Total PnL:** ${target_session.total_pnl:.2f}

## Learning Insights
- **Principles Applied:** {', '.join(target_session.learned_principles[:3]) if target_session.learned_principles else 'None'}
- **Best Papers:** {', '.join(target_session.best_performing_papers[:3]) if target_session.best_performing_papers else 'None'}
- **Gaps Identified:** {len(target_session.gaps_identified)}

### Identified Gaps
{chr(10).join(f"- {gap}" for gap in target_session.gaps_identified)}

## Next Steps
{self._generate_next_steps(target_session)}
"""
        
        return report
    
    def _generate_next_steps(self, session: LearningSession) -> str:
        """Genera siguientes pasos basado en análisis de sesión"""
        
        if session.get_winrate() >= 0.7:
            return "✓ Sesión exitosa. Mantener configuración actual."
        elif session.get_winrate() >= 0.5:
            return "→ Winrate aceptable. Optimizar con papers adicionales sobre validación (cur_001)."
        else:
            return "✗ Winrate bajo. Revisar principios fundamentales. Considerar reset a configuración anterior."
    
    def get_knowledge_stats(self) -> Dict:
        """Retorna estadísticas de uso de knowledge base"""
        
        return {
            'total_decisions': self.total_decisions,
            'total_sessions': len(self.session_history),
            'principles_available': len(self.retriever.principles_lib.principles),
            'papers_available': len(self.retriever.trading_lib.get_all_papers()),
            'papers_with_empirical_validation': len(self.retriever.trading_lib.get_empirically_validated()),
            'papers_live_tested': len(self.retriever.trading_lib.get_live_tested()),
        }
