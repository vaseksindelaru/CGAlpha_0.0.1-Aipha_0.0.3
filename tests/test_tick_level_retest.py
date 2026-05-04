"""
Tests for Tick-Level Retest Detection & Deferred Outcome Labeling
=================================================================
Validates the core Semana 2/3 architecture:
  1. check_intra_candle_retest() fires on zone touch with debounce
  2. DeferredOutcomeMonitor labels correctly (BOUNCE_STRONG, BREAKOUT, etc.)
  3. Adaptive lookahead scales with zone width
"""

import pytest
import time
from cgalpha_v3.infrastructure.signal_detector.triple_coincidence import (
    TripleCoincidenceDetector, ActiveZone
)
from cgalpha_v3.domain.deferred_outcome_monitor import (
    DeferredOutcomeMonitor, adaptive_lookahead, PendingLabel
)


# ── Helpers ──────────────────────────────────────────────────────

def make_zone(direction="bullish", top=100.0, bottom=99.0, atr=1.0, idx=0):
    return ActiveZone(
        candle_index=idx,
        zone_top=top,
        zone_bottom=bottom,
        vwap_at_detection=(top + bottom) / 2,
        detection_timestamp=int(time.time() * 1000),
        direction=direction,
        key_candle={"volume_percentile": 80, "body_percentage": 25},
        accumulation_zone={"start_idx": 0, "end_idx": 5, "quality_score": 0.7},
        mini_trend={"r2": 0.6, "direction": direction},
        atr_at_detection=atr,
        max_price_since_detection=top + 2 * atr,  # Already had clearance
        min_price_since_detection=bottom - 0.1,
    )


# ══════════════════════════════════════════════════════════════════
# T2: check_intra_candle_retest
# ══════════════════════════════════════════════════════════════════

class TestIntraCandleRetest:

    def test_hit_inside_zone(self):
        """Price inside zone triggers a hit."""
        det = TripleCoincidenceDetector()
        zone = make_zone(top=100.0, bottom=99.0)
        det.active_zones = [zone]

        hits = det.check_intra_candle_retest(99.5, 1000000)
        assert len(hits) == 1
        assert hits[0]["price"] == 99.5
        assert zone.retest_detected is True

    def test_miss_outside_zone(self):
        """Price outside zone returns no hits."""
        det = TripleCoincidenceDetector()
        zone = make_zone(top=100.0, bottom=99.0)
        det.active_zones = [zone]

        hits = det.check_intra_candle_retest(101.0, 1000000)
        assert len(hits) == 0
        assert zone.retest_detected is False

    def test_debounce_blocks_within_window(self):
        """Same zone can't trigger twice within 5s debounce."""
        det = TripleCoincidenceDetector()
        zone = make_zone(top=100.0, bottom=99.0)
        zone.last_retest_ts_ms = 1000000
        det.active_zones = [zone]

        # 3s later = within debounce window
        hits = det.check_intra_candle_retest(99.5, 1003000)
        assert len(hits) == 0

    def test_debounce_allows_after_window(self):
        """Zone triggers again after debounce window expires."""
        det = TripleCoincidenceDetector()
        zone = make_zone(top=100.0, bottom=99.0)
        zone.last_retest_ts_ms = 1000000
        det.active_zones = [zone]

        # 6s later = past debounce
        hits = det.check_intra_candle_retest(99.5, 1006000)
        assert len(hits) == 1

    def test_already_retested_zone_skipped(self):
        """Zone already retested is not checked again."""
        det = TripleCoincidenceDetector()
        zone = make_zone()
        zone.retest_detected = True
        det.active_zones = [zone]

        hits = det.check_intra_candle_retest(99.5, 2000000)
        assert len(hits) == 0

    def test_clearance_calculated_bullish(self):
        """Bullish clearance = (max_price - zone_top) / ATR."""
        det = TripleCoincidenceDetector()
        zone = make_zone(direction="bullish", top=100.0, bottom=99.0, atr=1.0)
        zone.max_price_since_detection = 104.0  # 4 ATR clearance
        det.active_zones = [zone]

        hits = det.check_intra_candle_retest(99.5, 1000000)
        assert len(hits) == 1
        assert hits[0]["clearance_atr"] == 4.0

    def test_clearance_calculated_bearish(self):
        """Bearish clearance = (zone_bottom - min_price) / ATR."""
        det = TripleCoincidenceDetector()
        zone = make_zone(direction="bearish", top=100.0, bottom=99.0, atr=1.0)
        zone.min_price_since_detection = 96.0  # 3 ATR clearance
        det.active_zones = [zone]

        hits = det.check_intra_candle_retest(99.5, 1000000)
        assert len(hits) == 1
        assert hits[0]["clearance_atr"] == 3.0

    def test_multiple_zones_only_matching_fire(self):
        """With multiple zones, only the one touched fires."""
        det = TripleCoincidenceDetector()
        z1 = make_zone(top=100.0, bottom=99.0, idx=0)
        z2 = make_zone(top=200.0, bottom=199.0, idx=1)
        det.active_zones = [z1, z2]

        hits = det.check_intra_candle_retest(99.5, 1000000)
        assert len(hits) == 1
        assert hits[0]["zone"].candle_index == 0


