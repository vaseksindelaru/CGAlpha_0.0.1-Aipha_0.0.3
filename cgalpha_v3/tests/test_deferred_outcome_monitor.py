"""
Tests para DeferredOutcomeMonitor — P4 Puerta de Cobertura Base
===============================================================
Componente prerrequisito de Oracle Fase B. _evaluate es la lógica de
etiquetado (la variable target del Oracle), tick actualiza MFE/MAE y
dispara la resolución, _flush_resolved persiste el dataset de entrenamiento.

Umbrales CRB P4 (diferenciados):
  _evaluate      >= 90%  (etiquetado — corazón del componente)
  tick           >= 80%
  _flush_resolved >= 80%
  total          >= 70%

CRB: cgalpha_v4/CRB_DeferredOutcomeMonitor_P4.md §6 Fase A puntos 2-4.
"""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from cgalpha_v3.domain.deferred_outcome_monitor import (
    DeferredOutcomeMonitor,
    PendingLabel,
    adaptive_lookahead,
)

# ─── Helpers ────────────────────────────────────────────────────────────────


def _make_pending_label(
    sample_id="test_001",
    zone_direction="bullish",
    zone_top=101.0,
    zone_bottom=99.0,
    entry_price=100.0,
    atr_at_detection=1.0,
    zone_width_atr=1.0,
    lookahead_bars=5,
    bars_elapsed=0,
    mfe=0.0,
    mae=0.0,
    snapshot_path="",
    **kwargs,
) -> PendingLabel:
    """Crea un PendingLabel con defaults razonables para tests."""
    return PendingLabel(
        sample_id=sample_id,
        capture_ts=1000000.0,
        zone_top=zone_top,
        zone_bottom=zone_bottom,
        zone_direction=zone_direction,
        zone_width_atr=zone_width_atr,
        atr_at_detection=atr_at_detection,
        lookahead_bars=lookahead_bars,
        entry_price=entry_price,
        snapshot_path=snapshot_path,
        bars_elapsed=bars_elapsed,
        mfe=mfe,
        mae=mae,
        **kwargs,
    )


def _make_snapshot(
    sample_id="test_001",
    ts_ms=1000000,
    price=100.0,
    direction="bullish",
    zone_top=101.0,
    zone_bottom=99.0,
    zone_width_atr=1.0,
    atr=1.0,
) -> dict:
    """Crea un snapshot mínimo compatible con register_retest."""
    return {
        "_meta": {
            "sample_id": sample_id,
            "capture_ts_unix_ms": ts_ms,
            "schema_version": "2.0.0",
        },
        "zone_geometry": {
            "zone_top": zone_top,
            "zone_bottom": zone_bottom,
            "direction": direction,
            "zone_width_atr": zone_width_atr,
        },
        "clearance": {
            "atr_at_detection": atr,
        },
        "l2_snapshot_at_touch": {
            "retest_price": price,
        },
    }


@pytest.fixture
def isolated_monitor(tmp_path):
    """Crea un DeferredOutcomeMonitor con rutas aisladas en tmp_path."""
    pending_path = str(tmp_path / "pending.json")
    completed_path = str(tmp_path / "completed.jsonl")
    snapshots_dir = tmp_path / "snapshots"
    snapshots_dir.mkdir()

    with patch(
        "cgalpha_v3.domain.deferred_outcome_monitor.PENDING_LABELS_PATH",
        pending_path,
    ), patch(
        "cgalpha_v3.domain.deferred_outcome_monitor.COMPLETED_SAMPLES_PATH",
        completed_path,
    ), patch(
        "cgalpha_v3.domain.deferred_outcome_monitor._PROJECT_ROOT",
        tmp_path,
    ):
        monitor = DeferredOutcomeMonitor()
        yield monitor, pending_path, completed_path, snapshots_dir


# ─── Tests de adaptive_lookahead ───────────────────────────────────────────


class TestAdaptiveLookahead:
    """Tests de la función adaptive_lookahead (PROTECTED_FUNCTIONS)."""

    def test_narrow_zone_min_5_bars(self):
        """Zona estrecha (0.3 ATR) → 6 bars (5 + 0.3*3 = 5.9 → int = 5, max(5,...) = 5)."""
        assert adaptive_lookahead(0.3) == 5

    def test_medium_zone(self):
        """Zona media (1.0 ATR) → 8 bars (5 + 1*3 = 8)."""
        assert adaptive_lookahead(1.0) == 8

    def test_wide_zone(self):
        """Zona amplia (2.0 ATR) → 11 bars (5 + 2*3 = 11)."""
        assert adaptive_lookahead(2.0) == 11

    def test_very_wide_zone_capped_at_20(self):
        """Zona muy amplia (10 ATR) → 20 bars (capped by min(20,...))."""
        assert adaptive_lookahead(10.0) == 20

    def test_zero_zone_width(self):
        """Zona de ancho 0 → 5 bars (max(5, min(20, 5)) = 5)."""
        assert adaptive_lookahead(0.0) == 5

    def test_negative_zone_width(self):
        """Ancho negativo (edge case) → 5 bars (max(5, ...) = 5)."""
        assert adaptive_lookahead(-1.0) == 5


