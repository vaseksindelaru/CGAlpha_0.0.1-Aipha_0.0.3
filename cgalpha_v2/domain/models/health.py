"""
cgalpha.domain.models.health — System Operations health and resource models.

This module defines the value objects for observability and resource management
in the System Operations bounded context.

Design notes:
- HealthEvent is an immutable record of a system event.
- HealthLevel is an enum mapping to the legacy HealthMonitor's levels.
- ResourceSnapshot captures CPU/RAM at a point in time.
- ResourceState is the traffic-light semaphore from CGAOps.

Ubiquitous Language:
    HealthEvent      → A significant system event (failure, recovery, degradation).
    HealthLevel      → Severity level: OK, WARNING, DEGRADED, CRITICAL.
    ResourceSnapshot → Point-in-time CPU/RAM measurement.
    ResourceState    → Green/Yellow/Red resource semaphore.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class HealthLevel(Enum):
    """Severity level for health events."""

    OK = "ok"
    WARNING = "warning"
    DEGRADED = "degraded"
    CRITICAL = "critical"


class HealthEventType(Enum):
    """Classification of health events."""

    CYCLE_COMPLETED = "cycle_completed"
    CYCLE_FAILED = "cycle_failed"
    RESOURCE_WARNING = "resource_warning"
    RESOURCE_CRITICAL = "resource_critical"
    MODEL_LOADED = "model_loaded"
    MODEL_FAILED = "model_failed"
    CONFIG_CHANGED = "config_changed"
    CONFIG_ROLLED_BACK = "config_rolled_back"
    PROPOSAL_APPLIED = "proposal_applied"
    PROPOSAL_QUARANTINED = "proposal_quarantined"
    LLM_AVAILABLE = "llm_available"
    LLM_UNAVAILABLE = "llm_unavailable"
    REDIS_CONNECTED = "redis_connected"
    REDIS_DISCONNECTED = "redis_disconnected"
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"


class ResourceState(Enum):
    """
    Traffic-light semaphore for system resource availability.

    GREEN:  All resources within normal range — full operation.
    YELLOW: Resources under pressure — defer non-essential work.
    RED:    Resources critical — only essential operations allowed.
    """

    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


@dataclass(frozen=True, slots=True)
class ResourceSnapshot:
    """
    Point-in-time measurement of system resources.

    Used by the resource supervisor (CGAOps) to decide whether to
    schedule evolutionary work or defer it.

    Attributes:
        cpu_percent:    CPU usage as percentage [0.0, 100.0].
        memory_percent: RAM usage as percentage [0.0, 100.0].
        state:          Computed resource state.
        timestamp:      When the measurement was taken.
    """

    cpu_percent: float
    memory_percent: float
    state: ResourceState
    timestamp: datetime

    def __post_init__(self) -> None:
        if not (0.0 <= self.cpu_percent <= 100.0):
            raise ValueError(
                f"ResourceSnapshot cpu_percent must be in [0, 100], "
                f"got {self.cpu_percent}"
            )
        if not (0.0 <= self.memory_percent <= 100.0):
            raise ValueError(
                f"ResourceSnapshot memory_percent must be in [0, 100], "
                f"got {self.memory_percent}"
            )


@dataclass(frozen=True, slots=True)
class HealthEvent:
    """
    An immutable record of a significant system event.

    HealthEvents are emitted by components and consumed by the
    HealthMonitor for alerting, logging, and trend analysis.

    Attributes:
        event_type:   Classification of the event.
        level:        Severity level.
        source:       Component that emitted the event.
        message:      Human-readable description.
        details:      Optional structured metadata.
        timestamp:    When the event occurred.
    """

    event_type: HealthEventType
    level: HealthLevel
    source: str
    message: str
    details: Optional[dict[str, Any]] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.source:
            raise ValueError("HealthEvent source cannot be empty")
        if not self.message:
            raise ValueError("HealthEvent message cannot be empty")
