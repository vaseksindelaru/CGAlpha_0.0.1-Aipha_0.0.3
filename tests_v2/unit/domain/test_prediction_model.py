"""Unit tests for cgalpha_v2.domain.models.prediction."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cgalpha_v2.domain.models import Feature, ModelMetadata, Prediction


def test_feature_empty_name_raises() -> None:
    with pytest.raises(ValueError, match="name"):
        Feature(name="", value=1.0)


def test_prediction_margin() -> None:
    prediction = Prediction(
        signal_id="SIG_1",
        passed=True,
        probability=0.8,
        threshold=0.7,
        model_id="model_1",
        features_used=10,
        created_at=datetime.now(timezone.utc),
    )
    assert prediction.margin == pytest.approx(0.1)


def test_prediction_probability_validation_raises() -> None:
    with pytest.raises(ValueError, match="probability"):
        Prediction(
            signal_id="SIG_1",
            passed=False,
            probability=1.1,
            threshold=0.7,
            model_id="model_1",
            features_used=10,
            created_at=datetime.now(timezone.utc),
        )


def test_prediction_threshold_validation_raises() -> None:
    with pytest.raises(ValueError, match="threshold"):
        Prediction(
            signal_id="SIG_1",
            passed=False,
            probability=0.5,
            threshold=-0.1,
            model_id="model_1",
            features_used=10,
            created_at=datetime.now(timezone.utc),
        )


def test_model_metadata_validation_raises() -> None:
    with pytest.raises(ValueError, match="accuracy"):
        ModelMetadata(
            model_id="m1",
            model_type="RandomForest",
            version="v1",
            trained_at=datetime.now(timezone.utc),
            accuracy=1.1,
            n_estimators=100,
            feature_names=("a", "b"),
        )

    with pytest.raises(ValueError, match="n_estimators"):
        ModelMetadata(
            model_id="m1",
            model_type="RandomForest",
            version="v1",
            trained_at=datetime.now(timezone.utc),
            accuracy=0.9,
            n_estimators=0,
            feature_names=("a", "b"),
        )
