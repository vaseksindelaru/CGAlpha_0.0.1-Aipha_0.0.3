"""
Tests for Oracle v6 — Fase A (EVO-TICKET-0001)
===============================================
Original 4 contract tests + expanded suite for >90% coverage.

Coverage targets:
  - OracleTrainerV6: predict() both paths (placeholder + real model)
  - OracleRegressorMAE_v6: __init__, predict_mae() both paths
  - OracleV6Base: save/load with checksum verification, FileNotFoundError,
    IntegrityError, load without sidecar checksum
  - _encode_categoricals: edge cases
  - Observability: structured log output verification
"""

import io
import json
import logging
import shutil
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from cgalpha_v4.oracle_v6_skeleton import (
    ENCODING_MAPS,
    IntegrityError,
    OraclePrediction,
    OracleRegressorMAE_v6,
    OracleTrainerV6,
    OracleV6Base,
)


class TestOracleV6Skeleton(unittest.TestCase):
    """Original 4 contract tests — must remain intact."""

    def setUp(self):
        self.test_dir = Path("tmp_test_oracle")
        self.test_dir.mkdir(exist_ok=True)
        self.oracle = OracleTrainerV6()

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_deterministic_encoding(self):
        """Verify that categories are encoded consistently."""
        data = {"regime": "LATERAL", "direction": "BULLISH", "delta_divergence": "NEUTRAL"}
        encoded = self.oracle._encode_categoricals(data)

        self.assertEqual(encoded["enc_regime"], float(ENCODING_MAPS["regime"]["LATERAL"]))
        self.assertEqual(encoded["enc_direction"], float(ENCODING_MAPS["direction"]["BULLISH"]))
        self.assertEqual(encoded["enc_delta_divergence"], float(ENCODING_MAPS["delta_divergence"]["NEUTRAL"]))

        # Unknown handling
        data_err = {"regime": "INVALID"}
        encoded_err = self.oracle._encode_categoricals(data_err)
        self.assertEqual(encoded_err["enc_regime"], 0.0)

    def test_placeholder_logic(self):
        """Verify is_placeholder before and after setting a dummy model."""
        self.assertTrue(self.oracle.is_placeholder())
        self.oracle.model = "dummy"
        self.assertFalse(self.oracle.is_placeholder())

    def test_prediction_output_structure(self):
        """Verify the OraclePrediction structure in placeholder mode."""
        features = {"vwap": 60000, "obi_10": 0.5}
        prediction = self.oracle.predict(features)

        self.assertEqual(prediction.confidence, 0.5)
        self.assertEqual(prediction.suggested_action, "IGNORE")
        self.assertTrue(prediction.is_placeholder)

    def test_save_load_contract(self):
        """Verify that metrics and feature_cols survive the save/load cycle."""
        self.oracle.metrics = {"accuracy": 0.85}
        self.oracle.model = "placeholder"  # dummy for joblib

        path = self.test_dir / "oracle_test.joblib"
        self.oracle.save(path)

        new_oracle = OracleTrainerV6()
        new_oracle.load(path)

        self.assertEqual(new_oracle.metrics["accuracy"], 0.85)
        self.assertEqual(new_oracle.feature_cols, self.oracle.feature_cols)


# ─── New tests: Checksum integrity (save/load) ──────────────────────────