# ─── Tests de _evaluate (bullish) ──────────────────────────────────────────


class TestEvaluateBullish:
    """Tests de _evaluate para zonas bullish.

    Lógica (L346-359):
      - BREAKOUT: price < zone_bottom
      - BOUNCE_STRONG: price > zone_top + 0.5*atr
      - BOUNCE_WEAK: lookahead expirado + mfe > 0.3*atr
      - INCONCLUSIVE: lookahead expirado + mfe <= 0.3*atr
      - None: no resuelto
    """

    def test_bullish_breakout_price_below_zone_bottom(self):
        """Precio perfora el fondo de la zona → BREAKOUT."""
        label = _make_pending_label(
            zone_direction="bullish",
            zone_top=101.0,
            zone_bottom=99.0,
            entry_price=100.0,
            atr_at_detection=1.0,
        )
        monitor = DeferredOutcomeMonitor.__new__(DeferredOutcomeMonitor)
        assert monitor._evaluate(label, price=98.5) == "BREAKOUT"

    def test_bullish_bounce_strong_price_above_zone_top_plus_half_atr(self):
        """Precio escapa decisivamente hacia arriba → BOUNCE_STRONG."""
        label = _make_pending_label(
            zone_direction="bullish",
            zone_top=101.0,
            zone_bottom=99.0,
            entry_price=100.0,
            atr_at_detection=1.0,
        )
        monitor = DeferredOutcomeMonitor.__new__(DeferredOutcomeMonitor)
        # zone_top + 0.5*atr = 101 + 0.5 = 101.5
        assert monitor._evaluate(label, price=102.0) == "BOUNCE_STRONG"

    def test_bullish_bounce_strong_exactly_at_threshold(self):
        """Precio exactamente en zone_top + 0.5*atr no es BOUNCE_STRONG (usa >)."""
        label = _make_pending_label(
            zone_direction="bullish",
            zone_top=101.0,
            zone_bottom=99.0,
            entry_price=100.0,
            atr_at_detection=1.0,
        )
        monitor = DeferredOutcomeMonitor.__new__(DeferredOutcomeMonitor)
        # price == zone_top + 0.5*atr → no es > → None (si no ha expirado)
        assert monitor._evaluate(label, price=101.5) is None

    def test_bullish_bounce_weak_lookahead_expired_mfe_above_threshold(self):
        """Lookahead expirado + MFE > 0.3*atr → BOUNCE_WEAK."""
        label = _make_pending_label(
            zone_direction="bullish",
            zone_top=101.0,
            zone_bottom=99.0,
            entry_price=100.0,
            atr_at_detection=1.0,
            lookahead_bars=5,
            bars_elapsed=5,
            mfe=0.5,  # > 0.3*atr = 0.3
        )
        monitor = DeferredOutcomeMonitor.__new__(DeferredOutcomeMonitor)
        # Precio dentro de la zona, no breakout ni bounce_strong
        assert monitor._evaluate(label, price=100.5) == "BOUNCE_WEAK"

    def test_bullish_inconclusive_lookahead_expired_mfe_below_threshold(self):
        """Lookahead expirado + MFE <= 0.3*atr → INCONCLUSIVE."""
        label = _make_pending_label(
            zone_direction="bullish",
            zone_top=101.0,
            zone_bottom=99.0,
            entry_price=100.0,
            atr_at_detection=1.0,
            lookahead_bars=5,
            bars_elapsed=5,
            mfe=0.2,  # < 0.3*atr = 0.3
        )
        monitor = DeferredOutcomeMonitor.__new__(DeferredOutcomeMonitor)
        assert monitor._evaluate(label, price=100.1) == "INCONCLUSIVE"

    def test_bullish_inconclusive_mfe_exactly_at_threshold(self):
        """MFE == 0.3*atr → INCONCLUSIVE (usa >, no >=)."""
        label = _make_pending_label(
            zone_direction="bullish",
            zone_top=101.0,
            zone_bottom=99.0,
            entry_price=100.0,
            atr_at_detection=1.0,
            lookahead_bars=5,
            bars_elapsed=5,
            mfe=0.3,  # == 0.3*atr
        )
        monitor = DeferredOutcomeMonitor.__new__(DeferredOutcomeMonitor)
        assert monitor._evaluate(label, price=100.0) == "INCONCLUSIVE"

    def test_bullish_returns_none_when_not_resolved(self):
        """Precio dentro de la zona, lookahead no expirado → None."""
        label = _make_pending_label(
            zone_direction="bullish",
            zone_top=101.0,
            zone_bottom=99.0,
            entry_price=100.0,
            atr_at_detection=1.0,
            lookahead_bars=5,
            bars_elapsed=2,
        )
        monitor = DeferredOutcomeMonitor.__new__(DeferredOutcomeMonitor)
        assert monitor._evaluate(label, price=100.5) is None


