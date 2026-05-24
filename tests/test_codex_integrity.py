from cgalpha_v3.learning.codex_kernel import CodexKernel


def _base_state():
    # Minimal accessible canonical state.
    return {
        "D-001": {
            "codex_id": "D-001",
            "type": "DECISION",
            "status": "ACTIVE",
            "statement": "Shadow/Main separation",
            "rationale": "Safety architecture",
            "schema_version": "4.0.0",
            "harness_inject_when": ["feature_proposal"],
        },
        "D-008": {
            "codex_id": "D-008",
            "type": "DECISION",
            "status": "ACTIVE",
            "statement": "Use proximity buffer",
            "rationale": "Capture near-zone institutional flow",
            "schema_version": "4.0.0",
            "harness_inject_when": ["signal_detector"],
        },
        "B-002": {
            "codex_id": "B-002",
            "type": "BUG",
            "status": "RESOLVED",
            "statement": "Persistence hook missing",
            "rationale": "Model state was not loaded on restart",
            "schema_version": "4.0.0",
            "harness_inject_when": ["model_training"],
        },
        "L-003": {
            "codex_id": "L-003",
            "type": "LESSON",
            "status": "ACTIVE",
            "statement": "No arbitrary thresholds",
            "rationale": "Calibrate by percentiles",
            "schema_version": "4.0.0",
            "harness_inject_when": ["optimizer"],
        },
    }


def test_kernel_accepts_valid_v4_entry():
    proposal = {
        "codex_id": "D-010",
        "type": "DECISION",
        "status": "PROPOSED",
        "statement": "Introduce rolling confidence window.",
        "rationale": "Stabilize confidence output under volatility spikes.",
        "schema_version": "4.0.0",
        "harness_inject_when": ["oracle_modification"],
    }
    assert CodexKernel.validate_proposal(proposal, _base_state()) is True


def test_kernel_rejects_missing_harness_inject_when():
    proposal = {
        "codex_id": "D-011",
        "type": "DECISION",
        "status": "PROPOSED",
        "statement": "Invalid schema sample",
        "rationale": "Missing mandatory field",
        "schema_version": "4.0.0",
    }
    assert CodexKernel.validate_proposal(proposal, _base_state()) is False


def test_kernel_rejects_wrong_schema_version():
    proposal = {
        "codex_id": "D-012",
        "type": "DECISION",
        "status": "PROPOSED",
        "statement": "Wrong schema version",
        "rationale": "Must fail if not v4",
        "schema_version": "1.0.0",
        "harness_inject_when": ["feature_proposal"],
    }
    assert CodexKernel.validate_proposal(proposal, _base_state()) is False


def test_kernel_protects_immutability_in_place_mutation():
    state = _base_state()
    malicious = {
        "codex_id": "D-008",
        "type": "DECISION",
        "status": "ACTIVE",
        "statement": "Hijacked historical meaning",
        "rationale": "Trying to rewrite history",
        "schema_version": "4.0.0",
        "harness_inject_when": ["signal_detector"],
    }
    assert CodexKernel.validate_proposal(malicious, state) is False


def test_kernel_protects_canonical_ids_from_delete():
    delete_proposal = {
        "action": "DELETE",
        "target_id": "D-001",
        "codex_id": "CEP-001",
        "type": "EVOLUTION_PROPOSAL",
        "status": "PROPOSED",
        "statement": "Delete canonical foundation",
        "rationale": "Should be blocked",
        "schema_version": "4.0.0",
        "harness_inject_when": ["memory_governance"],
    }
    assert CodexKernel.validate_proposal(delete_proposal, _base_state()) is False
