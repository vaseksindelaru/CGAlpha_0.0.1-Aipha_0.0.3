"""
Tests — Iteration Artifacts via GUI runtime cycles (cgalpha_v3)

Valida:
  - generación automática de iteration_summary.md + iteration_status.json
  - creación de carpetas únicas por ciclo en mismo minuto
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json

import pytest

from cgalpha_v3.gui import server


def _auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {server.AUTH_TOKEN}"}


@pytest.fixture(autouse=True)
def reset_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(server, "MEMORY_DIR", tmp_path / "memory")
    server._events_log.clear()
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
        }
    )


@pytest.fixture
def client():
    server.app.config["TESTING"] = True
    with server.app.test_client() as c:
        yield c


def test_risk_cycle_generates_iteration_artifacts(client):
    payload = {
        "max_drawdown_session_pct": 4.5,
        "max_position_size_pct": 1.5,
        "max_signals_per_hour": 8,
        "min_signal_quality_score": 0.72,
    }
    resp = client.post("/api/risk/params", json=payload, headers=_auth_headers())
    assert resp.status_code == 200

    iterations_dir = server.MEMORY_DIR / "iterations"
    created = sorted(d for d in iterations_dir.iterdir() if d.is_dir())
    assert len(created) == 1

    summary_path = created[0] / "iteration_summary.md"
    status_path = created[0] / "iteration_status.json"
    assert summary_path.exists()
    assert status_path.exists()

    status = json.loads(status_path.read_text())
    assert status["trigger"] == "risk_params_set"
    assert status["risk_parameters"]["max_drawdown_session_pct"] == 4.5
    assert status["risk_parameters"]["max_position_size_pct"] == 1.5
    assert status["risk_parameters"]["max_signals_per_hour"] == 8
    assert status["risk_parameters"]["min_signal_quality_score"] == 0.72
    assert any("Parámetros de riesgo actualizados" in ev for ev in status["gui_events_published"])

    summary = summary_path.read_text()
    assert "Registro automático de ciclo real GUI" in summary
    assert "risk_params_set" in summary


def test_multiple_cycles_create_unique_iteration_directories(client):
    resp_arm = client.post("/api/kill-switch/arm", headers=_auth_headers())
    assert resp_arm.status_code == 200

    resp_confirm = client.post("/api/kill-switch/confirm", headers=_auth_headers())
    assert resp_confirm.status_code == 200

    iterations_dir = server.MEMORY_DIR / "iterations"
    created = sorted(d for d in iterations_dir.iterdir() if d.is_dir())
    assert len(created) == 2
    assert len({d.name for d in created}) == 2

    triggers = []
    for d in created:
        status = json.loads((d / "iteration_status.json").read_text())
        triggers.append(status["trigger"])

    assert "kill_switch_arm" in triggers
    assert "kill_switch_confirm" in triggers