# ─── Tests de _evaluate (bearish) ──────────────────────────────────────────


class TestEvaluateBearish:
    """Tests de _evaluate para zonas bearish.

    Lógica (L361-374):
      - BREAKOUT: price > zone_top
      - BOUNCE_STRONG: price < zone_bottom - 0.5*atr
      - BOUNCE_WEAK: lookahead expirado + mfe > 0.3*atr
      - INCONCLUSIVE: lookahead expirado + mfe <= 0.3*atr
    """

    def test_bearish_breakout_price_above_zone_top(self):
        """Precio rompe hacia arriba → BREAKOUT."""
        label = _make_pending_label(
            zone_direction="bearish",
            zone_top=101.0,
            zone_bottom=99.0,
            entry_price=100.0,
            atr_at_detection=1.0,
        )
        monitor = DeferredOutcomeMonitor.__new__(DeferredOutcomeMonitor)
        assert monitor._evaluate(label, price=101.5) == "BREAKOUT"

    def test_bearish_bounce_strong_price_below_zone_bottom_minus_half_atr(self):
        """Precio escapa decisivamente hacia abajo → BOUNCE_STRONG."""
        label = _make_pending_label(
            zone_direction="bearish",
            zone_top=101.0,
            zone_bottom=99.0,
            entry_price=100.0,
            atr_at_detection=1.0,
        )
        monitor = DeferredOutcomeMonitor.__new__(DeferredOutcomeMonitor)
        # zone_bottom - 0.5*atr = 99 - 0.5 = 98.5
        assert monitor._evaluate(label, price=98.0) == "BOUNCE_STRONG"

    def test_bearish_bounce_weak_lookahead_expired(self):
        """Lookahead expirado + MFE > 0.3*atr → BOUNCE_WEAK."""
        label = _make_pending_label(
            zone_direction="bearish",
            zone_top=101.0,
            zone_bottom=99.0,
            entry_price=100.0,
            atr_at_detection=1.0,
            lookahead_bars=5,
            bars_elapsed=5,
            mfe=0.5,
        )
        monitor = DeferredOutcomeMonitor.__new__(DeferredOutcomeMonitor)
        assert monitor._evaluate(label, price=99.5) == "BOUNCE_WEAK"

    def test_bearish_inconclusive_lookahead_expired(self):
        """Lookahead expirado + MFE <= 0.3*atr → INCONCLUSIVE."""
        label = _make_pending_label(
            zone_direction="bearish",
            zone_top=101.0,
            zone_bottom=99.0,
            entry_price=100.0,
            atr_at_detection=1.0,
            lookahead_bars=5,
            bars_elapsed=5,
            mfe=0.2,
        )
        monitor = DeferredOutcomeMonitor.__new__(DeferredOutcomeMonitor)
        assert monitor._evaluate(label, price=99.8) == "INCONCLUSIVE"

    def test_bearish_returns_none_when_not_resolved(self):
        """Precio dentro de la zona, lookahead no expirado → None."""
        label = _make_pending_label(
            zone_direction="bearish",
            zone_top=101.0,
            zone_bottom=99.0,
            entry_price=100.0,
            atr_at_detection=1.0,
            lookahead_bars=5,
            bars_elapsed=2,
        )
        monitor = DeferredOutcomeMonitor.__new__(DeferredOutcomeMonitor)
        assert monitor._evaluate(label, price=99.5) is None


# ─── Tests de _evaluate (edge cases) ───────────────────────────────────────


