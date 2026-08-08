"""
Tests — Lila Library Manager (cgalpha_v3)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from cgalpha_v3.lila.library_manager import LibraryManager, LibrarySource


def make_source(
    source_type: str = "primary",
    title: str = "Test Paper",
    abstract: str = "Test abstract for dedup detection.",
    venue: str = "Journal of Finance",
) -> LibrarySource:
    return LibrarySource(
        source_id=LibraryManager.new_source_id(),
        title=title,
        authors=["Author, A."],
        year=2023,
        source_type=source_type,  # type: ignore[arg-type]
        venue=venue,
        url=None,
        abstract=abstract,
        relevant_finding="Hallazgo relevante.",
        applicability="Aplicable a CGAlpha v3.",
        tags=["ml", "trading"],
    )


@pytest.fixture
def lila() -> LibraryManager:
    return LibraryManager()


class TestLibraryIngestion:
    def test_ingest_primary_source(self, lila: LibraryManager):
        src = make_source("primary")
        result, is_new = lila.ingest(src)
        assert is_new
        assert lila.total_docs == 1

    def test_duplicate_detected(self, lila: LibraryManager):
        src1 = make_source("primary", title="Same", abstract="Same abstract.")
        src2 = make_source("secondary", title="Same", abstract="Same abstract.")
        _, new1 = lila.ingest(src1)
        _, new2 = lila.ingest(src2)
        assert new1
        assert not new2
        assert src2.duplicate_of == src1.source_id
        assert lila.total_docs == 1  # Solo 1 ingresado

    def test_primary_ratio(self, lila: LibraryManager):
        lila.ingest(make_source("primary", abstract="primary abstract"))
        lila.ingest(make_source("secondary", title="Blog Post", abstract="secondary abstract"))
        assert abs(lila.primary_ratio - 0.5) < 0.01


class TestClaimValidation:
    def test_claim_with_primary_passes(self, lila: LibraryManager):
        src = make_source("primary", abstract="claim source abstract")
        lila.ingest(src)
        ok, msg = lila.validate_claim([src.source_id], "Test claim")
        assert ok

    def test_claim_without_sources_fails(self, lila: LibraryManager):
        ok, msg = lila.validate_claim([], "Empty claim")
        assert not ok
        assert "insufficient_academic_basis" in msg

    def test_claim_only_tertiary_fails(self, lila: LibraryManager):
        src = make_source("tertiary", abstract="tertiary source abstract")
        lila.ingest(src)
        ok, msg = lila.validate_claim([src.source_id], "Tertiary-only claim")
        assert not ok
        assert "primaria" in msg


class TestSearch:
    def test_search_by_text(self, lila: LibraryManager):
        lila.ingest(make_source("primary", title="Momentum Strategies", abstract="momentum research"))
        results = lila.search("momentum")
        assert len(results) == 1

    def test_search_by_type(self, lila: LibraryManager):
        lila.ingest(make_source("primary", abstract="primary content"))
        lila.ingest(make_source("secondary", title="Blog", abstract="blog content"))
        primaries = lila.search(source_type="primary")
        assert all(s.source_type == "primary" for s in primaries)

    def test_search_by_tags(self, lila: LibraryManager):
        src = make_source("primary", abstract="tagged content")
        src.tags = ["momentum", "mean-reversion"]
        lila.ingest(src)
        results = lila.search(tags=["momentum"])
        assert len(results) == 1


class TestContradiction:
    def test_register_contradiction(self, lila: LibraryManager):
        s1 = make_source("primary", abstract="thesis abstract content A")
        s2 = make_source("primary", title="Counter Thesis", abstract="counter abstract content B")
        lila.ingest(s1)
        lila.ingest(s2)
        lila.register_contradiction(s1.source_id, s2.source_id, "Resultados opuestos")
        assert s2.source_id in lila._sources[s1.source_id].contradicts
        assert s1.source_id in lila._sources[s2.source_id].contradicts


class TestPrimarySourceGapRuntime:
    def test_detect_primary_source_gap_creates_backlog_item(self, lila: LibraryManager):
        tertiary = make_source("tertiary", title="Forum Note", abstract="opinion-based note")
        lila.ingest(tertiary)

        result = lila.detect_primary_source_gap(
            source_ids=[tertiary.source_id],
            claim="Momentum edge intradia",
            auto_backlog=True,
            requested_by="test_runtime",
        )

        assert result["primary_source_gap"] is True
        assert result["claim_ok"] is False
        assert result["backlog_item_id"] is not None

        backlog = lila.list_backlog(status="open", limit=10)
        assert len(backlog) == 1
        assert backlog[0].item_type == "primary_source_gap"
        assert backlog[0].requested_by == "test_runtime"

    def test_detect_primary_source_gap_without_gap_when_primary_exists(self, lila: LibraryManager):
        primary = make_source("primary", title="Primary Evidence", abstract="peer reviewed result")
        lila.ingest(primary)

        result = lila.detect_primary_source_gap(
            source_ids=[primary.source_id],
            claim="Momentum edge intradia",
            auto_backlog=True,
        )
        assert result["primary_source_gap"] is False
        assert result["claim_ok"] is True
        assert result["backlog_item_id"] is None
        assert lila.list_backlog(status="open", limit=10) == []


class TestAdaptiveBacklogEngine:
    def test_prioritization_orders_by_impact_risk_evidence(self, lila: LibraryManager):
        low = lila.add_backlog_item(
            title="Low priority",
            rationale="low impact",
            item_type="research_gap",
            impact=1,
            risk=1,
            evidence_gap=2,
        )
        high = lila.add_backlog_item(
            title="High priority",
            rationale="critical missing evidence",
            item_type="primary_source_gap",
            impact=5,
            risk=5,
            evidence_gap=5,
        )
        items = lila.list_backlog(status="open", limit=10)
        assert len(items) == 2
        assert items[0].item_id == high.item_id
        assert items[0].priority_score > items[1].priority_score
        assert low.priority_score < high.priority_score

    def test_theory_live_snapshot_reflects_backlog_and_recent_sources(self, lila: LibraryManager):
        s1 = make_source("secondary", title="Secondary", abstract="secondary text")
        s2 = make_source("primary", title="Primary", abstract="primary text")
        lila.ingest(s1)
        lila.ingest(s2)
        lila.add_backlog_item(
            title="Need primary confirmation",
            rationale="runtime gap",
            item_type="primary_source_gap",
            impact=5,
            risk=4,
            evidence_gap=5,
        )

        snapshot = lila.theory_live_snapshot(limit_sources=5, limit_backlog=5)
        assert snapshot["library"]["total_docs"] == 2
        assert snapshot["primary_source_gap_open"] is True
        assert len(snapshot["recent_sources"]) == 2
        assert snapshot["backlog"]["open"] == 1


class TestValidateScoreRange:
    def test_score_below_minimum_raises_value_error(self, lila: LibraryManager):
        with pytest.raises(ValueError, match="impact must be between 1 and 5"):
            lila.add_backlog_item(
                title="out of range",
                rationale="testing",
                item_type="research_gap",
                impact=0,
                risk=3,
                evidence_gap=3,
            )

    def test_score_above_maximum_raises_value_error(self, lila: LibraryManager):
        with pytest.raises(ValueError, match="risk must be between 1 and 5"):
            lila.add_backlog_item(
                title="out of range",
                rationale="testing",
                item_type="research_gap",
                impact=3,
                risk=6,
                evidence_gap=3,
            )


class TestResolveBacklogItem:
    def test_resolve_unknown_item_returns_none(self, lila: LibraryManager):
        result = lila.resolve_backlog_item(item_id="bl-nonexistent", resolution_note="N/A")
        assert result is None

    def test_resolve_existing_item_changes_status(self, lila: LibraryManager):
        item = lila.add_backlog_item(
            title="To resolve",
            rationale="testing resolve",
            item_type="theory_request",
            impact=3,
            risk=2,
            evidence_gap=4,
        )
        resolved = lila.resolve_backlog_item(item_id=item.item_id, resolution_note="Done")
        assert resolved is not None
        assert resolved.status == "resolved"
        assert resolved.resolution_note == "Done"
