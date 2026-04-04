"""
Tests — Rollback Manager (cgalpha_v3)

Cubre:
  - snapshot con artefactos mínimos
  - restore con verificación de hash
  - SLA P0 (<60s) validado automáticamente
  - detección de corrupción de snapshot (hash mismatch)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json

import pytest

from cgalpha_v3.application.rollback_manager import RollbackManager, _sha256_file


@pytest.fixture
def rm(tmp_path: Path) -> RollbackManager:
    return RollbackManager(snapshots_dir=tmp_path / "snapshots")


def test_take_snapshot_writes_expected_files(rm: RollbackManager):
    snap = rm.take_snapshot(
        proposal_id="prop-test-001",
        config={"a": 1, "b": True},
        model_params={"m": "rf", "n": 10},
        memory_l3l4={"playbook": "x", "strategy": "y"},
        git_sha="abc123",
    )
    assert snap.exists()
    for fn in ("config.json", "model_params.json", "memory_l3l4.json", "git_sha.txt", "manifest.json"):
        assert (snap / fn).exists(), f"Falta {fn}"


def test_restore_roundtrip_with_hash_verification(rm: RollbackManager):
    snap = rm.take_snapshot(
        proposal_id="prop-test-002",
        config={"alpha": 0.7},
        model_params={"depth": 8},
        memory_l3l4={"l3": ["rule1"], "l4": ["policy1"]},
        git_sha="deadbeef",
    )

    restored = rm.restore(snap, verify_hash=True)
    assert restored["config"]["alpha"] == 0.7
    assert restored["model_params"]["depth"] == 8
    assert restored["memory_l3l4"]["l3"] == ["rule1"]
    assert restored["git_sha"] == "deadbeef"


def test_restore_sla_p0_under_60_seconds(rm: RollbackManager):
    snap = rm.take_snapshot(
        proposal_id="prop-test-003",
        config={"risk": {"max_dd": 5}},
        model_params={"model": "rf"},
        memory_l3l4={"memo": "ok"},
        git_sha="sha-sla",
    )

    restored = rm.restore(snap, verify_hash=True)
    assert restored["elapsed_ms"] < 60_000, (
        f"SLA P0 roto: restore tardó {restored['elapsed_ms']:.2f}ms (límite 60000ms)"
    )


def test_restore_detects_hash_mismatch(rm: RollbackManager):
    snap = rm.take_snapshot(
        proposal_id="prop-test-004",
        config={"x": 1},
        model_params={"y": 2},
        memory_l3l4={"z": 3},
        git_sha="sha-corrupt",
    )

    config_path = snap / "config.json"
    bad = json.loads(config_path.read_text())
    bad["x"] = 999
    config_path.write_text(json.dumps(bad, indent=2))

    with pytest.raises(ValueError, match="Hash mismatch"):
        rm.restore(snap, verify_hash=True)


def test_list_snapshots_returns_latest_first(rm: RollbackManager):
    rm.take_snapshot("prop-list-1", {"v": 1})
    rm.take_snapshot("prop-list-2", {"v": 2})

    snaps = rm.list_snapshots()
    assert len(snaps) >= 2
    assert snaps[0]["proposal_id"] == "prop-list-2"


def test_sha256_file_returns_consistent_hash(tmp_path: Path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello world")
    h1 = _sha256_file(test_file)
    h2 = _sha256_file(test_file)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex digest length
    # Modify content → hash changes
    test_file.write_text("hello world modified")
    h3 = _sha256_file(test_file)
    assert h3 != h1
