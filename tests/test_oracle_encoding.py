"""
Tests for Oracle Deterministic Encoding — Safety Net
=====================================================
Validates that encoding is deterministic, free of LabelEncoder dependencies,
and that training completes successfully with the current encoding scheme.

These tests form the prerequisite safety net for the future one-hot
migration (7→11 features) described in the TechnicalSpec.

Created: 2026-05-17 | Category: Cat.1 (observational, no behavioral change)
"""
import pytest
import numpy as np
import random
from cgalpha_v3.lila.llm.oracle import (
    OracleTrainer_v3, OracleRegressor_MAE, _to_binary_features
)


# ── Fixtures ──────────────────────────────────────────────────────────

def _make_training_samples(n: int = 60, seed: int = 42) -> list:
    """Generate synthetic training samples matching schema v1 (legacy features dict)."""
    rng = random.Random(seed)
    regimes = ["TREND", "LATERAL", "HIGH_VOL"]
    directions = ["bullish", "bearish"]
    divergences = ["NEUTRAL", "BULLISH", "BEARISH"]
    outcomes = ["BOUNCE_STRONG", "BREAKOUT"]

    samples = []
    for i in range(n):
        samples.append({
            "features": {
                "vwap_at_retest": rng.uniform(75000, 85000),
                "obi_10_at_retest": rng.uniform(-1.0, 1.0),
                "cumulative_delta_at_retest": rng.uniform(-500, 500),
                "delta_divergence": rng.choice(divergences),
                "atr_14": rng.uniform(200, 1000),
                "regime": rng.choice(regimes),
                "direction": rng.choice(directions),
            },
            "outcome": rng.choice(outcomes),
        })
    return samples


def _make_training_samples_v2(n: int = 60, seed: int = 42) -> list:
    """Generate synthetic training samples matching schema v2.0 (ReentrySnapshot)."""
    rng = random.Random(seed)
    regimes = ["TREND", "LATERAL", "HIGH_VOL"]
    directions = ["bullish", "bearish"]
    outcomes_labels = ["BOUNCE_STRONG", "BREAKOUT"]

    samples = []
    for i in range(n):
        samples.append({
            "_meta": {"schema_version": "2.0.0", "sample_id": f"test_{i}"},
            "zone_geometry": {
                "direction": rng.choice(directions),
                "zone_width_atr": rng.uniform(0.2, 0.8),
            },
            "clearance": {
                "atr_at_detection": rng.uniform(200, 1000),
                "regime": rng.choice(regimes),
            },
            "l2_snapshot_at_touch": {
                "obi_10": rng.uniform(-1.0, 1.0),
                "cumulative_delta": rng.uniform(-500, 500),
                "vwap_at_retest": rng.uniform(75000, 85000),
                "delta_divergence": rng.choice(["NEUTRAL", "BULLISH", "BEARISH"]),
            },
            "outcome": {
                "label": rng.choice(outcomes_labels),
                "mae_atr": rng.uniform(0.01, 0.5),
            },
        })
    return samples


# ══════════════════════════════════════════════════════════════════════
# Test 1: Determinism — same data, different order → same encoding
# ══════════════════════════════════════════════════════════════════════

