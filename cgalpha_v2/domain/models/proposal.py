"""
cgalpha.domain.models.proposal — Code Evolution proposal entity.

This module defines the Proposal entity and supporting value objects for the
Code Evolution (Code Craft Sage) bounded context.

Design notes:
- Proposal is an entity identified by proposal_id.
- ProposalStatus tracks the lifecycle: PENDING → APPROVED/REJECTED → APPLIED.
- EvaluationResult captures the scoring logic (impact, risk, difficulty).
- ProposalSeverity maps to priority in the execution queue.
- All frozen — state transitions produce new Proposal instances.

Ubiquitous Language:
    Proposal          → A suggested change to system parameters or code.
    ProposalStatus    → Lifecycle state of a proposal.
    ProposalSeverity  → Urgency classification (low → critical).
    EvaluationResult  → Quantitative assessment of a proposal.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class ProposalStatus(Enum):
    """Lifecycle state of a change proposal."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    ROLLED_BACK = "rolled_back"
    QUARANTINED = "quarantined"


class ProposalSeverity(Enum):
    """
    Urgency classification for a proposal.

    Maps to execution queue priority:
    CRITICAL → immediate, HIGH → next cycle, MEDIUM → normal, LOW → deferred.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProposalSource(Enum):
    """Origin of the proposal."""

    GHOST_ARCHITECT = "ghost_architect"
    RISK_BARRIER_LAB = "risk_barrier_lab"
    MANUAL = "manual"
    CODE_CRAFT = "code_craft"


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    """
    Quantitative assessment of a proposal.

    The evaluator scores proposals on four dimensions, then computes
    a composite score to decide approval.

    Attributes:
        impact_score:     Expected positive impact [0.0, 1.0].
        risk_score:       Risk of negative side effects [0.0, 1.0].
        difficulty_score: Implementation difficulty [0.0, 1.0].
        complexity_score: System complexity impact [0.0, 1.0].
        composite_score:  Weighted combination of all dimensions.
        approved:         Whether the evaluator recommends approval.
        reason:           Explanation for the approval/rejection decision.
        crisis_multiplier: Emergency multiplier applied during crisis.
    """

    impact_score: float
    risk_score: float
    difficulty_score: float
    complexity_score: float
    composite_score: float
    approved: bool
    reason: str = ""
    crisis_multiplier: float = 1.0

    def __post_init__(self) -> None:
        for field_name, value in [
            ("impact_score", self.impact_score),
            ("risk_score", self.risk_score),
            ("difficulty_score", self.difficulty_score),
            ("complexity_score", self.complexity_score),
        ]:
            if not (0.0 <= value <= 1.0):
                raise ValueError(
                    f"EvaluationResult {field_name} must be in [0, 1], "
                    f"got {value}"
                )


@dataclass(frozen=True, slots=True)
class Proposal:
    """
    A change proposal — the primary entity in the Code Evolution context.

    A Proposal captures a suggested change to the system, its justification,
    its evaluation, and lifecycle state.  Proposals are created by the
    Ghost Architect or RiskBarrierLab, evaluated, and then either applied
    or rejected.

    Attributes:
        proposal_id:    Unique identifier (format: PROP_<timestamp>_<hash>).
        title:          Short human-readable title.
        description:    Full description of the proposed change.
        source:         Where the proposal originated.
        severity:       Urgency classification.
        status:         Current lifecycle state.
        target_parameter: Config path to change (e.g. 'Trading.tp_factor').
        current_value:  Current parameter value (as string for generality).
        proposed_value: Suggested new value.
        confidence:     Confidence in the proposal [0.0, 1.0].
        evaluation:     Quantitative evaluation result (if evaluated).
        created_at:     When the proposal was created.
        resolved_at:    When the proposal was applied/rejected (if resolved).
    """

    proposal_id: str
    title: str
    description: str
    source: ProposalSource
    severity: ProposalSeverity = ProposalSeverity.MEDIUM
    status: ProposalStatus = ProposalStatus.PENDING
    target_parameter: Optional[str] = None
    current_value: Optional[str] = None
    proposed_value: Optional[str] = None
    confidence: float = 0.5
    evaluation: Optional[EvaluationResult] = None
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.proposal_id:
            raise ValueError("Proposal proposal_id cannot be empty")
        if not self.title:
            raise ValueError("Proposal title cannot be empty")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"Proposal confidence must be in [0, 1], "
                f"got {self.confidence}"
            )

    @property
    def is_resolved(self) -> bool:
        """True if the proposal has been applied, rejected, or rolled back."""
        return self.status in (
            ProposalStatus.APPLIED,
            ProposalStatus.REJECTED,
            ProposalStatus.ROLLED_BACK,
            ProposalStatus.QUARANTINED,
        )

    @property
    def is_approved(self) -> bool:
        """True if the proposal was approved for application."""
        return self.status == ProposalStatus.APPROVED

    def with_status(self, new_status: ProposalStatus) -> Proposal:
        """
        Return a new Proposal with updated status.

        Because Proposal is frozen, state transitions produce new instances.
        This preserves immutability while allowing lifecycle progression.
        """
        # We create a new instance by extracting all fields
        from dataclasses import asdict

        data = asdict(self)
        data["status"] = new_status
        if new_status in (
            ProposalStatus.APPLIED,
            ProposalStatus.REJECTED,
            ProposalStatus.ROLLED_BACK,
            ProposalStatus.QUARANTINED,
        ):
            data["resolved_at"] = datetime.utcnow()
        return Proposal(**data)

    def with_evaluation(self, evaluation: EvaluationResult) -> Proposal:
        """Return a new Proposal with evaluation result attached."""
        from dataclasses import asdict

        data = asdict(self)
        data["evaluation"] = evaluation
        new_status = (
            ProposalStatus.APPROVED if evaluation.approved else ProposalStatus.REJECTED
        )
        data["status"] = new_status
        if not evaluation.approved:
            data["resolved_at"] = datetime.utcnow()
        return Proposal(**data)
