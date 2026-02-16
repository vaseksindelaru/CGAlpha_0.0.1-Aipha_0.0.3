"""
cgalpha.domain.models — Domain entities and value objects.

All models in this package are frozen dataclasses (immutable).
They carry no behavior beyond validation in __post_init__.

Re-exports for convenience:
    from cgalpha_v2.domain.models import Signal, Candle, TradeRecord, Prediction
"""

from __future__ import annotations

from cgalpha_v2.domain.models.signal import (
    Candle,
    Signal,
    SignalDirection,
    DetectorVerdict,
    TripleCoincidenceResult,
)
from cgalpha_v2.domain.models.prediction import (
    Feature,
    Prediction,
    ModelMetadata,
)
from cgalpha_v2.domain.models.trade import (
    TradeOutcome,
    TradeRecord,
    Trajectory,
)
from cgalpha_v2.domain.models.analysis import (
    Pattern,
    PatternType,
    Hypothesis,
    Recommendation,
    RecommendationPriority,
    CausalReport,
    ReadinessGate,
)
from cgalpha_v2.domain.models.proposal import (
    Proposal,
    ProposalSource,
    ProposalStatus,
    ProposalSeverity,
    EvaluationResult,
)
from cgalpha_v2.domain.models.health import (
    HealthEvent,
    HealthEventType,
    HealthLevel,
    ResourceSnapshot,
    ResourceState,
)
from cgalpha_v2.domain.models.config import (
    TradingConfig,
    OracleConfig,
    SystemConfig,
)

__all__ = [
    # signal
    "Candle",
    "Signal",
    "SignalDirection",
    "DetectorVerdict",
    "TripleCoincidenceResult",
    # prediction
    "Feature",
    "Prediction",
    "ModelMetadata",
    # trade
    "TradeOutcome",
    "TradeRecord",
    "Trajectory",
    # analysis
    "Pattern",
    "PatternType",
    "Hypothesis",
    "Recommendation",
    "RecommendationPriority",
    "CausalReport",
    "ReadinessGate",
    # proposal
    "Proposal",
    "ProposalSource",
    "ProposalStatus",
    "ProposalSeverity",
    "EvaluationResult",
    # health
    "HealthEvent",
    "HealthEventType",
    "HealthLevel",
    "ResourceSnapshot",
    "ResourceState",
    # config
    "TradingConfig",
    "OracleConfig",
    "SystemConfig",
]
