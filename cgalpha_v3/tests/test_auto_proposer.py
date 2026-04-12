"""Tests para AutoProposer real — Fase 1."""

from __future__ import annotations

from cgalpha_v3.lila.llm.proposer import AutoProposer


def test_no_proposals_when_metrics_good() -> None:
    proposer = AutoProposer.create_default()
    metrics = {
        "oracle_accuracy_oos": 0.75,
        "max_drawdown_pct": 3.0,
        "win_rate_pct": 60.0,
        "sharpe_neto": 1.5,
        "feature_importances": {
            "vwap_at_retest": 0.25,
            "obi_10_at_retest": 0.20,
            "cumulative_delta_at_retest": 0.18,
        },
    }

    proposals = proposer.analyze_drift(metrics)
    assert len(proposals) == 0


def test_proposals_when_accuracy_low() -> None:
    proposer = AutoProposer.create_default()
    metrics = {
        "oracle_accuracy_oos": 0.50,
        "max_drawdown_pct": 3.0,
        "win_rate_pct": 55.0,
        "sharpe_neto": 1.0,
        "feature_importances": {},
    }

    proposals = proposer.analyze_drift(metrics)
    assert len(proposals) >= 1
    assert any(p.target_attribute == "min_confidence" for p in proposals)


def test_proposals_when_drawdown_high() -> None:
    proposer = AutoProposer.create_default()
    metrics = {
        "oracle_accuracy_oos": 0.70,
        "max_drawdown_pct": 8.0,
        "win_rate_pct": 55.0,
        "sharpe_neto": 1.0,
        "feature_importances": {},
    }

    proposals = proposer.analyze_drift(metrics)
    assert any(p.target_attribute == "max_position_size_pct" for p in proposals)


def test_proposals_when_feature_importance_low() -> None:
    proposer = AutoProposer.create_default()
    metrics = {
        "oracle_accuracy_oos": 0.70,
        "max_drawdown_pct": 2.0,
        "win_rate_pct": 60.0,
        "sharpe_neto": 1.0,
        "feature_importances": {
            "vwap_at_retest": 0.01,
            "obi_10_at_retest": 0.25,
        },
    }

    proposals = proposer.analyze_drift(metrics)
    assert any(p.target_attribute == "feature:vwap_at_retest" for p in proposals)
