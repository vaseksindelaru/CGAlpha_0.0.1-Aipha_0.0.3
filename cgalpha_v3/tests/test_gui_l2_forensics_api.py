from __future__ import annotations

import json
from pathlib import Path

import pytest

from cgalpha_v3.gui import server


def _auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {server.AUTH_TOKEN}"}


class _DummyMonitor:
    def __init__(self, pending_summary: list[dict] | None = None, pending_count: int = 0, resolved_count: int = 0):
        self._pending_summary = pending_summary or []
        self._pending_count = pending_count
        self._resolved_count = resolved_count

    def get_pending_summary(self):
        return self._pending_summary

    def get_pending_count(self):
        return self._pending_count

    def get_resolved_count(self):
        return self._resolved_count


class _DummyAdapter:
    def __init__(self, monitor: _DummyMonitor):
        self.deferred_monitor = monitor


@pytest.fixture
def client():
    server.app.config["TESTING"] = True
    with server.app.test_client() as c:
        yield c


def test_l2_forensics_status_uses_disk_fallback_when_in_memory_is_empty(
    client,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    op_dir = tmp_path / "aipha_memory" / "operational"
    op_dir.mkdir(parents=True, exist_ok=True)

    (op_dir / "pending_labels.json").write_text(json.dumps([
        {
            "sample_id": "re_disk_001",
            "zone_direction": "bullish",
            "entry_price": 100.5,
            "bars_elapsed": 3,
            "lookahead_bars": 8,
            "mfe": 12.34,
            "mae": 4.56,
        }
    ]))

    (op_dir / "training_dataset_v2.jsonl").write_text(
        json.dumps({"outcome": {"label": "BREAKOUT"}}) + "\n" +
        json.dumps({"outcome": {"label": "BOUNCE_STRONG"}}) + "\n"
    )

    monitor = _DummyMonitor(pending_summary=[], pending_count=0, resolved_count=0)
    monkeypatch.setattr(server, "project_root", tmp_path)
    monkeypatch.setattr(server, "_adapters", {"BTCUSDT": _DummyAdapter(monitor)})

    res = client.get("/api/l2-forensics/status", headers=_auth_headers())
    assert res.status_code == 200
    body = res.get_json()

    assert body["pending_count"] == 1
    assert body["pending_source"] == "disk_fallback"
    assert body["dataset_total"] == 2
    assert body["outcome_distribution"]["BREAKOUT"] == 1
    assert body["outcome_distribution"]["BOUNCE_STRONG"] == 1
    assert body["active_monitors"][0]["sample_id"] == "re_disk_001"


def test_l2_forensics_status_prefers_in_memory_when_available(
    client,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    op_dir = tmp_path / "aipha_memory" / "operational"
    op_dir.mkdir(parents=True, exist_ok=True)

    (op_dir / "pending_labels.json").write_text(json.dumps([
        {
            "sample_id": "re_disk_999",
            "zone_direction": "bearish",
            "entry_price": 99.1,
            "bars_elapsed": 5,
            "lookahead_bars": 9,
            "mfe": 2.0,
            "mae": 3.0,
        }
    ]))
    (op_dir / "training_dataset_v2.jsonl").write_text("")

    memory_pending = [{
        "sample_id": "re_mem_001",
        "direction": "bullish",
        "entry_price": 101.0,
        "bars_elapsed": 1,
        "lookahead_bars": 7,
        "mfe": 0.0,
        "mae": 0.2,
    }]
    monitor = _DummyMonitor(pending_summary=memory_pending, pending_count=1, resolved_count=2)
    monkeypatch.setattr(server, "project_root", tmp_path)
    monkeypatch.setattr(server, "_adapters", {"BTCUSDT": _DummyAdapter(monitor)})

    res = client.get("/api/l2-forensics/status", headers=_auth_headers())
    assert res.status_code == 200
    body = res.get_json()

    assert body["pending_count"] == 1
    assert body["pending_source"] == "in_memory"
    assert body["resolved_count"] == 2
    assert body["active_monitors"][0]["sample_id"] == "re_mem_001"
