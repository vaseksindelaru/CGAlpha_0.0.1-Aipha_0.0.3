"""
Knowledge Retrieval: Sistema de búsqueda y ranking inteligente
Combina IR + relevancia + credibilidad
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import math

from cgalpha_v2.knowledge_base.phase_0_principles import PrinciplesLibrary, Principle
from cgalpha_v2.knowledge_base.phase_1_trading import TradingLibrary, TradingPaper, ApplicationArea


@dataclass
class RetrievalResult:
    """Resultado de búsqueda/recuperación"""
    paper: TradingPaper
    relevance_score: float  # 0-1
    credibility_score: float  # 0-1
    overall_score: float  # 0-1 (combinado)
    reasoning: str  # Por qué fue rankeado así


class KnowledgeRetriever:
    """
    Motor de recuperación inteligente de conocimiento
    Busca papers y principios de forma relevante
    """
    
    def __init__(self):
        self.principles_lib = PrinciplesLibrary()
        self.trading_lib = TradingLibrary()
        
        # Pesos para scoring
        self.weights = {
            'relevance': 0.40,  # IR + semantic match
            'credibility': 0.35,  # Peer review, citations
            'validation': 0.15,  # Empirical tests
            'recency': 0.10,  # Año del paper
        }
    
    def retrieve_papers_for_context(
        self,
        context: str,
        limit: int = 5,
        min_credibility_level: int = 2
    ) -> List[RetrievalResult]:
        """
        Recupera papers relevantes a un contexto específico
        
        context: ej. 'trading_entry_validation', 'exit_strategy_delta'
        """
        
        # Determinar áreas de aplicación relevantes
        context_to_applications = {
            'trading_entry_validation': [ApplicationArea.VWAP, ApplicationArea.OBI, ApplicationArea.ENTRY_VALIDATION],
            'trading_exit_strategy': [ApplicationArea.CUMULATIVE_DELTA, ApplicationArea.EXIT_STRATEGY],
            'scalping_eurusd': [ApplicationArea.SCALPING, ApplicationArea.VWAP, ApplicationArea.OBI],
            'microstructure': [ApplicationArea.OBI, ApplicationArea.MICROSTRUCTURE, ApplicationArea.CUMULATIVE_DELTA],
        }
        
        applications = context_to_applications.get(context, [])
        
        # Recuperar papers
        candidate_papers = []
        
        for app in applications:
            papers = self.trading_lib.get_by_application(app)
            candidate_papers.extend(papers)
        
        # Remover duplicados
        candidate_papers = list(set(candidate_papers))
        
        # Rankear
        ranked = self._rank_papers(candidate_papers, context)
        
        # Filtrar por credibilidad y retornar top-K
        return ranked[:limit]
    
    def _rank_papers(
        self,
        papers: List[TradingPaper],
        context: str
    ) -> List[RetrievalResult]:
        """
        Rankea papers según múltiples criterios
        """
        results = []
        
        for paper in papers:
            # Calcular componentes de score
            relevance = self._calculate_relevance(paper, context)
            credibility = paper.get_credibility_score()
            validation = 1.0 if paper.empirical_validation and paper.backtested_live else 0.5
            recency = self._calculate_recency_score(paper.year)
            
            # Score combinado ponderado
            overall = (
                relevance * self.weights['relevance'] +
                credibility * self.weights['credibility'] +
                validation * self.weights['validation'] +
                recency * self.weights['recency']
            )
            
            reasoning = self._generate_reasoning(
                paper, relevance, credibility, validation, recency
            )
            
            results.append(RetrievalResult(
                paper=paper,
                relevance_score=relevance,
                credibility_score=credibility,
                overall_score=overall,
                reasoning=reasoning
            ))
        
        # Sort by overall score
        results.sort(key=lambda r: r.overall_score, reverse=True)
        
        return results
    
    def _calculate_relevance(self, paper: TradingPaper, context: str) -> float:
        """
        Calcula relevancia de paper para contexto
        Considera: aplicaciones, relaciones, relevancia semántica
        """
        
        # Base relevance por contexto
        base_relevance = 0.5
        
        # Boost por aplicaciones relacionadas
        if context == 'trading_entry_validation':
            if ApplicationArea.ENTRY_VALIDATION in paper.applications:
                base_relevance = 0.8
            elif ApplicationArea.VWAP in paper.applications or ApplicationArea.OBI in paper.applications:
                base_relevance = 0.7
        
        elif context == 'trading_exit_strategy':
            if ApplicationArea.EXIT_STRATEGY in paper.applications:
                base_relevance = 0.85
            elif ApplicationArea.CUMULATIVE_DELTA in paper.applications:
                base_relevance = 0.75
        
        elif context == 'scalping_eurusd':
            if ApplicationArea.SCALPING in paper.applications:
                base_relevance = 0.9
            if paper.boundary_conditions and any('EURUSD' in bc or '1-5 min' in bc for bc in paper.boundary_conditions):
                base_relevance = min(1.0, base_relevance + 0.15)
        
        # Boost si tiene limitaciones (señal de honestidad)
        if paper.limitations:
            base_relevance = min(1.0, base_relevance + 0.05)
        
        return base_relevance
    
    def _calculate_recency_score(self, year: int) -> float:
        """
        Calcula score de recencia
        Más reciente = mejor, pero papers clásicos también valiosos
        """
        current_year = 2025
        years_old = current_year - year
        
        if years_old <= 3:
            return 1.0  # Muy reciente
        elif years_old <= 7:
            return 0.8  # Reciente
        elif years_old <= 15:
            return 0.6  # Mediano
        else:
            return 0.4  # Clásico pero aún válido
    
    def _generate_reasoning(
        self,
        paper: TradingPaper,
        relevance: float,
        credibility: float,
        validation: float,
        recency: float
    ) -> str:
        """Genera explicación de por qué fue rankeado así"""
        
        reasons = []
        
        if credibility >= 0.8:
            reasons.append(f"Alta credibilidad ({paper.credibility.name})")
        
        if paper.empirical_validation and paper.backtested_live:
            reasons.append("Validado empíricamente en trading real")
        elif paper.empirical_validation:
            reasons.append("Validado empíricamente")
        
        if paper.limitations:
            reasons.append("Menciona limitaciones honestamente")
        
        if recency >= 0.8:
            reasons.append(f"Muy reciente ({paper.year})")
        
        if paper.citation_count > 100:
            reasons.append(f"Altamente citado ({paper.citation_count} citas)")
        
        return " | ".join(reasons)
    
    def get_principles_for_context(self, context: str) -> List[Principle]:
        """Retorna principios aplicables a contexto"""
        return self.principles_lib.get_applicable_principles(context)
    
    def synthesize_context(self, context: str) -> str:
        """
        Sintetiza principios + papers para un contexto
        Útil para pasar a Claude como contexto
        """
        
        principles = self.get_principles_for_context(context)
        papers = self.retrieve_papers_for_context(context, limit=5)
        
        synthesis = f"# CONTEXTO: {context.upper()}\n\n"
        
        # Principios relevantes
        synthesis += "## PRINCIPIOS A APLICAR:\n\n"
        for principle in principles:
            synthesis += f"- {principle.title}\n"
            synthesis += f"  {principle.description}\n\n"
        
        # Papers relevantes
        synthesis += "## PAPERS RECOMENDADOS:\n\n"
        for result in papers:
            synthesis += f"### {result.paper.title}\n"
            synthesis += f"Authors: {', '.join(result.paper.authors)}\n"
            synthesis += f"Year: {result.paper.year}\n"
            synthesis += f"Credibility: {result.paper.credibility.name}\n"
            synthesis += f"Relevance Score: {result.overall_score:.2%}\n"
            synthesis += f"Reasoning: {result.reasoning}\n"
            synthesis += f"Abstract: {result.paper.abstract}\n\n"
        
        return synthesis
