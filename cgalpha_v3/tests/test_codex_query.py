"""
Test suite for query_codex() and Codex persistence.

Validates that the MemoryPolicyEngine can:
1. Filter Codex entries by harness_inject_when, type, status, affects_files
2. Respect the level >= PLAYBOOKS gate
3. Require the "codex" tag
4. Sort by authority (level desc) then recency (created_at desc)
5. Persist Codex entries to both memory_entries/ and codex/<type>/
6. Parse structured JSON content via get_codex_content()
"""
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from cgalpha_v3.learning.memory_policy import MemoryPolicyEngine
from cgalpha_v3.domain.models.signal import MemoryEntry, MemoryLevel


def _make_codex_entry(
    engine: MemoryPolicyEngine,
    codex_id: str,
    entry_type: str = "DECISION",
    status: str = "ACTIVE",
    level: MemoryLevel = MemoryLevel.STRATEGY,
    inject_when: list[str] | None = None,
    affects_files: list[str] | None = None,
    affects_components: list[str] | None = None,
    categories_applicable: list[int] | None = None,
    related_entries: list[dict] | None = None,
) -> MemoryEntry:
    """Helper to create a properly structured Codex entry."""
    content = {
        "codex_id": codex_id,
        "type": entry_type,
        "version": 1,
        "schema_version": 1,
        "status": status,
        "title": f"Test entry {codex_id}",
        "statement": f"Statement for {codex_id}",
        "rationale": f"Rationale for {codex_id}",
        "evidence_ids": [],
        "affects_files": affects_files or [],
        "affects_components": affects_components or [],
        "categories_applicable": categories_applicable or [],
        "contradicts": [],
        "supersedes": None,
        "superseded_by": None,
        "related_entries": related_entries or [],
        "review_trigger": None,
        "harness_inject_when": inject_when or [],
    }

    entry = engine.ingest_raw(
        content=json.dumps(content),
        field="architect",
        tags=["codex", codex_id],
    )

    # Promote to the target level
    if level == MemoryLevel.PLAYBOOKS:
        engine.promote(
            entry_id=entry.entry_id,
            target_level=MemoryLevel.FACTS,
            approved_by="Lila",
        )
        engine.promote(
            entry_id=entry.entry_id,
            target_level=MemoryLevel.RELATIONS,
            approved_by="Lila",
        )
        engine.promote(
            entry_id=entry.entry_id,
            target_level=MemoryLevel.PLAYBOOKS,
            approved_by="human",
        )
    elif level == MemoryLevel.STRATEGY:
        engine.promote(
            entry_id=entry.entry_id,
            target_level=MemoryLevel.FACTS,
            approved_by="Lila",
        )
        engine.promote(
            entry_id=entry.entry_id,
            target_level=MemoryLevel.RELATIONS,
            approved_by="Lila",
        )
        engine.promote(
            entry_id=entry.entry_id,
            target_level=MemoryLevel.PLAYBOOKS,
            approved_by="human",
        )
        engine.promote(
            entry_id=entry.entry_id,
            target_level=MemoryLevel.STRATEGY,
            approved_by="human",
        )

    return engine.entries[entry.entry_id]


# ─────────────────────────────────────────────────────────────
# BASIC QUERY TESTS
# ─────────────────────────────────────────────────────────────


def test_query_codex_returns_only_codex_tagged_entries():
    """Entries without 'codex' tag are invisible to query_codex."""
    engine = MemoryPolicyEngine()

    # Create a STRATEGY-level entry WITHOUT the codex tag
    entry = engine.ingest_raw(
        content=json.dumps({"type": "DECISION", "status": "ACTIVE"}),
        field="architect",
        tags=["not_codex"],
    )
    engine.promote(entry_id=entry.entry_id, target_level=MemoryLevel.FACTS, approved_by="Lila")
    engine.promote(entry_id=entry.entry_id, target_level=MemoryLevel.RELATIONS, approved_by="Lila")
    engine.promote(entry_id=entry.entry_id, target_level=MemoryLevel.PLAYBOOKS, approved_by="human")
    engine.promote(entry_id=entry.entry_id, target_level=MemoryLevel.STRATEGY, approved_by="human")

    results = engine.query_codex()
    assert len(results) == 0


def test_query_codex_rejects_low_level_entries():
    """Entries at level < PLAYBOOKS are excluded even with 'codex' tag."""
    engine = MemoryPolicyEngine()

    # Create a RELATIONS-level entry WITH codex tag
    entry = engine.ingest_raw(
        content=json.dumps({"type": "DECISION", "status": "PROPOSED"}),
        field="architect",
        tags=["codex", "D-099"],
    )
    engine.promote(entry_id=entry.entry_id, target_level=MemoryLevel.FACTS, approved_by="Lila")
    engine.promote(entry_id=entry.entry_id, target_level=MemoryLevel.RELATIONS, approved_by="Lila")

    results = engine.query_codex()
    assert len(results) == 0


