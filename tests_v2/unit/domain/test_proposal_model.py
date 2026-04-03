"""Unit tests for cgalpha_v2.domain.models.proposal."""

from __future__ import annotations

from cgalpha_v2.domain.models import (
    EvaluationResult,
    Proposal,
    ProposalSource,
    ProposalStatus,
)

import pytest


def test_evaluation_result_validation_raises() -> None:
    with pytest.raises(ValueError, match="impact_score"):
        EvaluationResult(
            impact_score=1.1,
            risk_score=0.5,
            difficulty_score=0.5,
            complexity_score=0.5,
            composite_score=0.5,
            approved=True,
        )


def test_proposal_validation_raises() -> None:
    with pytest.raises(ValueError, match="proposal_id"):
        Proposal(
            proposal_id="",
            title="t",
            description="d",
            source=ProposalSource.MANUAL,
        )

    with pytest.raises(ValueError, match="title"):
        Proposal(
            proposal_id="P1",
            title="",
            description="d",
            source=ProposalSource.MANUAL,
        )

    with pytest.raises(ValueError, match="confidence"):
        Proposal(
            proposal_id="P1",
            title="t",
            description="d",
            source=ProposalSource.MANUAL,
            confidence=1.2,
        )


def test_proposal_status_helpers() -> None:
    proposal = Proposal(
        proposal_id="P1",
        title="Increase threshold",
        description="desc",
        source=ProposalSource.MANUAL,
        status=ProposalStatus.APPROVED,
    )
    assert proposal.is_approved is True
    assert proposal.is_resolved is False


def test_with_status_sets_resolved_at_for_terminal_states() -> None:
    proposal = Proposal(
        proposal_id="P1",
        title="Increase threshold",
        description="desc",
        source=ProposalSource.MANUAL,
    )
    rejected = proposal.with_status(ProposalStatus.REJECTED)
    assert rejected.status == ProposalStatus.REJECTED
    assert rejected.resolved_at is not None


def test_with_evaluation_transitions_status() -> None:
    proposal = Proposal(
        proposal_id="P1",
        title="Increase threshold",
        description="desc",
        source=ProposalSource.MANUAL,
    )
    approved_eval = EvaluationResult(
        impact_score=0.8,
        risk_score=0.2,
        difficulty_score=0.3,
        complexity_score=0.2,
        composite_score=0.7,
        approved=True,
    )
    approved_proposal = proposal.with_evaluation(approved_eval)
    assert approved_proposal.status == ProposalStatus.APPROVED
    assert approved_proposal.resolved_at is None

    rejected_eval = EvaluationResult(
        impact_score=0.2,
        risk_score=0.8,
        difficulty_score=0.7,
        complexity_score=0.8,
        composite_score=0.3,
        approved=False,
    )
    rejected_proposal = proposal.with_evaluation(rejected_eval)
    assert rejected_proposal.status == ProposalStatus.REJECTED
    assert rejected_proposal.resolved_at is not None


def test_with_status_keeps_evaluation_object_type() -> None:
    proposal = Proposal(
        proposal_id="P1",
        title="Increase threshold",
        description="desc",
        source=ProposalSource.MANUAL,
    )
    evaluation = EvaluationResult(
        impact_score=0.8,
        risk_score=0.2,
        difficulty_score=0.3,
        complexity_score=0.2,
        composite_score=0.7,
        approved=True,
    )
    with_eval = proposal.with_evaluation(evaluation)
    moved = with_eval.with_status(ProposalStatus.APPLIED)
    assert isinstance(moved.evaluation, EvaluationResult)
