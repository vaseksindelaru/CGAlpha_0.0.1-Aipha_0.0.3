"""
cgAlpha_0.0.1 — Tests for Memory v4 IDENTITY level
====================================================
Tests for ACCIÓN 1: IDENTITY memory level, load_from_disk,
persistence, and regime shift immunity.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cgalpha_v3.domain.models.signal import MemoryLevel
from cgalpha_v3.learning.memory_policy import MemoryPolicyEngine


def test_identity_level_exists():
    assert MemoryLevel.IDENTITY.value == "5"


def test_identity_ttl_is_infinite():
    assert MemoryPolicyEngine.TTL_BY_LEVEL_HOURS[MemoryLevel.IDENTITY] is None


def test_identity_requires_human_approval():
    engine = MemoryPolicyEngine()
    entry = engine.ingest_raw(content="test", field="architect")
    # Promote through intermediate levels first
    engine.promote(entry_id=entry.entry_id, target_level=MemoryLevel.NORMALIZED,
                   approved_by="auto")
    engine.promote(entry_id=entry.entry_id, target_level=MemoryLevel.FACTS,
                   approved_by="Lila")
    engine.promote(entry_id=entry.entry_id, target_level=MemoryLevel.RELATIONS,
                   approved_by="Lila")
    engine.promote(entry_id=entry.entry_id, target_level=MemoryLevel.PLAYBOOKS,
                   approved_by="human")
    engine.promote(entry_id=entry.entry_id, target_level=MemoryLevel.STRATEGY,
                   approved_by="human")
    with pytest.raises(ValueError, match="approved_by='human'"):
        engine.promote(
            entry_id=entry.entry_id,
            target_level=MemoryLevel.IDENTITY,
            approved_by="Lila"
        )


def test_identity_promotion_succeeds_with_human():
    engine = MemoryPolicyEngine()
    entry = engine.ingest_raw(content="mantra", field="architect")
    engine.promote(entry_id=entry.entry_id, target_level=MemoryLevel.NORMALIZED,
                   approved_by="auto")
    engine.promote(entry_id=entry.entry_id, target_level=MemoryLevel.FACTS,
                   approved_by="Lila")
    engine.promote(entry_id=entry.entry_id, target_level=MemoryLevel.RELATIONS,
                   approved_by="Lila")
    engine.promote(entry_id=entry.entry_id, target_level=MemoryLevel.PLAYBOOKS,
                   approved_by="human")
    engine.promote(entry_id=entry.entry_id, target_level=MemoryLevel.STRATEGY,
                   approved_by="human")
    result = engine.promote(
        entry_id=entry.entry_id,
        target_level=MemoryLevel.IDENTITY,
        approved_by="human"
    )
    assert result.level == MemoryLevel.IDENTITY
    assert result.expires_at is None


def test_identity_not_degraded_by_regime_shift():
    engine = MemoryPolicyEngine()
    entry = engine.ingest_raw(content="mantra", field="architect")
    # Fast-track to IDENTITY
    engine.promote(entry_id=entry.entry_id, target_level=MemoryLevel.NORMALIZED,
                   approved_by="auto")
    engine.promote(entry_id=entry.entry_id, target_level=MemoryLevel.FACTS,
                   approved_by="Lila")
    engine.promote(entry_id=entry.entry_id, target_level=MemoryLevel.RELATIONS,
                   approved_by="Lila")
    engine.promote(entry_id=entry.entry_id, target_level=MemoryLevel.PLAYBOOKS,
                   approved_by="human")
    engine.promote(entry_id=entry.entry_id, target_level=MemoryLevel.STRATEGY,
                   approved_by="human")
    engine.promote(entry_id=entry.entry_id, target_level=MemoryLevel.IDENTITY,
                   approved_by="human")

    # Extreme regime shift
    vol_series = [1.0] * 40 + [10.0] * 20
    result = engine.detect_and_apply_regime_shift(vol_series)

    assert engine.entries[entry.entry_id].level == MemoryLevel.IDENTITY
    assert not engine.entries[entry.entry_id].stale


def test_load_from_disk(tmp_path):
    entry_data = {
        "entry_id": "test-uuid-001",
        "level": "1",
        "content": "test content",
        "source_id": None,
        "source_type": "secondary",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        "approved_by": "auto",
        "field": "trading",
        "tags": ["test"],
        "stale": False
    }
    (tmp_path / "test-uuid-001.json").write_text(json.dumps(entry_data))

    engine = MemoryPolicyEngine()
    result = engine.load_from_disk(str(tmp_path))

    assert result["loaded"] == 1
    assert "test-uuid-001" in engine.entries
    assert engine.entries["test-uuid-001"].level == MemoryLevel.FACTS


def test_expired_entries_not_loaded(tmp_path):
    entry_data = {
        "entry_id": "expired-uuid",
        "level": "0a",
        "content": "old data",
        "created_at": "2025-01-01T00:00:00+00:00",
        "expires_at": "2025-01-02T00:00:00+00:00",
        "approved_by": "auto",
        "field": "trading",
        "tags": [],
        "stale": False
    }
    (tmp_path / "expired-uuid.json").write_text(json.dumps(entry_data))

    engine = MemoryPolicyEngine()
    result = engine.load_from_disk(str(tmp_path))

    assert result["loaded"] == 0
    assert "expired-uuid" not in engine.entries


def test_must_get_raises_on_missing():
    engine = MemoryPolicyEngine()
    with pytest.raises(KeyError, match="not found in memory"):
        engine._must_get("nonexistent-uuid")


def test_must_get_returns_existing():
    engine = MemoryPolicyEngine()
    entry = engine.ingest_raw(content="test", field="trading")
    result = engine._must_get(entry.entry_id)
    assert result.content == "test"


def test_parse_level_identity():
    assert MemoryPolicyEngine.parse_level("5") == MemoryLevel.IDENTITY
    assert MemoryPolicyEngine.parse_level("identity") == MemoryLevel.IDENTITY


def test_parse_level_invalid():
    with pytest.raises(ValueError, match="invalid_level"):
        MemoryPolicyEngine.parse_level("99")


def test_get_identity_entries():
    engine = MemoryPolicyEngine()
    e1 = engine.ingest_raw(content="fact", field="trading")
    e2 = engine.ingest_raw(content="mantra", field="architect")
    # Promote e2 to IDENTITY
    engine.promote(entry_id=e2.entry_id, target_level=MemoryLevel.NORMALIZED,
                   approved_by="auto")
    engine.promote(entry_id=e2.entry_id, target_level=MemoryLevel.FACTS,
                   approved_by="Lila")
    engine.promote(entry_id=e2.entry_id, target_level=MemoryLevel.RELATIONS,
                   approved_by="Lila")
    engine.promote(entry_id=e2.entry_id, target_level=MemoryLevel.PLAYBOOKS,
                   approved_by="human")
    engine.promote(entry_id=e2.entry_id, target_level=MemoryLevel.STRATEGY,
                   approved_by="human")
    engine.promote(entry_id=e2.entry_id, target_level=MemoryLevel.IDENTITY,
                   approved_by="human")

    identities = engine.get_identity_entries()
    assert len(identities) == 1
    assert identities[0].entry_id == e2.entry_id


def test_snapshot_includes_identity_metrics():
    engine = MemoryPolicyEngine()
    snap = engine.snapshot()
    assert "identity_entries" in snap
    assert "pending_proposals" in snap
    assert "memory_health" in snap
    assert snap["memory_health"] == "no_identity"


def test_persist_and_reload_identity(tmp_path):
    """End-to-end: create IDENTITY, persist, reload in new engine."""
    engine = MemoryPolicyEngine()
    engine.MEMORY_DIR = tmp_path / "entries"
    engine.IDENTITY_DIR = tmp_path / "identity"

    entry = engine.ingest_raw(content="mantra fundacional", field="architect")
    engine.promote(entry_id=entry.entry_id, target_level=MemoryLevel.NORMALIZED,
                   approved_by="auto")
    engine.promote(entry_id=entry.entry_id, target_level=MemoryLevel.FACTS,
                   approved_by="Lila")
    engine.promote(entry_id=entry.entry_id, target_level=MemoryLevel.RELATIONS,
                   approved_by="Lila")
    engine.promote(entry_id=entry.entry_id, target_level=MemoryLevel.PLAYBOOKS,
                   approved_by="human")
    engine.promote(entry_id=entry.entry_id, target_level=MemoryLevel.STRATEGY,
                   approved_by="human")
    engine.promote(entry_id=entry.entry_id, target_level=MemoryLevel.IDENTITY,
                   approved_by="human")

    # Verify files written
    json_path = engine.MEMORY_DIR / f"{entry.entry_id}.json"
    assert json_path.exists()
    identity_files = list(engine.IDENTITY_DIR.glob("*.json"))
    assert len(identity_files) >= 1

    # Reload in new engine
    engine2 = MemoryPolicyEngine()
    result = engine2.load_from_disk(str(engine.MEMORY_DIR))
    assert result["loaded"] >= 1
    reloaded = engine2.entries[entry.entry_id]
    assert reloaded.level == MemoryLevel.IDENTITY
    assert reloaded.content == "mantra fundacional"


def test_search_by_content():
    engine = MemoryPolicyEngine()
    engine.ingest_raw(content="Oracle training results", field="trading")
    engine.ingest_raw(content="Pipeline config update", field="architect")

    results = engine.search(query="Oracle")
    assert len(results) == 1
    assert "Oracle" in results[0].content


def test_get_pending_proposals():
    engine = MemoryPolicyEngine()
    e1 = engine.ingest_raw(content="pending proposal", field="architect",
                           tags=["pending", "cat_2"])
    engine.promote(entry_id=e1.entry_id, target_level=MemoryLevel.NORMALIZED,
                   approved_by="auto")
    engine.promote(entry_id=e1.entry_id, target_level=MemoryLevel.FACTS,
                   approved_by="Lila")
    engine.promote(entry_id=e1.entry_id, target_level=MemoryLevel.RELATIONS,
                   approved_by="Lila")

    e2 = engine.ingest_raw(content="not pending", field="trading")

    pending = engine.get_pending_proposals()
    assert len(pending) == 1
    assert pending[0].entry_id == e1.entry_id


def test_load_from_disk_corrupt_identity(tmp_path, caplog):
    corrupt = '{"level": "5", "entry_id": "bad", CORRUPTED'
    (tmp_path / "bad.json").write_text(corrupt)

    engine = MemoryPolicyEngine()
    with caplog.at_level(logging.CRITICAL):
        result = engine.load_from_disk(str(tmp_path))

    assert result["errors"] == 1
    assert result["identity_error"] is True
