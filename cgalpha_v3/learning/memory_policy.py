"""
cgAlpha_0.0.1 — Intelligent Memory Policy Engine
=================================================
Implementa P2.1-P2.4 + v4 IDENTITY level:
  - campo memory_librarian activo
  - política 0a/0b/1/2/3/4/5 con promoción/degradación
  - TTL y retención automática
  - degradación por cambio de régimen (>2σ sostenido 20 sesiones)
  - v4: IDENTITY level (5) — inmune a régimen shift, TTL infinito
  - v4: load_from_disk() para persistencia entre sesiones
"""
from __future__ import annotations

import hashlib
import json
import logging
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

from cgalpha_v3.domain.models.signal import MemoryEntry, MemoryLevel

logger = logging.getLogger("memory_policy")

LearningField = Literal["codigo", "math", "trading", "architect", "memory_librarian"]


@dataclass
class RegimeShiftEvent:
    shift_id: str
    created_at: datetime
    mean_historic: float
    std_historic: float
    mean_recent: float
    threshold: float
    affected_entries: int = 0


@dataclass
class MemoryPolicyEngine:
    entries: dict[str, MemoryEntry] = field(default_factory=dict)
    regime_events: list[RegimeShiftEvent] = field(default_factory=list)
    _regime_seq: int = 0

    MEMORY_DIR = Path("cgalpha_v3/memory/memory_entries")
    IDENTITY_DIR = Path("cgalpha_v3/memory/identity")

    TTL_BY_LEVEL_HOURS = {
        MemoryLevel.RAW: 24,
        MemoryLevel.NORMALIZED: 24 * 7,
        MemoryLevel.FACTS: 24 * 30,
        MemoryLevel.RELATIONS: 24 * 90,
        MemoryLevel.PLAYBOOKS: None,
        MemoryLevel.STRATEGY: None,
        MemoryLevel.IDENTITY: None,
    }
    APPROVER_BY_LEVEL = {
        MemoryLevel.RAW: "auto",
        MemoryLevel.NORMALIZED: "auto",
        MemoryLevel.FACTS: "Lila",
        MemoryLevel.RELATIONS: "Lila",
        MemoryLevel.PLAYBOOKS: "human",
        MemoryLevel.STRATEGY: "human",
        MemoryLevel.IDENTITY: "human",
    }
    LEVEL_ORDER = [
        MemoryLevel.RAW,
        MemoryLevel.NORMALIZED,
        MemoryLevel.FACTS,
        MemoryLevel.RELATIONS,
        MemoryLevel.PLAYBOOKS,
        MemoryLevel.STRATEGY,
        MemoryLevel.IDENTITY,
    ]

    def ingest_raw(
        self,
        *,
        content: str,
        field: LearningField,
        source_id: str | None = None,
        source_type: Literal["primary", "secondary", "tertiary"] | None = None,
        tags: list[str] | None = None,
        now: datetime | None = None,
    ) -> MemoryEntry:
        now_dt = now or datetime.now(timezone.utc)
        entry = MemoryEntry.new(
            content=content,
            level=MemoryLevel.RAW,
            field=field,
            source_id=source_id,
            source_type=source_type,
            tags=tags or [],
            expires_at=self._expiry_for_level(MemoryLevel.RAW, now_dt),
        )
        entry.approved_by = self.APPROVER_BY_LEVEL[MemoryLevel.RAW]
        self.entries[entry.entry_id] = entry
        return entry

    def normalize(
        self,
        entry_id: str,
        *,
        tags: list[str] | None = None,
        now: datetime | None = None,
    ) -> MemoryEntry:
        return self.promote(
            entry_id=entry_id,
            target_level=MemoryLevel.NORMALIZED,
            approved_by=self.APPROVER_BY_LEVEL[MemoryLevel.NORMALIZED],
            tags=tags,
            now=now,
        )

    def promote(
        self,
        *,
        entry_id: str,
        target_level: MemoryLevel,
        approved_by: str,
        tags: list[str] | None = None,
        now: datetime | None = None,
    ) -> MemoryEntry:
        now_dt = now or datetime.now(timezone.utc)
        entry = self._must_get(entry_id)
        current_idx = self.LEVEL_ORDER.index(entry.level)
        target_idx = self.LEVEL_ORDER.index(target_level)
        if target_idx <= current_idx:
            raise ValueError("target_level must be above current level")

        # v4: Promoción a IDENTITY requiere aprobación humana explícita
        if target_level == MemoryLevel.IDENTITY:
            if approved_by != "human":
                raise ValueError(
                    "Promoción a IDENTITY requiere approved_by='human'. "
                    "Lila puede proponer pero no ejecutar esta promoción."
                )

        entry.level = target_level
        entry.approved_by = approved_by
        entry.expires_at = self._expiry_for_level(target_level, now_dt)
        if tags:
            for tag in tags:
                if tag not in entry.tags:
                    entry.tags.append(tag)

        # v4: dispatch de persistencia según nivel
        if target_level == MemoryLevel.IDENTITY:
            self._persist_identity_entry(entry)
        else:
            self._persist_memory_entry(entry)

        return entry

    def degrade(
        self,
        *,
        entry_id: str,
        target_level: MemoryLevel,
        reason: str,
        now: datetime | None = None,
    ) -> MemoryEntry:
        now_dt = now or datetime.now(timezone.utc)
        entry = self._must_get(entry_id)
        current_idx = self.LEVEL_ORDER.index(entry.level)
        target_idx = self.LEVEL_ORDER.index(target_level)
        if target_idx >= current_idx:
            raise ValueError("target_level must be below current level")

        entry.level = target_level
        entry.stale = True
        entry.approved_by = self.APPROVER_BY_LEVEL[target_level]
        entry.expires_at = self._expiry_for_level(target_level, now_dt)
        if reason:
            entry.tags.append(f"degraded:{reason}")
        return entry

    def apply_ttl_retention(self, *, now: datetime | None = None) -> dict[str, object]:
        now_dt = now or datetime.now(timezone.utc)
        expired: list[str] = []
        for entry_id, entry in list(self.entries.items()):
            if entry.expires_at and entry.expires_at <= now_dt:
                expired.append(entry_id)
                self.entries.pop(entry_id, None)
        return {
            "removed_count": len(expired),
            "removed_ids": expired,
            "remaining": len(self.entries),
        }

    def detect_and_apply_regime_shift(
        self,
        volatility_series: list[float],
        *,
        now: datetime | None = None,
    ) -> dict[str, object]:
        """
        Regla P2.4:
          cambio de régimen si media reciente de 20 sesiones > media histórica + 2σ.
        """
        now_dt = now or datetime.now(timezone.utc)

        if len(volatility_series) < 40:
            return {"regime_shift": False, "reason": "insufficient_history"}

        historic = volatility_series[:-20]
        recent = volatility_series[-20:]
        if len(historic) < 20:
            return {"regime_shift": False, "reason": "insufficient_historic_window"}

        mean_h = statistics.fmean(historic)
        std_h = statistics.pstdev(historic)
        threshold = mean_h + (2.0 * std_h)
        mean_r = statistics.fmean(recent)
        sustained = all(v > threshold for v in recent)
        shift = sustained and mean_r > threshold
        if not shift:
            return {
                "regime_shift": False,
                "threshold": threshold,
                "mean_historic": mean_h,
                "mean_recent": mean_r,
            }

        affected = 0
        for entry in self.entries.values():
            # v4 GUARD: IDENTITY entries are NEVER degraded by regime shift
            if entry.level == MemoryLevel.IDENTITY:
                continue

            if entry.level == MemoryLevel.STRATEGY:
                entry.level = MemoryLevel.PLAYBOOKS
                entry.stale = True
                entry.approved_by = self.APPROVER_BY_LEVEL[MemoryLevel.PLAYBOOKS]
                affected += 1
            elif entry.level == MemoryLevel.PLAYBOOKS:
                entry.level = MemoryLevel.RELATIONS
                entry.stale = True
                entry.approved_by = self.APPROVER_BY_LEVEL[MemoryLevel.RELATIONS]
                entry.expires_at = self._expiry_for_level(MemoryLevel.RELATIONS, now_dt)
                affected += 1

        self._regime_seq += 1
        event = RegimeShiftEvent(
            shift_id=f"regime-{self._regime_seq:04d}",
            created_at=now_dt,
            mean_historic=mean_h,
            std_historic=std_h,
            mean_recent=mean_r,
            threshold=threshold,
            affected_entries=affected,
        )
        self.regime_events.append(event)
        return {
            "regime_shift": True,
            "event": {
                "shift_id": event.shift_id,
                "created_at": event.created_at.isoformat(),
                "mean_historic": event.mean_historic,
                "std_historic": event.std_historic,
                "mean_recent": event.mean_recent,
                "threshold": event.threshold,
                "affected_entries": event.affected_entries,
            },
        }

    def list_entries(
        self,
        *,
        level: MemoryLevel | None = None,
        field: LearningField | None = None,
        limit: int = 50,
    ) -> list[MemoryEntry]:
        entries = list(self.entries.values())
        if level is not None:
            entries = [e for e in entries if e.level == level]
        if field is not None:
            entries = [e for e in entries if e.field == field]
        entries.sort(key=lambda e: e.created_at, reverse=True)
        return entries[:limit]

    def snapshot(self) -> dict[str, object]:
        levels = {lvl.value: 0 for lvl in self.LEVEL_ORDER}
        fields: dict[LearningField, int] = {
            "codigo": 0,
            "math": 0,
            "trading": 0,
            "architect": 0,
            "memory_librarian": 0,
        }
        stale = 0
        now_dt = datetime.now(timezone.utc)
        expiring_24h = 0
        for entry in self.entries.values():
            levels[entry.level.value] += 1
            fields[entry.field] += 1
            if entry.stale:
                stale += 1
            if entry.expires_at and entry.expires_at <= now_dt + timedelta(hours=24):
                expiring_24h += 1

        # v4 metrics
        identity_count = levels.get("5", 0)
        pending_count = sum(1 for e in self.entries.values() if "pending" in e.tags)

        return {
            "total_entries": len(self.entries),
            "levels": levels,
            "fields": fields,
            "stale_entries": stale,
            "expiring_within_24h": expiring_24h,
            "last_regime_shift": self.regime_events[-1].created_at.isoformat() if self.regime_events else None,
            "regime_events_count": len(self.regime_events),
            # v4 additions
            "identity_entries": identity_count,
            "pending_proposals": pending_count,
            "memory_health": "healthy" if identity_count > 0 else "no_identity",
        }

    # ───────────────────────────────────────────────────────────
    # v4: SEARCH AND QUERY METHODS
    # ───────────────────────────────────────────────────────────

    def search(self, *, query: str, level: MemoryLevel | None = None,
               field: str | None = None, limit: int = 20) -> list[MemoryEntry]:
        """Búsqueda por substring en el contenido. v4.1: semántica."""
        results = []
        query_lower = query.lower()
        for entry in self.entries.values():
            if level and entry.level != level:
                continue
            if field and entry.field != field:
                continue
            if query_lower in entry.content.lower():
                results.append(entry)
        results.sort(key=lambda e: e.created_at, reverse=True)
        return results[:limit]

    def get_identity_entries(self) -> list[MemoryEntry]:
        """Atajo para obtener todas las entradas IDENTITY."""
        return self.list_entries(level=MemoryLevel.IDENTITY, limit=100)

    def get_pending_proposals(self) -> list[MemoryEntry]:
        """Atajo para el Orchestrator: propuestas pendientes."""
        entries = self.list_entries(level=MemoryLevel.RELATIONS, limit=200)
        return [e for e in entries if "pending" in e.tags]

    # ───────────────────────────────────────────────────────────
    # v4: PERSISTENCE TO DISK
    # ───────────────────────────────────────────────────────────

    def load_from_disk(self, directory: str | None = None) -> dict:
        """
        Carga todas las entradas de memoria desde ficheros JSON en disco.
        Se llama una vez al iniciar el servidor. Resuelve BUG-7.
        """
        dir_path = Path(directory) if directory else self.MEMORY_DIR
        if not dir_path.exists():
            return {"loaded": 0, "errors": 0, "reason": "directory_not_found"}

        loaded = 0
        errors = 0
        identity_error = False
        level_counts = {lvl.value: 0 for lvl in self.LEVEL_ORDER}

        for json_file in sorted(dir_path.glob("*.json")):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                entry = MemoryEntry(
                    entry_id=data["entry_id"],
                    level=self.parse_level(data["level"]),
                    content=data["content"],
                    source_id=data.get("source_id"),
                    source_type=data.get("source_type"),
                    created_at=datetime.fromisoformat(data["created_at"]),
                    expires_at=(
                        datetime.fromisoformat(data["expires_at"])
                        if data.get("expires_at") else None
                    ),
                    approved_by=data.get("approved_by", "auto"),
                    field=data.get("field", "trading"),
                    tags=data.get("tags", []),
                    stale=data.get("stale", False),
                )

                now_dt = datetime.now(timezone.utc)
                if entry.expires_at and entry.expires_at <= now_dt:
                    continue

                self.entries[entry.entry_id] = entry
                level_counts[entry.level.value] += 1
                loaded += 1

            except json.JSONDecodeError as e:
                errors += 1
                logger.warning(f"JSON corrupto en {json_file.name}: {e}")
                if self._might_be_identity(json_file):
                    identity_error = True
            except (KeyError, ValueError) as e:
                errors += 1
                logger.warning(f"Campo faltante/inválido en {json_file.name}: {e}")
                if self._might_be_identity(json_file):
                    identity_error = True
            except Exception as e:
                errors += 1
                logger.error(f"Error cargando {json_file.name}: {type(e).__name__}: {e}")
                if self._might_be_identity(json_file):
                    identity_error = True

        if identity_error:
            logger.critical(
                "⚠️ IDENTITY entry no pudo cargarse desde disco — "
                "el mantra puede estar perdido. Verificar memory/identity/"
            )

        return {
            "loaded": loaded,
            "errors": errors,
            "levels": level_counts,
            "total_on_disk": loaded + errors,
            "identity_error": identity_error,
        }

    def _persist_memory_entry(self, entry: MemoryEntry) -> None:
        """Persiste un entry a disco como JSON."""
        self.MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        path = self.MEMORY_DIR / f"{entry.entry_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "entry_id": entry.entry_id,
                "level": entry.level.value,
                "content": entry.content,
                "source_id": entry.source_id,
                "source_type": entry.source_type,
                "created_at": entry.created_at.isoformat(),
                "expires_at": entry.expires_at.isoformat() if entry.expires_at else None,
                "approved_by": entry.approved_by,
                "field": entry.field,
                "tags": entry.tags,
                "stale": entry.stale,
            }, f, indent=2, ensure_ascii=False)

    def _persist_identity_entry(self, entry: MemoryEntry) -> None:
        """
        Persistencia reforzada para nivel IDENTITY.
        Crea fichero estándar + backup con hash.
        """
        self._persist_memory_entry(entry)

        content_hash = hashlib.sha256(entry.content.encode()).hexdigest()[:16]
        self.IDENTITY_DIR.mkdir(parents=True, exist_ok=True)
        backup_path = self.IDENTITY_DIR / f"{entry.entry_id}_{content_hash}.json"
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump({
                "entry_id": entry.entry_id,
                "level": entry.level.value,
                "content": entry.content,
                "content_hash": content_hash,
                "created_at": entry.created_at.isoformat(),
                "approved_by": entry.approved_by,
                "field": entry.field,
                "tags": entry.tags,
            }, f, indent=2, ensure_ascii=False)

    @staticmethod
    def _might_be_identity(json_file: Path) -> bool:
        """Heurística para detectar si un fichero corrupto era IDENTITY."""
        try:
            text = json_file.read_text(encoding="utf-8", errors="ignore")
            return '"5"' in text or '"IDENTITY"' in text or '"mantra"' in text
        except Exception:
            return False

    # ───────────────────────────────────────────────────────────
    # INTERNAL HELPERS
    # ───────────────────────────────────────────────────────────

    @classmethod
    def parse_level(cls, value: str) -> MemoryLevel:
        norm = value.strip().lower()
        map_by_value = {lvl.value: lvl for lvl in cls.LEVEL_ORDER}
        if norm in map_by_value:
            return map_by_value[norm]
        aliases = {
            "raw": MemoryLevel.RAW,
            "normalized": MemoryLevel.NORMALIZED,
            "facts": MemoryLevel.FACTS,
            "relations": MemoryLevel.RELATIONS,
            "playbooks": MemoryLevel.PLAYBOOKS,
            "strategy": MemoryLevel.STRATEGY,
            "identity": MemoryLevel.IDENTITY,
        }
        if norm in aliases:
            return aliases[norm]
        raise ValueError(f"invalid_level:{value}")

    def _must_get(self, entry_id: str) -> MemoryEntry:
        entry = self.entries.get(entry_id)
        if entry is None:
            raise KeyError(
                f"Entry '{entry_id}' not found in memory. "
                f"May have expired or not been loaded from disk."
            )
        return entry

    def _expiry_for_level(self, level: MemoryLevel, now_dt: datetime) -> datetime | None:
        ttl_h = self.TTL_BY_LEVEL_HOURS[level]
        if ttl_h is None:
            return None
        return now_dt + timedelta(hours=ttl_h)

