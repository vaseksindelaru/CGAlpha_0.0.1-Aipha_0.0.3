"""Unit tests for cgalpha_v2.domain.models.analysis."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cgalpha_v2.domain.models import (
    CausalReport,
    Hypothesis,
    Pattern,
    PatternType,
    ReadinessGate,
    Recommendation,
    RecommendationPriority,
)


def test_pattern_validation_raises_on_bad_values() -> None:
    with pytest.raises(ValueError, match="frequency"):
        Pattern(
            pattern_type=PatternType.CUSTOM,
            name="p",
            description="d",
            frequency=1.1,
            confidence=0.5,
            affected_trades=1,
            total_trades=2,
        )

    with pytest.raises(ValueError, match="confidence"):
        Pattern(
            pattern_type=PatternType.CUSTOM,
            name="p",
            description="d",
            frequency=0.5,
            confidence=-0.1,
            affected_trades=1,
            total_trades=2,
        )

    with pytest.raises(ValueError, match="affected_trades"):
        Pattern(
            pattern_type=PatternType.CUSTOM,
            name="p",
            description="d",
            frequency=0.5,
            confidence=0.5,
            affected_trades=3,
            total_trades=2,
        )


def test_hypothesis_source_validation_raises() -> None:
    with pytest.raises(ValueError, match="source"):
        Hypothesis(
            hypothesis_id="h1",
            pattern_name="p1",
            cause="c",
            mechanism="m",
            evidence_strength=0.5,
            source="manual",
        )


def test_recommendation_validation_raises() -> None:
    with pytest.raises(ValueError, match="confidence"):
        Recommendation(
            title="t",
            description="d",
            target_parameter="Trading.tp_factor",
            confidence=1.1,
        )

    with pytest.raises(ValueError, match="title"):
        Recommendation(
            title="",
            description="d",
            target_parameter="Trading.tp_factor",
            confidence=0.5,
        )


def test_causal_report_gate_properties() -> None:
    recommendation_low = Recommendation(
        title="Low",
        description="desc",
        target_parameter="Trading.tp_factor",
        priority=RecommendationPriority.LOW,
    )
    recommendation_critical = Recommendation(
        title="Critical",
        description="desc",
        target_parameter="Trading.sl_factor",
        priority=RecommendationPriority.CRITICAL,
    )
    report = CausalReport(
        report_id="R1",
        records_analyzed=10,
        patterns=(),
        hypotheses=(),
        recommendations=(recommendation_low, recommendation_critical),
        readiness_gates=(
            ReadinessGate(name="g1", passed=True),
            ReadinessGate(name="g2", passed=True),
        ),
        duration_seconds=1.2,
        created_at=datetime.now(timezone.utc),
    )
    assert report.all_gates_pass is True
    assert report.critical_recommendations == (recommendation_critical,)


def test_causal_report_without_gates_is_not_ready() -> None:
    report = CausalReport(
        report_id="R2",
        records_analyzed=0,
        patterns=(),
        hypotheses=(),
        recommendations=(),
    )
    assert report.all_gates_pass is False