class TestEvaluateEdgeCases:
    """Tests de edge cases de _evaluate."""

    def test_atr_fallback_to_0_1_percent_of_price(self):
        """Si atr_at_detection <= 0, usa 0.1% del entry_price como fallback."""
        label = _make_pending_label(
            zone_direction="bullish",
            zone_top=101.0,
            zone_bottom=99.0,
            entry_price=100000.0,
            atr_at_detection=0.0,  # Trigger fallback
        )
        monitor = DeferredOutcomeMonitor.__new__(DeferredOutcomeMonitor)
        # atr = 100000 * 0.001 = 100
        # BOUNCE_STRONG: price > 101 + 0.5*100 = 151
        assert monitor._evaluate(label, price=200.0) == "BOUNCE_STRONG"

    def test_atr_negative_uses_fallback(self):
        """atr_at_detection negativo también trigger el fallback."""
        label = _make_pending_label(
            zone_direction="bullish",
            zone_top=101.0,
            zone_bottom=99.0,
            entry_price=100.0,
            atr_at_detection=-1.0,
        )
        monitor = DeferredOutcomeMonitor.__new__(DeferredOutcomeMonitor)
        # atr = 100 * 0.001 = 0.1
        # BOUNCE_STRONG: price > 101 + 0.5*0.1 = 101.05
        assert monitor._evaluate(label, price=102.0) == "BOUNCE_STRONG"

    def test_bullish_breakout_takes_precedence_over_bounce_strong(self):
        """Si price < zone_bottom, BREAKOUT tiene prioridad (se evalúa primero)."""
        label = _make_pending_label(
            zone_direction="bullish",
            zone_top=101.0,
            zone_bottom=99.0,
            entry_price=100.0,
            atr_at_detection=1.0,
        )
        monitor = DeferredOutcomeMonitor.__new__(DeferredOutcomeMonitor)
        # price=98 < zone_bottom=99 → BREAKOUT (no BOUNCE_STRONG)
        assert monitor._evaluate(label, price=98.0) == "BREAKOUT"


# ─── Tests de tick (MFE/MAE) ───────────────────────────────────────────────


class TestTickMfeMae:
    """Tests de tick() — actualización de MFE/MAE."""

    def test_tick_updates_mfe_bullish(self):
        """Bullish: favorable = price - entry. MFE se actualiza si favorable > mfe."""
        label = _make_pending_label(
            zone_direction="bullish",
            entry_price=100.0,
            zone_top=110.0,  # Lejos para no disparar BOUNCE_STRONG
            zone_bottom=90.0,  # Lejos para no disparar BREAKOUT
            atr_at_detection=1.0,
            lookahead_bars=10,
        )
        monitor = DeferredOutcomeMonitor.__new__(DeferredOutcomeMonitor)
        monitor.pending = [label]
        monitor._persist_pending = lambda: None  # No-op para test

        # Precio sube a 102 → favorable = 2.0 (no dispara resolución)
        monitor.tick(current_price=102.0, bar_closed=False)
        assert label.mfe == 2.0

    def test_tick_updates_mae_bullish(self):
        """Bullish: adverse = entry - price. MAE se actualiza si adverse > mae."""
        label = _make_pending_label(
            zone_direction="bullish",
            entry_price=100.0,
            zone_top=110.0,  # Lejos para no disparar BOUNCE_STRONG
            zone_bottom=90.0,  # Lejos para no disparar BREAKOUT
            atr_at_detection=1.0,
            lookahead_bars=10,
        )
        monitor = DeferredOutcomeMonitor.__new__(DeferredOutcomeMonitor)
        monitor.pending = [label]
        monitor._persist_pending = lambda: None

        # Precio baja a 98 → adverse = 2.0 (dentro de la zona, no dispara)
        monitor.tick(current_price=98.0, bar_closed=False)
        assert label.mae == 2.0

    def test_tick_updates_mfe_bearish(self):
        """Bearish: favorable = entry - price. MFE se actualiza si price baja."""
        label = _make_pending_label(
            zone_direction="bearish",
            entry_price=100.0,
            zone_top=110.0,  # Lejos para no disparar BREAKOUT
            zone_bottom=90.0,  # Lejos para no disparar BOUNCE_STRONG
            atr_at_detection=1.0,
            lookahead_bars=10,
        )
        monitor = DeferredOutcomeMonitor.__new__(DeferredOutcomeMonitor)
        monitor.pending = [label]
        monitor._persist_pending = lambda: None

        # Precio baja a 98 → favorable = 100 - 98 = 2.0
        monitor.tick(current_price=98.0, bar_closed=False)
        assert label.mfe == 2.0

    def test_tick_updates_mae_bearish(self):
        """Bearish: adverse = price - entry. MAE se actualiza si price sube."""
        label = _make_pending_label(
            zone_direction="bearish",
            entry_price=100.0,
            zone_top=110.0,  # Lejos para no disparar BREAKOUT
            zone_bottom=90.0,  # Lejos para no disparar BOUNCE_STRONG
            atr_at_detection=1.0,
            lookahead_bars=10,
        )
        monitor = DeferredOutcomeMonitor.__new__(DeferredOutcomeMonitor)
        monitor.pending = [label]
        monitor._persist_pending = lambda: None

        # Precio sube a 102 → adverse = 2.0 (dentro de la zona, no dispara)
        monitor.tick(current_price=102.0, bar_closed=False)
        assert label.mae == 2.0

    def test_tick_mfe_only_increases(self):
        """MFE solo aumenta, nunca disminuye (máximo favorable)."""
        label = _make_pending_label(
            zone_direction="bullish",
            entry_price=100.0,
            zone_top=105.0,
            zone_bottom=95.0,
            atr_at_detection=1.0,
            lookahead_bars=10,
        )
        monitor = DeferredOutcomeMonitor.__new__(DeferredOutcomeMonitor)
        monitor.pending = [label]
        monitor._persist_pending = lambda: None

        monitor.tick(current_price=103.0)  # mfe = 3.0
        monitor.tick(current_price=101.0)  # favorable = 1.0 < 3.0 → no update
        assert label.mfe == 3.0

    def test_tick_mae_only_increases(self):
        """MAE solo aumenta, nunca disminuye (máximo adverse)."""
        label = _make_pending_label(
            zone_direction="bullish",
            entry_price=100.0,
            zone_top=105.0,
            zone_bottom=95.0,
            atr_at_detection=1.0,
            lookahead_bars=10,
        )
        monitor = DeferredOutcomeMonitor.__new__(DeferredOutcomeMonitor)
        monitor.pending = [label]
        monitor._persist_pending = lambda: None

        monitor.tick(current_price=97.0)  # mae = 3.0
        monitor.tick(current_price=99.0)  # adverse = 1.0 < 3.0 → no update
        assert label.mae == 3.0


