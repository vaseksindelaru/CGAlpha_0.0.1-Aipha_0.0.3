"""
CGAlpha v3 — P3.1 Bounded Context Hardening Tests (Full)
======================================================
Tests exhaustivos para cerrar brechas de cobertura en:
- Memory Policy (Logic errors)
- Health Monitoring (SLO Breaches)
- API Error Paths (Server integration)
"""
from __future__ import annotations

import json
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from cgalpha_v3.gui.server import app, AUTH_TOKEN
from cgalpha_v3.learning.memory_policy import MemoryPolicyEngine, MemoryLevel
from cgalpha_v3.risk.health_monitor import HealthMonitor, HealthStatus


@pytest.fixture(autouse=True)
def reset_health_monitor():
    from cgalpha_v3.gui.server import _health_monitor
    for slo in _health_monitor.slos.values():
        slo.values = []
    yield
    for slo in _health_monitor.slos.values():
        slo.values = []


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# --- Bounded Context: Learning/Memory (P3.1 Hardening) ---

def test_memory_policy_promote_degrade_logic_errors():
    engine = MemoryPolicyEngine()
    e = engine.ingest_raw(content="test content", field="codigo")
    
    # 1. Promote to current or lower should fail
    with pytest.raises(ValueError, match="target_level must be above current level"):
        engine.promote(entry_id=e.entry_id, target_level=MemoryLevel.RAW, approved_by="tester")
    
    # Promote to FACTS
    engine.promote(entry_id=e.entry_id, target_level=MemoryLevel.FACTS, approved_by="tester")
    
    # 2. Degrade to current or higher should fail
    with pytest.raises(ValueError, match="target_level must be below current level"):
        engine.degrade(entry_id=e.entry_id, target_level=MemoryLevel.FACTS, reason="tester")
    with pytest.raises(ValueError, match="target_level must be below current level"):
        engine.degrade(entry_id=e.entry_id, target_level=MemoryLevel.STRATEGY, reason="tester")


# --- Bounded Context: Health Monitoring (P3.5 + P3.1) ---

def test_health_monitor_slo_breach_and_snapshot():
    monitor = HealthMonitor()
    
    # Record normal latency
    monitor.record_metric("exp_latency", 10.0)
    status = monitor.status_snapshot()
    assert status["status"] == "healthy"
    assert status["breaches"] == 0
    assert status["slos"]["exp_latency"]["breached"] is False
    
    # Breach exp_latency (target < 60)
    # Mean of (10, 110) = 60. 60 >= 60 is True for condition '<'
    monitor.record_metric("exp_latency", 110.0)
    status = monitor.status_snapshot()
    assert status["status"] == "degraded"
    assert status["breaches"] == 1
    assert status["slos"]["exp_latency"]["breached"] is True
    
    # Breach more SLOs to reach critical (breaches >= 3)
    monitor.record_metric("leakage_rate", 0.5)  # Target < 0.05. Mean 0.5 > 0.05
    monitor.record_metric("dq_freshness", 20.0) # Target < 15. Mean 20.0 > 15
    
    status = monitor.status_snapshot()
    assert status["status"] == "critical"
    assert status["breaches"] == 3
    
    alerts = monitor.check_for_alerts()
    assert len(alerts) == 3
    # Check for keywords in descriptions
    assert any("Latencia" in a for a in alerts)
    assert any("leakage" in a for a in alerts)


# --- Bounded Context: API / Server Error Paths (P3.1) ---

def test_api_status_includes_health(client):
    res = client.get("/api/status", headers={"Authorization": f"Bearer {AUTH_TOKEN}"})
    assert res.status_code == 200
    data = res.get_json()
    assert "health" in data
    assert "production_ready" in data
    assert "production_gate_reason" in data
    checks = data["production_readiness_checks"]
    assert checks["oracle_model_is_real"] in (True, False)
    assert checks["bridge_jsonl_has_real_data"] in (True, False)
    assert checks["evolution_loop_active"] in (True, False)
    assert checks["memory_identity_loaded"] in (True, False)