class TestChecksumIntegrity(unittest.TestCase):
    """Verify SHA-256 checksum verification in save/load cycle."""

    def setUp(self):
        self.test_dir = Path("tmp_test_checksum")
        self.test_dir.mkdir(exist_ok=True)
        self.oracle = OracleTrainerV6()
        self.oracle.model = "placeholder"
        self.oracle.metrics = {"test": 1.0}

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_checksum_sidecar_created(self):
        """save() must produce both .joblib and .joblib.sha256 files."""
        path = self.test_dir / "model.joblib"
        self.oracle.save(path)

        self.assertTrue(path.exists())
        checksum_path = Path(str(path) + ".sha256")
        self.assertTrue(checksum_path.exists())

        # Checksum should be a 64-char hex string
        checksum = checksum_path.read_text().strip()
        self.assertEqual(len(checksum), 64)

    def test_load_with_valid_checksum(self):
        """load() succeeds when checksum matches."""
        path = self.test_dir / "model.joblib"
        self.oracle.save(path)

        loaded = OracleTrainerV6()
        loaded.load(path)  # Should not raise
        self.assertEqual(loaded.metrics["test"], 1.0)

    def test_load_with_corrupted_file_raises_integrity_error(self):
        """load() raises IntegrityError when file is corrupted after save."""
        path = self.test_dir / "model.joblib"
        self.oracle.save(path)

        # Corrupt the model file
        with open(path, "ab") as f:
            f.write(b"CORRUPTED")

        loaded = OracleTrainerV6()
        with self.assertRaises(IntegrityError) as ctx:
            loaded.load(path)
        self.assertIn("Checksum mismatch", str(ctx.exception))

    def test_load_without_sidecar_skips_verification(self):
        """load() proceeds without error if .sha256 sidecar is missing."""
        path = self.test_dir / "model.joblib"
        self.oracle.save(path)

        # Remove sidecar
        checksum_path = Path(str(path) + ".sha256")
        checksum_path.unlink()

        loaded = OracleTrainerV6()
        loaded.load(path)  # Should not raise
        self.assertEqual(loaded.metrics["test"], 1.0)

    def test_load_file_not_found(self):
        """load() raises FileNotFoundError for non-existent path."""
        loaded = OracleTrainerV6()
        with self.assertRaises(FileNotFoundError):
            loaded.load(self.test_dir / "nonexistent.joblib")


# ─── New tests: OracleRegressorMAE_v6 ───────────────────────────────────

class TestOracleRegressorMAE(unittest.TestCase):
    """Coverage for OracleRegressorMAE_v6 (Capa 2), previously at 0%."""

    def setUp(self):
        self.test_dir = Path("tmp_test_mae")
        self.test_dir.mkdir(exist_ok=True)
        self.regressor = OracleRegressorMAE_v6()

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_regressor_init(self):
        """Verify MAE regressor initializes with correct name and feature_cols."""
        self.assertEqual(self.regressor.name, "OracleRegressorMAE_v6")
        self.assertIn("zone_width_atr", self.regressor.feature_cols)
        self.assertTrue(self.regressor.is_placeholder())

    def test_placeholder_predict_mae(self):
        """Placeholder mode returns 0.5 ATR default."""
        result = self.regressor.predict_mae({"vwap": 60000})
        self.assertEqual(result, 0.5)

    def test_real_model_predict_mae(self):
        """Non-placeholder mode calls model.predict() correctly."""
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.35]
        self.regressor.model = mock_model

        features = {
            "vwap": 60000, "obi_10": 0.5, "cum_delta": 100,
            "atr": 50, "zone_width_atr": 1.2,
            "regime": "TREND", "direction": "BULLISH", "delta_divergence": "NEUTRAL",
        }
        result = self.regressor.predict_mae(features)
        self.assertEqual(result, 0.35)
        mock_model.predict.assert_called_once()

    def test_regressor_save_load(self):
        """Verify save/load with checksum for regressor."""
        self.regressor.model = "placeholder"
        self.regressor.metrics = {"mae": 0.42}
        path = self.test_dir / "mae.joblib"
        self.regressor.save(path)

        loaded = OracleRegressorMAE_v6()
        loaded.load(path)
        self.assertEqual(loaded.metrics["mae"], 0.42)
        self.assertIn("zone_width_atr", loaded.feature_cols)


# ─── New tests: Predict with real model (non-placeholder) ───────────────

