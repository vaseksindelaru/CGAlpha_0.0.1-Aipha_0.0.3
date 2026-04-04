from __future__ import annotations

from datetime import datetime, timedelta, timezone

from cgalpha_v3.domain.models.signal import MemoryLevel
from cgalpha_v3.learning.memory_policy import MemoryPolicyEngine


def test_p2_1_memory_librarian_field_active():
    engine = MemoryPolicyEngine()
    entry = engine.ingest_raw(content="library event", field="memory_librarian")
    assert entry.field == "memory_librarian"
    snap = engine.snapshot()
    assert snap["fields"]["memory_librarian"] >= 1


def test_p2_2_policy_promote_and_degrade():
    engine = MemoryPolicyEngine()
    entry = engine.ingest_raw(content="raw", field="trading")
    engine.normalize(entry.entry_id)
    promoted = engine.promote(
        entry_id=entry.entry_id,
        target_level=MemoryLevel.FACTS,
        approved_by="Lila",
    )
    assert promoted.level == MemoryLevel.FACTS
    degraded = engine.degrade(
        entry_id=entry.entry_id,
        target_level=MemoryLevel.NORMALIZED,
        reason="contradiction",
    )
    assert degraded.level == MemoryLevel.NORMALIZED
    assert degraded.stale is True


def test_p2_3_ttl_retention_removes_expired_entries():
    engine = MemoryPolicyEngine()
    now = datetime.now(timezone.utc)
    entry = engine.ingest_raw(content="short lived", field="codigo", now=now)
    result = engine.apply_ttl_retention(now=now + timedelta(hours=25))
    assert entry.entry_id in result["removed_ids"]
    assert result["removed_count"] == 1


def test_p2_4_regime_shift_degrades_high_levels():
    engine = MemoryPolicyEngine()
    e = engine.ingest_raw(content="strategy note", field="trading")
    engine.normalize(e.entry_id)
    engine.promote(entry_id=e.entry_id, target_level=MemoryLevel.FACTS, approved_by="Lila")
    engine.promote(entry_id=e.entry_id, target_level=MemoryLevel.RELATIONS, approved_by="Lila")
    engine.promote(entry_id=e.entry_id, target_level=MemoryLevel.PLAYBOOKS, approved_by="human")
    engine.promote(entry_id=e.entry_id, target_level=MemoryLevel.STRATEGY, approved_by="human")

    historic = [0.7 + (i * 0.01) for i in range(25)]
    recent_shift = [3.0 + (i * 0.05) for i in range(20)]
    out = engine.detect_and_apply_regime_shift(historic + recent_shift)
    assert out["regime_shift"] is True
    assert engine.entries[e.entry_id].level in (MemoryLevel.PLAYBOOKS, MemoryLevel.RELATIONS)
    assert engine.entries[e.entry_id].stale is True


def test_list_entries_filtering():
    engine = MemoryPolicyEngine()
    engine.ingest_raw(content="c1", field="codigo")
    engine.ingest_raw(content="c2", field="codigo")
    e3 = engine.ingest_raw(content="m1", field="math")
    engine.normalize(e3.entry_id)

    # Filter by field
    codigo_entries = engine.list_entries(field="codigo")
    assert len(codigo_entries) == 2
    assert all(e.field == "codigo" for e in codigo_entries)

    # Filter by level
    norm_entries = engine.list_entries(level=MemoryLevel.NORMALIZED)
    assert len(norm_entries) == 1
    assert norm_entries[0].content == "m1"

    # Both
    results = engine.list_entries(level=MemoryLevel.RAW, field="math")
    assert len(results) == 0


def test_parse_level_aliases():
    engine = MemoryPolicyEngine()
    assert engine.parse_level("0a") == MemoryLevel.RAW
    assert engine.parse_level("RAW") == MemoryLevel.RAW
    assert engine.parse_level(" 3 ") == MemoryLevel.PLAYBOOKS
    assert engine.parse_level("playbooks") == MemoryLevel.PLAYBOOKS
    try:
        engine.parse_level("invalid")
    except ValueError as e:
        assert "invalid_level" in str(e)