# ─── Tests de tick (bars_elapsed) ──────────────────────────────────────────


class TestTickBarsElapsed:
    """Tests de tick() — incremento de bars_elapsed."""

    def test_tick_increments_bars_elapsed_on_bar_closed(self):
        """bar_closed=True incrementa bars_elapsed en 1."""
        label = _make_pending_label(
            zone_direction="bullish",
            entry_price=100.0,
            zone_top=105.0,
            zone_bottom=95.0,
            atr_at_detection=1.0,
            lookahead_bars=10,
            bars_elapsed=0,
        )
        monitor = DeferredOutcomeMonitor.__new__(DeferredOutcomeMonitor)
        monitor.pending = [label]
        monitor._persist_pending = lambda: None

        monitor.tick(current_price=100.0, bar_closed=True)
        assert label.bars_elapsed == 1

    def test_tick_does_not_increment_bars_elapsed_without_bar_closed(self):
        """bar_closed=False no incrementa bars_elapsed."""
        label = _make_pending_label(
            zone_direction="bullish",
            entry_price=100.0,
            zone_top=105.0,
            zone_bottom=95.0,
            atr_at_detection=1.0,
            lookahead_bars=10,
            bars_elapsed=0,
        )
        monitor = DeferredOutcomeMonitor.__new__(DeferredOutcomeMonitor)
        monitor.pending = [label]
        monitor._persist_pending = lambda: None

        monitor.tick(current_price=100.0, bar_closed=False)
        assert label.bars_elapsed == 0

    def test_tick_multiple_bar_closes_accumulate(self):
        """Múltiples ticks con bar_closed=True acumulan bars_elapsed."""
        label = _make_pending_label(
            zone_direction="bullish",
            entry_price=100.0,
            zone_top=105.0,
            zone_bottom=95.0,
            atr_at_detection=1.0,
            lookahead_bars=10,
            bars_elapsed=0,
        )
        monitor = DeferredOutcomeMonitor.__new__(DeferredOutcomeMonitor)
        monitor.pending = [label]
        monitor._persist_pending = lambda: None

        for _ in range(5):
            monitor.tick(current_price=100.0, bar_closed=True)
        assert label.bars_elapsed == 5


# ─── Tests de tick (resolución y flush) ────────────────────────────────────