def test_query_codex_basic_retrieval():
    """A properly constructed Codex entry is retrieved with no filters."""
    engine = MemoryPolicyEngine()
    _make_codex_entry(engine, "D-001")

    results = engine.query_codex()
    assert len(results) == 1
    content = json.loads(results[0].content)
    assert content["codex_id"] == "D-001"


# ─────────────────────────────────────────────────────────────
# FILTER TESTS
# ─────────────────────────────────────────────────────────────


def test_query_codex_filter_inject_when():
    """Only entries matching inject_when are returned."""
    engine = MemoryPolicyEngine()
    _make_codex_entry(engine, "D-001", inject_when=["oracle_modification", "feature_proposal"])
    _make_codex_entry(engine, "D-002", inject_when=["cat2_oracle"])
    _make_codex_entry(engine, "L-001", entry_type="LESSON", inject_when=["oracle_modification"])

    results = engine.query_codex(inject_when="oracle_modification")
    codex_ids = {json.loads(r.content)["codex_id"] for r in results}
    assert codex_ids == {"D-001", "L-001"}


def test_query_codex_filter_entry_type():
    """Filter by entry type (DECISION, LESSON, BUG, etc.)."""
    engine = MemoryPolicyEngine()
    _make_codex_entry(engine, "D-001", entry_type="DECISION")
    _make_codex_entry(engine, "L-001", entry_type="LESSON", level=MemoryLevel.PLAYBOOKS)
    _make_codex_entry(engine, "B-001", entry_type="BUG", level=MemoryLevel.PLAYBOOKS)

    results = engine.query_codex(entry_type="LESSON")
    assert len(results) == 1
    assert json.loads(results[0].content)["codex_id"] == "L-001"


def test_query_codex_filter_status():
    """Filter by exact status."""
    engine = MemoryPolicyEngine()
    _make_codex_entry(engine, "D-001", status="ACTIVE")
    _make_codex_entry(engine, "D-002", status="SUPERSEDED")

    results = engine.query_codex(status="ACTIVE")
    assert len(results) == 1
    assert json.loads(results[0].content)["codex_id"] == "D-001"


def test_query_codex_filter_status_in():
    """Filter by status in a list."""
    engine = MemoryPolicyEngine()
    _make_codex_entry(engine, "D-001", status="ACTIVE")
    _make_codex_entry(engine, "D-002", status="SUPERSEDED")
    _make_codex_entry(engine, "B-001", entry_type="BUG", status="PARTIAL")

    results = engine.query_codex(status_in=["ACTIVE", "PARTIAL"])
    codex_ids = {json.loads(r.content)["codex_id"] for r in results}
    assert codex_ids == {"D-001", "B-001"}


def test_query_codex_filter_affects_files():
    """Filter by file intersection."""
    engine = MemoryPolicyEngine()
    _make_codex_entry(engine, "D-001", affects_files=["cgalpha_v3/lila/llm/oracle.py"])
    _make_codex_entry(engine, "D-002", affects_files=["cgalpha_v3/trading/shadow_trader.py"])

    results = engine.query_codex(
        affects_files=["cgalpha_v3/lila/llm/oracle.py", "cgalpha_v3/application/pipeline.py"]
    )
    assert len(results) == 1
    assert json.loads(results[0].content)["codex_id"] == "D-001"


def test_query_codex_filter_affects_components():
    """Filter by component intersection."""
    engine = MemoryPolicyEngine()
    _make_codex_entry(engine, "D-001", affects_components=["OracleTrainer_v3", "ShadowOracle"])
    _make_codex_entry(engine, "D-002", affects_components=["NexusGate"])

    results = engine.query_codex(affects_components=["OracleTrainer_v3"])
    assert len(results) == 1
    assert json.loads(results[0].content)["codex_id"] == "D-001"


def test_query_codex_filter_categories():
    """Filter by category applicability."""
    engine = MemoryPolicyEngine()
    _make_codex_entry(engine, "R-001", entry_type="RULE", categories_applicable=[2, 3])
    _make_codex_entry(engine, "R-002", entry_type="RULE", categories_applicable=[1])

    results = engine.query_codex(categories_applicable=3)
    assert len(results) == 1
    assert json.loads(results[0].content)["codex_id"] == "R-001"


def test_query_codex_combined_filters():
    """Multiple filters combine with AND logic."""
    engine = MemoryPolicyEngine()
    _make_codex_entry(engine, "D-001", status="ACTIVE", inject_when=["oracle_modification"])
    _make_codex_entry(engine, "D-002", status="ACTIVE", inject_when=["cat2_oracle"])
    _make_codex_entry(engine, "D-003", status="SUPERSEDED", inject_when=["oracle_modification"])

    results = engine.query_codex(status="ACTIVE", inject_when="oracle_modification")
    assert len(results) == 1
    assert json.loads(results[0].content)["codex_id"] == "D-001"


# ─────────────────────────────────────────────────────────────
# SORTING TESTS
# ─────────────────────────────────────────────────────────────