class TestPredictWithModel(unittest.TestCase):
    """Coverage for OracleTrainerV6.predict() non-placeholder path."""

    def test_predict_execute_threshold(self):
        """Model returning P(BOUNCE)=0.80 → EXECUTE."""
        oracle = OracleTrainerV6()
        mock_model = MagicMock()
        mock_model.predict_proba.return_value = [[0.20, 0.80]]
        oracle.model = mock_model

        features = {
            "sample_id": "test-001",
            "vwap": 60000, "obi_10": 0.5, "cum_delta": 100, "atr": 50,
            "regime": "LATERAL", "direction": "BEARISH", "delta_divergence": "NEUTRAL",
        }
        pred = oracle.predict(features)
        self.assertEqual(pred.trade_id, "test-001")
        self.assertAlmostEqual(pred.confidence, 0.80)
        self.assertEqual(pred.suggested_action, "EXECUTE")
        self.assertFalse(pred.is_placeholder)

    def test_predict_ignore_below_threshold(self):
        """Model returning P(BOUNCE)=0.55 → IGNORE."""
        oracle = OracleTrainerV6()
        mock_model = MagicMock()
        mock_model.predict_proba.return_value = [[0.45, 0.55]]
        oracle.model = mock_model

        features = {
            "vwap": 60000, "obi_10": 0.5, "cum_delta": 100, "atr": 50,
            "regime": "TREND", "direction": "BULLISH", "delta_divergence": "BEARISH",
        }
        pred = oracle.predict(features)
        self.assertAlmostEqual(pred.confidence, 0.55)
        self.assertEqual(pred.suggested_action, "IGNORE")

    def test_predict_exactly_at_threshold(self):
        """Model returning P(BOUNCE)=0.70 exactly → EXECUTE (>= boundary)."""
        oracle = OracleTrainerV6()
        mock_model = MagicMock()
        mock_model.predict_proba.return_value = [[0.30, 0.70]]
        oracle.model = mock_model

        features = {"vwap": 60000, "obi_10": 0.5, "cum_delta": 100, "atr": 50}
        pred = oracle.predict(features)
        self.assertEqual(pred.suggested_action, "EXECUTE")


# ─── New tests: Observability (structured logging) ──────────────────────

class TestObservability(unittest.TestCase):
    """Verify structured JSON logging from predict() and predict_mae()."""

    def setUp(self):
        self.log_stream = io.StringIO()
        self.handler = logging.StreamHandler(self.log_stream)
        self.handler.setLevel(logging.DEBUG)
        self.logger = logging.getLogger("oracle_v6")
        self.logger.addHandler(self.handler)
        self.logger.setLevel(logging.DEBUG)

    def tearDown(self):
        self.logger.removeHandler(self.handler)

    def test_placeholder_predict_logs_warning(self):
        """Placeholder predict() emits WARNING-level structured JSON log."""
        oracle = OracleTrainerV6()
        oracle.predict({"sample_id": "obs-001"})

        log_output = self.log_stream.getvalue()
        self.assertIn('"event": "prediction"', log_output)
        self.assertIn('"is_placeholder": true', log_output)
        self.assertIn('"trade_id": "obs-001"', log_output)

        # Verify it's valid JSON
        log_json = json.loads(log_output.strip())
        self.assertEqual(log_json["event"], "prediction")
        self.assertIn("encoding_inputs", log_json)
        self.assertIn("encoding_outputs", log_json)
        self.assertIn("timestamp", log_json)

    def test_real_predict_logs_info(self):
        """Non-placeholder predict() emits INFO-level structured JSON log."""
        oracle = OracleTrainerV6()
        mock_model = MagicMock()
        mock_model.predict_proba.return_value = [[0.30, 0.70]]
        oracle.model = mock_model

        oracle.predict({"sample_id": "obs-002", "regime": "TREND"})

        log_output = self.log_stream.getvalue()
        log_json = json.loads(log_output.strip())
        self.assertEqual(log_json["event"], "prediction")
        self.assertFalse(log_json["is_placeholder"])
        self.assertEqual(log_json["encoding_inputs"]["regime"], "TREND")

    def test_placeholder_mae_logs_warning(self):
        """Placeholder predict_mae() emits WARNING-level log."""
        regressor = OracleRegressorMAE_v6()
        regressor.predict_mae({"sample_id": "mae-001"})

        log_output = self.log_stream.getvalue()
        log_json = json.loads(log_output.strip())
        self.assertEqual(log_json["event"], "prediction_mae")
        self.assertTrue(log_json["is_placeholder"])
        self.assertEqual(log_json["predicted_mae_atr"], 0.5)

    def test_real_mae_logs_info(self):
        """Non-placeholder predict_mae() emits INFO-level log."""
        regressor = OracleRegressorMAE_v6()
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.42]
        regressor.model = mock_model

        regressor.predict_mae({
            "sample_id": "mae-002",
            "vwap": 60000, "obi_10": 0.5, "cum_delta": 100,
            "atr": 50, "zone_width_atr": 1.2,
            "regime": "LATERAL",
        })

        log_output = self.log_stream.getvalue()
        log_json = json.loads(log_output.strip())
        self.assertEqual(log_json["event"], "prediction_mae")
        self.assertFalse(log_json["is_placeholder"])
        self.assertAlmostEqual(log_json["predicted_mae_atr"], 0.42)

    def test_log_fields_completeness(self):
        """Verify all required fields are present in log output."""
        oracle = OracleTrainerV6()
        oracle.predict({"sample_id": "fields-001", "regime": "HIGH_VOL"})

        log_output = self.log_stream.getvalue()
        log_json = json.loads(log_output.strip())

        required_fields = [
            "event", "timestamp", "trade_id", "confidence",
            "suggested_action", "is_placeholder",
            "encoding_inputs", "encoding_outputs",
        ]
        for f in required_fields:
            self.assertIn(f, log_json, f"Missing required log field: {f}")

    def test_save_logs_info(self):
        """save() emits structured log with checksum."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            oracle = OracleTrainerV6()
            oracle.model = "placeholder"
            oracle.save(Path(tmpdir) / "model.joblib")

            log_output = self.log_stream.getvalue()
            log_json = json.loads(log_output.strip())
            self.assertEqual(log_json["event"], "model_saved")
            self.assertIn("checksum", log_json)

    def test_load_logs_info(self):
        """load() emits structured log with checksum verification status."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            oracle = OracleTrainerV6()
            oracle.model = "placeholder"
            path = Path(tmpdir) / "model.joblib"
            oracle.save(path)

            # Clear log
            self.log_stream.truncate(0)
            self.log_stream.seek(0)

            loaded = OracleTrainerV6()
            loaded.load(path)

            log_output = self.log_stream.getvalue()
            log_json = json.loads(log_output.strip())
            self.assertEqual(log_json["event"], "model_loaded")
            self.assertTrue(log_json["checksum_verified"])