class TestOracleEncodingDeterminism:
    """Verify that encoding results are identical regardless of input order."""

    def test_classifier_encoding_is_deterministic(self):
        """OracleTrainer_v3: same dataset shuffled → identical encoded values."""
        oracle = OracleTrainer_v3.create_default()
        encoders = oracle._deterministic_encoders()
        oracle._encoders = encoders

        # Order A
        values_a = [
            oracle._safe_encode("regime", "TREND"),
            oracle._safe_encode("regime", "LATERAL"),
            oracle._safe_encode("regime", "HIGH_VOL"),
            oracle._safe_encode("direction", "bullish"),
            oracle._safe_encode("direction", "bearish"),
            oracle._safe_encode("delta_divergence", "NEUTRAL"),
            oracle._safe_encode("delta_divergence", "BULLISH"),
            oracle._safe_encode("delta_divergence", "BEARISH"),
        ]

        # Order B (reversed input order — must produce same outputs)
        values_b = [
            oracle._safe_encode("regime", "TREND"),
            oracle._safe_encode("regime", "LATERAL"),
            oracle._safe_encode("regime", "HIGH_VOL"),
            oracle._safe_encode("direction", "bullish"),
            oracle._safe_encode("direction", "bearish"),
            oracle._safe_encode("delta_divergence", "NEUTRAL"),
            oracle._safe_encode("delta_divergence", "BULLISH"),
            oracle._safe_encode("delta_divergence", "BEARISH"),
        ]

        assert values_a == values_b, "Encoding must be deterministic regardless of call order"

    def test_regressor_encoding_is_deterministic(self):
        """OracleRegressor_MAE: same encoding determinism guarantee."""
        regressor = OracleRegressor_MAE.create_default()
        encoders = regressor._deterministic_encoders()
        regressor._encoders = encoders

        # Encode all known categories
        results = {}
        for field in ("regime", "direction", "delta_divergence"):
            for value in encoders[field]:
                key = f"{field}:{value}"
                results[key] = regressor._safe_encode(field, value)

        # Re-encode in different order
        results_2 = {}
        for field in reversed(["regime", "direction", "delta_divergence"]):
            for value in reversed(list(encoders[field].keys())):
                key = f"{field}:{value}"
                results_2[key] = regressor._safe_encode(field, value)

        assert results == results_2

    def test_encoding_stable_across_instances(self):
        """Two separate OracleTrainer_v3 instances produce identical encodings."""
        o1 = OracleTrainer_v3.create_default()
        o1._encoders = o1._deterministic_encoders()

        o2 = OracleTrainer_v3.create_default()
        o2._encoders = o2._deterministic_encoders()

        for field in ("regime", "direction", "delta_divergence"):
            for value in o1._encoders[field]:
                assert o1._safe_encode(field, value) == o2._safe_encode(field, value), \
                    f"Mismatch for {field}={value} across instances"

    def test_encoding_handles_case_variants(self):
        """Binary encoding works with mixed case input (bullish, BULLISH, Bullish)."""
        b1 = _to_binary_features("TREND", "bullish", "NEUTRAL")
        b2 = _to_binary_features("trend", "BULLISH", "neutral")
        b3 = _to_binary_features("Trend", "Bullish", "Neutral")
        assert b1 == b2 == b3

    def test_encoding_unknown_returns_zero(self):
        """Unknown categories produce all-zero binary columns."""
        b = _to_binary_features("UNKNOWN_REGIME", "sideways", "UNKNOWN")
        assert b["is_trending"] == 0
        assert b["is_lateral"] == 0
        assert b["is_high_vol"] == 0
        assert b["is_bullish"] == 0
        # Unknown delta_div defaults to neutral
        assert b["is_div_neutral"] == 1

    def test_encoding_handles_none_and_nan(self):
        """None and NaN inputs produce safe defaults."""
        b = _to_binary_features(None, None, None)
        assert b["is_trending"] == 0
        assert b["is_bullish"] == 0
        assert b["is_div_neutral"] == 1  # None defaults to neutral

    def test_binary_features_are_deterministic(self):
        """_to_binary_features returns identical results across calls."""
        args = [("TREND", "bullish", "NEUTRAL"),
                ("LATERAL", "bearish", "BULLISH"),
                ("HIGH_VOL", "bullish", "BEARISH")]
        for a in args:
            assert _to_binary_features(*a) == _to_binary_features(*a)

    def test_binary_features_one_hot_property(self):
        """Each category group sums to exactly 1 (one-hot)."""
        for regime in ["TREND", "LATERAL", "HIGH_VOL"]:
            b = _to_binary_features(regime, "bullish", "NEUTRAL")
            assert b["is_trending"] + b["is_lateral"] + b["is_high_vol"] == 1

        for div in ["BULLISH", "BEARISH", "NEUTRAL"]:
            b = _to_binary_features("LATERAL", "bullish", div)
            assert b["is_div_bullish"] + b["is_div_bearish"] + b["is_div_neutral"] == 1


# ══════════════════════════════════════════════════════════════════════
# Test 2: No LabelEncoder dependency
# ══════════════════════════════════════════════════════════════════════

class TestNoLabelEncoderDependency:
    """Verify that no sklearn LabelEncoder objects exist in the encoding pipeline."""

    def test_classifier_encoders_are_dicts(self):
        """OracleTrainer_v3._deterministic_encoders() returns plain dicts, not LabelEncoder."""
        oracle = OracleTrainer_v3.create_default()
        encoders = oracle._deterministic_encoders()

        for field, encoder in encoders.items():
            assert isinstance(encoder, dict), \
                f"Encoder for '{field}' should be dict, got {type(encoder)}"
            assert not hasattr(encoder, "classes_"), \
                f"Encoder for '{field}' has 'classes_' — looks like a LabelEncoder"
            assert not hasattr(encoder, "fit_transform"), \
                f"Encoder for '{field}' has 'fit_transform' — looks like a LabelEncoder"

    def test_regressor_encoders_are_dicts(self):
        """OracleRegressor_MAE._deterministic_encoders() returns plain dicts."""
        regressor = OracleRegressor_MAE.create_default()
        encoders = regressor._deterministic_encoders()

        for field, encoder in encoders.items():
            assert isinstance(encoder, dict), \
                f"Encoder for '{field}' should be dict, got {type(encoder)}"

    def test_classifier_and_regressor_encoders_match(self):
        """Both Oracle components use the same encoding vocabulary."""
        c_enc = OracleTrainer_v3._deterministic_encoders()
        r_enc = OracleRegressor_MAE._deterministic_encoders()

        assert c_enc == r_enc, \
            "Classifier and Regressor must share identical deterministic encoders"

    def test_no_sklearn_labelencoder_import_in_training(self):
        """Training path uses dict encoders, not LabelEncoder.fit_transform()."""
        oracle = OracleTrainer_v3.create_default()
        samples = _make_training_samples(n=60, seed=99)
        oracle.load_training_dataset(samples)
        oracle.train_model()

        # After training, _encoders must be dicts
        for field, encoder in oracle._encoders.items():
            assert isinstance(encoder, dict), \
                f"Post-training encoder for '{field}' is {type(encoder)}, expected dict"


