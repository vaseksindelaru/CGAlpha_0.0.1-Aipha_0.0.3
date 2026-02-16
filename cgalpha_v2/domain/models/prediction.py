"""
cgalpha.domain.models.prediction — Prediction (Oracle) value objects.

This module defines the value objects for the Prediction bounded context.
The Oracle acts as a probabilistic filter: given a set of features extracted
from a candle, it predicts whether a signal is likely to be profitable.

Design notes:
- Feature is a named numeric value (e.g. 'rsi_14' → 65.3).
- Prediction captures the Oracle's binary verdict + probability.
- ModelMetadata describes the serialized model without loading it.
- All classes are frozen dataclasses — immutable, hashable, safe to cache.

Ubiquitous Language:
    Feature         → A named numeric input to the Oracle model.
    Prediction      → The Oracle's verdict: pass/reject + probability.
    ModelMetadata   → Descriptive info about a trained model file.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True, slots=True)
class Feature:
    """
    A single named feature extracted from market data.

    Features are the inputs to the Oracle model.  Each has a canonical name
    and a numeric value.

    Attributes:
        name:  Feature identifier (e.g. 'rsi_14', 'volume_ratio').
        value: Numeric value of the feature.
    """

    name: str
    value: float

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Feature name cannot be empty")


@dataclass(frozen=True, slots=True)
class Prediction:
    """
    The Oracle's prediction for a given signal.

    The Oracle outputs a binary classification (pass/reject) with a
    probability score.  Signals with probability below the confidence
    threshold are filtered out.

    Attributes:
        signal_id:     The signal being evaluated.
        passed:        True if Oracle recommends passing the signal through.
        probability:   Model's predicted probability of success [0.0, 1.0].
        threshold:     Confidence threshold used for this prediction.
        model_id:      Identifier of the model that produced this prediction.
        features_used: Number of features that were fed to the model.
        created_at:    When the prediction was made.
    """

    signal_id: str
    passed: bool
    probability: float
    threshold: float
    model_id: str
    features_used: int
    created_at: datetime

    def __post_init__(self) -> None:
        if not (0.0 <= self.probability <= 1.0):
            raise ValueError(
                f"Prediction probability must be in [0, 1], "
                f"got {self.probability}"
            )
        if not (0.0 <= self.threshold <= 1.0):
            raise ValueError(
                f"Prediction threshold must be in [0, 1], "
                f"got {self.threshold}"
            )

    @property
    def margin(self) -> float:
        """How far above/below the threshold the prediction is."""
        return self.probability - self.threshold


@dataclass(frozen=True, slots=True)
class ModelMetadata:
    """
    Descriptive metadata for a serialized Oracle model.

    This does NOT load the model — it only describes it for logging,
    validation, and selection purposes.

    Attributes:
        model_id:       Unique identifier (e.g. 'rf_v2_20260115').
        model_type:     Algorithm name (e.g. 'RandomForest').
        version:        Model version string.
        trained_at:     When the model was trained.
        accuracy:       Reported accuracy on validation set [0.0, 1.0].
        n_estimators:   Number of estimators (trees).
        feature_names:  List of feature names the model expects.
        file_path:      Relative path to the .joblib file.
    """

    model_id: str
    model_type: str
    version: str
    trained_at: datetime
    accuracy: float
    n_estimators: int
    feature_names: tuple[str, ...]
    file_path: Optional[str] = None

    def __post_init__(self) -> None:
        if not (0.0 <= self.accuracy <= 1.0):
            raise ValueError(
                f"ModelMetadata accuracy must be in [0, 1], "
                f"got {self.accuracy}"
            )
        if self.n_estimators < 1:
            raise ValueError(
                f"ModelMetadata n_estimators must be ≥ 1, "
                f"got {self.n_estimators}"
            )
