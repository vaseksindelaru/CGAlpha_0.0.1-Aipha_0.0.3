"""
Oracle v6 — Meta-Labeling Framework (Fase A)
===========================================
Reconstrucción determinista del Oracle para cgAlpha_v4.

EVO-TICKET-0001 — Fase A entregables:
  1. Encoding determinista consolidado (ENCODING_MAPS).
  2. save/load con sumas de comprobación (SHA-256).
  3. Observabilidad: logging estructurado JSON de cada predicción.

Cambios respecto al skeleton original:
  - save() ahora incluye SHA-256 checksum del payload serializado.
  - load() verifica checksum al cargar; lanza IntegrityError si falla.
  - predict() y predict_mae() emiten log estructurado JSON (INFO/WARNING).
  - Comentario D-002/D-004 corregido (el encoding no tiene D-ID aún).
"""

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger("oracle_v6")


class IntegrityError(Exception):
    """Raised when a loaded model fails checksum verification."""
    pass


@dataclass
class OraclePrediction:
    trade_id: str
    confidence: float
    suggested_action: str
    is_placeholder: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


# Deterministic Categorical Mappings (D-008 — Nexus §3)
# Canonical encoding: same inputs → same floats, always.
# UNKNOWN = 0 for every category (safe fallback).
# This map is immutable once assigned a D-ID.
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
        """Convert categories to deterministic floats using ENCODING_MAPS.

        Unknown or missing categories always map to 0 (UNKNOWN).
        All values are uppercased before lookup for consistency.
        """
        encoded = {}
        for feat, mapping in ENCODING_MAPS.items():
            val = str(data.get(feat, "UNKNOWN")).upper()
            encoded[f"enc_{feat}"] = float(mapping.get(val, mapping["UNKNOWN"]))
        return encoded

    def save(self, path: Path):
        """Persist model with SHA-256 checksum for integrity verification.

        The checksum is computed over the serialized payload bytes
        and stored as a sidecar file (<path>.sha256).
        """
        import joblib
        import io

        payload = {
            "name": self.name,
            "model": self.model,
            "metrics": self.metrics,
            "feature_cols": self.feature_cols,
            "version": "v6.0.0-fase-a",
        }

        # Serialize to bytes for checksum computation
        buf = io.BytesIO()
        joblib.dump(payload, buf)
        raw_bytes = buf.getvalue()

        checksum = hashlib.sha256(raw_bytes).hexdigest()

        # Write model file
        path = Path(path)
        path.write_bytes(raw_bytes)

        # Write sidecar checksum file
        checksum_path = Path(str(path) + ".sha256")
        checksum_path.write_text(checksum)

        logger.info(json.dumps({
            "event": "model_saved",
            "name": self.name,
            "path": str(path),
            "checksum": checksum,
            "version": "v6.0.0-fase-a",
        }))

    def load(self, path: Path):
        """Load model with SHA-256 integrity verification.

        Raises:
            FileNotFoundError: if the model file does not exist.
            IntegrityError: if checksum verification fails.
        """
        import joblib

        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Oracle model not found at {path}")

        # Read raw bytes and verify checksum
        raw_bytes = path.read_bytes()
        actual_checksum = hashlib.sha256(raw_bytes).hexdigest()

        checksum_path = Path(str(path) + ".sha256")
        if checksum_path.exists():
            expected_checksum = checksum_path.read_text().strip()
            if actual_checksum != expected_checksum:
                raise IntegrityError(
                    f"Checksum mismatch for {path}: "
                    f"expected {expected_checksum}, got {actual_checksum}"
                )

        # Deserialize from bytes
        import io
        payload = joblib.load(io.BytesIO(raw_bytes))
        self.model = payload["model"]
        self.metrics = payload.get("metrics", {})
        self.feature_cols = payload.get("feature_cols", [])

        logger.info(json.dumps({
            "event": "model_loaded",
            "name": self.name,
            "path": str(path),
            "checksum": actual_checksum,
            "checksum_verified": checksum_path.exists(),
        }))


