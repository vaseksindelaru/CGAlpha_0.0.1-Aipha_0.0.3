from __future__ import annotations

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


def test_learning_memory_endpoints_require_auth(client):
    assert client.get("/api/learning/memory/status").status_code == 401
    assert client.post("/api/learning/memory/ingest", json={}).status_code == 401


def test_p2_1_to_p2_3_learning_memory_runtime(client):
    ingest = client.post(
        "/api/learning/memory/ingest",
        json={
            "content": "Lila validated claim and updated evidence map",
            "field": "memory_librarian",
            "source_type": "secondary",
            "tags": "lila,library",
            "auto_normalize": True,
        },
        headers=_auth_headers(),
    )
    assert ingest.status_code == 200
    entry = ingest.get_json()["entry"]
    assert entry["field"] == "memory_librarian"
    assert entry["level"] in ("0a", "0b")

    status = client.get("/api/learning/memory/status", headers=_auth_headers())
    assert status.status_code == 200
    body = status.get_json()
    assert body["fields"]["memory_librarian"] >= 1
    assert body["total_entries"] >= 1

    promote = client.post(
        "/api/learning/memory/promote",
        json={"entry_id": entry["entry_id"], "target_level": "1", "approved_by": "Lila"},
        headers=_auth_headers(),
    )
    assert promote.status_code == 200
    assert promote.get_json()["entry"]["level"] == "1"

    retention = client.post("/api/learning/memory/retention/run", json={}, headers=_auth_headers())
    assert retention.status_code == 200
    assert "retention" in retention.get_json()


def test_p2_4_regime_shift_runtime_api(client):
    ingest = client.post(
        "/api/learning/memory/ingest",
        json={"content": "strategy memory", "field": "trading", "auto_normalize": True},
        headers=_auth_headers(),
    )
    entry_id = ingest.get_json()["entry"]["entry_id"]
    client.post(
        "/api/learning/memory/promote",
        json={"entry_id": entry_id, "target_level": "3", "approved_by": "human"},
        headers=_auth_headers(),
    )
    client.post(
        "/api/learning/memory/promote",
        json={"entry_id": entry_id, "target_level": "4", "approved_by": "human"},
        headers=_auth_headers(),
    )

    historic = [0.7 + (i * 0.01) for i in range(25)]
    recent = [3.2 + (i * 0.04) for i in range(20)]
    check = client.post(
        "/api/learning/memory/regime/check",
        json={"volatility_series": historic + recent},
        headers=_auth_headers(),
    )
    assert check.status_code == 200
    out = check.get_json()
    assert out["result"]["regime_shift"] is True


def test_identity_promotion_requires_explicit_confirmation(client):
    ingest = client.post(
        "/api/learning/memory/ingest",
        json={"content": "mantra", "field": "architect", "auto_normalize": True},
        headers=_auth_headers(),
    )
    assert ingest.status_code == 200
    entry_id = ingest.get_json()["entry"]["entry_id"]

    for target in ("1", "2", "3"):
        res = client.post(
            "/api/learning/memory/promote",
            json={"entry_id": entry_id, "target_level": target, "approved_by": "human"},
            headers=_auth_headers(),
        )
        assert res.status_code == 200

    denied = client.post(
        "/api/learning/memory/promote",
        json={"entry_id": entry_id, "target_level": "5", "approved_by": "human"},
        headers=_auth_headers(),
    )
    assert denied.status_code == 403
    assert denied.get_json()["error"] == "identity_confirmation_required"

    allowed = client.post(
        "/api/learning/memory/promote",
        json={
            "entry_id": entry_id,
            "target_level": "5",
            "approved_by": "human",
            "identity_confirmation": f"PROMOTE_IDENTITY:{entry_id}",
        },
        headers=_auth_headers(),
    )
    assert allowed.status_code == 200
    assert allowed.get_json()["entry"]["level"] == "5"
