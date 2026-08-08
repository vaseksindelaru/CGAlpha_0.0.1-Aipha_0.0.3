"""
cgAlpha_0.0.1 — Evolution Orchestrator v4
==========================================
Central hub that connects the 4 islands:
  AutoProposer → Orchestrator → CodeCraftSage
                              → ExperimentRunner
                              → MemoryPolicyEngine

Classification (§4 Prompt Fundacional):
  Cat.1 (automatic): parameter changes, auto-applied + auto-tested
  Cat.2 (semi-auto): structural changes, require human approval
  Cat.3 (supervised): architectural changes, require full review session
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from cgalpha_v3.domain.models.signal import MemoryLevel
from cgalpha_v3.lila.llm.llm_switcher import LLMSwitcher
from cgalpha_v3.lila.parameter_landscape import (
    build_parameter_landscape_map,
    load_parameter_landscape_map,
)

logger = logging.getLogger("evolution_orchestrator_v4")


# ───────────────────────────────────────────────────────────
# DATA MODELS
# ───────────────────────────────────────────────────────────

@dataclass
class EvolutionResult:
    """Resultado de ejecutar una propuesta de evolución."""
    category: int  # 1, 2, 3
    status: str  # "APPLIED", "PENDING_APPROVAL", "ESCALATED", "REJECTED", "FAILED"
    proposal_id: str = ""
    spec_summary: str = ""
    tests_passed: bool = False
    tests_count: int = 0
    branch_name: str = ""
    error: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


# ───────────────────────────────────────────────────────────
# CLASSIFICATION RULES (deterministic first, LLM fallback)
# ───────────────────────────────────────────────────────────

# Change types that are Cat.1 (auto-applicable)
CAT_1_CHANGE_TYPES = {"parameter", "threshold", "hyperparameter"}

# Change types that are Cat.2 (semi-auto)
CAT_2_CHANGE_TYPES = {"feature", "optimization", "bugfix"}

# Change types that are Cat.3 (supervised)
CAT_3_CHANGE_TYPES = {"structural", "architectural", "new_component", "identity"}

# Target files that always escalate to Cat.3
CAT_3_PROTECTED_FILES = {
    "evolution_orchestrator.py",
    "memory_policy.py",
    "llm_switcher.py",
    "server.py",
    "LILA_v3_NORTH_STAR.md",
}

# Maximum escalation attempts before Cat.2 → Cat.3
MAX_ESCALATION_ATTEMPTS = 3


@dataclass
class EvolutionOrchestratorV4:
    """
    Central hub for cgAlpha evolution.

    Receives TechnicalSpecs from AutoProposer, classifies them,
    routes to CodeCraftSage for implementation, and persists results
    in the MemoryPolicyEngine.
    """
    memory: Any = None  # MemoryPolicyEngine
    switcher: Optional[LLMSwitcher] = None
    sage: Any = None  # CodeCraftSage
    assistant: Any = None  # LLMAssistant
    evolution_log_path: Path = field(default_factory=lambda: Path("cgalpha_v3/memory/evolution_log.jsonl"))
    project_root: Path = field(default_factory=lambda: Path("cgalpha_v3"))
    landscape_artifact_path: Path = field(default_factory=lambda: Path("cgalpha_v3/data/parameter_landscape_map.json"))
    _cooldown_seconds: int = 300  # 5 min between same-spec proposals
    _last_proposals: dict = field(default_factory=dict)
    _escalation_counts: dict = field(default_factory=dict)
    _stats: dict = field(default_factory=lambda: {
        "total_proposals": 0,
        "cat_1_applied": 0,
        "cat_2_pending": 0,
        "cat_2_approved": 0,
        "cat_2_rejected": 0,
        "cat_3_pending": 0,
        "cat_3_approved": 0,
        "cat_3_rejected": 0,
        "escalations": 0,
        "landscape_generated": 0,
        "failures": 0,
    })

    def propose_parameter_landscape(self, requested_by: str = "lila_v4") -> EvolutionResult:
        """
        Build a Cat.2 proposal for S3 Step 4 (Parameter Landscape Map).
        """
        from cgalpha_v3.lila.llm.proposer import TechnicalSpec

        spec = TechnicalSpec(
            change_type="optimization",
            target_file=str(self.landscape_artifact_path),
            target_attribute="parameter_landscape_map",
            old_value=0.0,
            new_value=1.0,
            reason=(
                "Escaneo determinista de parametros configurables para crear "
                f"parameter_landscape_map.json (requested_by={requested_by})."
            ),
            causal_score_est=0.60,
            confidence=0.80,
        )
        return self.process_proposal(spec)

    # ───────────────────────────────────────────────────────
    # CORE: CLASSIFY
    # ───────────────────────────────────────────────────────

    def classify(self, spec: Any) -> int:
        """
        Classify a TechnicalSpec into category 1, 2, or 3.

        Uses deterministic rules first (§4.3). Only uses LLM as
        fallback for ambiguous cases.

        Args:
            spec: TechnicalSpec dataclass

        Returns:
            1, 2, or 3
        """
        change_type = getattr(spec, "change_type", "").lower().strip()
        target_file = getattr(spec, "target_file", "")
        confidence = getattr(spec, "confidence", 0.0)

        # Rule 1: Protected files → always Cat.3
        target_basename = Path(target_file).name if target_file else ""
        if target_basename in CAT_3_PROTECTED_FILES:
            logger.info(f"Classify: {target_basename} is protected → Cat.3")
            return 3

        # Rule 2: Identity-related → Cat.3
        if change_type in CAT_3_CHANGE_TYPES:
            logger.info(f"Classify: change_type='{change_type}' → Cat.3")
            return 3

        # Rule 3: Parameter change with high confidence → Cat.1
        if change_type in CAT_1_CHANGE_TYPES and confidence >= 0.7:
            logger.info(f"Classify: change_type='{change_type}', conf={confidence:.2f} → Cat.1")
            return 1

        # Rule 4: Known semi-auto types → Cat.2
        if change_type in CAT_2_CHANGE_TYPES:
            logger.info(f"Classify: change_type='{change_type}' → Cat.2")
            return 2

        # Rule 5: Low confidence parameter → Cat.2 (needs review)
        if change_type in CAT_1_CHANGE_TYPES and confidence < 0.7:
            logger.info(f"Classify: change_type='{change_type}' but conf={confidence:.2f} < 0.7 → Cat.2")
            return 2

        # Rule 6: Unknown type → default Cat.2
        logger.warning(f"Classify: unknown change_type='{change_type}' → Cat.2 (default)")
        return 2

    def __post_init__(self):
        self._constraints = self._load_constraints()

    def _load_constraints(self) -> dict:
        """Load parameter_constraints.json (Safety Envelope)."""
        constraints_path = Path("cgalpha_v3/config/parameter_constraints.json")
        if constraints_path.exists():
            try:
                data = json.loads(constraints_path.read_text(encoding="utf-8"))
                flat = {}
                for component, params in data.get("constraints", {}).items():
                    for param_name, bounds in params.items():
                        flat[param_name] = {**bounds, "component": component}
                logger.info(f"🛡️ Safety Envelope loaded: {len(flat)} constraints")
                return flat
            except Exception as e:
                logger.warning(f"Failed to load constraints: {e}")
        return {}

    def _validate_constraints(self, spec: Any) -> tuple[bool, str]:
        """Validate a TechnicalSpec's new_value against the Safety Envelope.
        
        Returns (is_valid, error_message).
        """
        if not self._constraints:
            return True, ""

        attr = getattr(spec, "target_attribute", "")
        new_value = getattr(spec, "new_value", None)

        if attr not in self._constraints or new_value is None:
            return True, ""

        bounds = self._constraints[attr]
        min_val = bounds.get("min")
        max_val = bounds.get("max")

        if min_val is not None and new_value < min_val:
            return False, (
                f"SAFETY ENVELOPE VIOLATION: {attr}={new_value} < min={min_val}. "
                f"Reason: {bounds.get('reason', '')}"
            )
        if max_val is not None and new_value > max_val:
            return False, (
                f"SAFETY ENVELOPE VIOLATION: {attr}={new_value} > max={max_val}. "
                f"Reason: {bounds.get('reason', '')}"
            )
        return True, ""

    # ───────────────────────────────────────────────────────
    # CORE: PROCESS PROPOSAL
    # ───────────────────────────────────────────────────────

    def process_proposal(self, spec: Any) -> EvolutionResult:
        """
        Main entry point: receive a TechnicalSpec, classify, and route.

        Returns EvolutionResult with status and details.
        """
        self._stats["total_proposals"] += 1
        spec_key = f"{getattr(spec, 'target_file', '')}:{getattr(spec, 'target_attribute', '')}"

        # ── Safety Envelope gate ──
        is_valid, violation_msg = self._validate_constraints(spec)
        if not is_valid:
            self._stats["failures"] += 1
            logger.warning(f"🛡️ REJECTED by Safety Envelope: {violation_msg}")
            result = EvolutionResult(
                category=0,
                status="REJECTED_SAFETY",
                spec_summary=spec_key,
                error=violation_msg,
            )
            self._append_evolution_log(spec, result)
            return result

        # Cooldown check
        last_time = self._last_proposals.get(spec_key, 0)
        if time.time() - last_time < self._cooldown_seconds:
            return EvolutionResult(
                category=0,
                status="COOLDOWN",
                spec_summary=spec_key,
                error=f"Same spec proposed within {self._cooldown_seconds}s cooldown"
            )

        self._last_proposals[spec_key] = time.time()
        category = self.classify(spec)

        if category == 1:
            return self._execute_cat_1(spec, spec_key)
        elif category == 2:
            return self._queue_cat_2(spec, spec_key)
        elif category == 3:
            return self._queue_cat_3(spec, spec_key)
        else:
            return EvolutionResult(
                category=category,
                status="FAILED",
                error=f"Invalid category: {category}"
            )

    # ───────────────────────────────────────────────────────
    # CAT.1: AUTOMATIC EXECUTION
    # ───────────────────────────────────────────────────────

    def _execute_cat_1(self, spec: Any, spec_key: str) -> EvolutionResult:
        """
        Cat.1: Apply parameter change automatically.
        CodeCraftSage patches → tests run → git commit.
        """
        result = EvolutionResult(
            category=1,
            status="APPLIED",
            spec_summary=spec_key,
            proposal_id=f"ev-{int(time.time())}",
        )

        if self.sage:
            try:
                exec_result = self.sage.execute_proposal(
                    spec,
                    ghost_approved=True,
                    human_approved=False  # Cat.1 doesn't need human
                )
                result.tests_passed = getattr(exec_result, "tests_passed", True)
                result.branch_name = getattr(exec_result, "branch_name", "")

                if not result.tests_passed:
                    result.status = "FAILED"
                    result.error = "Tests failed after applying patch"
                    self._stats["failures"] += 1
                    return result

            except Exception as e:
                result.status = "FAILED"
                result.error = str(e)
                self._stats["failures"] += 1
                logger.error(f"Cat.1 execution failed: {e}")
                self._append_evolution_log(spec, result)
                return result

        self._stats["cat_1_applied"] += 1

        # Persist to memory
        if self.memory:
            entry = self.memory.ingest_raw(
                content=json.dumps({
                    "type": "evolution_result",
                    "category": 1,
                    "spec_key": spec_key,
                    "status": result.status,
                    "proposal_id": result.proposal_id,
                    "timestamp": result.timestamp,
                }),
                field="architect",
                tags=["evolution", "cat_1", "auto_applied"],
            )
            self.memory.promote(
                entry_id=entry.entry_id,
                target_level=MemoryLevel.NORMALIZED,
                approved_by="auto",
            )

        self._append_evolution_log(spec, result)
        logger.info(f"✅ Cat.1 APPLIED: {spec_key}")
        return result

    # ───────────────────────────────────────────────────────
    # CAT.2: QUEUE FOR APPROVAL
    # ───────────────────────────────────────────────────────

    def _queue_cat_2(self, spec: Any, spec_key: str) -> EvolutionResult:
        """
        Cat.2: Queue proposal for human approval via GUI.
        """
        result = EvolutionResult(
            category=2,
            status="PENDING_APPROVAL",
            spec_summary=spec_key,
            proposal_id=f"ev-{int(time.time())}",
        )

        self._stats["cat_2_pending"] += 1

        if self.memory:
            entry = self.memory.ingest_raw(
                content=json.dumps({
                    "type": "pending_proposal",
                    "category": 2,
                    "spec_key": spec_key,
                    "proposal_id": result.proposal_id,
                    "spec": self._spec_to_dict(spec),
                    "status": "pending",
                    "timestamp": result.timestamp,
                }),
                field="architect",
                tags=["evolution", "cat_2", "pending"],
            )
            self.memory.promote(
                entry_id=entry.entry_id,
                target_level=MemoryLevel.NORMALIZED,
                approved_by="auto",
            )
            self.memory.promote(
                entry_id=entry.entry_id,
                target_level=MemoryLevel.FACTS,
                approved_by="Lila",
            )
            self.memory.promote(
                entry_id=entry.entry_id,
                target_level=MemoryLevel.RELATIONS,
                approved_by="Lila",
                tags=["pending"],
            )

        self._append_evolution_log(spec, result)
        logger.info(f"📋 Cat.2 QUEUED: {spec_key} → waiting for approval")
        return result

    # ───────────────────────────────────────────────────────
    # CAT.3: SUPERVISED QUEUE
    # ───────────────────────────────────────────────────────

    def _queue_cat_3(self, spec: Any, spec_key: str) -> EvolutionResult:
        """
        Cat.3: Queue for supervised review session.
        """
        result = EvolutionResult(
            category=3,
            status="PENDING_APPROVAL",
            spec_summary=spec_key,
            proposal_id=f"ev-{int(time.time())}",
        )

        self._stats["cat_3_pending"] += 1

        if self.memory:
            entry = self.memory.ingest_raw(
                content=json.dumps({
                    "type": "pending_proposal",
                    "category": 3,
                    "spec_key": spec_key,
                    "proposal_id": result.proposal_id,
                    "spec": self._spec_to_dict(spec),
                    "status": "pending_supervised",
                    "timestamp": result.timestamp,
                }),
                field="architect",
                tags=["evolution", "cat_3", "pending", "supervised"],
            )
            self.memory.promote(
                entry_id=entry.entry_id,
                target_level=MemoryLevel.NORMALIZED,
                approved_by="auto",
            )
            self.memory.promote(
                entry_id=entry.entry_id,
                target_level=MemoryLevel.FACTS,
                approved_by="Lila",
            )
            self.memory.promote(
                entry_id=entry.entry_id,
                target_level=MemoryLevel.RELATIONS,
                approved_by="Lila",
                tags=["pending"],
            )

        self._append_evolution_log(spec, result)
        logger.info(f"🔒 Cat.3 QUEUED (supervised): {spec_key}")
        return result

    # ───────────────────────────────────────────────────────
    # APPROVAL / REJECTION (called from GUI endpoints)
    # ───────────────────────────────────────────────────────

    def approve_proposal(self, proposal_id: str, approved_by: str = "human") -> EvolutionResult:
        """
        Approve a pending Cat.2/Cat.3 proposal.
        Triggers execution via CodeCraftSage.
        """
        if not self.memory:
            return EvolutionResult(category=0, status="FAILED", error="No memory engine")

        pending = self.memory.get_pending_proposals()
        target = None
        for entry in pending:
            try:
                if not entry.content:
                    continue
                data = json.loads(entry.content)
                if data.get("proposal_id") == proposal_id:
                    target = entry
                    break
            except json.JSONDecodeError:
                logger.warning(f"Skipping corrupt memory entry: {entry.entry_id}")
                continue

        if not target:
            return EvolutionResult(
                category=0, status="FAILED",
                error=f"Proposal {proposal_id} not found in pending"
            )

        data = json.loads(target.content)
        category = data.get("category", 2)

        # Update status
        data["status"] = "approved"
        data["approved_by"] = approved_by
        data["approved_at"] = datetime.now(timezone.utc).isoformat()
        target.content = json.dumps(data)
        if "pending" in target.tags:
            target.tags.remove("pending")
        target.tags.append("approved")
        self.memory._persist_memory_entry(target)

        if category == 2:
            self._stats["cat_2_approved"] += 1
        else:
            self._stats["cat_3_approved"] += 1

        result = EvolutionResult(
            category=category,
            status="APPLIED",
            proposal_id=proposal_id,
            spec_summary=data.get("spec_key", ""),
        )

        logger.info(f"✅ Proposal {proposal_id} APPROVED by {approved_by}")

        spec_dict = data.get("spec", {})

        if self._is_parameter_landscape_spec(spec_dict):
            try:
                artifact = self._generate_parameter_landscape(approved_by=approved_by)
                data["landscape_artifact_path"] = str(self.landscape_artifact_path)
                data["landscape_parameter_count"] = artifact.get("parameter_count", 0)
                target.content = json.dumps(data)
                self.memory._persist_memory_entry(target)
                result.status = "SUCCESS"
                result.tests_passed = True
                logger.info(
                    "🗺️ Parameter Landscape generado (%s parámetros): %s",
                    artifact.get("parameter_count", 0),
                    self.landscape_artifact_path,
                )
            except Exception as e:
                result.status = "ERROR"
                result.error = f"Landscape generation error: {str(e)}"
                logger.error("💥 Error generando Parameter Landscape: %s", e)

            self._append_evolution_log(None, result, approved_by=approved_by)
            return result

        # Trigger Execution via Sage
        if self.sage:
            try:
                # Reconstruir TechnicalSpec desde data
                from cgalpha_v3.lila.llm.proposer import TechnicalSpec
                spec = TechnicalSpec(**spec_dict)
                
                exec_result = self.sage.execute_proposal(
                    spec,
                    ghost_approved=True,
                    human_approved=True 
                )
                result.tests_passed = getattr(exec_result, "tests_passed", False)
                result.branch_name = getattr(exec_result, "branch_name", "")
                
                if result.tests_passed:
                    result.status = "SUCCESS"
                    logger.info(f"🚀 Evolución ejecutada exitosamente: {proposal_id}")
                else:
                    result.status = "FAILED"
                    result.error = getattr(exec_result, "error_message", "Tests failed")
                    logger.error(f"❌ Evolución fallida (Tests): {result.error}")
            except Exception as e:
                result.status = "ERROR"
                result.error = f"Execution error: {str(e)}"
                logger.error(f"💥 Error crítico en ejecución de aprobación: {e}")

        self._append_evolution_log(None, result, approved_by=approved_by)
        return result

    def reject_proposal(self, proposal_id: str, reason: str = "",
                        rejected_by: str = "human") -> EvolutionResult:
        """
        Reject a pending proposal.
        """
        if not self.memory:
            return EvolutionResult(category=0, status="FAILED", error="No memory engine")

        pending = self.memory.get_pending_proposals()
        target = None
        for entry in pending:
            data = json.loads(entry.content)
            if data.get("proposal_id") == proposal_id:
                target = entry
                break

        if not target:
            return EvolutionResult(
                category=0, status="FAILED",
                error=f"Proposal {proposal_id} not found in pending"
            )

        data = json.loads(target.content)
        category = data.get("category", 2)

        data["status"] = "rejected"
        data["rejection_reason"] = reason
        data["rejected_by"] = rejected_by
        target.content = json.dumps(data)
        if "pending" in target.tags:
            target.tags.remove("pending")
        target.tags.append("rejected")
        self.memory._persist_memory_entry(target)

        if category == 2:
            self._stats["cat_2_rejected"] += 1
        else:
            self._stats["cat_3_rejected"] += 1

        result = EvolutionResult(
            category=category,
            status="REJECTED",
            proposal_id=proposal_id,
            spec_summary=data.get("spec_key", ""),
            error=reason,
        )

        logger.info(f"❌ Proposal {proposal_id} REJECTED: {reason}")
        self._append_evolution_log(None, result, approved_by=f"rejected:{rejected_by}")
        return result

    # ───────────────────────────────────────────────────────
    # ESCALATION
    # ───────────────────────────────────────────────────────

    def check_escalations(self) -> list[str]:
        """
        Check for Cat.2 proposals that have been pending too long.
        Escalate to Cat.3 after MAX_ESCALATION_ATTEMPTS cycles.
        """
        if not self.memory:
            return []

        escalated = []
        pending = self.memory.get_pending_proposals()

        for entry in pending:
            data = json.loads(entry.content)
            if data.get("category") != 2:
                continue

            pid = data.get("proposal_id", "")
            self._escalation_counts[pid] = self._escalation_counts.get(pid, 0) + 1

            if self._escalation_counts[pid] >= MAX_ESCALATION_ATTEMPTS:
                # Escalate: Cat.2 → Cat.3
                data["category"] = 3
                data["escalated_from"] = 2
                data["escalation_reason"] = f"No response after {MAX_ESCALATION_ATTEMPTS} cycles"
                entry.content = json.dumps(data)
                entry.tags.append("escalated")
                self.memory._persist_memory_entry(entry)

                self._stats["escalations"] += 1
                escalated.append(pid)
                logger.warning(f"⬆️ Proposal {pid} ESCALATED: Cat.2 → Cat.3")

        return escalated

    # ───────────────────────────────────────────────────────
    # LOGGING AND HELPERS
    # ───────────────────────────────────────────────────────

    def _append_evolution_log(self, spec: Any, result: EvolutionResult,
                              approved_by: str = "auto") -> None:
        """Append an entry to evolution_log.jsonl."""
        self.evolution_log_path.parent.mkdir(parents=True, exist_ok=True)

        log_entry = {
            "timestamp": result.timestamp,
            "category": result.category,
            "status": result.status,
            "proposal_id": result.proposal_id,
            "spec_summary": result.spec_summary,
            "approved_by": approved_by,
            "tests_passed": result.tests_passed,
            "branch_name": result.branch_name,
            "error": result.error,
        }

        if spec:
            log_entry["spec"] = self._spec_to_dict(spec)

        try:
            with open(self.evolution_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to write evolution log: {e}")

    @staticmethod
    def _spec_to_dict(spec: Any) -> dict:
        """Convert TechnicalSpec to dict safely."""
        return {
            "change_type": getattr(spec, "change_type", ""),
            "target_file": getattr(spec, "target_file", ""),
            "target_attribute": getattr(spec, "target_attribute", ""),
            "old_value": getattr(spec, "old_value", 0.0),
            "new_value": getattr(spec, "new_value", 0.0),
            "reason": getattr(spec, "reason", ""),
            "causal_score_est": getattr(spec, "causal_score_est", 0.0),
            "confidence": getattr(spec, "confidence", 0.0),
            "new_code": getattr(spec, "new_code", None),
            "old_code": getattr(spec, "old_code", None),
        }

    def get_stats(self) -> dict:
        """Return evolution statistics for GUI/snapshot."""
        return dict(self._stats)

    def get_pending_summary(self) -> list[dict]:
        """Return pending proposals for GUI display (compat v4)."""
        if not self.memory:
            return []

        pending = self.memory.get_pending_proposals()
        result = []
        for entry in pending:
            try:
                data = json.loads(entry.content)
                spec = data.get("spec", {})
                
                # Mapeo a formato GUI v3/v4 + Compatibilidad Tests
                result.append({
                    "id": data.get("proposal_id", ""),
                    "proposal_id": data.get("proposal_id", ""), # Requerido por tests
                    "timestamp": data.get("timestamp", ""),
                    "component": spec.get("target_file", "").split("/")[-1],
                    "change": f"{spec.get('target_attribute', '')}: {spec.get('old_value')} -> {spec.get('new_value')}",
                    "reason": spec.get("reason", ""),
                    "detailed_description": f"File: {spec.get('target_file')}\nType: {spec.get('change_type')}",
                    "estimated_delta": spec.get("causal_score_est", 0.0),
                    "confidence": spec.get("confidence", 0.0),
                    "status": data.get("status", "pending"),
                })
            except (json.JSONDecodeError, AttributeError):
                continue
        return result

    def get_parameter_landscape(self) -> dict[str, Any] | None:
        """Return latest parameter landscape artifact if present."""
        return load_parameter_landscape_map(self.landscape_artifact_path)

    @staticmethod
    def _is_parameter_landscape_spec(spec_dict: dict[str, Any]) -> bool:
        target_file = Path(str(spec_dict.get("target_file", ""))).name.lower()
        target_attribute = str(spec_dict.get("target_attribute", "")).strip().lower()
        change_type = str(spec_dict.get("change_type", "")).strip().lower()
        is_landscape_target = (
            target_file == "parameter_landscape_map.json"
            or target_attribute == "parameter_landscape_map"
        )
        return is_landscape_target and change_type in {"optimization", "feature", "parameter"}

    def _generate_parameter_landscape(self, approved_by: str) -> dict[str, Any]:
        """
        Generate and persist the Parameter Landscape artifact (S3 Step 4).
        """
        artifact = build_parameter_landscape_map(
            project_root=self.project_root,
            artifact_path=self.landscape_artifact_path,
            switcher=self.switcher,
            use_llm=False,
        )

        self._stats["landscape_generated"] += 1

        if self.memory:
            entry = self.memory.ingest_raw(
                content=json.dumps({
                    "type": "parameter_landscape_map",
                    "artifact_path": str(self.landscape_artifact_path),
                    "parameter_count": artifact.get("parameter_count", 0),
                    "generated_at": artifact.get("generated_at"),
                    "approved_by": approved_by,
                }),
                field="architect",
                tags=["evolution", "cat_2", "landscape", "artifact"],
            )
            self.memory.promote(
                entry_id=entry.entry_id,
                target_level=MemoryLevel.NORMALIZED,
                approved_by="auto",
            )
            self.memory.promote(
                entry_id=entry.entry_id,
                target_level=MemoryLevel.FACTS,
                approved_by="Lila",
            )
            self.memory.promote(
                entry_id=entry.entry_id,
                target_level=MemoryLevel.RELATIONS,
                approved_by="Lila",
            )

        return artifact