class OracleTrainerV6(OracleV6Base):
    """Refined Meta-Labeling Classifier (Capa 1).

    Predicts P(BOUNCE) for a detected signal.
    Threshold: 0.70 → EXECUTE (D-003 immutable truth).
    """

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
        """Make a meta-labeling prediction with structured logging.

        Every call (including placeholder) emits a JSON log entry.
        """
        encoding_inputs = {
            feat: features.get(feat, "UNKNOWN")
            for feat in ENCODING_MAPS.keys()
        }
        encoding_outputs = self._encode_categoricals(features)

        if self.is_placeholder():
            prediction = OraclePrediction(
                trade_id=features.get("sample_id", "unknown"),
                confidence=0.5,
                suggested_action="IGNORE",
                is_placeholder=True,
            )
            logger.warning(json.dumps({
                "event": "prediction",
                "timestamp": time.time(),
                "trade_id": prediction.trade_id,
                "confidence": prediction.confidence,
                "suggested_action": prediction.suggested_action,
                "is_placeholder": True,
                "encoding_inputs": encoding_inputs,
                "encoding_outputs": encoding_outputs,
            }))
            return prediction

        # Prepare feature vector
        vec = {k: features.get(k, 0.0) for k in ["vwap", "obi_10", "cum_delta", "atr"]}
        vec.update(encoding_outputs)

        df = pd.DataFrame([vec], columns=self.feature_cols).fillna(0.0)
        proba = self.model.predict_proba(df)[0][1]  # Probability of BOUNCE (1)

        prediction = OraclePrediction(
            trade_id=features.get("sample_id", "unknown"),
            confidence=float(proba),
            suggested_action="EXECUTE" if proba >= 0.70 else "IGNORE",
        )

        logger.info(json.dumps({
            "event": "prediction",
            "timestamp": time.time(),
            "trade_id": prediction.trade_id,
            "confidence": prediction.confidence,
            "suggested_action": prediction.suggested_action,
            "is_placeholder": False,
            "encoding_inputs": encoding_inputs,
            "encoding_outputs": encoding_outputs,
        }))
        return prediction


class OracleRegressorMAE_v6(OracleV6Base):
    """Refined MAE Regressor (Capa 2).

    Predicts expected Maximum Adverse Excursion in ATR units.
    Used by ShadowTrader for position sizing (Fase B dependency).
    """

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
        """Predict MAE with structured logging.

        Returns 0.5 ATR as default when in placeholder mode.
        """
        encoding_inputs = {
            feat: features.get(feat, "UNKNOWN")
            for feat in ENCODING_MAPS.keys()
        }
        encoding_outputs = self._encode_categoricals(features)

        if self.is_placeholder():
            logger.warning(json.dumps({
                "event": "prediction_mae",
                "timestamp": time.time(),
                "trade_id": features.get("sample_id", "unknown"),
                "predicted_mae_atr": 0.5,
                "is_placeholder": True,
                "encoding_inputs": encoding_inputs,
                "encoding_outputs": encoding_outputs,
            }))
            return 0.5  # Default 0.5 ATR

        vec = {
            k: features.get(k, 0.0)
            for k in ["vwap", "obi_10", "cum_delta", "atr", "zone_width_atr"]
        }
        vec.update(encoding_outputs)

        df = pd.DataFrame([vec], columns=self.feature_cols).fillna(0.0)
        result = float(self.model.predict(df)[0])

        logger.info(json.dumps({
            "event": "prediction_mae",
            "timestamp": time.time(),
            "trade_id": features.get("sample_id", "unknown"),
            "predicted_mae_atr": result,
            "is_placeholder": False,
            "encoding_inputs": encoding_inputs,
            "encoding_outputs": encoding_outputs,
        }))
        return result