def test_api_experiment_run_leakage_recording(client):
    before_all = client.get(
        "/api/incidents?limit=200",
        headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
    ).get_json()["incidents"]
    before_ids = {inc["incident_id"] for inc in before_all}
    before_open_count = client.get(
        "/api/incidents?status=open&limit=200",
        headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
    ).get_json()["count"]

    # Mock behavior to trigger leakage
    with patch("cgalpha_v3.application.experiment_runner.ExperimentRunner.run_experiment") as mock_run:
        from cgalpha_v3.data_quality.gates import TemporalLeakageError
        mock_run.side_effect = TemporalLeakageError("Simulated leakage")
        
        # Propose first
        client.post("/api/experiment/propose", 
                    headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
                    json={"hypothesis": "Leakage test"})
        
        res = client.post("/api/experiment/run", 
                         headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
                         json={"mock_rows": 100})
        
        assert res.status_code == 400
        assert res.get_json()["error"] == "temporal_leakage"
        
        # Verify health monitor recorded it (via /api/status)
        status_res = client.get("/api/status", headers={"Authorization": f"Bearer {AUTH_TOKEN}"})
        health = status_res.get_json()["health"]
        assert health["slos"]["leakage_rate"]["current"] == 1.0

    after_open_count = client.get(
        "/api/incidents?status=open&limit=200",
        headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
    ).get_json()["count"]
    assert after_open_count == before_open_count

    after_all = client.get(
        "/api/incidents?limit=200",
        headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
    ).get_json()["incidents"]
    new_simulated = [
        inc for inc in after_all
        if inc["incident_id"] not in before_ids and "simulated leakage" in inc["event"].lower()
    ]
    assert new_simulated
    assert new_simulated[0]["incident_type"] == "simulated"
    assert new_simulated[0]["status"] == "resolved"


def test_api_library_error_paths(client):
    # Missing fields in ingest
    res = client.post("/api/library/ingest", 
                     headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
                     json={"title": "Missing abstract"})
    assert res.status_code == 400
    assert "missing_fields" in res.get_json()["error"]

    # Invalid source_type
    res = client.post("/api/library/ingest", 
                     headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
                     json={
                         "title": "T", "abstract": "A", "year": 2020, 
                         "source_type": "invalid"
                     })
    assert res.status_code == 400
    assert "invalid_source_type" in res.get_json()["error"]

    # Source not found
    res = client.get("/api/library/sources/non-existent-id", 
                    headers={"Authorization": f"Bearer {AUTH_TOKEN}"})
    assert res.status_code == 404


def test_api_learning_memory_error_paths(client):
    # Ingest error cases
    res = client.post("/api/learning/memory/ingest", headers={"Authorization": f"Bearer {AUTH_TOKEN}"}, json={})
    assert res.status_code == 400
    assert res.get_json()["error"] == "content_required"

    res = client.post("/api/learning/memory/ingest", headers={"Authorization": f"Bearer {AUTH_TOKEN}"}, json={"content": "C", "field": "invalid"})
    assert res.status_code == 400
    assert res.get_json()["error"] == "invalid_field"

    res = client.post("/api/learning/memory/ingest", headers={"Authorization": f"Bearer {AUTH_TOKEN}"}, json={"content": "C", "field": "codigo", "source_type": "bad"})
    assert res.status_code == 400
    assert res.get_json()["error"] == "invalid_source_type"

    # Promote error cases
    res = client.post("/api/learning/memory/promote", headers={"Authorization": f"Bearer {AUTH_TOKEN}"}, json={})
    assert res.status_code == 400
    assert res.get_json()["error"] == "entry_id_required"

    res = client.post("/api/learning/memory/promote", headers={"Authorization": f"Bearer {AUTH_TOKEN}"}, json={"entry_id": "X"})
    assert res.status_code == 400
    assert res.get_json()["error"] == "target_level_required"

    res = client.post("/api/learning/memory/promote", headers={"Authorization": f"Bearer {AUTH_TOKEN}"}, json={"entry_id": "X", "target_level": "none"})
    assert res.status_code == 400
    assert "invalid_level" in res.get_json()["error"]

    # Regime check error cases
    res = client.post("/api/learning/memory/regime/check", headers={"Authorization": f"Bearer {AUTH_TOKEN}"}, json={})
    assert res.status_code == 400
    assert res.get_json()["error"] == "volatility_series_required"

    res = client.post("/api/learning/memory/regime/check", headers={"Authorization": f"Bearer {AUTH_TOKEN}"}, json={"volatility_series": ["bad"]})
    assert res.status_code == 400
    assert "invalid_volatility_series" in res.get_json()["error"]


def test_api_rollback_error_paths(client):
    # Restore missing path
    res = client.post("/api/rollback/restore", headers={"Authorization": f"Bearer {AUTH_TOKEN}"}, json={})
    assert res.status_code == 400
    assert res.get_json()["error"] == "path_required"

    # Restore invalid path
    res = client.post("/api/rollback/restore", headers={"Authorization": f"Bearer {AUTH_TOKEN}"}, json={"path": "/none"})
    assert res.status_code == 500  # Exception caught as 500


def test_api_auth_failure(client):
    res = client.get("/api/status", headers={"Authorization": "Bearer bad"})
    assert res.status_code == 401


def test_api_events_limit(client):
    res = client.get("/api/events?limit=invalid", headers={"Authorization": f"Bearer {AUTH_TOKEN}"})
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)
