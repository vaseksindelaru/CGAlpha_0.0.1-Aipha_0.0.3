"""
CGAlpha v3 — Codex Kernel (Legal Layer)
=======================================
Deterministic integrity court for Codex entries.

Core principle: laws before data.
The Kernel validates candidate entries/proposals against three invariants:
1) Historical immutability (append/supersede, never silent overwrite)
2) Canonical shielding (foundational IDs cannot be deleted/inaccessible)
3) Mandatory v4 schema (including harness_inject_when)
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, Iterable

logger = logging.getLogger("codex_kernel")


class CodexKernel:
    """Deterministic validator for Codex integrity constraints."""

    SCHEMA_VERSION = "4.0.0"

    # Foundational IDs that must remain accessible.
    CANONICAL_IDS = {
        "D-001", "D-008",
        "B-002",
        "L-003",
    }

    VALID_TYPES = {
        "DECISION", "LESSON", "FEATURE", "BUG", "RULE", "PATTERN", "EVOLUTION_PROPOSAL"
    }

    VALID_STATUSES = {
        "PROPOSED", "PARTIAL", "ACTIVE", "DEPRECATED", "SUPERSEDED", "APPROVED", "RESOLVED"
    }

    REQUIRED_FIELDS_V4 = {
        "codex_id",
        "type",
        "status",
        "statement",
        "rationale",
        "schema_version",
        "harness_inject_when",
    }

    @classmethod
    def validate_proposal(cls, proposal: Dict[str, Any], current_codex_state: Dict[str, Dict[str, Any]]) -> bool:
        """
        Validate a candidate entry/proposal against kernel invariants.

        Returns True only if all checks pass. Never raises by design.
        """
        try:
            entry = cls._extract_entry_payload(proposal)

            if not cls._check_schema_v4(entry):
                return False

            if not cls._check_immutability(entry, current_codex_state):
                return False

            if not cls._check_canonical_protection(proposal, current_codex_state):
                return False

            logger.info("✅ Kernel accepted %s", entry.get("codex_id"))
            return True
        except Exception as exc:
            logger.error("🚨 Kernel validation error: %s", exc)
            return False

    @classmethod
    def _extract_entry_payload(cls, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize wrapper proposals (e.g. EVOLUTION_PROPOSAL with content)
        into the payload entry to be validated.
        """
        if proposal.get("type") == "EVOLUTION_PROPOSAL" and isinstance(proposal.get("content"), dict):
            return proposal["content"]
        return proposal

    @classmethod
    def _check_schema_v4(cls, entry: Dict[str, Any]) -> bool:
        missing = cls.REQUIRED_FIELDS_V4 - set(entry.keys())
        if missing:
            logger.error("❌ Schema v4 violation: missing fields %s", sorted(missing))
            return False

        if str(entry.get("schema_version")) != cls.SCHEMA_VERSION:
            logger.error(
                "❌ Schema version mismatch: got %s, expected %s",
                entry.get("schema_version"),
                cls.SCHEMA_VERSION,
            )
            return False

        entry_type = str(entry.get("type", "")).upper()
        if entry_type not in cls.VALID_TYPES:
            logger.error("❌ Invalid type: %s", entry.get("type"))
            return False

        status = str(entry.get("status", "")).upper()
        if status not in cls.VALID_STATUSES:
            logger.error("❌ Invalid status: %s", entry.get("status"))
            return False

        inject = entry.get("harness_inject_when")
        if not isinstance(inject, list) or not inject or not all(isinstance(x, str) and x.strip() for x in inject):
            logger.error("❌ Invalid harness_inject_when: must be a non-empty list[str]")
            return False

        if not isinstance(entry.get("statement"), str) or not entry["statement"].strip():
            logger.error("❌ Invalid statement: must be non-empty string")
            return False

        if not isinstance(entry.get("rationale"), str) or not entry["rationale"].strip():
            logger.error("❌ Invalid rationale: must be non-empty string")
            return False

        return True

    @classmethod
    def _check_immutability(cls, entry: Dict[str, Any], current_state: Dict[str, Dict[str, Any]]) -> bool:
        """
        Historical immutability:
        - Existing entry cannot change statement/rationale in-place.
        - Changes must be represented as a new codex_id superseding the old one.
        """
        codex_id = entry.get("codex_id")
        if codex_id not in current_state:
            return True

        old = current_state[codex_id]
        statement_changed = entry.get("statement") != old.get("statement")
        rationale_changed = entry.get("rationale") != old.get("rationale")

        if statement_changed or rationale_changed:
            logger.error(
                "❌ Immutability violation: in-place mutation on %s. Use supersede flow.",
                codex_id,
            )
            return False

        return True

    @classmethod
    def _check_canonical_protection(cls, proposal: Dict[str, Any], current_state: Dict[str, Dict[str, Any]]) -> bool:
        """
        Canonical shielding:
        - Explicit DELETE against canonical IDs is forbidden.
        - ACTIVE canonical IDs must remain accessible in current state.
        """
        action = str(proposal.get("action", proposal.get("type", ""))).upper()
        target_id = proposal.get("target_id")

        if action == "DELETE" and target_id in cls.CANONICAL_IDS:
            logger.error("❌ Canonical protection violation: cannot delete %s", target_id)
            return False

        missing = [cid for cid in cls.CANONICAL_IDS if cid not in current_state]
        if missing:
            logger.error("❌ Canonical accessibility violation: missing canonical IDs %s", missing)
            return False

        return True

    @staticmethod
    def calculate_hash(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @classmethod
    def canonical_state_from_entries(cls, entries: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Helper for tests/tooling: index entries by codex_id."""
        out: Dict[str, Dict[str, Any]] = {}
        for e in entries:
            if isinstance(e, dict) and e.get("codex_id"):
                out[str(e["codex_id"])] = e
        return out

    @classmethod
    def summarize_validation_contract(cls) -> Dict[str, Any]:
        """Machine-readable contract for docs/tests."""
        return {
            "schema_version": cls.SCHEMA_VERSION,
            "required_fields": sorted(cls.REQUIRED_FIELDS_V4),
            "valid_types": sorted(cls.VALID_TYPES),
            "valid_statuses": sorted(cls.VALID_STATUSES),
            "canonical_ids": sorted(cls.CANONICAL_IDS),
        }
