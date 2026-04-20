"""
Tests para el puente v4: AutoProposer -> EvolutionOrchestrator.
"""

from __future__ import annotations

from types import SimpleNamespace

from cgalpha_v3.application.pipeline import TripleCoincidencePipeline


def _make_proposal(attr: str) -> SimpleNamespace:
    return SimpleNamespace(target_attribute=attr)


def test_route_auto_proposals_without_orchestrator_returns_empty():
    pipeline = TripleCoincidencePipeline.__new__(TripleCoincidencePipeline)
    pipeline.evolution_orchestrator = None

    proposals = [_make_proposal("min_confidence")]
    routed = pipeline._route_auto_proposals(proposals)

    assert routed == []


def test_route_auto_proposals_calls_orchestrator_and_maps_results():
    calls: list[str] = []

    class FakeOrchestrator:
        def process_proposal(self, proposal):
            calls.append(proposal.target_attribute)
            return SimpleNamespace(
                category=2,
                status="PENDING_APPROVAL",
                proposal_id=f"ev-{proposal.target_attribute}",
                error="",
            )

    pipeline = TripleCoincidencePipeline.__new__(TripleCoincidencePipeline)
    pipeline.evolution_orchestrator = FakeOrchestrator()

    proposals = [_make_proposal("min_confidence"), _make_proposal("volume_threshold")]
    routed = pipeline._route_auto_proposals(proposals)

    assert calls == ["min_confidence", "volume_threshold"]
    assert len(routed) == 2
    assert routed[0]["status"] == "PENDING_APPROVAL"
    assert routed[0]["proposal_id"] == "ev-min_confidence"
    assert routed[1]["target_attribute"] == "volume_threshold"