class TestTickResolutionAndFlush:
    """Tests de tick() — resolución de labels y flush."""

    def test_tick_resolves_bounce_strong_and_flushes(self, tmp_path):
        """tick resuelve BOUNCE_STRONG y hace flush al dataset."""
        pending_path = str(tmp_path / "pending.json")
        completed_path = str(tmp_path / "completed.jsonl")
        snapshots_dir = tmp_path / "snapshots"
        snapshots_dir.mkdir()

        # Crear snapshot en disco (necesario para _flush_resolved)
        snapshot = _make_snapshot(sample_id="test_resolve_001")
        snap_path = str(snapshots_dir / "test_resolve_001.json")
        Path(snap_path).write_text(json.dumps(snapshot))

        label = _make_pending_label(
            sample_id="test_resolve_001",
            zone_direction="bullish",
            entry_price=100.0,
            zone_top=101.0,
            zone_bottom=99.0,
            atr_at_detection=1.0,
            lookahead_bars=10,
            snapshot_path=snap_path,
        )

        with patch(
            "cgalpha_v3.domain.deferred_outcome_monitor.PENDING_LABELS_PATH",
            pending_path,
        ), patch(
            "cgalpha_v3.domain.deferred_outcome_monitor.COMPLETED_SAMPLES_PATH",
            completed_path,
        ), patch(
            "cgalpha_v3.domain.deferred_outcome_monitor._PROJECT_ROOT",
            tmp_path,
        ):
            monitor = DeferredOutcomeMonitor()
            monitor.pending = [label]
            monitor._seen_ids = {label.sample_id}
            monitor._seen_fingerprints = set()

            # Precio > zone_top + 0.5*atr = 101.5 → BOUNCE_STRONG
            results = monitor.tick(current_price=102.0, bar_closed=False)

            assert len(results) == 1
            assert results[0]["outcome"] == "BOUNCE_STRONG"
            assert results[0]["sample_id"] == "test_resolve_001"
            assert label.resolved is True

            # Verificar que se escribió al dataset
            with open(completed_path) as f:
                line = f.readline()
                data = json.loads(line)
            assert data["outcome"]["label"] == "BOUNCE_STRONG"

    def test_tick_removes_resolved_from_pending(self, tmp_path):
        """Labels resueltos se remueven de la cola pending."""
        pending_path = str(tmp_path / "pending.json")
        completed_path = str(tmp_path / "completed.jsonl")
        snapshots_dir = tmp_path / "snapshots"
        snapshots_dir.mkdir()

        snapshot = _make_snapshot(sample_id="test_remove_001")
        snap_path = str(snapshots_dir / "test_remove_001.json")
        Path(snap_path).write_text(json.dumps(snapshot))

        label = _make_pending_label(
            sample_id="test_remove_001",
            zone_direction="bullish",
            entry_price=100.0,
            zone_top=101.0,
            zone_bottom=99.0,
            atr_at_detection=1.0,
            lookahead_bars=10,
            snapshot_path=snap_path,
        )

        with patch(
            "cgalpha_v3.domain.deferred_outcome_monitor.PENDING_LABELS_PATH",
            pending_path,
        ), patch(
            "cgalpha_v3.domain.deferred_outcome_monitor.COMPLETED_SAMPLES_PATH",
            completed_path,
        ), patch(
            "cgalpha_v3.domain.deferred_outcome_monitor._PROJECT_ROOT",
            tmp_path,
        ):
            monitor = DeferredOutcomeMonitor()
            monitor.pending = [label]
            monitor._seen_ids = {label.sample_id}
            monitor._seen_fingerprints = set()

            assert monitor.get_pending_count() == 1
            monitor.tick(current_price=102.0, bar_closed=False)
            assert monitor.get_pending_count() == 0

    def test_tick_returns_empty_list_when_no_resolutions(self):
        """Si no hay resoluciones, tick retorna lista vacía."""
        label = _make_pending_label(
            zone_direction="bullish",
            entry_price=100.0,
            zone_top=105.0,
            zone_bottom=95.0,
            atr_at_detection=1.0,
            lookahead_bars=10,
        )
        monitor = DeferredOutcomeMonitor.__new__(DeferredOutcomeMonitor)
        monitor.pending = [label]
        monitor._persist_pending = lambda: None

        results = monitor.tick(current_price=100.0, bar_closed=False)
        assert results == []

    def test_tick_skips_already_resolved_labels(self):
        """Labels ya resueltos se saltan en el loop de tick."""
        label = _make_pending_label(
            zone_direction="bullish",
            entry_price=100.0,
            zone_top=105.0,
            zone_bottom=95.0,
            atr_at_detection=1.0,
            lookahead_bars=10,
        )
        label.resolved = True
        label.outcome = "BOUNCE_STRONG"

        monitor = DeferredOutcomeMonitor.__new__(DeferredOutcomeMonitor)
        monitor.pending = [label]
        monitor._persist_pending = lambda: None

        results = monitor.tick(current_price=110.0, bar_closed=False)
        assert results == []


# ─── Tests de _flush_resolved ──────────────────────────────────────────────


