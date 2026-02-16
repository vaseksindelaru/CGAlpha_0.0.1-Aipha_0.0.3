"""
cgalpha.domain.models.analysis — Causal Analysis value objects.

This module defines the value objects for the Causal Analysis (Ghost Architect)
bounded context.  These represent the artifacts produced by the analysis
pipeline: detected patterns, causal hypotheses, and actionable recommendations.

Design notes:
- Pattern captures a recurring statistical regularity across trades.
- Hypothesis is a causal explanation for *why* a pattern occurs.
- Recommendation is the actionable output (what to change, with what impact).
- CausalReport is the aggregate container for one full analysis run.
- ReadinessGate captures the preconditions for advancing to the next phase.
- All frozen — the pipeline produces new instances, never mutates.

Ubiquitous Language:
    Pattern         → A recurring characteristic across trade snapshots.
    Hypothesis      → A causal explanation for a detected pattern.
    Recommendation  → An actionable suggestion derived from hypotheses.
    CausalReport    → The full output of one causal analysis run.
    ReadinessGate   → A boolean precondition for phase advancement.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class PatternType(Enum):
    """Types of patterns the Ghost Architect can detect."""

    FAKEOUT = "fakeout"
    NEWS_IMPACT = "news_impact"
    MICROSTRUCTURE = "microstructure"
    MFE_MAE_RATIO = "mfe_mae_ratio"
    WIN_RATE_DRIFT = "win_rate_drift"
    CUSTOM = "custom"


class RecommendationPriority(Enum):
    """Priority level for a recommendation."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class Pattern:
    """
    A recurring pattern detected across multiple trade snapshots.

    Patterns are statistical regularities that may indicate an underlying
    causal mechanism.  They are detected by specialized detectors and
    passed to the HypothesisBuilder.

    Attributes:
        pattern_type:   Classification of the pattern.
        name:           Human-readable name (e.g. 'Fakeout after news events').
        description:    Detailed description of what was detected.
        frequency:      How often this pattern occurs (0.0-1.0 of total trades).
        confidence:     Statistical confidence in the pattern [0.0, 1.0].
        affected_trades: Number of trades exhibiting this pattern.
        total_trades:   Total trades analyzed.
        metadata:       Pattern-specific data (e.g. thresholds, metrics).
        detected_at:    When the pattern was detected.
    """

    pattern_type: PatternType
    name: str
    description: str
    frequency: float
    confidence: float
    affected_trades: int
    total_trades: int
    metadata: Optional[dict[str, Any]] = None
    detected_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not (0.0 <= self.frequency <= 1.0):
            raise ValueError(
                f"Pattern frequency must be in [0, 1], got {self.frequency}"
            )
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"Pattern confidence must be in [0, 1], got {self.confidence}"
            )
        if self.affected_trades > self.total_trades:
            raise ValueError(
                f"Pattern affected_trades ({self.affected_trades}) > "
                f"total_trades ({self.total_trades})"
            )


@dataclass(frozen=True, slots=True)
class Hypothesis:
    """
    A causal hypothesis explaining why a pattern occurs.

    Hypotheses are generated either by LLM inference or by heuristic
    rules.  Each links a detected pattern to a potential root cause
    and suggests a mechanism.

    Attributes:
        hypothesis_id:  Unique identifier.
        pattern_name:   Name of the pattern this explains.
        cause:          Proposed root cause.
        mechanism:      How the cause produces the observed pattern.
        evidence_strength: Strength of evidence (0.0-1.0).
        source:         How the hypothesis was generated ('llm' or 'heuristic').
        testable:       Whether this hypothesis can be tested/validated.
        created_at:     When the hypothesis was generated.
    """

    hypothesis_id: str
    pattern_name: str
    cause: str
    mechanism: str
    evidence_strength: float
    source: str
    testable: bool = True
    created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not (0.0 <= self.evidence_strength <= 1.0):
            raise ValueError(
                f"Hypothesis evidence_strength must be in [0, 1], "
                f"got {self.evidence_strength}"
            )
        if self.source not in ("llm", "heuristic"):
            raise ValueError(
                f"Hypothesis source must be 'llm' or 'heuristic', "
                f"got '{self.source}'"
            )


@dataclass(frozen=True, slots=True)
class Recommendation:
    """
    An actionable recommendation derived from causal analysis.

    Recommendations are the final output of the Ghost Architect.
    They describe a specific change to make, why, and what the
    expected impact would be.

    Attributes:
        title:           Short description of the recommendation.
        description:     Detailed explanation and rationale.
        target_parameter: Parameter to change (e.g. 'Trading.tp_factor').
        current_value:   Current value of the parameter.
        suggested_value: Proposed new value.
        expected_impact: Description of expected impact.
        priority:        Priority level.
        confidence:      Confidence that this will improve performance [0.0, 1.0].
        hypothesis_id:   ID of the supporting hypothesis.
        created_at:      When the recommendation was generated.
    """

    title: str
    description: str
    target_parameter: str
    current_value: Optional[str] = None
    suggested_value: Optional[str] = None
    expected_impact: Optional[str] = None
    priority: RecommendationPriority = RecommendationPriority.MEDIUM
    confidence: float = 0.5
    hypothesis_id: Optional[str] = None
    created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"Recommendation confidence must be in [0, 1], "
                f"got {self.confidence}"
            )
        if not self.title:
            raise ValueError("Recommendation title cannot be empty")


@dataclass(frozen=True, slots=True)
class ReadinessGate:
    """
    A boolean precondition for advancing to the next operational phase.

    Readiness gates are defined in the Constitution v0.0.3. All gates
    must pass before the system can move from Paper to Live mode.

    Attributes:
        name:       Gate identifier (e.g. 'data_quality_pass').
        passed:     Whether the gate is satisfied.
        value:      The measured value (for threshold-based gates).
        threshold:  The required threshold.
        message:    Human-readable status message.
    """

    name: str
    passed: bool
    value: Optional[float] = None
    threshold: Optional[float] = None
    message: str = ""


@dataclass(frozen=True, slots=True)
class CausalReport:
    """
    The aggregate output of one complete causal analysis run.

    This is the top-level container returned by the CausalAnalysisPipeline.
    It bundles all patterns, hypotheses, recommendations, and gate results.

    Attributes:
        report_id:       Unique identifier for this analysis run.
        records_analyzed: Number of trade records analyzed.
        patterns:        Detected patterns.
        hypotheses:      Generated hypotheses.
        recommendations: Actionable recommendations.
        readiness_gates: Gate evaluation results.
        duration_seconds: How long the analysis took.
        created_at:      When the report was created.
    """

    report_id: str
    records_analyzed: int
    patterns: tuple[Pattern, ...]
    hypotheses: tuple[Hypothesis, ...]
    recommendations: tuple[Recommendation, ...]
    readiness_gates: tuple[ReadinessGate, ...] = ()
    duration_seconds: float = 0.0
    created_at: Optional[datetime] = None

    @property
    def all_gates_pass(self) -> bool:
        """True if every readiness gate is satisfied."""
        if not self.readiness_gates:
            return False
        return all(g.passed for g in self.readiness_gates)

    @property
    def critical_recommendations(self) -> tuple[Recommendation, ...]:
        """Recommendations with CRITICAL or HIGH priority."""
        return tuple(
            r
            for r in self.recommendations
            if r.priority
            in (RecommendationPriority.CRITICAL, RecommendationPriority.HIGH)
        )
