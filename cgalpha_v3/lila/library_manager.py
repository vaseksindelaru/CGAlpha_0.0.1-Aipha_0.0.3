"""
CGAlpha v3 — Lila: Library Manager (Sección C)
===============================================
Bibliotecario central con gobernanza de calidad de fuentes.

REGLAS:
  - Ningún claim operativo se apoya solo en fuentes terciarias.
  - Mínimo 1 fuente primaria peer-reviewed por claim técnico relevante.
  - Trazabilidad: source_id obligatorio en cada recomendación.
  - Detección de duplicados y contradicciones con registro explícito.
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

log = logging.getLogger(__name__)

SourceType = Literal["primary", "secondary", "tertiary"]
BacklogStatus = Literal["open", "in_progress", "resolved"]
BacklogType = Literal["primary_source_gap", "theory_request", "evidence_conflict", "research_gap"]

# Fuentes primarias aceptadas (Sección C)
PRIMARY_VENUES = {
    "acl", "nips", "neurips", "icml", "jof", "journal_of_finance",
    "journal_of_financial_economics", "review_of_financial_studies",
    "management_science", "quantitative_finance",
}


@dataclass
class LibrarySource:
    """Fuente de la biblioteca de Lila."""
    source_id:        str
    title:            str
    authors:          list[str]
    year:             int
    source_type:      SourceType
    venue:            str          # Nombre de journal o conferencia
    url:              str | None
    abstract:         str
    relevant_finding: str
    applicability:    str
    tags:             list[str] = field(default_factory=list)
    ev_level:         int = 0     # 0=desconocido, 1=primaria, 2=secundaria, 3=terciaria
    ingested_at:      datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    duplicate_of:     str | None = None    # source_id de la fuente original si es duplicado
    contradicts:      list[str] = field(default_factory=list)  # source_ids con los que contradice
    executive_summary: str = ""
    tech_summary:      str = ""

    def __post_init__(self) -> None:
        # Nivel de evidencia automático
        ev_map: dict[SourceType, int] = {"primary": 1, "secondary": 2, "tertiary": 3}
        self.ev_level = ev_map[self.source_type]


@dataclass
class AdaptiveBacklogItem:
    """Elemento del backlog adaptativo liderado por Lila (impacto-riesgo-evidencia)."""
    item_id: str
    title: str
    rationale: str
    item_type: BacklogType
    impact: int
    risk: int
    evidence_gap: int
    priority_score: float
    requested_by: str = "lila"
    claim: str = ""
    related_source_ids: list[str] = field(default_factory=list)
    recommended_source_type: SourceType = "primary"
    status: BacklogStatus = "open"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolution_note: str = ""


class LibraryManager:
    """
    Gestiona la biblioteca de conocimiento de Lila.

    Funciones (Sección C):
      1. Ingesta con clasificación de tipo de fuente
      2. Regla de calidad (no solo terciarias en claims operativos)
      3. Métrica: ratio primarias/totales
      4. Detección de duplicados y contradicciones
      5. Búsqueda por texto/tags/tipo
      6. Trazabilidad source_id en recomendaciones
    """

    def __init__(self) -> None:
        self._sources: dict[str, LibrarySource] = {}
        self._content_hashes: dict[str, str] = {}  # hash → source_id
        self._adaptive_backlog: dict[str, AdaptiveBacklogItem] = {}
        self._primary_gap_index: dict[str, str] = {}

    # ── INGESTA ──────────────────────────────────
    def ingest(self, source: LibrarySource) -> tuple[LibrarySource, bool]:
        """
        Ingesta una fuente. Detecta duplicados por hash de contenido.
        Retorna (source, is_new).
        """
        content_hash = self._hash(source.title + source.abstract)

        # Detección de duplicado
        if content_hash in self._content_hashes:
            original_id = self._content_hashes[content_hash]
            source.duplicate_of = original_id
            log.warning(f"[Lila] Duplicado detectado: '{source.title}' == {original_id}")
            return source, False

        # Validación de fuente primaria
        if source.source_type == "primary":
            venue_key = source.venue.lower().replace(" ", "_")
            if not any(pv in venue_key for pv in PRIMARY_VENUES):
                log.warning(
                    f"[Lila] Fuente marcada 'primary' pero venue '{source.venue}' "
                    f"no está en lista de venues primarios reconocidos."
                )

        self._sources[source.source_id] = source
        self._content_hashes[content_hash] = source.source_id
        log.info(
            f"[Lila] Ingesta: [{source.source_type.upper()}] '{source.title}' "
            f"({source.year}) → {source.source_id}"
        )
        return source, True

    # ── CONTRADICCIONES ──────────────────────────
    def register_contradiction(
        self,
        source_id_a: str,
        source_id_b: str,
        note: str = "",
    ) -> None:
        """Registra contradicción entre dos fuentes."""
        for sid_a, sid_b in [(source_id_a, source_id_b), (source_id_b, source_id_a)]:
            if sid_a in self._sources:
                if sid_b not in self._sources[sid_a].contradicts:
                    self._sources[sid_a].contradicts.append(sid_b)
        log.warning(
            f"[Lila] Contradicción registrada entre {source_id_a} ↔ {source_id_b}. {note}"
        )

    # ── VALIDACIÓN DE CLAIM ───────────────────────
    def validate_claim(
        self,
        source_ids: list[str],
        claim: str = "",
    ) -> tuple[bool, str]:
        """
        Valida que un claim técnico tenga al menos 1 fuente primaria (Sección C, regla 2).
        Retorna (ok, mensaje).
        """
        sources = [self._sources[sid] for sid in source_ids if sid in self._sources]
        primaries = [s for s in sources if s.source_type == "primary"]

        if not sources:
            return False, f"claim '{claim}' sin fuentes registradas → insufficient_academic_basis"
        if not primaries:
            return False, (
                f"claim '{claim}' apoyado solo en fuentes "
                f"{[s.source_type for s in sources]} — se requiere ≥1 primaria"
            )
        return True, f"OK: {len(primaries)} fuente(s) primaria(s)"

    def detect_primary_source_gap(
        self,
        source_ids: list[str],
        claim: str = "",
        auto_backlog: bool = True,
        requested_by: str = "runtime",
    ) -> dict[str, Any]:
        """
        Detecta brecha de evidencia primaria en runtime.

        Si detecta gap y auto_backlog=True, crea (o reutiliza) backlog item priorizado.
        """
        ok, message = self.validate_claim(source_ids, claim)
        sources = [self._sources[sid] for sid in source_ids if sid in self._sources]
        primaries = [s for s in sources if s.source_type == "primary"]
        missing_ids = [sid for sid in source_ids if sid not in self._sources]
        gap = not ok
        backlog_item: AdaptiveBacklogItem | None = None

        if gap and auto_backlog:
            fingerprint = self._hash(f"{claim.strip().lower()}::{','.join(sorted(source_ids))}")
            existing_id = self._primary_gap_index.get(fingerprint)
            existing_item = self._adaptive_backlog.get(existing_id) if existing_id else None

            if existing_item and existing_item.status in ("open", "in_progress"):
                backlog_item = existing_item
            else:
                claim_text = claim.strip() or "claim_sin_descripcion"
                backlog_item = self.add_backlog_item(
                    title=f"Primary source gap: {claim_text[:90]}",
                    rationale=(
                        "Claim técnico sin evidencia primaria suficiente detectado en runtime. "
                        "Se requiere mínimo 1 fuente primaria peer-reviewed antes de escalar."
                    ),
                    item_type="primary_source_gap",
                    impact=5,
                    risk=4,
                    evidence_gap=5,
                    requested_by=requested_by,
                    claim=claim_text,
                    related_source_ids=source_ids,
                    recommended_source_type="primary",
                )
                self._primary_gap_index[fingerprint] = backlog_item.item_id

        return {
            "primary_source_gap": gap,
            "claim_ok": ok,
            "validation_message": message,
            "sources_total": len(sources),
            "primary_count": len(primaries),
            "missing_source_ids": missing_ids,
            "backlog_item_id": backlog_item.item_id if backlog_item else None,
        }

    # ── BÚSQUEDA ──────────────────────────────────
    def search(
        self,
        query: str = "",
        source_type: SourceType | None = None,
        tags: list[str] | None = None,
        limit: int = 20,
    ) -> list[LibrarySource]:
        """Búsqueda por texto, tipo y/o tags."""
        results = list(self._sources.values())

        if source_type:
            results = [s for s in results if s.source_type == source_type]

        if tags:
            results = [
                s for s in results
                if any(t in s.tags for t in tags)
            ]

        if query:
            ql = query.lower()
            results = [
                s for s in results
                if ql in s.title.lower()
                or ql in s.abstract.lower()
                or ql in s.relevant_finding.lower()
                or any(ql in t.lower() for t in s.tags)
            ]

        return results[:limit]

    def recent_sources(self, limit: int = 10) -> list[LibrarySource]:
        """Fuentes más recientes para Theory Live."""
        ordered = sorted(
            self._sources.values(),
            key=lambda s: s.ingested_at,
            reverse=True,
        )
        return ordered[:limit]

    # ── BACKLOG ADAPTATIVO (Sección C) ────────────
    def add_backlog_item(
        self,
        *,
        title: str,
        rationale: str,
        item_type: BacklogType,
        impact: int,
        risk: int,
        evidence_gap: int,
        requested_by: str = "lila",
        claim: str = "",
        related_source_ids: list[str] | None = None,
        recommended_source_type: SourceType = "primary",
    ) -> AdaptiveBacklogItem:
        """Crea item priorizado por impacto-riesgo-evidencia."""
        self._validate_score_range(impact, "impact")
        self._validate_score_range(risk, "risk")
        self._validate_score_range(evidence_gap, "evidence_gap")

        score = self._priority_score(
            impact=impact,
            risk=risk,
            evidence_gap=evidence_gap,
        )
        now = datetime.now(timezone.utc)
        item = AdaptiveBacklogItem(
            item_id=f"bl-{uuid.uuid4().hex[:8]}",
            title=title.strip() or "backlog_item",
            rationale=rationale.strip() or "N/A",
            item_type=item_type,
            impact=impact,
            risk=risk,
            evidence_gap=evidence_gap,
            priority_score=score,
            requested_by=requested_by,
            claim=claim.strip(),
            related_source_ids=related_source_ids or [],
            recommended_source_type=recommended_source_type,
            created_at=now,
            updated_at=now,
        )
        self._adaptive_backlog[item.item_id] = item
        return item

    def list_backlog(
        self,
        *,
        status: BacklogStatus | None = "open",
        limit: int = 20,
    ) -> list[AdaptiveBacklogItem]:
        """Lista backlog adaptativo, ordenado por prioridad desc."""
        items = list(self._adaptive_backlog.values())
        if status is not None:
            items = [i for i in items if i.status == status]
        items.sort(
            key=lambda i: (i.priority_score, i.created_at.timestamp()),
            reverse=True,
        )
        return items[:limit]

    def resolve_backlog_item(
        self,
        item_id: str,
        resolution_note: str = "",
    ) -> AdaptiveBacklogItem | None:
        """Marca item como resuelto."""
        item = self._adaptive_backlog.get(item_id)
        if not item:
            return None
        item.status = "resolved"
        item.updated_at = datetime.now(timezone.utc)
        item.resolution_note = resolution_note.strip()
        return item

    def adaptive_backlog_snapshot(self, limit: int = 10) -> dict[str, Any]:
        """Snapshot para GUI Theory Live."""
        open_items = self.list_backlog(status="open", limit=10_000)
        in_progress_items = self.list_backlog(status="in_progress", limit=10_000)
        resolved_items = self.list_backlog(status="resolved", limit=10_000)
        primary_gap_open = sum(1 for i in open_items if i.item_type == "primary_source_gap")
        top_items = self.list_backlog(status="open", limit=limit)

        return {
            "open": len(open_items),
            "in_progress": len(in_progress_items),
            "resolved": len(resolved_items),
            "primary_source_gap_open": primary_gap_open,
            "top_priority_score": top_items[0].priority_score if top_items else 0.0,
            "top_items": top_items,
        }

    def theory_live_snapshot(self, limit_sources: int = 6, limit_backlog: int = 6) -> dict[str, Any]:
        """Snapshot consolidado de Theory Live conectado a Library/Lila."""
        counts = {
            "primary": len(self.search(source_type="primary", limit=10_000)),
            "secondary": len(self.search(source_type="secondary", limit=10_000)),
            "tertiary": len(self.search(source_type="tertiary", limit=10_000)),
        }
        backlog = self.adaptive_backlog_snapshot(limit=limit_backlog)
        return {
            "library": self.library_snapshot(),
            "counts": counts,
            "primary_source_gap_open": backlog["primary_source_gap_open"] > 0,
            "recent_sources": self.recent_sources(limit=limit_sources),
            "backlog": backlog,
        }

    # ── MÉTRICAS (Sección C) ──────────────────────
    @property
    def primary_ratio(self) -> float:
        """Ratio fuentes primarias / totales. Visible en GUI (Sección C MVP)."""
        if not self._sources:
            return 0.0
        primaries = sum(1 for s in self._sources.values() if s.source_type == "primary")
        return primaries / len(self._sources)

    @property
    def total_docs(self) -> int:
        return len(self._sources)

    @property
    def pending_review(self) -> int:
        """Fuentes sin summary técnico generado."""
        return sum(1 for s in self._sources.values() if not s.tech_summary)

    def library_snapshot(self) -> dict:
        """Compatible con library_status_snapshot (Sección J)."""
        return {
            "total_docs":    self.total_docs,
            "primary_ratio": round(self.primary_ratio, 3),
            "pending_review": self.pending_review,
            "last_ingestion": (
                max((s.ingested_at for s in self._sources.values()), default=None)
            ),
        }

    # ── UTILS ─────────────────────────────────────
    @staticmethod
    def _validate_score_range(value: int, field_name: str) -> None:
        if value < 1 or value > 5:
            raise ValueError(f"{field_name} must be between 1 and 5")

    @staticmethod
    def _priority_score(*, impact: int, risk: int, evidence_gap: int) -> float:
        """
        Score 0..100 priorizando impacto-riesgo-evidencia.
        Pesos: impacto 0.45, riesgo 0.35, evidencia 0.20.
        """
        weighted = (impact * 0.45) + (risk * 0.35) + (evidence_gap * 0.20)
        return round((weighted / 5.0) * 100.0, 2)

    @staticmethod
    def _hash(content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()

    @staticmethod
    def new_source_id() -> str:
        return f"src-{uuid.uuid4().hex[:8]}"
