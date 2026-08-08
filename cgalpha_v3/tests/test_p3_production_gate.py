"""
CGAlpha v3 — P3.6 Production Gate Tests
=======================================
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from cgalpha_v3.gui.server import app, AUTH_TOKEN, _experiment_history, _health_monitor
from cgalpha_v3.application.experiment_runner import ExperimentResult, FrictionDefaults
from cgalpha_v3.domain.models.signal import MemoryLevel


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def clean_history():
    _experiment_history.clear()
    for slo in _health_monitor.slos.values():
        slo.values = []
    yield


def test_production_gate_rejection_no_experiment(client):
    # Intentar promover a L4 sin experimento
    res = client.post("/api/learning/memory/promote",
                     headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
                     json={
                         "entry_id": "test-id",
                         "target_level": "strategy"
                     })
    assert res.status_code == 403
    assert res.get_json()["error"] == "production_gate_rejected"
    assert "ExperimentResult vinculado" in res.get_json()["message"]


def test_production_gate_rejection_failed_experiment(client):
    # Experimento con métricas pobres
    exp = ExperimentResult(
        experiment_id="exp-failed",
        proposal_id="prop-1",
        generated_at=datetime.now(timezone.utc),
        friction=FrictionDefaults(),
        metrics={"sharpe_ratio_oos": 0.1}, # Fails > 0.8
        walk_forward_windows=[],
        window_metrics=[],
        approach_type_histogram={},
        no_leakage_checked=True,
    )
    _experiment_history.append(exp)
    
    res = client.post("/api/learning/memory/promote",
                     headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
                     json={
                         "entry_id": "test-id",
                         "target_level": "4",
                         "experiment_id": "exp-failed"
                     })
    assert res.status_code == 403
    assert "Sharpe Ratio OOS insuficiente" in res.get_json()["message"]


def test_production_gate_approval_perfect_experiment(client):
    # Ingestar algo primero para tener un entry_id válido que promover
    _ingest_res = client.post("/api/learning/memory/ingest",
                             headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
                             json={"content": "Math", "field": "math"})
    entry_id = _ingest_res.get_json()["entry"]["entry_id"]
    
    # Promover a L3 primero (no requiere gate)
    client.post("/api/learning/memory/promote",
                headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
                json={"entry_id": entry_id, "target_level": "3"})

    # Experimento exitoso
    exp = ExperimentResult(
        experiment_id="exp-good",
        proposal_id="prop-1",
        generated_at=datetime.now(timezone.utc),
        friction=FrictionDefaults(),
        metrics={
            "sharpe_ratio_oos": 1.2,
            "max_drawdown_oos": 4.0,
            "profit_factor_oos": 1.5
        },
        walk_forward_windows=[],
        window_metrics=[],
        approach_type_histogram={},
        no_leakage_checked=True,
    )
    _experiment_history.append(exp)
    
    # Promover a L4 con experimento exitoso
    res = client.post("/api/learning/memory/promote",
                     headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
                     json={
                         "entry_id": entry_id,
                         "target_level": "4",
                         "experiment_id": "exp-good"
                     })
    assert res.status_code == 200
    assert res.get_json()["entry"]["level"] == "4"
