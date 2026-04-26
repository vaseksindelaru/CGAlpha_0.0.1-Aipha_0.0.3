"""
cgAlpha_0.0.1 — Tests for Evolution Orchestrator v4
====================================================
Tests for ACCIÓN 3: classification, processing, approval,
rejection, escalation, and logging.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from cgalpha_v3.domain.models.signal import MemoryLevel
from cgalpha_v3.lila.evolution_orchestrator import (
    EvolutionOrchestratorV4,
    EvolutionResult,
    MAX_ESCALATION_ATTEMPTS,
)
from cgalpha_v3.learning.memory_policy import MemoryPolicyEngine


@dataclass
class MockSpec:
    """Minimal TechnicalSpec mock."""
    change_type: str = "parameter"
    target_file: str = "config.py"
    target_attribute: str = "volume_threshold"
    old_value: float = 1.2
    new_value: float = 1.5
    reason: str = "test"
    causal_score_est: float = 0.8
    confidence: float = 0.85


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_mock_project(root: Path) -> None:
    _write(
        root / "config.py",
        """
CFG = {
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
    _write(root / "data/phase1_results/auto_proposer_output.json", "{\"volume_threshold\": 1.2}")


# ───────────────────────────────────────────────
# CLASSIFICATION TESTS
# ───────────────────────────────────────────────

def test_classify_parameter_high_confidence_is_cat_1():
    orch = EvolutionOrchestratorV4()
    spec = MockSpec(change_type="parameter", confidence=0.85)
    assert orch.classify(spec) == 1


def test_classify_parameter_low_confidence_is_cat_2():
    orch = EvolutionOrchestratorV4()
    spec = MockSpec(change_type="parameter", confidence=0.5)
    assert orch.classify(spec) == 2


def test_classify_feature_is_cat_2():
    orch = EvolutionOrchestratorV4()
    spec = MockSpec(change_type="feature")
    assert orch.classify(spec) == 2


def test_classify_structural_is_cat_3():
    orch = EvolutionOrchestratorV4()
    spec = MockSpec(change_type="structural")
    assert orch.classify(spec) == 3


def test_classify_protected_file_is_cat_3():
    orch = EvolutionOrchestratorV4()
    spec = MockSpec(change_type="parameter", confidence=0.99,
                    target_file="evolution_orchestrator.py")
    assert orch.classify(spec) == 3


def test_classify_memory_policy_is_cat_3():
    orch = EvolutionOrchestratorV4()
    spec = MockSpec(target_file="memory_policy.py")
    assert orch.classify(spec) == 3


def test_classify_north_star_doc_is_cat_3():
    orch = EvolutionOrchestratorV4()
    spec = MockSpec(target_file="LILA_v3_NORTH_STAR.md")
    assert orch.classify(spec) == 3


def test_classify_unknown_type_defaults_cat_2():
    orch = EvolutionOrchestratorV4()
    spec = MockSpec(change_type="xyzzy_unknown")
    assert orch.classify(spec) == 2


# ───────────────────────────────────────────────
# PROCESS PROPOSAL TESTS
# ───────────────────────────────────────────────

def test_process_cat_1_applied(tmp_path):
    memory = MemoryPolicyEngine()
    orch = EvolutionOrchestratorV4(
        memory=memory,
        evolution_log_path=tmp_path / "evolution_log.jsonl"
    )
    spec = MockSpec(change_type="parameter", confidence=0.9)
    result = orch.process_proposal(spec)
    assert result.category == 1
    assert result.status == "APPLIED"
    assert orch.get_stats()["cat_1_applied"] == 1


def test_process_cat_2_queued(tmp_path):
    memory = MemoryPolicyEngine()
    orch = EvolutionOrchestratorV4(
        memory=memory,
        evolution_log_path=tmp_path / "evolution_log.jsonl"
    )
    spec = MockSpec(change_type="feature")
    result = orch.process_proposal(spec)
    assert result.category == 2
    assert result.status == "PENDING_APPROVAL"
    assert orch.get_stats()["cat_2_pending"] == 1


def test_process_cat_3_queued(tmp_path):
    memory = MemoryPolicyEngine()
    orch = EvolutionOrchestratorV4(
        memory=memory,
        evolution_log_path=tmp_path / "evolution_log.jsonl"
    )
    spec = MockSpec(change_type="structural")
    result = orch.process_proposal(spec)
    assert result.category == 3
    assert result.status == "PENDING_APPROVAL"


def test_cooldown_blocks_duplicate(tmp_path):
    orch = EvolutionOrchestratorV4(
        evolution_log_path=tmp_path / "evolution_log.jsonl"
    )
    spec = MockSpec()
    orch.process_proposal(spec)
    result2 = orch.process_proposal(spec)
    assert result2.status == "COOLDOWN"


# ───────────────────────────────────────────────
# APPROVAL / REJECTION TESTS
# ───────────────────────────────────────────────

def test_approve_pending_proposal(tmp_path):
    memory = MemoryPolicyEngine()
    orch = EvolutionOrchestratorV4(
        memory=memory,
        evolution_log_path=tmp_path / "evolution_log.jsonl"
    )
    spec = MockSpec(change_type="feature")
    result = orch.process_proposal(spec)
    pid = result.proposal_id

    approve_result = orch.approve_proposal(pid)
    assert approve_result.status == "APPLIED"
    assert orch.get_stats()["cat_2_approved"] == 1


def test_reject_pending_proposal(tmp_path):
    memory = MemoryPolicyEngine()
    orch = EvolutionOrchestratorV4(
        memory=memory,
        evolution_log_path=tmp_path / "evolution_log.jsonl"
    )
    spec = MockSpec(change_type="feature")
    result = orch.process_proposal(spec)
    pid = result.proposal_id

    reject_result = orch.reject_proposal(pid, reason="not convinced")
    assert reject_result.status == "REJECTED"
    assert orch.get_stats()["cat_2_rejected"] == 1


def test_approve_nonexistent_proposal(tmp_path):
    memory = MemoryPolicyEngine()
    orch = EvolutionOrchestratorV4(
        memory=memory,
        evolution_log_path=tmp_path / "evolution_log.jsonl"
    )
    result = orch.approve_proposal("nonexistent-id")
    assert result.status == "FAILED"


# ───────────────────────────────────────────────
# ESCALATION TESTS
# ───────────────────────────────────────────────

def test_escalation_after_max_attempts(tmp_path):
    memory = MemoryPolicyEngine()
    orch = EvolutionOrchestratorV4(
        memory=memory,
        evolution_log_path=tmp_path / "evolution_log.jsonl"
    )
    spec = MockSpec(change_type="feature")
    result = orch.process_proposal(spec)
    pid = result.proposal_id

    for _ in range(MAX_ESCALATION_ATTEMPTS):
        escalated = orch.check_escalations()

    assert len(escalated) == 1
    assert pid in escalated
    assert orch.get_stats()["escalations"] == 1


# ───────────────────────────────────────────────
# LOGGING TESTS
# ───────────────────────────────────────────────

def test_evolution_log_written(tmp_path):
    orch = EvolutionOrchestratorV4(
        evolution_log_path=tmp_path / "evolution_log.jsonl"
    )
    spec = MockSpec()
    orch.process_proposal(spec)

    log_path = tmp_path / "evolution_log.jsonl"
    assert log_path.exists()
    lines = log_path.read_text().strip().split("\n")
    assert len(lines) >= 1
    entry = json.loads(lines[0])
    assert "category" in entry
    assert "timestamp" in entry
    assert "status" in entry


def test_get_stats_structure():
    orch = EvolutionOrchestratorV4()
    stats = orch.get_stats()
    assert "total_proposals" in stats
    assert "cat_1_applied" in stats
    assert "cat_2_pending" in stats
    assert "escalations" in stats


def test_get_pending_summary(tmp_path):
    memory = MemoryPolicyEngine()
    orch = EvolutionOrchestratorV4(
        memory=memory,
        evolution_log_path=tmp_path / "evolution_log.jsonl"
    )
    spec = MockSpec(change_type="feature")
    result = orch.process_proposal(spec)

    summary = orch.get_pending_summary()
    assert len(summary) >= 1
    assert summary[0]["proposal_id"] == result.proposal_id


def test_evolution_result_dataclass():
    r = EvolutionResult(category=1, status="APPLIED")
    assert r.category == 1
    assert r.status == "APPLIED"
    assert r.timestamp  # auto-set


def test_landscape_proposal_generates_artifact_on_approval(tmp_path: Path):
    memory = MemoryPolicyEngine()
    memory.MEMORY_DIR = tmp_path / "memory_entries"
    memory.IDENTITY_DIR = tmp_path / "identity"

    project_root = tmp_path / "project"
    _build_mock_project(project_root)
    artifact_path = tmp_path / "data" / "parameter_landscape_map.json"

    orch = EvolutionOrchestratorV4(
        memory=memory,
        evolution_log_path=tmp_path / "evolution_log.jsonl",
        project_root=project_root,
        landscape_artifact_path=artifact_path,
    )

    queued = orch.propose_parameter_landscape(requested_by="test")
    assert queued.category == 2
    assert queued.status == "PENDING_APPROVAL"

    approved = orch.approve_proposal(queued.proposal_id)
    assert approved.status == "SUCCESS"
    assert artifact_path.exists()

    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert artifact["parameter_count"] >= 15

    rel_entries = memory.list_entries(level=MemoryLevel.RELATIONS, limit=200)
    assert any("parameter_landscape_map" in entry.content for entry in rel_entries)
