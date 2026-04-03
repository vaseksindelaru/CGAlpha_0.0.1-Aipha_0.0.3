"""
CGAlpha v2 Application Layer
Integración: Knowledge Base ↔ Trading Engine ↔ Learning
"""

__version__ = "2.0.0"

from cgalpha_v2.app.learning_integration import (
    LearningIntegrationEngine,
    LearningSession,
    TradingDecisionContext
)

from cgalpha_v2.app.trading_app import (
    CGAlphaTradingApplication,
    TradingApplicationFactory
)

__all__ = [
    'LearningIntegrationEngine',
    'LearningSession',
    'TradingDecisionContext',
    'CGAlphaTradingApplication',
    'TradingApplicationFactory',
]
