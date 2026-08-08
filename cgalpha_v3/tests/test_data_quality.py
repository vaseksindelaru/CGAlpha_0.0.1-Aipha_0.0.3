"""
Tests — Data Quality Gates (cgalpha_v3)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from datetime import datetime, timezone, timedelta

from cgalpha_v3.data_quality.gates import (
    DataQualityGate, TemporalLeakageError, check_oos_leakage,
)


def make_klines(n: int = 5, interval_ms: int = 300_000) -> list[dict]:
    """Genera klines válidos para tests."""
    base = 1_700_000_000_000
    return [
        {
            "open_time":  base + i * interval_ms,
            "close_time": base + i * interval_ms + interval_ms - 1,
            "open":       60000.0 + i,
            "high":       60010.0 + i,
            "low":        59990.0 + i,
            "close":      60005.0 + i,
            "volume":     100.0 + i,
        }
        for i in range(n)
    ]


@pytest.fixture
def gate() -> DataQualityGate:
    return DataQualityGate(stale_threshold_s=60.0)


class TestDataQualityGate:
    def test_valid_klines_pass(self, gate: DataQualityGate):
        klines = make_klines(10)
        ts_fresh = datetime.now(timezone.utc) - timedelta(seconds=10)
        report = gate.run(klines, "BTCUSDT", "5m", last_update_ts=ts_fresh)
        assert report.status == "valid"
        assert report.passed
        assert len(report.errors) == 0

    def test_empty_klines_fail(self, gate: DataQualityGate):
        report = gate.run([], "BTCUSDT", "5m")
        assert report.status == "corrupted"
        assert not report.passed
        assert any("vacío" in e.message for e in report.errors)

    def test_stale_data_degrades(self, gate: DataQualityGate):
        klines = make_klines(5)
        ts_old = datetime.now(timezone.utc) - timedelta(seconds=120)
        report = gate.run(klines, "BTCUSDT", "5m", last_update_ts=ts_old)
        assert report.status in ("stale", "valid")  # only warning expected
        stale_results = [r for r in report.results if "stale" in r.message or "Fresco" not in r.message]
        freshness = next((r for r in report.results if "freshness" in r.gate), None)
        assert freshness is not None
        assert not freshness.passed

    def test_inverted_timestamps_fail(self, gate: DataQualityGate):
        klines = make_klines(4)
        klines[2]["open_time"] = klines[1]["open_time"]  # duplicado → inversión
        report = gate.run(klines, "BTCUSDT", "5m")
        assert report.status == "corrupted"
        order_result = next(r for r in report.results if "order" in r.gate)
        assert not order_result.passed

    def test_missing_fields_fail(self, gate: DataQualityGate):
        klines = [{"open_time": 1_700_000_000_000}]  # faltan campos
        report = gate.run(klines, "BTCUSDT", "5m")
        assert report.status == "corrupted"
        schema_result = next(r for r in report.results if "schema" in r.gate)
        assert not schema_result.passed


class TestTemporalLeakage:
    def test_no_leakage_passes(self):
        check_oos_leakage(
            train_end_ts=1000.0,
            oos_start_ts=1200.0,
            feature_timestamps=[900.0, 950.0, 1100.0],
        )  # No debe lanzar

    def test_leakage_raises(self):
        with pytest.raises(TemporalLeakageError, match="TemporalLeakageError"):
            check_oos_leakage(
                train_end_ts=1000.0,
                oos_start_ts=1200.0,
                feature_timestamps=[900.0, 1300.0, 1400.0],  # 1300 y 1400 están en zona OOS
            )
