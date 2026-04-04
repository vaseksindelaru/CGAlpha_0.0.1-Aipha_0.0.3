from __future__ import annotations

import json
from pathlib import Path

import pytest

from cgalpha_v3.gui import server
from cgalpha_v3.learning.memory_policy import MemoryPolicyEngine
from cgalpha_v3.lila.library_manager import LibraryManager


def _auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {server.AUTH_TOKEN}"}


@pytest.fixture(autouse=True)
def reset_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(server, "MEMORY_DIR", tmp_path / "memory")
    monkeypatch.setattr(server, "DOCS_DIR", tmp_path / "docs")
    monkeypatch.setattr(server, "_lila_mgr", LibraryManager())
    monkeypatch.setattr(server, "_memory_engine", MemoryPolicyEngine())
    server._incident_registry.clear()
    server._adr_registry.clear()
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
            "regime_shift_active": False,
            "panels_active": ["mission_control", "market_live", "risk_dashboard"],
        }
    )


@pytest.fixture
def client():
    server.app.config["TESTING"] = True
    with server.app.test_client() as c:
        yield c


def test_incident_and_adr_endpoints_require_auth(client):
    assert client.get("/api/incidents").status_code == 401
    assert client.post("/api/incidents/inc-1234/resolve", json={}).status_code == 401
    assert client.get("/api/adr/recent").status_code == 401


def test_p2_9_incident_response_runtime_wiring(client):
    arm = client.post("/api/kill-switch/arm", headers=_auth_headers())
    assert arm.status_code == 200
    confirm = client.post("/api/kill-switch/confirm", headers=_auth_headers())
    assert confirm.status_code == 200

    listed = client.get("/api/incidents?status=open&limit=20", headers=_auth_headers())
    assert listed.status_code == 200
    payload = listed.get_json()
    assert payload["count"] >= 2
    assert len(payload["incidents"]) >= 2

    newest = payload["incidents"][0]
    assert newest["priority"] in {"P0", "P1"}
    assert newest["status"] == "open"
    post_mortem = Path(newest["post_mortem_path"])
    assert post_mortem.exists()
    assert "Post-Mortem" in post_mortem.read_text()


def test_p2_10_adr_per_iteration_and_incident_resolution(client):
    arm = client.post("/api/kill-switch/arm", headers=_auth_headers())
    assert arm.status_code == 200

    incidents = client.get("/api/incidents?status=open", headers=_auth_headers())
    incident = incidents.get_json()["incidents"][0]
    incident_id = incident["incident_id"]

    resolved = client.post(
        f"/api/incidents/{incident_id}/resolve",
        json={"resolution_note": "validated by test"},
        headers=_auth_headers(),
    )
    assert resolved.status_code == 200
    resolved_body = resolved.get_json()
    assert resolved_body["status"] == "resolved"
    assert resolved_body["resolution_note"] == "validated by test"

    stored_json = server.MEMORY_DIR / "incidents" / f"{incident_id}.json"
    assert stored_json.exists()
    stored = json.loads(stored_json.read_text())
    assert stored["status"] == "resolved"

    resolved_list = client.get("/api/incidents?status=resolved", headers=_auth_headers())
    resolved_items = resolved_list.get_json()["incidents"]
    assert any(item["incident_id"] == incident_id for item in resolved_items)

    adrs = client.get("/api/adr/recent?limit=20", headers=_auth_headers())
    assert adrs.status_code == 200
    body = adrs.get_json()
    assert body["count"] >= 2
    assert len(body["adrs"]) >= 2
    assert Path(body["adrs"][0]["path"]).exists()