# ══════════════════════════════════════════════════════════════════
# T1/T5: DeferredOutcomeMonitor
# ══════════════════════════════════════════════════════════════════

class TestDeferredOutcomeMonitor:

    def _make_monitor_with_label(self, direction="bullish", top=100.0, bottom=99.0, atr=1.0):
        """Creates a monitor with one pending label."""
        mon = DeferredOutcomeMonitor()
        label = PendingLabel(
            sample_id="test_sample",
            capture_ts=time.time(),
            zone_top=top,
            zone_bottom=bottom,
            zone_direction=direction,
            zone_width_atr=(top - bottom) / atr,
            atr_at_detection=atr,
            lookahead_bars=8,
            entry_price=(top + bottom) / 2,
            snapshot_path="/tmp/nonexistent.json",  # Won't flush in these tests
        )
        mon.pending = [label]
        return mon, label

    def test_bounce_strong_bullish(self):
        """Bullish: price > zone_top + 0.5*ATR → BOUNCE_STRONG."""
        mon, label = self._make_monitor_with_label(direction="bullish", top=100.0, atr=1.0)
        result = mon._evaluate(label, 100.6)  # > 100 + 0.5 = 100.5
        assert result == "BOUNCE_STRONG"

    def test_breakout_bullish(self):
        """Bullish: price < zone_bottom → BREAKOUT."""
        mon, label = self._make_monitor_with_label(direction="bullish", bottom=99.0)
        result = mon._evaluate(label, 98.9)  # < 99
        assert result == "BREAKOUT"

    def test_bounce_strong_bearish(self):
        """Bearish: price < zone_bottom - 0.5*ATR → BOUNCE_STRONG."""
        mon, label = self._make_monitor_with_label(direction="bearish", bottom=99.0, atr=1.0)
        result = mon._evaluate(label, 98.4)  # < 99 - 0.5 = 98.5
        assert result == "BOUNCE_STRONG"

    def test_breakout_bearish(self):
        """Bearish: price > zone_top → BREAKOUT."""
        mon, label = self._make_monitor_with_label(direction="bearish", top=100.0)
        result = mon._evaluate(label, 100.1)
        assert result == "BREAKOUT"

    def test_inconclusive_on_lookahead_expiry(self):
        """No movement after lookahead → INCONCLUSIVE."""
        mon, label = self._make_monitor_with_label(direction="bullish", top=100.0, bottom=99.0, atr=1.0)
        label.bars_elapsed = 8  # = lookahead_bars
        label.mfe = 0.1  # < 0.3 * ATR
        result = mon._evaluate(label, 99.5)  # Still in zone
        assert result == "INCONCLUSIVE"

    def test_bounce_weak_on_lookahead_expiry(self):
        """Moderate MFE but no escape after lookahead → BOUNCE_WEAK."""
        mon, label = self._make_monitor_with_label(direction="bullish", top=100.0, bottom=99.0, atr=1.0)
        label.bars_elapsed = 8
        label.mfe = 0.4  # > 0.3 * ATR
        result = mon._evaluate(label, 99.8)  # Still in zone
        assert result == "BOUNCE_WEAK"

    def test_pending_when_unresolved(self):
        """Price in zone, bars not expired → None (keep monitoring)."""
        mon, label = self._make_monitor_with_label(direction="bullish", top=100.0, bottom=99.0)
        label.bars_elapsed = 3
        result = mon._evaluate(label, 99.5)
        assert result is None

    def test_tick_updates_mfe_mae(self):
        """tick() updates MFE and MAE correctly."""
        mon, label = self._make_monitor_with_label(direction="bullish", top=100.0, bottom=99.0)
        label.entry_price = 99.5

        mon.tick(100.2, bar_closed=False)  # +0.7 favorable
        assert label.mfe == pytest.approx(0.7, abs=0.01)

        mon.tick(99.0, bar_closed=False)  # -0.5 adverse
        assert label.mae == pytest.approx(0.5, abs=0.01)
        assert label.mfe == pytest.approx(0.7, abs=0.01)  # MFE doesn't decrease

    def test_no_default_bounce_fallback(self):
        """The old L965 'return BOUNCE' fallback is ELIMINATED."""
        mon, label = self._make_monitor_with_label()
        # Price stays perfectly at entry, no bars pass
        for _ in range(5):
            result = mon._evaluate(label, label.entry_price)
            assert result is None  # NOT 'BOUNCE'


# ══════════════════════════════════════════════════════════════════
# Adaptive Lookahead
# ══════════════════════════════════════════════════════════════════

class TestAdaptiveLookahead:

    def test_narrow_zone(self):
        """Narrow zone (0.3 ATR) → short lookahead."""
        assert adaptive_lookahead(0.3) == 5

    def test_medium_zone(self):
        """Medium zone (1.0 ATR) → moderate lookahead."""
        assert adaptive_lookahead(1.0) == 8

    def test_wide_zone(self):
        """Wide zone (2.0 ATR) → longer lookahead."""
        assert adaptive_lookahead(2.0) == 11

    def test_extreme_zone_capped(self):
        """Extremely wide zone is capped at 20."""
        assert adaptive_lookahead(10.0) == 20

    def test_minimum_floor(self):
        """Minimum lookahead is 5 bars."""
        assert adaptive_lookahead(0.0) == 5
