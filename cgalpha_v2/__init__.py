"""
CGAlpha v2 - Reconstructed Architecture

This package contains the reconstructed CGAlpha system with:
- Clean Architecture (domain/application/infrastructure/interfaces)
- Ports & Adapters pattern
- Explicit dependency injection
- Immutable domain models

Migration Status: Phase 2.1 Complete (Foundation)
"""

__version__ = "0.2.0-alpha"
__author__ = "Vaclav Sindelar"

# Domain layer exports
from cgalpha_v2.domain.models import (
    Signal,
    Candle,
    SignalDirection,
    TradeRecord,
    TradeOutcome,
    Prediction,
    Pattern,
    Hypothesis,
    Recommendation,
    Proposal,
    HealthEvent,
    SystemConfig,
)

# Config exports
from cgalpha_v2.config import ProjectPaths, Settings

# Shared exports
from cgalpha_v2.shared.exceptions import (
    CGAlphaError,
    ConfigurationError,
    DataError,
    TradingError,
    PredictionError,
    AnalysisError,
    EvolutionError,
    OperationsError,
    LLMError,
)

__all__ = [
    # Version
    "__version__",
    # Domain Models
    "Signal",
    "Candle", 
    "SignalDirection",
    "TradeRecord",
    "TradeOutcome",
    "Prediction",
    "Pattern",
    "Hypothesis",
    "Recommendation",
    "Proposal",
    "HealthEvent",
    "SystemConfig",
    # Config
    "ProjectPaths",
    "Settings",
    # Exceptions
    "CGAlphaError",
    "ConfigurationError",
    "DataError",
    "TradingError",
    "PredictionError",
    "AnalysisError",
    "EvolutionError",
    "OperationsError",
    "LLMError",
]
