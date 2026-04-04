"""
CGAlpha v3 — Intelligent Memory Policy Engine
==============================================
Implementa P2.1-P2.4:
  - campo memory_librarian activo
  - política 0a/0b/1/2/3/4 con promoción/degradación
  - TTL y retención automática
  - degradación por cambio de régimen (>2σ sostenido 20 sesiones)
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Literal

from cgalpha_v3.domain.models.signal import MemoryEntry, MemoryLevel

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

    TTL_BY_LEVEL_HOURS = {
        MemoryLevel.RAW: 24,
        MemoryLevel.NORMALIZED: 24 * 7,
        MemoryLevel.FACTS: 24 * 30,
        MemoryLevel.RELATIONS: 24 * 90,
        MemoryLevel.PLAYBOOKS: None,
        MemoryLevel.STRATEGY: None,
    }
    APPROVER_BY_LEVEL = {
        MemoryLevel.RAW: "auto",
        MemoryLevel.NORMALIZED: "auto",
        MemoryLevel.FACTS: "Lila",
        MemoryLevel.RELATIONS: "Lila",
        MemoryLevel.PLAYBOOKS: "human",
        MemoryLevel.STRATEGY: "human",
    }
    LEVEL_ORDER = [
        MemoryLevel.RAW,
        MemoryLevel.NORMALIZED,
        MemoryLevel.FACTS,
        MemoryLevel.RELATIONS,
        MemoryLevel.PLAYBOOKS,
        MemoryLevel.STRATEGY,
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

        entry.level = target_level
        entry.approved_by = approved_by
        entry.expires_at = self._expiry_for_level(target_level, now_dt)
        if tags:
            for tag in tags:
                if tag not in entry.tags:
                    entry.tags.append(tag)
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

        return {
            "total_entries": len(self.entries),
            "levels": levels,
            "fields": fields,
            "stale_entries": stale,
            "expiring_within_24h": expiring_24h,
            "last_regime_shift": self.regime_events[-1].created_at.isoformat() if self.regime_events else None,
            "regime_events_count": len(self.regime_events),
        }

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
        }
        if norm in aliases:
            return aliases[norm]
        raise ValueError(f"invalid_level:{value}")

    def _must_get(self, entry_id: str) -> MemoryEntry:
        entry = self.entries.get(entry_id)
        if entry is None:
            raise ValueError("entry_not_found")
        return entry

    def _expiry_for_level(self, level: MemoryLevel, now_dt: datetime) -> datetime | None:
        ttl_h = self.TTL_BY_LEVEL_HOURS[level]
        if ttl_h is None:
            return None
        return now_dt + timedelta(hours=ttl_h)

