from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from cgalpha_v3.gui import server


class _OracleMock:
    def __init__(self, model):
        self.model = model


def test_production_readiness_snapshot_true_when_checks_pass(tmp_path, monkeypatch):
    bridge_path = tmp_path / "aipha_memory" / "evolutionary" / "bridge.jsonl"
    bridge_path.parent.mkdir(parents=True, exist_ok=True)
    bridge_path.write_text(json.dumps({"entry_price": 25000.0}) + "\n")

    monkeypatch.setattr(server, "project_root", tmp_path)
    monkeypatch.setattr(server, "_oracle_v3", _OracleMock(model=object()))
    monkeypatch.setitem(
        server._system_state,
        "oracle",
        {
            "enabled": True,
            "min_confidence": 0.7,
            "model_type": "random_forest",
            "retrain_interval_hours": 24,
            "use_oracle_filtering": False,
        },
    )
    monkeypatch.setitem(
        server._system_state,
        "last_event_ts",
        datetime.now(timezone.utc).isoformat(),
    )

    status = server._production_readiness_snapshot(
        memory_snapshot={"identity_entries": 2, "levels": {"5": 2}}
    )

    assert status["production_ready"] is True
    assert status["checks"]["oracle_model_is_real"] is True
    assert status["checks"]["bridge_jsonl_has_real_data"] is True
    assert status["checks"]["evolution_loop_active"] is True
    assert status["checks"]["memory_identity_loaded"] is True


def test_production_readiness_snapshot_false_with_pending_checks(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "project_root", tmp_path)
    monkeypatch.setattr(server, "_oracle_v3", _OracleMock(model=None))
    monkeypatch.setitem(
        server._system_state,
        "oracle",
        {
            "enabled": False,
            "min_confidence": 0.7,
            "model_type": "placeholder",
            "retrain_interval_hours": 24,
            "use_oracle_filtering": False,
        },
    )
    monkeypatch.setitem(
        server._system_state,
        "last_event_ts",
        (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
    )

    status = server._production_readiness_snapshot(
        memory_snapshot={"identity_entries": 0, "levels": {"5": 0}}
    )

    assert status["production_ready"] is False
    assert "oracle_model_is_real" in status["production_gate_reason"]
    assert status["checks"]["oracle_model_is_real"] is False
    assert status["checks"]["bridge_jsonl_has_real_data"] is False
    assert status["checks"]["evolution_loop_active"] is False
    assert status["checks"]["memory_identity_loaded"] is False
