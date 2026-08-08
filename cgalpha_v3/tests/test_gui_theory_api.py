from __future__ import annotations

from pathlib import Path

import pytest

from cgalpha_v3.gui import server
from cgalpha_v3.lila.library_manager import LibraryManager


def _auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {server.AUTH_TOKEN}"}


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_landscape_project(root: Path) -> None:
    _write(
        root / "config.py",
        """
SETTINGS = {
    "volume_threshold": 1.2,
    "quality_threshold": 0.45,
    "min_confidence": 0.70,
    "max_drawdown_session_pct": 5.0,
    "max_position_size_pct": 2.0,
    "max_signals_per_hour": 10,
    "min_signal_quality_score": 0.65,
    "lookback_candles": 30,
    "atr_period": 14,
    "atr_multiplier": 1.5,
    "retest_timeout_bars": 40,
    "slippage_bps": 2.0,
    "fee_taker_pct": 0.04,
    "cooldown_seconds": 300,
    "retrain_interval_hours": 24,
    "max_tokens": 1000
}
""",
    )
    _write(root / "lila/llm/proposer.py", "volume_threshold = 1.2\n")
    _write(root / "application/change_proposer.py", "min_confidence = 0.7\n")
    _write(root / "application/pipeline.py", "max_drawdown_session_pct = 5.0\n")


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


def test_theory_live_requires_auth(client):
    resp = client.get("/api/theory/live")
    assert resp.status_code == 401


def test_p1_5_primary_source_gap_runtime_detection(client):
    ingest = client.post(
        "/api/library/ingest",
        json={
            "title": "Blog only signal claim",
            "authors": "Anon",
            "year": 2024,
            "source_type": "tertiary",
            "venue": "forum",
            "abstract": "Observation without peer review",
            "relevant_finding": "Momentum works always",
            "applicability": "none",
        },
        headers=_auth_headers(),
    )
    assert ingest.status_code == 200
    source_id = ingest.get_json()["source"]["source_id"]

    validate = client.post(
        "/api/library/claims/validate",
        json={
            "claim": "Momentum intradia robusto",
            "source_ids": [source_id],
            "auto_backlog": True,
            "requested_by": "gui_test",
        },
        headers=_auth_headers(),
    )
    assert validate.status_code == 200
    body = validate.get_json()
    assert body["primary_source_gap"] is True
    assert body["claim_ok"] is False
    assert body["backlog_item_id"] is not None

    status = client.get("/api/status", headers=_auth_headers())
    assert status.status_code == 200
    assert status.get_json()["primary_source_gap"] is True


def test_p1_6_backlog_engine_create_list_resolve(client):
    create = client.post(
        "/api/lila/backlog",
        json={
            "title": "Need primary study for regime filter",
            "rationale": "Evidence gap found in runtime",
            "item_type": "theory_request",
            "impact": 4,
            "risk": 3,
            "evidence_gap": 5,
            "requested_by": "auditor",
            "claim": "Regime filter X",
            "related_source_ids": "src-a,src-b",
            "recommended_source_type": "primary",
        },
        headers=_auth_headers(),
    )
    assert create.status_code == 200
    item = create.get_json()
    assert item["item_type"] == "theory_request"
    assert item["priority_score"] > 0

    listed = client.get("/api/lila/backlog?status=open&limit=20", headers=_auth_headers())
    assert listed.status_code == 200
    list_body = listed.get_json()
    assert list_body["count"] >= 1
    assert any(i["item_id"] == item["item_id"] for i in list_body["items"])

    resolved = client.post(
        f"/api/lila/backlog/{item['item_id']}/resolve",
        json={"resolution_note": "Covered by new primary source"},
        headers=_auth_headers(),
    )
    assert resolved.status_code == 200
    assert resolved.get_json()["status"] == "resolved"


def test_p1_11_theory_live_connected_to_lila_snapshot(client):
    payloads = [
        {
            "title": "Primary paper",
            "authors": "Alice",
            "year": 2023,
            "source_type": "primary",
            "venue": "Journal of Finance",
            "abstract": "Primary evidence text",
            "relevant_finding": "edge",
            "applicability": "filter",
        },
        {
            "title": "Secondary note",
            "authors": "Bob",
            "year": 2025,
            "source_type": "secondary",
            "venue": "Blog",
            "abstract": "Secondary evidence text",
            "relevant_finding": "note",
            "applicability": "context",
        },
    ]
    for payload in payloads:
        resp = client.post("/api/library/ingest", json=payload, headers=_auth_headers())
        assert resp.status_code == 200

    theory = client.get("/api/theory/live", headers=_auth_headers())
    assert theory.status_code == 200
    body = theory.get_json()
    assert body["library"]["total_docs"] == 2
    assert body["counts"]["primary"] == 1
    assert body["counts"]["secondary"] == 1
    assert body["primary_source_gap_open"] is False
    assert len(body["recent_sources"]) == 2
    assert "backlog" in body


def test_evolution_landscape_end_to_end_via_api(client, tmp_path: Path):
    project_root = tmp_path / "project"
    _build_landscape_project(project_root)

    server._evolution_orchestrator.project_root = project_root
    server._evolution_orchestrator.landscape_artifact_path = tmp_path / "data" / "parameter_landscape_map.json"
    server._evolution_orchestrator.memory.MEMORY_DIR = tmp_path / "memory_entries"
    server._evolution_orchestrator.memory.IDENTITY_DIR = tmp_path / "identity"

    propose_resp = client.post(
        "/api/evolution/landscape/propose",
        json={"requested_by": "gui_test"},
    )
    assert propose_resp.status_code == 200
    proposal_id = propose_resp.get_json()["proposal_id"]
    assert proposal_id

    approve_resp = client.post(f"/api/evolution/proposal/{proposal_id}/approve")
    assert approve_resp.status_code == 200
    assert approve_resp.get_json()["status"] == "SUCCESS"

    artifact_resp = client.get("/api/evolution/landscape")
    assert artifact_resp.status_code == 200
    artifact = artifact_resp.get_json()
    assert artifact["parameter_count"] >= 15
