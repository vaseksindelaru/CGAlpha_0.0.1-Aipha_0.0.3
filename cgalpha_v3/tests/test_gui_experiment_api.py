from __future__ import annotations

from pathlib import Path

import pytest

from cgalpha_v3.gui import server
from cgalpha_v3.lila.library_manager import LibraryManager


def _auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {server.AUTH_TOKEN}"}


@pytest.fixture(autouse=True)
def reset_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(server, "MEMORY_DIR", tmp_path / "memory")
    monkeypatch.setattr(server, "_lila_mgr", LibraryManager())
    server._events_log.clear()
    server._latest_proposal = None
    server._latest_experiment = None
    server._experiment_history.clear()
    server._system_state.update(
        {
            "phase": "FASE_0",
            "status": "idle",
            "kill_switch": "armed",
            "last_event": "Sistema inicializado",
            "circuit_breaker": "inactive",
            "drawdown_session_pct": 0.0,
            "max_drawdown_session_pct": 5.0,
            "max_position_size_pct": 2.0,
            "max_signals_per_hour": 10,
            "min_signal_quality_score": 0.65,
            "data_quality": "valid",
            "primary_source_gap": False,
            "experiment_loop_status": "idle",
            "panels_active": ["mission_control", "market_live", "risk_dashboard"],
        }
    )


@pytest.fixture
def client():
    server.app.config["TESTING"] = True
    with server.app.test_client() as c:
        yield c


def test_experiment_endpoints_require_auth(client):
    assert client.get("/api/experiment/status").status_code == 401
    assert client.post("/api/experiment/propose", json={}).status_code == 401
    assert client.post("/api/experiment/run", json={}).status_code == 401


def test_p1_8_p1_9_p1_12_propose_and_run_flow(client):
    propose = client.post(
        "/api/experiment/propose",
        json={
            "hypothesis": "Improve retest filter by quality threshold",
            "approach_types": "RETEST,BREAKOUT",
            "source_ids": "src-a,src-b",
        },
        headers=_auth_headers(),
    )
    assert propose.status_code == 200
    pbody = propose.get_json()
    assert pbody["backtesting"]["frictions"]["fee_taker_pct"] == 0.05
    assert pbody["backtesting"]["walk_forward_windows"] == 3

    run = client.post("/api/experiment/run", json={}, headers=_auth_headers())
    assert run.status_code == 200
    rbody = run.get_json()
    assert rbody["no_leakage_checked"] is True
    assert len(rbody["walk_forward_windows"]) >= 3
    assert "net_return_pct" in rbody["metrics"]
    assert "friction_cost_pct" in rbody["metrics"]
    assert "approach_type_histogram" in rbody
    assert sum(rbody["approach_type_histogram"].values()) > 0

    status = client.get("/api/experiment/status", headers=_auth_headers())
    assert status.status_code == 200
    sbody = status.get_json()
    assert sbody["status"] == "completed"
    assert sbody["has_proposal"] is True
    assert sbody["has_experiment"] is True


def test_p1_10_no_leakage_e2e_error_exposed_in_api(client):
    propose = client.post(
        "/api/experiment/propose",
        json={"hypothesis": "Leakage check", "approach_types": "TOUCH"},
        headers=_auth_headers(),
    )
    assert propose.status_code == 200

    # Forzamos timestamp contaminado en zona OOS.
    contaminated = [9_999_999_999.0]
    run = client.post(
        "/api/experiment/run",
        json={"feature_timestamps": contaminated},
        headers=_auth_headers(),
    )
    assert run.status_code == 400
    body = run.get_json()
    assert body["error"] == "temporal_leakage"

    status = client.get("/api/experiment/status", headers=_auth_headers())
    assert status.status_code == 200
    assert status.get_json()["status"] == "failed_leakage"
