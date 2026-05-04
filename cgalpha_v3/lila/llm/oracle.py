from dataclasses import dataclass
import json
from typing import Any, List, Dict, Tuple
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.utils import resample
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import brier_score_loss

from cgalpha_v3.domain.base_component import BaseComponentV3, ComponentManifest
from cgalpha_v3.domain.records import MicrostructureRecord

@dataclass
class OraclePrediction:
    trade_id: str
    confidence: float        # 0-1 (predict_proba del modelo)
    suggested_action: str    # "EXECUTE" | "IGNORE"
    estimated_delta_causal: float
    is_placeholder: bool = False  # True cuando no hay modelo entrenado

class OracleTrainer_v3(BaseComponentV3):
    """
    ╔═══════════════════════════════════════════════════════╗
    ║  MOSAIC ADAPTER — Componente v3                      ║
    ║  Heritage: legacy_vault/v1/cgalpha/labs/             ║
    ║            execution_optimizer_lab.py               ║
    ║  Heritage Contribution:                              ║
    ║    - Modelo de Meta-Labeling (López de Prado)        ║
    ║    - Selección de features de microestructura        ║
    ║  v3 Adaptations:                                     ║
    │    - Entrenamiento con dataset de retests            │
    │    - Features: VWAP, OBI, cumulative delta          │
    │    - Scoring binario: confidence > 0.70              ║
    ╚═══════════════════════════════════════════════════════╝
    """

    def __init__(self, manifest: ComponentManifest):
        super().__init__(manifest)
        self.min_confidence = 0.65# Umbral canónico
        self.model: RandomForestClassifier | str | None = None
        self.training_data: List[Dict[str, Any]] = []
        self._encoders: Dict[str, LabelEncoder] = {}
        self._training_metrics: Dict[str, Any] | None = None
        self._feature_cols = [
            "vwap_at_retest",
            "obi_10_at_retest",
            "cumulative_delta_at_retest",
            "delta_divergence",
            "atr_14",
            "regime",
            "direction",
        ]

    def load_training_dataset(self, training_samples: List[Dict]):
        """
        Carga dataset de entrenamiento desde SignalDetector.

        Args:
            training_samples: Lista de TrainingSample con features y outcomes
        """
        self.training_data = training_samples

    def train_model(self):
        """
        Entrena el modelo con el dataset cargado previo paso por el Data Quality Gate.
        """
        if not self.training_data:
            raise ValueError("No training data loaded. Call load_training_dataset() first.")

        # --- DATA QUALITY GATE (#2) ---
        quality_passed, quality_report = self._run_quality_gate()
        
        # Guardar reporte para trazabilidad
        report_path = Path("aipha_memory/reports/oracle_quality_latest.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(quality_report, indent=2))
        
        if not quality_passed:
            import logging
            logging.getLogger(__name__).warning(f"❌ DATA QUALITY GATE FAILED: {quality_report['reason']}")
            # Retornamos sin entrenar para mantener el modelo anterior (o el placeholder)
            self._training_metrics = {"quality_gate": "FAILED", "reason": quality_report['reason']}
            return False

        records = [self._normalize_sample(sample) for sample in self.training_data]
        df = pd.DataFrame(records)

        for col in self._feature_cols:
            if col not in df.columns:
                df[col] = np.nan

        if "outcome" not in df.columns:
            raise ValueError("Training dataset must include 'outcome'.")

        cat_defaults = {
            "delta_divergence": "NEUTRAL",
            "regime": "LATERAL",
            "direction": "bullish",
        }

        for col, default in cat_defaults.items():
            df[col] = df[col].fillna(default).astype(str)

        self._encoders = {}
        for col in ("delta_divergence", "regime", "direction"):
            encoder = LabelEncoder()
            df[col] = encoder.fit_transform(df[col])
            self._encoders[col] = encoder

        X = (
            df[self._feature_cols]
            .apply(pd.to_numeric, errors="coerce")
            .fillna(0.0)
        )
        y = (
            df["outcome"]
            .astype(str)
            .str.upper()
            .map({"BOUNCE": 1, "BREAKOUT": 0})
        )

        valid_mask = y.notna()
        X = X.loc[valid_mask]
        y = y.loc[valid_mask].astype(int)
        if X.empty:
            raise ValueError("No valid rows with outcome BOUNCE/BREAKOUT were found.")

        # BUG-1 fix: separar train/test para métricas OOS reales
        if len(X) >= 10:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
        else:
            # Dataset muy pequeño: sin split para no perder datos
            X_train, X_test, y_train, y_test = X, X, y, y

        # BUG-3 fix: oversampling de clase minoritaria SOLO en training set
        minority_count = int(y_train.value_counts().min())
        majority_count = int(y_train.value_counts().max())
        rebalance_applied = False
        if minority_count > 0 and majority_count / max(minority_count, 1) > 3:
            minority_label = int(y_train.value_counts().idxmin())
            minority_mask = y_train == minority_label
            X_minority = X_train[minority_mask]
            y_minority = y_train[minority_mask]
            X_majority = X_train[~minority_mask]
            y_majority = y_train[~minority_mask]
            X_min_resampled, y_min_resampled = resample(
                X_minority, y_minority,
                replace=True,
                n_samples=len(X_majority),
                random_state=42,
            )
            X_train = pd.concat([X_majority, X_min_resampled])
            y_train = pd.concat([y_majority, y_min_resampled])
            rebalance_applied = True
            import logging
            logging.getLogger(__name__).info(
                f"🔄 BUG-3 rebalance: {minority_count} minority → {len(X_majority)} "
                f"(oversampled to match majority)"
            )

        base_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            min_samples_leaf=2,
            random_state=42,
            class_weight="balanced",
        )
        
        # Calibración Platt Scaling (sigmoid) — ideal para datasets < 1000 samples
        self.model = CalibratedClassifierCV(base_model, method='sigmoid', cv='prefit')
        
        # Primero entrenar base con training set
        base_model.fit(X_train, y_train)
        # Luego calibrar (usando el mismo training set ya que cv='prefit')
        self.model.fit(X_train, y_train)

        # Métricas OOS Reales
        y_test_probs = self.model.predict_proba(X_test)[:, 1]
        test_accuracy = float(self.model.score(X_test, y_test))
        brier_score = float(brier_score_loss(y_test, y_test_probs))
        
        # Paso 3: K-fold CV (Estabilidad del modelo)
        cv_scores = cross_val_score(base_model, X_train, y_train, cv=5, scoring='accuracy')
        cv_mean = float(cv_scores.mean())
        cv_std = float(cv_scores.std())
        class_distribution = (
            y.map({1: "BOUNCE", 0: "BREAKOUT"})
            .value_counts()
            .to_dict()
        )
        importances = dict(
            zip(
                self._feature_cols,
                [round(float(v), 4) for v in base_model.feature_importances_],
            )
        )
        self._training_metrics = {
            "n_samples": int(len(X)),
            "n_train": int(len(X_train)),
            "n_test": int(len(X_test)),
            "train_accuracy": round(float(self.model.score(X_train, y_train)), 4),
            "test_accuracy": round(test_accuracy, 4),
            "cv_mean": round(cv_mean, 4),
            "cv_std": round(cv_std, 4),
            "brier_score": round(brier_score, 6),
            "n_features": len(self._feature_cols),
            "rebalance_applied": rebalance_applied,
            "feature_importances": importances,
            "calibration_method": "platt_sigmoid",
            "is_calibrated": True
        }
        # Inyectar firma causal basada en este dataset
        self._causal_signature = {
            "obi_mean": float(X["obi_10_at_retest"].mean()),
            "obi_std": float(X["obi_10_at_retest"].std()),
            "delta_mean": float(X["cumulative_delta_at_retest"].mean()),
            "delta_std": float(X["cumulative_delta_at_retest"].std())
        }

    def get_causal_signature(self) -> Dict[str, float]:
        """Retorna la firma estadística del dataset de entrenamiento (Baseline)."""
        return getattr(self, "_causal_signature", {
            "obi_mean": 0.05, "obi_std": 0.35,
            "delta_mean": 0.0, "delta_std": 100.0
        })

    def save_to_disk(self, path: str):
        """Guarda modelo y metadatos."""
        import joblib
        data = {
            "model": self.model,
            "encoders": self._encoders,
            "metrics": self._training_metrics,
            "causal_signature": self.get_causal_signature()
        }
        joblib.dump(data, path)

    def _run_quality_gate(self) -> Tuple[bool, Dict]:
        """
        Verifica: 
        1. Volumen de datos (min 50 samples)
        2. Desbalance de clases (> 15% por clase)
        3. Integridad (NaN ratio < 5%)
        """
        if not self.training_data:
            return False, {"reason": "No data", "passed": False}
        
        df = pd.DataFrame([self._normalize_sample(s) for s in self.training_data])
        
        # 1. Volumen
        n_samples = len(df)
        if n_samples < 50:
            return False, {"reason": f"Insufficient samples ({n_samples} < 50)", "passed": False, "n": n_samples}
            
        # 2. Desbalance
        if 'outcome' not in df.columns:
            return False, {"reason": "Missing outcome column", "passed": False}
            
        counts = df['outcome'].astype(str).str.upper().value_counts(normalize=True)
        min_class_pct = counts.min()
        if min_class_pct < 0.15:
            return False, {"reason": f"Extreme class imbalance ({min_class_pct:.1%})", "passed": False, "counts": counts.to_dict()}
            
        # 3. Integridad (NaNs en features críticas)
        nan_counts = df[self._feature_cols].isna().sum().sum()
        total_cells = n_samples * len(self._feature_cols)
        nan_ratio = nan_counts / total_cells if total_cells > 0 else 0
        if nan_ratio > 0.05:
            return False, {"reason": f"Too many NaNs ({nan_ratio:.1%})", "passed": False, "nan_ratio": nan_ratio}
            
        return True, {
            "passed": True,
            "n_samples": n_samples,
            "class_balance": counts.to_dict(),
            "nan_ratio": nan_ratio,
            "timestamp": str(pd.Timestamp.now())
        }

    def load_from_disk(self, path: str):
        """Carga modelo y metadatos."""
        import joblib
        data = joblib.load(path)
        self.model = data["model"]
        self._encoders = data["encoders"]
        self._training_metrics = data["metrics"]
        self._causal_signature = data["causal_signature"]

    def predict(self, micro: MicrostructureRecord, signal_data: Dict) -> OraclePrediction:
        """
        Evalua una señal detectada antes de su ejecucion.
        Predice si el retest resultará en BOUNCE o BREAKOUT.

        Args:
            micro: MicrostructureRecord con features en el momento del retest
            signal_data: Datos de la señal original

        Returns:
            OraclePrediction con confidence y acción sugerida
        """
        if self.model is None or self.model == "placeholder_model_trained":
            return OraclePrediction(
                trade_id=str(signal_data.get("index", "unknown")),
                confidence=0.85,
                suggested_action="EXECUTE",
                estimated_delta_causal=0.74,
                is_placeholder=True,
            )

        row = {
            "vwap_at_retest": float(self._pick(micro, "vwap", signal_data.get("vwap_at_retest", 0.0))),
            "obi_10_at_retest": float(self._pick(micro, "obi_10", signal_data.get("obi_10_at_retest", 0.0))),
            "cumulative_delta_at_retest": float(
                self._pick(micro, "cumulative_delta", signal_data.get("cumulative_delta_at_retest", 0.0))
            ),
            "delta_divergence": float(
                self._safe_encode(
                    "delta_divergence",
                    self._pick(micro, "delta_divergence", signal_data.get("delta_divergence", "NEUTRAL")),
                )
            ),
            "atr_14": float(self._pick(micro, "atr_14", signal_data.get("atr_14", 0.0))),
            "regime": float(
                self._safe_encode("regime", self._pick(micro, "regime", signal_data.get("regime", "LATERAL")))
            ),
            "direction": float(
                self._safe_encode("direction", signal_data.get("direction", self._pick(micro, "direction", "bullish")))
            ),
        }

        features = pd.DataFrame([row], columns=self._feature_cols).fillna(0.0)
        proba = self.model.predict_proba(features)[0]
        confidence = self._bounce_probability(proba)
        action = "EXECUTE" if confidence >= self.min_confidence else "IGNORE"

        return OraclePrediction(
            trade_id=str(signal_data.get("index", "unknown")),
            confidence=round(float(confidence), 4),
            suggested_action=action,
            estimated_delta_causal=round(float(confidence - 0.5), 4),
        )

    def _safe_encode(self, field: str, value: Any) -> int:
        """Encodea categorías con fallback robusto para valores no vistos."""
        if field not in self._encoders:
            return 0
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return 0
        encoder = self._encoders[field]
        value_str = str(value)
        known = {str(v) for v in encoder.classes_}
        if value_str not in known:
            return 0
        return int(encoder.transform([value_str])[0])

    def get_training_metrics(self) -> Dict[str, Any] | None:
        """Retorna métricas del último entrenamiento."""
        return self._training_metrics

    def retrain_recursive(self, training_data_path: str):
        """
        Re-entrena el Oracle con los nuevos OutcomeOrdinals del bridge.jsonl.
        Detecta drift y actualiza el Delta Causal estimado.
        """
        with open(training_data_path, "r", encoding="utf-8") as handle:
            loaded = json.load(handle)

        if isinstance(loaded, dict):
            if isinstance(loaded.get("training_data"), list):
                loaded = loaded["training_data"]
            elif isinstance(loaded.get("samples"), list):
                loaded = loaded["samples"]
            elif isinstance(loaded.get("dataset"), list):
                loaded = loaded["dataset"]
            else:
                raise ValueError("training_data_path does not contain a list-like dataset.")

        if not isinstance(loaded, list):
            raise ValueError("training_data_path must point to a JSON list.")

        self.training_data.extend(loaded)
        self.train_model()

    def _normalize_sample(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        normalized: Dict[str, Any] = {}
        nested = sample.get("features")
        if isinstance(nested, dict):
            normalized.update(nested)
        for col in self._feature_cols:
            if col in sample:
                normalized[col] = sample[col]
        normalized["outcome"] = sample.get("outcome")
        return normalized

    @staticmethod
    def _pick(record: Any, field: str, fallback: Any) -> Any:
        if record is None:
            return fallback
        if isinstance(record, dict):
            return record.get(field, fallback)
        return getattr(record, field, fallback)

    def _bounce_probability(self, proba: np.ndarray) -> float:
        classes = list(getattr(self.model, "classes_", []))
        if not classes:
            return 0.85
        if len(classes) == 1:
            return 1.0 if int(classes[0]) == 1 else 0.0
        try:
            idx = classes.index(1)
        except ValueError:
            idx = 1 if len(classes) > 1 else 0
        return float(proba[idx])

    @classmethod
    def create_default(cls):
        manifest = ComponentManifest(
            name="OracleTrainer_v3",
            category="filtering",
            function="Meta-Labeling: Predicción de outcome de retest basado en microestructura",
            inputs=["MicrostructureRecord", "SignalData"],
            outputs=["OraclePrediction"],
            heritage_source="legacy_vault/v1/cgalpha/labs/execution_optimizer_lab.py",
            heritage_contribution="Meta-Labeling principle and feature selection logic.",
            v3_adaptations="Training with retest dataset and trinity-based features.",
            causal_score=0.92 # El componente más confiable de v2 (83% acc)
        )
        return cls(manifest)