# ─── New tests: Encoding edge cases ────────────────────────────────────

class TestEncodingEdgeCases(unittest.TestCase):
    """Additional coverage for _encode_categoricals edge cases."""

    def test_case_insensitivity(self):
        """Encoding should be case-insensitive (lowercase input → same output)."""
        oracle = OracleV6Base("test")
        data_upper = {"regime": "LATERAL"}
        data_lower = {"regime": "lateral"}
        data_mixed = {"regime": "Lateral"}

        self.assertEqual(
            oracle._encode_categoricals(data_upper),
            oracle._encode_categoricals(data_lower),
        )
        self.assertEqual(
            oracle._encode_categoricals(data_upper),
            oracle._encode_categoricals(data_mixed),
        )

    def test_missing_all_categories(self):
        """Missing categories default to UNKNOWN=0."""
        oracle = OracleV6Base("test")
        encoded = oracle._encode_categoricals({})
        self.assertEqual(encoded["enc_regime"], 0.0)
        self.assertEqual(encoded["enc_direction"], 0.0)
        self.assertEqual(encoded["enc_delta_divergence"], 0.0)

    def test_none_value_category(self):
        """None values should stringify and map to UNKNOWN."""
        oracle = OracleV6Base("test")
        encoded = oracle._encode_categoricals({"regime": None})
        self.assertEqual(encoded["enc_regime"], 0.0)

    def test_encoding_determinism_across_instances(self):
        """Same inputs → same outputs across different instances."""
        oracle1 = OracleTrainerV6()
        oracle2 = OracleTrainerV6()
        data = {"regime": "TREND", "direction": "BEARISH", "delta_divergence": "BULLISH"}
        self.assertEqual(
            oracle1._encode_categoricals(data),
            oracle2._encode_categoricals(data),
        )

    def test_all_valid_categories_covered(self):
        """Every valid category in ENCODING_MAPS produces a non-UNKNOWN value."""
        oracle = OracleV6Base("test")
        for feat, mapping in ENCODING_MAPS.items():
            for label, expected_val in mapping.items():
                data = {feat: label}
                encoded = oracle._encode_categoricals(data)
                self.assertEqual(
                    encoded[f"enc_{feat}"],
                    float(expected_val),
                    f"Encoding mismatch for {feat}={label}",
                )


if __name__ == "__main__":
    unittest.main()
