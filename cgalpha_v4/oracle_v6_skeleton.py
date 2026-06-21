"""
Oracle v6 — Meta-Labeling Framework (Fase A)
===========================================
Reconstrucción determinista del Oracle para cgAlpha_v4.
Fixes: FEATURE_COLS naming, Deterministic Encoding, Modular Regressor.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class OraclePrediction:
    trade_id: str
    confidence: float
    suggested_action: str
    is_placeholder: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


# Deterministic Categorical Mappings
# NOTE: previously tagged (D-002/D-004) incorrectly. D-002 is outcome_lookahead
# and D-004 is fingerprint dedup. Encoding determinism has no D-ID yet.
# If ENCODING_MAPS becomes immutable truth, assign a new D-ID in Nexus §3.
ENCODING_MAPS = {
    "regime": {"UNKNOWN": 0, "LATERAL": 1, "TREND": 2, "HIGH_VOL": 3},
    "direction": {"UNKNOWN": 0, "BULLISH": 1, "BEARISH": 2},
    "delta_divergence": {"UNKNOWN": 0, "NEUTRAL": 1, "BULLISH": 2, "BEARISH": 3},
}


class OracleV6Base:
    """Base class for Oracle models with deterministic encoding and persistence."""

    def __init__(self, name: str):
        self.name = name
        self.model = None
        self.metrics = {}
        self.feature_cols = []

    def is_placeholder(self) -> bool:
        return self.model is None or self.model == "placeholder"

    def _encode_categoricals(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Convert categories to deterministic floats using ENCODING_MAPS."""
        encoded = {}
        for feat, mapping in ENCODING_MAPS.items():
            val = str(data.get(feat, "UNKNOWN")).upper()
            encoded[f"enc_{feat}"] = float(mapping.get(val, mapping["UNKNOWN"]))
        return encoded

    def save(self, path: Path):
        """Standard joblib/pickle persistence with metadata check."""
        import joblib

        payload = {
            "name": self.name,
            "model": self.model,
            "metrics": self.metrics,
            "feature_cols": self.feature_cols,
            "version": "v6.0.0-fase-a",
        }
        joblib.dump(payload, path)

    def load(self, path: Path):
        import joblib

        if not path.exists():
            raise FileNotFoundError(f"Oracle model not found at {path}")
        payload = joblib.load(path)
        self.model = payload["model"]
        self.metrics = payload.get("metrics", {})
        self.feature_cols = payload.get("feature_cols", [])


class OracleTrainerV6(OracleV6Base):
    """Refined Meta-Labeling Classifier (Capa 1)."""

    def __init__(self):
        super().__init__("OracleClassifier_v6")
        self.target_col = "outcome_binary"
        self.feature_cols = [
            "vwap",
            "obi_10",
            "cum_delta",
            "atr",
            "enc_regime",
            "enc_direction",
            "enc_delta_divergence",
        ]

    def predict(self, features: Dict[str, Any]) -> OraclePrediction:
        if self.is_placeholder():
            return OraclePrediction(
                trade_id=features.get("sample_id", "unknown"),
                confidence=0.5,
                suggested_action="IGNORE",
                is_placeholder=True,
            )

        # Prepare vector
        vec = {k: features.get(k, 0.0) for k in ["vwap", "obi_10", "cum_delta", "atr"]}
        vec.update(self._encode_categoricals(features))

        df = pd.DataFrame([vec], columns=self.feature_cols).fillna(0.0)
        proba = self.model.predict_proba(df)[0][1]  # Probability of BOUNCE (1)

        return OraclePrediction(
            trade_id=features.get("sample_id", "unknown"),
            confidence=float(proba),
            suggested_action="EXECUTE" if proba >= 0.70 else "IGNORE",
        )


class OracleRegressorMAE_v6(OracleV6Base):
    """Refined MAE Regressor (Capa 2)."""

    def __init__(self):
        super().__init__("OracleRegressorMAE_v6")
        self.feature_cols = [
            "vwap",
            "obi_10",
            "cum_delta",
            "atr",
            "zone_width_atr",
            "enc_regime",
            "enc_direction",
            "enc_delta_divergence",
        ]

    def predict_mae(self, features: Dict[str, Any]) -> float:
        if self.is_placeholder():
            return 0.5  # Default 0.5 ATR

        vec = {
            k: features.get(k, 0.0)
            for k in ["vwap", "obi_10", "cum_delta", "atr", "zone_width_atr"]
        }
        vec.update(self._encode_categoricals(features))

        df = pd.DataFrame([vec], columns=self.feature_cols).fillna(0.0)
        return float(self.model.predict(df)[0])
