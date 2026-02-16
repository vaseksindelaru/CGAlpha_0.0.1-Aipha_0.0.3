"""
cgalpha.domain.ports.prediction_port — Ports for ML prediction and feature extraction.

These ports abstract the Oracle's ML model and feature engineering pipeline.
The domain never knows whether predictions come from RandomForest, XGBoost,
or a mock that always returns True.

Implementations live in cgalpha.infrastructure.ml.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from cgalpha_v2.domain.models.prediction import Prediction
    from cgalpha_v2.domain.models.signal import Candle


@runtime_checkable
class FeatureExtractor(Protocol):
    """
    Port for extracting features from candle data.

    Features are named numeric values fed to the Oracle model.
    The extractor transforms raw OHLCV data into a feature vector.
    """

    def extract(self, candle: "Candle") -> dict[str, float]:
        """
        Extract features from a single candle.

        Args:
            candle: The candle to extract features from.

        Returns:
            Dictionary mapping feature names to numeric values.
            Keys must match the feature_names expected by the model.

        Raises:
            FeatureExtractionError: If extraction fails.
        """
        ...


@runtime_checkable
class Predictor(Protocol):
    """
    Port for ML prediction (Oracle).

    The predictor takes extracted features and returns a probability
    score for signal quality.
    """

    def predict(
        self,
        features: dict[str, float],
        signal_id: str,
    ) -> "Prediction":
        """
        Generate a prediction for the given features.

        Args:
            features:  Feature dictionary (name → value).
            signal_id: ID of the signal being evaluated.

        Returns:
            Prediction with probability, threshold, and pass/reject verdict.

        Raises:
            PredictionError: If the model fails to produce a prediction.
            ModelLoadError:  If the model is not loaded.
        """
        ...

    def is_available(self) -> bool:
        """
        Check if the predictor is ready to make predictions.

        Returns:
            True if the model is loaded and healthy.
        """
        ...
