"""Unit tests for cgalpha_v2.domain.models.health."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cgalpha_v2.domain.models import (
    HealthEvent,
    HealthEventType,
    HealthLevel,
    ResourceSnapshot,
    ResourceState,
)


def test_resource_snapshot_validation_raises_on_out_of_range() -> None:
    with pytest.raises(ValueError, match="cpu_percent"):
        ResourceSnapshot(
            cpu_percent=-1.0,
            memory_percent=50.0,
            state=ResourceState.GREEN,
            timestamp=datetime.now(timezone.utc),
        )

    with pytest.raises(ValueError, match="memory_percent"):
        ResourceSnapshot(
            cpu_percent=50.0,
            memory_percent=101.0,
            state=ResourceState.GREEN,
            timestamp=datetime.now(timezone.utc),
        )


def test_health_event_validation_raises_on_empty_fields() -> None:
    with pytest.raises(ValueError, match="source"):
        HealthEvent(
            event_type=HealthEventType.SYSTEM_STARTUP,
            level=HealthLevel.OK,
            source="",
            message="ok",
        )

    with pytest.raises(ValueError, match="message"):
        HealthEvent(
            event_type=HealthEventType.SYSTEM_STARTUP,
            level=HealthLevel.OK,
            source="system",
            message="",
        )
