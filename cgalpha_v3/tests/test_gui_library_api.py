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


def test_library_status_requires_auth(client):
    resp = client.get("/api/library/status")
    assert resp.status_code == 401


def test_p0_1_dashboard_panels_visible_in_status_and_html(client):
    status = client.get("/api/status", headers=_auth_headers())
    assert status.status_code == 200
    body = status.get_json()
    assert set(["mission_control", "market_live", "risk_dashboard"]).issubset(set(body["panels_active"]))

    html_path = Path(server.STATIC_DIR) / "index.html"
    html = html_path.read_text(encoding="utf-8")
    assert "Mission Control" in html
    assert "Market Live" in html
    assert "Risk Dashboard" in html


def test_library_ingest_and_search_roundtrip(client):
    payload = {
        "title": "Momentum Regimes in Crypto",
        "authors": "Alice Doe, Bob Roe",
        "year": 2024,
        "source_type": "primary",
        "venue": "Journal of Finance",
        "abstract": "We test momentum effects in BTC and ETH.",
        "relevant_finding": "Momentum persists in selected regimes.",
        "applicability": "Useful for signal filtering.",
        "tags": "momentum,crypto",
    }
    ingest = client.post("/api/library/ingest", json=payload, headers=_auth_headers())
    assert ingest.status_code == 200
    ingest_body = ingest.get_json()
    assert ingest_body["is_new"] is True
    source_id = ingest_body["source"]["source_id"]

    status = client.get("/api/library/status", headers=_auth_headers())
    assert status.status_code == 200
    st = status.get_json()
    assert st["total_docs"] == 1
    assert st["counts"]["primary"] == 1
    assert st["primary_ratio"] == 1.0

    query = client.get("/api/library/sources?query=momentum", headers=_auth_headers())
    assert query.status_code == 200
    qr = query.get_json()
    assert qr["count"] == 1
    assert qr["results"][0]["source_id"] == source_id

    detail = client.get(f"/api/library/sources/{source_id}", headers=_auth_headers())
    assert detail.status_code == 200
    dt = detail.get_json()
    assert dt["title"] == payload["title"]
    assert "momentum" in dt["tags"]


def test_library_duplicate_detection(client):
    p1 = {
        "title": "Same Paper",
        "year": 2024,
        "source_type": "primary",
        "venue": "NeurIPS",
        "abstract": "Same abstract text.",
    }
    p2 = {
        "title": "Same Paper",
        "year": 2024,
        "source_type": "secondary",
        "venue": "Blog",
        "abstract": "Same abstract text.",
    }
    r1 = client.post("/api/library/ingest", json=p1, headers=_auth_headers())
    assert r1.status_code == 200
    first_id = r1.get_json()["source"]["source_id"]

    r2 = client.post("/api/library/ingest", json=p2, headers=_auth_headers())
    assert r2.status_code == 200
    body = r2.get_json()
    assert body["is_new"] is False
    assert body["source"]["duplicate_of"] == first_id


def test_library_ingest_rejects_invalid_source_type(client):
    payload = {
        "title": "Invalid Type",
        "year": 2024,
        "source_type": "invalid",
        "abstract": "x",
    }
    resp = client.post("/api/library/ingest", json=payload, headers=_auth_headers())
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "invalid_source_type"
