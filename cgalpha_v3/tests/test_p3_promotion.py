"""
CGAlpha v3 — P3.3 Promotion Validator Tests
===========================================
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from cgalpha_v3.application.promotion_validator import PromotionStatus, PromotionValidator
from cgalpha_v3.application.experiment_runner import ExperimentResult, FrictionDefaults
from cgalpha_v3.risk.health_monitor import HealthStatus


@pytest.fixture
def validator():
    return PromotionValidator()


def test_promotion_approved_all_criteria(validator):
    # Experimento perfecto
    result = ExperimentResult(
        experiment_id="exp-123",
        proposal_id="prop-1",
        generated_at=datetime.now(timezone.utc),
        friction=FrictionDefaults(),
        metrics={
            "sharpe_ratio_oos": 1.5,
            "max_drawdown_oos": 5.0,
            "profit_factor_oos": 1.8,
        },
        walk_forward_windows=[],
        window_metrics=[],
        approach_type_histogram={},
        no_leakage_checked=True,
    )
    health = {"status": "healthy"}
    
    report = validator.validate_experiment(result, health)
    assert report.status == PromotionStatus.APPROVED
    assert report.overall_score == 1.0
    assert len(report.reasons) == 0


def test_promotion_rejected_poor_metrics(validator):
    # Mal Sharpe y DD
    result = ExperimentResult(
        experiment_id="exp-bad",
        proposal_id="prop-1",
        generated_at=datetime.now(timezone.utc),
        friction=FrictionDefaults(),
        metrics={
            "sharpe_ratio_oos": 0.2, # < 0.8
            "max_drawdown_oos": 30.0, # > 15.0
            "profit_factor_oos": 1.1, # < 1.3
        },
        walk_forward_windows=[],
        window_metrics=[],
        approach_type_histogram={},
        no_leakage_checked=True,
    )
    health = {"status": "healthy"}
    
    report = validator.validate_experiment(result, health)
    assert report.status == PromotionStatus.REJECTED
    assert report.checks["sharpe_oos"] is False
    assert report.checks["drawdown_oos"] is False
    assert report.checks["profit_factor_oos"] is False
    assert len(report.reasons) == 3


def test_promotion_rejected_system_degraded(validator):
    result = ExperimentResult(
        experiment_id="exp-123",
        proposal_id="prop-1",
        generated_at=datetime.now(timezone.utc),
        friction=FrictionDefaults(),
        metrics={
            "sharpe_ratio_oos": 1.5,
            "max_drawdown_oos": 5.0,
            "profit_factor_oos": 1.8,
        },
        walk_forward_windows=[],
        window_metrics=[],
        approach_type_histogram={},
        no_leakage_checked=True,
    )
    # Sistema degradado (breach de SLOs)
    health = {"status": "degraded"}
    
    report = validator.validate_experiment(result, health)
    assert report.status == PromotionStatus.REJECTED
    assert report.checks["system_healthy"] is False
    assert "Estado del sistema no apto" in report.reasons[0]


def test_promotion_rejected_no_leakage_check(validator):
    result = ExperimentResult(
        experiment_id="exp-123",
        proposal_id="prop-1",
        generated_at=datetime.now(timezone.utc),
        friction=FrictionDefaults(),
        metrics={
            "sharpe_ratio_oos": 1.5,
            "max_drawdown_oos": 5.0,
            "profit_factor_oos": 1.8,
        },
        walk_forward_windows=[],
        window_metrics=[],
        approach_type_histogram={},
        no_leakage_checked=False, # ERROR: obligatorio
    )
    health = {"status": "healthy"}
    
    report = validator.validate_experiment(result, health)
    assert report.status == PromotionStatus.REJECTED
    assert report.checks["no_leakage"] is False
