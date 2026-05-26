"""
Regression test: Spatial Multi-Touch Deduplication (B-008)
=========================================================
Simula el escenario exacto donde 3 zonas solapadas disparan al mismo
milisegundo y precio. Solo el primer registro debe sobrevivir.

Valida que la protección funciona para TODAS las clases de outcome,
no solo BOUNCE_STRONG.
"""

import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch

import pytest


def _make_snapshot(zone_id: int, ts_ms: int, price: float, direction: str) -> dict:
    """Genera un snapshot mínimo con coordenadas causales idénticas pero zone_id diferente."""
    return {
        "_meta": {
            "sample_id": f"re_20260526_104148_BTCUSDT_{direction}_{zone_id}",
            "capture_ts_unix_ms": ts_ms,
            "schema_version": "2.0.0",
        },
        "zone_geometry": {
            "zone_top": price + 50,
            "zone_bottom": price - 50,
            "direction": direction,
            "zone_width_atr": 0.5,
        },
        "clearance": {
            "atr_at_detection": 200.0,
        },
        "l2_snapshot_at_touch": {
            "retest_price": price,
            "vwap_at_retest": price + 5,
            "obi_10": 0.12,
            "cumulative_delta": 340.0,
        },
    }


def test_spatial_multitouch_blocks_duplicates():
    """3 zonas distintas, mismo tick, deben producir exactamente 1 registro."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pending_path = os.path.join(tmpdir, "pending_labels.json")
        completed_path = os.path.join(tmpdir, "training_dataset_v2.jsonl")
        snapshots_dir = os.path.join(tmpdir, "snapshots")

        # Crear archivos vacíos
        Path(pending_path).write_text("[]")
        Path(completed_path).touch()
        Path(snapshots_dir).mkdir()

        with patch("cgalpha_v3.domain.deferred_outcome_monitor.PENDING_LABELS_PATH", pending_path), \
             patch("cgalpha_v3.domain.deferred_outcome_monitor.COMPLETED_SAMPLES_PATH", completed_path), \
             patch("cgalpha_v3.domain.deferred_outcome_monitor._PROJECT_ROOT", Path(tmpdir)):

            from cgalpha_v3.domain.deferred_outcome_monitor import DeferredOutcomeMonitor

            monitor = DeferredOutcomeMonitor()

            # Mismo timestamp (ms), mismo precio, misma dirección — 3 zone_ids diferentes
            ts = 1716721308000
            price = 77543.85

            snap_a = _make_snapshot(zone_id=471, ts_ms=ts, price=price, direction="bearish")
            snap_b = _make_snapshot(zone_id=469, ts_ms=ts, price=price, direction="bearish")
            snap_c = _make_snapshot(zone_id=161, ts_ms=ts, price=price, direction="bearish")

            id_a = monitor.register_retest(snap_a)
            id_b = monitor.register_retest(snap_b)
            id_c = monitor.register_retest(snap_c)

            # Solo el primero debe haber entrado a la cola
            assert monitor.get_pending_count() == 1, (
                f"Esperado 1 pending, pero hay {monitor.get_pending_count()}"
            )
            assert monitor.pending[0].sample_id == id_a


def test_different_events_are_not_blocked():
    """Eventos con diferente timestamp o precio NO deben ser bloqueados."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pending_path = os.path.join(tmpdir, "pending_labels.json")
        completed_path = os.path.join(tmpdir, "training_dataset_v2.jsonl")
        snapshots_dir = os.path.join(tmpdir, "snapshots")

        Path(pending_path).write_text("[]")
        Path(completed_path).touch()
        Path(snapshots_dir).mkdir()

        with patch("cgalpha_v3.domain.deferred_outcome_monitor.PENDING_LABELS_PATH", pending_path), \
             patch("cgalpha_v3.domain.deferred_outcome_monitor.COMPLETED_SAMPLES_PATH", completed_path), \
             patch("cgalpha_v3.domain.deferred_outcome_monitor._PROJECT_ROOT", Path(tmpdir)):

            from cgalpha_v3.domain.deferred_outcome_monitor import DeferredOutcomeMonitor

            monitor = DeferredOutcomeMonitor()

            # Evento 1: bearish a las 12:41
            snap_1 = _make_snapshot(zone_id=471, ts_ms=1716721308000, price=77543.85, direction="bearish")
            # Evento 2: mismo precio, 5 minutos después (timestamp diferente)
            snap_2 = _make_snapshot(zone_id=472, ts_ms=1716721608000, price=77543.85, direction="bearish")
            # Evento 3: mismo timestamp, precio diferente
            snap_3 = _make_snapshot(zone_id=473, ts_ms=1716721308000, price=78000.00, direction="bearish")
            # Evento 4: mismo timestamp y precio, dirección opuesta
            snap_4 = _make_snapshot(zone_id=474, ts_ms=1716721308000, price=77543.85, direction="bullish")

            monitor.register_retest(snap_1)
            monitor.register_retest(snap_2)
            monitor.register_retest(snap_3)
            monitor.register_retest(snap_4)

            assert monitor.get_pending_count() == 4, (
                f"Esperado 4 pending (todos son eventos causalmente distintos), "
                f"pero hay {monitor.get_pending_count()}"
            )


def test_fingerprint_survives_restart():
    """Tras flush + reinicio, la huella causal debe recargar y seguir bloqueando."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pending_path = os.path.join(tmpdir, "pending_labels.json")
        completed_path = os.path.join(tmpdir, "training_dataset_v2.jsonl")
        snapshots_dir = os.path.join(tmpdir, "snapshots")

        Path(pending_path).write_text("[]")
        Path(snapshots_dir).mkdir()

        # Pre-poblar el dataset con un sample que tenga cierta huella
        sample = _make_snapshot(zone_id=471, ts_ms=1716721308000, price=77543.85, direction="bearish")
        sample["outcome"] = {"label": "BOUNCE_STRONG", "mfe": 300, "mae": 50}
        Path(completed_path).write_text(json.dumps(sample) + "\n")

        with patch("cgalpha_v3.domain.deferred_outcome_monitor.PENDING_LABELS_PATH", pending_path), \
             patch("cgalpha_v3.domain.deferred_outcome_monitor.COMPLETED_SAMPLES_PATH", completed_path), \
             patch("cgalpha_v3.domain.deferred_outcome_monitor._PROJECT_ROOT", Path(tmpdir)):

            from cgalpha_v3.domain.deferred_outcome_monitor import DeferredOutcomeMonitor

            # Simular reinicio: crear instancia nueva que recarga desde disco
            monitor = DeferredOutcomeMonitor()

            # Intentar registrar un snapshot con la MISMA huella causal
            snap_dup = _make_snapshot(zone_id=999, ts_ms=1716721308000, price=77543.85, direction="bearish")
            monitor.register_retest(snap_dup)

            # Debe ser bloqueado por la huella recargada
            assert monitor.get_pending_count() == 0, (
                f"Esperado 0 pending (huella ya existía en disco), "
                f"pero hay {monitor.get_pending_count()}"
            )