class TestFlushResolved:
    """Tests de _flush_resolved() — persistencia del dataset de entrenamiento."""

    def test_flush_writes_outcome_with_all_fields(self, tmp_path):
        """_flush_resolved escribe outcome con label, mfe, mae, mfe_atr, mae_atr."""
        pending_path = str(tmp_path / "pending.json")
        completed_path = str(tmp_path / "completed.jsonl")
        snapshots_dir = tmp_path / "snapshots"
        snapshots_dir.mkdir()

        snapshot = _make_snapshot(sample_id="flush_001")
        snap_path = str(snapshots_dir / "flush_001.json")
        Path(snap_path).write_text(json.dumps(snapshot))

        label = _make_pending_label(
            sample_id="flush_001",
            zone_direction="bullish",
            entry_price=100.0,
            zone_top=101.0,
            zone_bottom=99.0,
            atr_at_detection=2.0,
            lookahead_bars=5,
            snapshot_path=snap_path,
            mfe=3.0,
            mae=1.0,
        )
        label.resolved = True
        label.outcome = "BOUNCE_STRONG"
        label.resolution_ts = 1234567.0
        label.bars_elapsed = 3

        with patch(
            "cgalpha_v3.domain.deferred_outcome_monitor.PENDING_LABELS_PATH",
            pending_path,
        ), patch(
            "cgalpha_v3.domain.deferred_outcome_monitor.COMPLETED_SAMPLES_PATH",
            completed_path,
        ), patch(
            "cgalpha_v3.domain.deferred_outcome_monitor._PROJECT_ROOT",
            tmp_path,
        ):
            monitor = DeferredOutcomeMonitor()
            monitor._flush_resolved([label])

            with open(completed_path) as f:
                data = json.loads(f.readline())

            assert data["outcome"]["label"] == "BOUNCE_STRONG"
            assert data["outcome"]["mfe"] == 3.0
            assert data["outcome"]["mae"] == 1.0
            assert data["outcome"]["mfe_atr"] == 1.5  # 3.0 / 2.0
            assert data["outcome"]["mae_atr"] == 0.5  # 1.0 / 2.0
            assert data["outcome"]["bars_to_resolution"] == 3
            assert data["outcome"]["lookahead_bars_used"] == 5

    def test_flush_writes_touch_context_with_all_fields(self, tmp_path):
        """_flush_resolved escribe touch_context con campos de Shadow Harvesting."""
        pending_path = str(tmp_path / "pending.json")
        completed_path = str(tmp_path / "completed.jsonl")
        snapshots_dir = tmp_path / "snapshots"
        snapshots_dir.mkdir()

        snapshot = _make_snapshot(sample_id="flush_ctx_001")
        snap_path = str(snapshots_dir / "flush_ctx_001.json")
        Path(snap_path).write_text(json.dumps(snapshot))

        label = _make_pending_label(
            sample_id="flush_ctx_001",
            zone_direction="bullish",
            entry_price=100.0,
            zone_top=101.0,
            zone_bottom=99.0,
            atr_at_detection=1.0,
            lookahead_bars=5,
            snapshot_path=snap_path,
            touch_sequence=2,
            polarity_flipped=True,
            zone_original_direction="bearish",
            prior_touch_outcomes=["BOUNCE_STRONG"],
            hours_since_flip=1.5,
        )
        label.resolved = True
        label.outcome = "BOUNCE_STRONG"

        with patch(
            "cgalpha_v3.domain.deferred_outcome_monitor.PENDING_LABELS_PATH",
            pending_path,
        ), patch(
            "cgalpha_v3.domain.deferred_outcome_monitor.COMPLETED_SAMPLES_PATH",
            completed_path,
        ), patch(
            "cgalpha_v3.domain.deferred_outcome_monitor._PROJECT_ROOT",
            tmp_path,
        ):
            monitor = DeferredOutcomeMonitor()
            monitor._flush_resolved([label])

            with open(completed_path) as f:
                data = json.loads(f.readline())

            tc = data["touch_context"]
            assert tc["touch_sequence"] == 2
            assert tc["polarity_flipped"] is True
            assert tc["zone_original_direction"] == "bearish"
            assert tc["effective_direction"] == "bullish"  # flipped from bearish
            assert tc["is_secondary_retest"] is True  # touch_sequence > 1
            assert tc["is_tertiary_retest"] is False  # touch_sequence <= 2
            assert tc["hours_since_flip"] == 1.5

    def test_flush_appends_to_completed_samples_path(self, tmp_path):
        """_flush_resolved appenda (no sobrescribe) al dataset."""
        pending_path = str(tmp_path / "pending.json")
        completed_path = str(tmp_path / "completed.jsonl")
        snapshots_dir = tmp_path / "snapshots"
        snapshots_dir.mkdir()

        # Pre-poblar el dataset con una línea
        Path(completed_path).write_text(json.dumps({"existing": True}) + "\n")

        snapshot = _make_snapshot(sample_id="flush_append_001")
        snap_path = str(snapshots_dir / "flush_append_001.json")
        Path(snap_path).write_text(json.dumps(snapshot))

        label = _make_pending_label(
            sample_id="flush_append_001",
            snapshot_path=snap_path,
        )
        label.resolved = True
        label.outcome = "BREAKOUT"

        with patch(
            "cgalpha_v3.domain.deferred_outcome_monitor.PENDING_LABELS_PATH",
            pending_path,
        ), patch(
            "cgalpha_v3.domain.deferred_outcome_monitor.COMPLETED_SAMPLES_PATH",
            completed_path,
        ), patch(
            "cgalpha_v3.domain.deferred_outcome_monitor._PROJECT_ROOT",
            tmp_path,
        ):
            monitor = DeferredOutcomeMonitor()
            monitor._flush_resolved([label])

            with open(completed_path) as f:
                lines = f.readlines()
            assert len(lines) == 2  # existing + new
            assert json.loads(lines[0])["existing"] is True
            assert json.loads(lines[1])["outcome"]["label"] == "BREAKOUT"

    def test_flush_skips_missing_snapshot_file(self, tmp_path):
        """Si el snapshot file no existe, _flush_resolved lo saltea con warning."""
        pending_path = str(tmp_path / "pending.json")
        completed_path = str(tmp_path / "completed.jsonl")

        label = _make_pending_label(
            sample_id="missing_snap",
            snapshot_path="/nonexistent/path/snap.json",
        )
        label.resolved = True
        label.outcome = "BOUNCE_STRONG"

        with patch(
            "cgalpha_v3.domain.deferred_outcome_monitor.PENDING_LABELS_PATH",
            pending_path,
        ), patch(
            "cgalpha_v3.domain.deferred_outcome_monitor.COMPLETED_SAMPLES_PATH",
            completed_path,
        ), patch(
            "cgalpha_v3.domain.deferred_outcome_monitor._PROJECT_ROOT",
            tmp_path,
        ):
            monitor = DeferredOutcomeMonitor()
            flushed_ids = monitor._flush_resolved([label])

            # No se flusheó porque el snapshot no existe
            assert len(flushed_ids) == 0
            # El archivo completed.jsonl no debe tener contenido (puede existir
            # vacío porque _flush_resolved hace mkdir del parent, pero no escribe)
            if Path(completed_path).exists():
                assert Path(completed_path).read_text() == ""

    def test_flush_returns_flushed_ids(self, tmp_path):
        """_flush_resolved retorna la lista de sample_ids flusheados."""
        pending_path = str(tmp_path / "pending.json")
        completed_path = str(tmp_path / "completed.jsonl")
        snapshots_dir = tmp_path / "snapshots"
        snapshots_dir.mkdir()

        snapshot = _make_snapshot(sample_id="flush_ids_001")
        snap_path = str(snapshots_dir / "flush_ids_001.json")
        Path(snap_path).write_text(json.dumps(snapshot))

        label = _make_pending_label(
            sample_id="flush_ids_001",
            snapshot_path=snap_path,
        )
        label.resolved = True
        label.outcome = "BOUNCE_STRONG"

        with patch(
            "cgalpha_v3.domain.deferred_outcome_monitor.PENDING_LABELS_PATH",
            pending_path,
        ), patch(
            "cgalpha_v3.domain.deferred_outcome_monitor.COMPLETED_SAMPLES_PATH",
            completed_path,
        ), patch(
            "cgalpha_v3.domain.deferred_outcome_monitor._PROJECT_ROOT",
            tmp_path,
        ):
            monitor = DeferredOutcomeMonitor()
            flushed_ids = monitor._flush_resolved([label])
            assert flushed_ids == ["flush_ids_001"]


# ─── Tests de get_pending_count / get_resolved_count ───────────────────────


class TestPendingCount:
    """Tests de get_pending_count y get_resolved_count."""

    def test_get_pending_count_returns_unresolved(self):
        monitor = DeferredOutcomeMonitor.__new__(DeferredOutcomeMonitor)
        l1 = _make_pending_label(sample_id="a")
        l2 = _make_pending_label(sample_id="b")
        l2.resolved = True
        l3 = _make_pending_label(sample_id="c")
        monitor.pending = [l1, l2, l3]
        assert monitor.get_pending_count() == 2  # l1 y l3

    def test_get_resolved_count_returns_resolved(self):
        monitor = DeferredOutcomeMonitor.__new__(DeferredOutcomeMonitor)
        l1 = _make_pending_label(sample_id="a")
        l2 = _make_pending_label(sample_id="b")
        l2.resolved = True
        monitor.pending = [l1, l2]
        assert monitor.get_resolved_count() == 1

    def test_get_pending_count_empty(self):
        monitor = DeferredOutcomeMonitor.__new__(DeferredOutcomeMonitor)
        monitor.pending = []
        assert monitor.get_pending_count() == 0
        assert monitor.get_resolved_count() == 0
