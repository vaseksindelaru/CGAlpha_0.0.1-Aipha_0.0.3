"""Tests para Oracle RF real — Fase 1."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from cgalpha_v3.domain.records import MicrostructureRecord
from cgalpha_v3.lila.llm.oracle import OraclePrediction, OracleTrainer_v3


def _make_training_data(n: int = 30, nested: bool = False) -> list[dict]:
    rng = np.random.default_rng(42)
    samples: list[dict] = []

    for i in range(n):
        outcome = "BREAKOUT" if i % 5 == 0 else "BOUNCE"
        features = {
            "vwap_at_retest": float(65000 + rng.normal(0, 1500)),
            "obi_10_at_retest": float(rng.uniform(-0.7, 0.7)),
            "cumulative_delta_at_retest": float(rng.normal(0, 450)),
            "delta_divergence": str(
                rng.choice(["BULLISH_ABSORPTION", "BEARISH_EXHAUSTION", "NEUTRAL"])
            ),
            "atr_14": float(rng.uniform(250, 950)),
            "regime": str(rng.choice(["TREND", "LATERAL", "HIGH_VOL"])),
            "direction": str(rng.choice(["bullish", "bearish"])),
        }
        if nested:
            sample = {
                "features": features,
                "outcome": outcome,
                "zone_id": f"{i}_zone",
                "retest_timestamp": 1700000000000 + i * 3600000,
            }
        else:
            sample = {**features, "outcome": outcome}
        samples.append(sample)

    return samples


def _sample_micro() -> MicrostructureRecord:
    return MicrostructureRecord(
        timestamp=1000,
        symbol="BTCUSDT",
        open=65000,
        high=65500,
        low=64800,
        close=65200,
        volume=1500,
        vwap=65100,
        vwap_std_1=100,
        vwap_std_2=200,
        obi_10=0.15,
        cumulative_delta=250,
        delta_divergence="BULLISH_ABSORPTION",
        atr_14=450,
        regime="LATERAL",
    )


def test_train_model_real() -> None:
    oracle = OracleTrainer_v3.create_default()
    oracle.load_training_dataset(_make_training_data(30))
    oracle.train_model()

    assert oracle.model is not None
    assert oracle.model != "placeholder_model_trained"


def test_train_model_with_nested_features_dataset() -> None:
    oracle = OracleTrainer_v3.create_default()
    oracle.load_training_dataset(_make_training_data(30, nested=True))
    oracle.train_model()

    metrics = oracle.get_training_metrics()
    assert metrics is not None
    assert metrics["n_samples"] == 30


def test_predict_with_trained_model() -> None:
    oracle = OracleTrainer_v3.create_default()
    oracle.load_training_dataset(_make_training_data(30))
    oracle.train_model()

    pred = oracle.predict(_sample_micro(), {"index": 100, "direction": "bullish"})
    assert isinstance(pred, OraclePrediction)
    assert 0.0 <= pred.confidence <= 1.0
    assert pred.suggested_action in ("EXECUTE", "IGNORE")


def test_training_metrics_available() -> None:
    oracle = OracleTrainer_v3.create_default()
    oracle.load_training_dataset(_make_training_data(30))
    oracle.train_model()

    metrics = oracle.get_training_metrics()
    assert metrics is not None
    assert "train_accuracy" in metrics
    assert "feature_importances" in metrics
    assert metrics["n_samples"] == 30


def test_safe_encode_unknown_category() -> None:
    oracle = OracleTrainer_v3.create_default()
    oracle.load_training_dataset(_make_training_data(30))
    oracle.train_model()

    result = oracle._safe_encode("regime", "UNKNOWN_REGIME")
    assert result == 0


def test_backward_compatible_placeholder() -> None:
    oracle = OracleTrainer_v3.create_default()
    pred = oracle.predict(_sample_micro(), {"index": 1})
    assert pred.confidence == 0.85
    assert pred.suggested_action == "EXECUTE"


def test_min_samples_threshold() -> None:
    oracle = OracleTrainer_v3.create_default()
    oracle.load_training_dataset(_make_training_data(5))
    oracle.train_model()
    assert oracle.model is not None


def test_retrain_recursive_merges_dataset(tmp_path: Path) -> None:
    oracle = OracleTrainer_v3.create_default()
    oracle.load_training_dataset(_make_training_data(10))
    oracle.train_model()

    path = tmp_path / "new_training.json"
    new_data = _make_training_data(8, nested=True)
    path.write_text(json.dumps(new_data), encoding="utf-8")

    before = len(oracle.training_data)
    oracle.retrain_recursive(str(path))
    after = len(oracle.training_data)

    assert after == before + 8
    assert oracle.model is not None