def test_query_codex_sorts_by_level_then_recency():
    """STRATEGY entries appear before PLAYBOOKS; newer before older."""
    engine = MemoryPolicyEngine()
    _make_codex_entry(engine, "L-001", entry_type="LESSON", level=MemoryLevel.PLAYBOOKS)
    _make_codex_entry(engine, "D-001", entry_type="DECISION", level=MemoryLevel.STRATEGY)
    _make_codex_entry(engine, "L-002", entry_type="LESSON", level=MemoryLevel.PLAYBOOKS)

    results = engine.query_codex()
    codex_ids = [json.loads(r.content)["codex_id"] for r in results]
    # D-001 (STRATEGY) first, then L-002 (newer PLAYBOOKS), then L-001 (older PLAYBOOKS)
    assert codex_ids[0] == "D-001"


def test_query_codex_max_entries_cap():
    """max_entries caps the result set."""
    engine = MemoryPolicyEngine()
    for i in range(10):
        _make_codex_entry(engine, f"D-{i:03d}")

    results = engine.query_codex(max_entries=3)
    assert len(results) == 3


# ─────────────────────────────────────────────────────────────
# CONTENT PARSER
# ─────────────────────────────────────────────────────────────


def test_get_codex_content_valid():
    """get_codex_content returns parsed dict for valid entry."""
    engine = MemoryPolicyEngine()
    entry = _make_codex_entry(engine, "D-001")

    content = engine.get_codex_content(entry)
    assert content["codex_id"] == "D-001"
    assert content["type"] == "DECISION"
    assert content["schema_version"] == 1


def test_get_codex_content_rejects_non_codex():
    """get_codex_content raises ValueError for non-Codex entries."""
    engine = MemoryPolicyEngine()
    entry = engine.ingest_raw(content="not codex", field="architect", tags=["other"])

    with pytest.raises(ValueError, match="not a Codex entry"):
        engine.get_codex_content(entry)


# ─────────────────────────────────────────────────────────────
# PERSISTENCE
# ─────────────────────────────────────────────────────────────


def test_persist_codex_entry_creates_backup(tmp_path, monkeypatch):
    """_persist_codex_entry writes to memory_entries/ AND codex/<type>/."""
    engine = MemoryPolicyEngine()
    monkeypatch.setattr(MemoryPolicyEngine, "MEMORY_DIR", tmp_path / "memory_entries")
    monkeypatch.setattr(MemoryPolicyEngine, "CODEX_DIR", tmp_path / "codex")

    entry = _make_codex_entry(engine, "D-001")
    engine._persist_codex_entry(entry)

    # Source of truth exists
    mem_file = tmp_path / "memory_entries" / f"{entry.entry_id}.json"
    assert mem_file.exists()

    # Human-readable backup exists in correct subdir
    backup_file = tmp_path / "codex" / "decisions" / "D-001.json"
    assert backup_file.exists()

    backup = json.loads(backup_file.read_text())
    assert backup["codex_id"] == "D-001"
    assert backup["type"] == "DECISION"
    assert backup["status"] == "ACTIVE"
    assert backup["schema_version"] == 1


def test_persist_codex_entry_lesson_subdir(tmp_path, monkeypatch):
    """LESSON entries go to codex/lessons/, BUG entries to codex/bugs/."""
    engine = MemoryPolicyEngine()
    monkeypatch.setattr(MemoryPolicyEngine, "MEMORY_DIR", tmp_path / "memory_entries")
    monkeypatch.setattr(MemoryPolicyEngine, "CODEX_DIR", tmp_path / "codex")

    lesson = _make_codex_entry(engine, "L-001", entry_type="LESSON", level=MemoryLevel.PLAYBOOKS)
    engine._persist_codex_entry(lesson)
    assert (tmp_path / "codex" / "lessons" / "L-001.json").exists()

    bug = _make_codex_entry(engine, "B-001", entry_type="BUG", level=MemoryLevel.PLAYBOOKS)
    engine._persist_codex_entry(bug)
    assert (tmp_path / "codex" / "bugs" / "B-001.json").exists()


# ─────────────────────────────────────────────────────────────
# SCHEMA VALIDATION: related_entries field
# ─────────────────────────────────────────────────────────────


def test_codex_entry_supports_related_entries():
    """related_entries field is preserved in Codex entries (empty is valid)."""
    engine = MemoryPolicyEngine()
    entry = _make_codex_entry(engine, "D-002", related_entries=[
        {"id": "L-005", "relation": "caused_by"},
        {"id": "B-005", "relation": "led_to"},
    ])

    content = engine.get_codex_content(entry)
    assert len(content["related_entries"]) == 2
    assert content["related_entries"][0]["relation"] == "caused_by"


def test_codex_entry_related_entries_empty_by_default():
    """related_entries defaults to empty list."""
    engine = MemoryPolicyEngine()
    entry = _make_codex_entry(engine, "D-003")

    content = engine.get_codex_content(entry)
    assert content["related_entries"] == []
