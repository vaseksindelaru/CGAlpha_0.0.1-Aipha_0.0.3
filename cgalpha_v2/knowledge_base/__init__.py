"""
CGAlpha v2 - Knowledge Base System
Arquitectura de dos capas para recomendación inteligente de fuentes
"""

__version__ = "1.0.0"

from cgalpha_v2.knowledge_base.phase_0_principles import PrinciplesLibrary
from cgalpha_v2.knowledge_base.phase_1_trading import TradingLibrary
from cgalpha_v2.knowledge_base.retrieval import KnowledgeRetriever
from cgalpha_v2.knowledge_base.curator import IntelligentCurator

__all__ = [
    'PrinciplesLibrary',
    'TradingLibrary',
    'KnowledgeRetriever',
    'IntelligentCurator',
]