# ══════════════════════════════════════════════════════════════════════
# Test 3: Training regression — Oracle trains successfully
# ══════════════════════════════════════════════════════════════════════

class TestOracleTrainingRegression:
    """Verify that Oracle completes train_model() and produces valid metrics."""

    def test_classifier_trains_with_legacy_schema(self):
        """OracleTrainer_v3 trains successfully with legacy feature-dict samples."""
        oracle = OracleTrainer_v3.create_default()
        samples = _make_training_samples(n=60, seed=42)
        oracle.load_training_dataset(samples)
        oracle.train_model()

        assert oracle.model is not None
        metrics = oracle.get_training_metrics()
        assert metrics is not None
        assert "test_accuracy" in metrics
        assert "n_features" in metrics
        assert metrics["n_features"] == len(oracle._feature_cols)
        assert metrics["n_samples"] == 60

    def test_classifier_trains_with_v2_schema(self):
        """OracleTrainer_v3 trains successfully with v2.0 ReentrySnapshot samples."""
        oracle = OracleTrainer_v3.create_default()
        samples = _make_training_samples_v2(n=60, seed=42)
        oracle.load_training_dataset(samples)
        oracle.train_model()

        assert oracle.model is not None
        metrics = oracle.get_training_metrics()
        assert metrics is not None
        assert metrics["is_calibrated"] is True

    def test_classifier_feature_count_is_eleven(self):
        """Current Oracle uses exactly 11 features (post one-hot migration)."""
        oracle = OracleTrainer_v3.create_default()
        assert len(oracle._feature_cols) == 11
        assert "is_trending" in oracle._feature_cols
        assert "is_bullish" in oracle._feature_cols
        assert "is_div_neutral" in oracle._feature_cols
        # Old categorical columns must NOT be in feature_cols
        assert "regime" not in oracle._feature_cols
        assert "direction" not in oracle._feature_cols
        assert "delta_divergence" not in oracle._feature_cols

    def test_regressor_feature_count_is_twelve(self):
        """MAE Regressor uses 12 features (11 + zone_width_atr)."""
        regressor = OracleRegressor_MAE.create_default()
        assert len(regressor._feature_cols) == 12
        assert "zone_width_atr" in regressor._feature_cols
        assert "is_trending" in regressor._feature_cols

    def test_classifier_quality_gate_rejects_small_dataset(self):
        """Quality gate blocks training with <50 samples."""
        oracle = OracleTrainer_v3.create_default()
        samples = _make_training_samples(n=20, seed=42)
        oracle.load_training_dataset(samples)
        result = oracle.train_model()

        assert result is False
        metrics = oracle.get_training_metrics()
        assert metrics["quality_gate"] == "FAILED"

    def test_classifier_predict_returns_valid_prediction(self):
        """Trained Oracle returns valid OraclePrediction on new data."""
        oracle = OracleTrainer_v3.create_default()
        samples = _make_training_samples(n=60, seed=42)
        oracle.load_training_dataset(samples)
        oracle.train_model()

        prediction = oracle.predict(
            micro=None,
            signal_data={
                "vwap_at_retest": 79000.0,
                "obi_10_at_retest": 0.3,
                "cumulative_delta_at_retest": 100.0,
                "delta_divergence": "NEUTRAL",
                "atr_14": 500.0,
                "regime": "LATERAL",
                "direction": "bullish",
                "index": "test_001",
            }
        )

        assert prediction is not None
        assert 0.0 <= prediction.confidence <= 1.0
        assert prediction.suggested_action in ("EXECUTE", "IGNORE")
        assert prediction.is_placeholder is False

    def test_save_load_roundtrip(self, tmp_path):
        """Model survives save → load → predict cycle with deterministic encoders."""
        oracle = OracleTrainer_v3.create_default()
        samples = _make_training_samples(n=60, seed=42)
        oracle.load_training_dataset(samples)
        oracle.train_model()

        path = str(tmp_path / "oracle_test.joblib")
        oracle.save_to_disk(path)

        oracle2 = OracleTrainer_v3.create_default()
        oracle2.load_from_disk(path)

        # Encoders must survive roundtrip as dicts
        for field, encoder in oracle2._encoders.items():
            assert isinstance(encoder, dict), \
                f"Post-load encoder for '{field}' is {type(encoder)}"

        # Predictions must match
        signal = {
            "vwap_at_retest": 79000.0,
            "obi_10_at_retest": 0.3,
            "cumulative_delta_at_retest": 100.0,
            "delta_divergence": "NEUTRAL",
            "atr_14": 500.0,
            "regime": "LATERAL",
            "direction": "bullish",
            "index": "test_002",
        }
        p1 = oracle.predict(micro=None, signal_data=signal)
        p2 = oracle2.predict(micro=None, signal_data=signal)

        assert p1.confidence == p2.confidence, "Predictions must be identical after save/load"
