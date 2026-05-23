import pytest
from cgalpha_v3.learning.codex_kernel import CodexKernel

def test_kernel_accepts_valid_proposal():
    proposal = {
        "codex_id": "L-003",
        "type": "LESSON",
        "status": "APPROVED",
        "statement": "Calibration using real data percentiles is better than arbitrary thresholds.",
        "schema_version": "1.0.0"
    }
    # Estado actual vacío
    assert CodexKernel.validate_proposal(proposal, {}) is True

def test_kernel_rejects_missing_required_fields():
    proposal = {
        "codex_id": "L-003",
        "type": "LESSON",
        # Falta 'status' y 'statement'
    }
    assert CodexKernel.validate_proposal(proposal, {}) is False

def test_kernel_protects_immutability():
    current_state = {
        "D-008": {
            "statement": "Original decision about proximity buffer."
        }
    }
    
    # Intento de cambiar el pasado (mismo ID, distinto statement)
    malicious_proposal = {
        "codex_id": "D-008",
        "type": "DECISION",
        "status": "APPROVED",
        "statement": "I have hijacked this decision and changed its meaning.",
        "schema_version": "1.0.0"
    }
    
    assert CodexKernel.validate_proposal(malicious_proposal, current_state) is False

def test_kernel_protects_canonical_ids():
    # Intento de eliminación de un ID protegido
    delete_proposal = {
        "codex_id": "CEP-001",
        "type": "DELETE", # Aunque no es un tipo de contenido, simulamos la acción
        "target_id": "D-001",
        "status": "PROPOSED",
        "statement": "Deleting build foundations",
        "schema_version": "1.0.0"
    }
    
    # El kernel debe detectar que target_id es canónico
    assert CodexKernel.validate_proposal(delete_proposal, {}) is False

def test_kernel_rejects_invalid_types():
    proposal = {
        "codex_id": "X-001",
        "type": "MAGIC_GOSSIP", # Tipo no permitido
        "status": "APPROVED",
        "statement": "Invalid type test",
        "schema_version": "1.0.0"
    }
    assert CodexKernel.validate_proposal(proposal, {}) is False
