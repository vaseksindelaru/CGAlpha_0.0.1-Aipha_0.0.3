"""
CGAlpha v3 — Codex Kernel (Legal Layer)
=======================================
Tribunal constitucional de la memoria de CGAlpha. Define los invariantes
inmutables que el AutoProposer no puede violar durante la automejora.
"""

import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger("codex_kernel")

class CodexKernel:
    # --- CONFIGURACIÓN DE LEYES ---
    SCHEMA_VERSION = "1.0.0"
    
    # IDs Canónicos que NUNCA pueden ser eliminados o inaccesibles
    CANONICAL_IDS = {
        "D-001", "D-002", "D-008", # Decisions (Arquitectura, Proximity Buffer)
        "B-001", "B-002",           # Bugs (Clock Drift, Oracle Persistence)
        "L-001", "L-003",           # Lessons (ZigZag Thresholds)
    }

    REQUIRED_FIELDS = {
        "codex_id", "type", "status", "statement", "schema_version"
    }

    VALID_TYPES = {"DECISION", "LESSON", "FEATURE", "BUG", "RULE", "PATTERN", "EVOLUTION_PROPOSAL"}

    @staticmethod
    def validate_proposal(proposal: Dict[str, Any], current_codex_state: Dict[str, Any]) -> bool:
        """
        Valida una propuesta de evolución (CEP) contra los invariantes del kernel.
        Si retorna False, el Master Harness rechaza el cambio automáticamente.
        """
        try:
            # 1. Validación de Esquema Mínimo
            if not CodexKernel._check_schema(proposal):
                return False

            # 2. Validación de Inmutabilidad (Hash Integrity)
            # No se permite que una propuesta modifique la RAÍZ de una entrada previa
            if not CodexKernel._check_immutability(proposal, current_codex_state):
                return False

            # 3. Validación de IDs Canónicos
            if not CodexKernel._check_canonical_protection(proposal, current_codex_state):
                return False

            logger.info(f"✅ Propuesta {proposal.get('codex_id')} VALIDADA por el Kernel.")
            return True

        except Exception as e:
            logger.error(f"🚨 Error crítico en validación del Kernel: {e}")
            return False

    @staticmethod
    def _check_schema(proposal: Dict[str, Any]) -> bool:
        content = proposal.get("content", {}) if proposal.get("type") == "EVOLUTION_PROPOSAL" else proposal
        missing = CodexKernel.REQUIRED_FIELDS - set(content.keys())
        if missing:
            logger.error(f"❌ Fallo de Esquema: Campos faltantes {missing}")
            return False
        
        if content.get("type", "").upper() not in CodexKernel.VALID_TYPES:
            logger.error(f"❌ Tipo inválido: {content.get('type')}")
            return False
        return True

    @staticmethod
    def _check_immutability(proposal: Dict[str, Any], current_state: Dict[str, Any]) -> bool:
        # PANTALLA DE PROTECCIÓN: Un CEP no puede redefinir el statement de un ID previo
        codex_id = proposal.get("codex_id")
        if codex_id in current_state:
            old_entry = current_state[codex_id]
            # Si intentan cambiar el 'statement' original, es una violación
            if proposal.get("statement") != old_entry.get("statement"):
                logger.error(f"❌ Violación de Inmutabilidad: Intento de modificar statement en {codex_id}")
                return False
        return True

    @staticmethod
    def _check_canonical_protection(proposal: Dict[str, Any], current_state_keys: List[str]) -> bool:
        # Si la propuesta es una evolución que 'depreca' campos, verificamos que
        # los IDs canónicos sigan siendo legibles bajo el nuevo esquema.
        # (Por ahora, bloqueo directo de eliminaciones de IDs canónicos)
        if proposal.get("type") == "DELETE" and proposal.get("target_id") in CodexKernel.CANONICAL_IDS:
            logger.error(f"❌ Intento de eliminar ID Canónico protegido: {proposal.get('target_id')}")
            return False
        return True

    @staticmethod
    def calculate_hash(content: str) -> str:
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
