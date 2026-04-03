"""
Trading Engine mejorado con Knowledge Base
Toma decisiones basadas en información principiada
"""

from typing import Optional, Dict, List, Tuple
from datetime import datetime
import logging

from cgalpha_v2.core.trading_engine import CGAlphaScalpingEngine
from cgalpha_v2.knowledge_base import IntelligentCurator, KnowledgeRetriever


class CGAlphaWithKnowledge(CGAlphaScalpingEngine):
    """
    Trading engine mejorado que utiliza la Knowledge Base
    para tomar decisiones más inteligentes
    """
    
    def __init__(self, symbol: str = 'EURUSD'):
        super().__init__(symbol)
        
        self.curator = IntelligentCurator()
        self.retriever = self.curator.retriever
        
        # Cache de contextos
        self.context_entry = self.retriever.synthesize_context('trading_entry_validation')
        self.context_exit = self.retriever.synthesize_context('trading_exit_strategy')
        
        self.logger.info(
            f"Trading Engine initialized with Knowledge Base | "
            f"Papers: {len(self.retriever.trading_lib.get_all_papers())} | "
            f"Principles: {len(self.retriever.principles_lib.principles)}"
        )
    
    def get_entry_validation_context(self) -> str:
        """Retorna contexto principiado para validación de entrada"""
        return self.context_entry
    
    def get_exit_validation_context(self) -> str:
        """Retorna contexto principiado para validación de salida"""
        return self.context_exit
    
    def explain_entry_decision(self, signal: Dict) -> str:
        """
        Explica decisión de entrada usando conocimiento base
        """
        
        principles = self.retriever.get_principles_for_context('trading_entry_validation')
        
        explanation = f"ENTRADA JUSTIFICADA POR:\n\n"
        
        for principle in principles[:3]:  # Top 3 principios
            explanation += f"✓ {principle.title}\n"
            if signal.get('position_side') == 'LONG':
                explanation += f"  Aplicación: {principle.applications[0]}\n"
        
        explanation += f"\nSignal Metrics:\n"
        explanation += f"- Confidence: {signal.get('confidence', 0):.2%}\n"
        explanation += f"- VWAP validated: {signal.get('metrics', {}).get('barrier') is not None}\n"
        explanation += f"- OBI confirmed: {signal.get('reason', '').find('OBI') > -1}\n"
        
        return explanation
    
    def get_knowledge_summary(self) -> Dict:
        """Retorna resumen de conocimiento disponible"""
        
        stats = self.curator.get_statistics()
        
        return {
            'total_papers': stats['total_papers'],
            'validated_papers': stats['empirically_validated'],
            'live_tested_papers': stats['live_tested'],
            'principles_available': stats['principles_count'],
            'avg_citations': stats['avg_citations'],
            'library_status': 'READY'
        }
