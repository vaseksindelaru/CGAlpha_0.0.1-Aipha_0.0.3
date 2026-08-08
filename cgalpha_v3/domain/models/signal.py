"""
CGAlpha v3 — Domain Models
===========================
Modelos de dominio puros. Sin dependencias externas.

Sección O (Prompt Maestro): ApproachType obligatorio en Signal.
Sección M: RiskAssessment obligatorio en Proposal.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field as dc_field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal


# ──────────────────────────────────────────────────────────────
# TAXONOMÍA DE ACERCAMIENTOS (Sección O)
# ──────────────────────────────────────────────────────────────

class ApproachType(str, Enum):
    """Tipo de acercamiento a zona de interés. Obligatorio en cada label."""
    TOUCH      = "TOUCH"       # Precio alcanza zona sin cierre beyond
    RETEST     = "RETEST"      # Regresa tras haber cerrado fuera
    REJECTION  = "REJECTION"   # Mecha opuesta >60% del rango
    BREAKOUT   = "BREAKOUT"    # Cierre confirmado beyond zona
    OVERSHOOT  = "OVERSHOOT"   # Cierre beyond zona sin retorno en N velas
    FAKE_BREAK = "FAKE_BREAK"  # Cierre beyond zona con retorno en N velas
    TRIPLE_COINCIDENCE = "TRIPLE_COINCIDENCE"  # Triple coincidencia: vela clave + zona acumulación + mini-tendencia


# ──────────────────────────────────────────────────────────────
# SEÑAL DE TRADING
# ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Signal:
    """
    Señal de trading de CGAlpha v3.
    `approach_type` es OBLIGATORIO (Sección O).
    `quality_score` debe ser ≥ min_signal_quality_score (Sección M).
    """
    signal_id:     str
    symbol:        str
    interval:      str
    direction:     Literal["LONG", "SHORT", "NEUTRAL"]
    approach_type: ApproachType
    quality_score: float          # 0.0 – 1.0
    price:         float
    generated_at:  datetime
    zone_id:       str | None = None
    source_id:     str | None = None   # Trazabilidad a fuente (Sección H)
    metadata:      dict[str, Any] = dc_field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.quality_score <= 1.0:
            raise ValueError(f"quality_score debe estar en [0,1], recibido: {self.quality_score}")

    @classmethod
    def new(
        cls,
        symbol: str,
        interval: str,
        direction: Literal["LONG", "SHORT", "NEUTRAL"],
        approach_type: ApproachType,
        quality_score: float,
        price: float,
        **kwargs: Any,
    ) -> "Signal":
        return cls(
            signal_id=str(uuid.uuid4()),
            symbol=symbol,
            interval=interval,
            direction=direction,
            approach_type=approach_type,
            quality_score=quality_score,
            price=price,
            generated_at=datetime.now(timezone.utc),
            **kwargs,
        )


# ──────────────────────────────────────────────────────────────
# EVALUACIÓN DE RIESGO (Sección M)
# ──────────────────────────────────────────────────────────────

@dataclass
class RiskAssessment:
    """
    Evaluación de riesgo obligatoria en toda propuesta.
    Sin estos campos, la propuesta es rechazada automáticamente (Sección M).
    """
    max_drawdown_impact_pct:   float        # Estimado de impacto en drawdown
    position_sizing_impact:    Literal["none", "increase", "decrease"]
    kill_switch_threshold:     str          # Condición que activaría kill-switch
    circuit_breaker_interaction: str        # Descripción de interacción con CB


# ──────────────────────────────────────────────────────────────
# PROPUESTA DE CAMBIO
# ──────────────────────────────────────────────────────────────

@dataclass
class Proposal:
    """
    Propuesta de mejora del Change Proposer (Sección E).
    Requiere `risk_assessment` completo.
    Requiere `approach_types_targeted` para taxonomía (Sección O).
    """
    proposal_id:            str
    agent_id:               str
    generated_at:           datetime
    session_id:             str
    hypothesis:             str
    approach_types_targeted: list[ApproachType]
    risk_assessment:        RiskAssessment
    symbols:                list[str] = dc_field(default_factory=lambda: ["BTCUSDT"])
    namespace:              str = "v3"
    scientific_justification: dict[str, Any] = dc_field(default_factory=dict)
    changes:                list[dict[str, Any]] = dc_field(default_factory=list)
    backtesting:            dict[str, Any] = dc_field(default_factory=dict)
    expected_impact:        dict[str, Any] = dc_field(default_factory=dict)
    risks:                  list[str] = dc_field(default_factory=list)
    validation_plan:        dict[str, Any] = dc_field(default_factory=dict)
    rollback:               dict[str, Any] = dc_field(default_factory=dict)
    complexity_delta:       Literal["none", "low", "medium", "high"] = "low"
    reversible:             bool = True
    status:                 Literal["pending", "validated", "rejected"] = "pending"

    def __post_init__(self) -> None:
        if self.namespace != "v3":
            raise ValueError("Namespace inválido: solo se acepta 'v3'. Usa --allow-legacy para v1/v2.")
        if not self.risk_assessment:
            raise ValueError("RiskAssessment es obligatorio en toda propuesta (Sección M).")

    @classmethod
    def new(
        cls,
        hypothesis: str,
        approach_types_targeted: list[ApproachType],
        risk_assessment: RiskAssessment,
        agent_id: str = "llm-cgalpha-v3",
        **kwargs: Any,
    ) -> "Proposal":
        return cls(
            proposal_id=f"prop-{uuid.uuid4().hex[:8]}",
            agent_id=agent_id,
            generated_at=datetime.now(timezone.utc),
            session_id=str(uuid.uuid4()),
            hypothesis=hypothesis,
            approach_types_targeted=approach_types_targeted,
            risk_assessment=risk_assessment,
            **kwargs,
        )


# ──────────────────────────────────────────────────────────────
# MEMORIA ESTRUCTURADA (Sección D)
# ──────────────────────────────────────────────────────────────

class MemoryLevel(str, Enum):
    """Niveles de memoria. Tabla completa en Sección D del Prompt Maestro."""
    RAW        = "0a"   # Raw intake,  TTL 24h,  aprobador: Automático
    NORMALIZED = "0b"   # Normalizado, TTL 7d,   aprobador: Automático
    FACTS      = "1"    # Hechos,      TTL 30d,  aprobador: Lila
    RELATIONS  = "2"    # Relaciones,  TTL 90d,  aprobador: Lila
    PLAYBOOKS  = "3"    # Playbooks,   TTL ver., aprobador: Humano
    STRATEGY   = "4"    # Estrategia,  TTL indef, aprobador: Humano
    IDENTITY   = "5"    # ADN de Lila, TTL ∞,    aprobador: Humano + firma v4


@dataclass
class MemoryEntry:
    """Entrada del sistema de memoria con nivel 0a–4."""
    entry_id:     str
    level:        MemoryLevel
    content:      str
    source_id:    str | None
    source_type:  Literal["primary", "secondary", "tertiary"] | None
    created_at:   datetime
    expires_at:   datetime | None  # None = indefinido (nivel 4)
    approved_by:  str              # "auto" | "Lila" | "human"
    field:        Literal["codigo", "math", "trading", "architect", "memory_librarian"]
    tags:         list[str] = dc_field(default_factory=list)
    stale:        bool = False     # True si variable dinámica sin actualizar (Sección J)

    @classmethod
    def new(
        cls,
        content: str,
        level: MemoryLevel,
        field: Literal["codigo", "math", "trading", "architect", "memory_librarian"],
        **kwargs: Any,
    ) -> "MemoryEntry":
        return cls(
            entry_id=str(uuid.uuid4()),
            level=level,
            content=content,
            created_at=datetime.now(timezone.utc),
            approved_by="auto",
            field=field,
            **kwargs,
        )
