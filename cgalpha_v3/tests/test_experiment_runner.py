from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cgalpha_v3.application.change_proposer import ChangeProposer
from cgalpha_v3.application.experiment_runner import ExperimentRunner
from cgalpha_v3.data_quality.gates import TemporalLeakageError
from cgalpha_v3.domain.models.signal import ApproachType


def _mock_rows(n: int = 180) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    base_ts = datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp()
    price = 100.0
    for i in range(n):
        open_ts = base_ts + (i * 300.0)
        close_ts = open_ts + 300.0
        open_price = price
        price += 0.05 if (i % 12) < 9 else -0.03
        close_price = price
        rows.append(
            {
                "open_time": open_ts,
                "close_time": close_ts,
                "open": open_price,
                "high": max(open_price, close_price) + 0.04,
                "low": min(open_price, close_price) - 0.04,
                "close": close_price,
            }
        )
    return rows


def test_p1_8_change_proposer_has_friction_defaults_active():
    proposer = ChangeProposer()
    proposal = proposer.create_proposal(
        hypothesis="test hypothesis",
        approach_types_targeted=[ApproachType.RETEST, ApproachType.BREAKOUT],
    )

    frictions = proposal.backtesting["frictions"]
    assert frictions["fee_taker_pct"] == 0.05
    assert frictions["fee_maker_pct"] == 0.02
    assert frictions["slippage_bps"] == 2.0
    assert frictions["latency_ms"] == 100.0
    assert proposal.backtesting["walk_forward_windows"] == 3


def test_p1_9_walk_forward_has_three_windows_and_temporal_splits():
    runner = ExperimentRunner()
    windows = runner.build_walk_forward_windows(_mock_rows(180), windows=3)

    assert len(windows) >= 3
    for w in windows:
        assert w.train_rows > 0
        assert w.validation_rows > 0
        assert w.oos_rows > 0
        assert w.train_end_ts <= w.validation_start_ts
        assert w.validation_end_ts <= w.oos_start_ts


def test_p1_10_no_leakage_e2e_raises_on_contaminated_features():
    proposer = ChangeProposer()
    runner = ExperimentRunner()
    rows = _mock_rows(180)
    proposal = proposer.create_proposal(
        hypothesis="leakage check",
        approach_types_targeted=[ApproachType.TOUCH],
    )

    # Timestamp forzado dentro de OOS para gatillar TemporalLeakageError.
    contaminated_ts = rows[-1]["open_time"]
    with pytest.raises(TemporalLeakageError):
        runner.run_experiment(
            proposal=proposal,
            rows=rows,
            feature_timestamps=[contaminated_ts],
        )


def test_p1_12_experiment_returns_net_metrics_post_friction():
    proposer = ChangeProposer()
    runner = ExperimentRunner()
    proposal = proposer.create_proposal(
        hypothesis="net metrics test",
        approach_types_targeted=[ApproachType.RETEST],
    )
    result = runner.run_experiment(proposal=proposal, rows=_mock_rows(180))

    assert result.no_leakage_checked is True
    assert len(result.walk_forward_windows) >= 3
    assert "net_return_pct" in result.metrics
    assert "friction_cost_pct" in result.metrics
    assert "approach_type_histogram" in result.as_dict()
    assert sum(result.approach_type_histogram.values()) > 0
