from dataclasses import dataclass
import json
from typing import Any, List, Dict, Tuple
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.utils import resample
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import brier_score_loss

try:
    from sklearn.frozen import FrozenEstimator  # sklearn >= 1.6
except ImportError:
    FrozenEstimator = None  # sklearn < 1.6

from cgalpha_v3.domain.base_component import BaseComponentV3, ComponentManifest
from cgalpha_v3.domain.records import MicrostructureRecord


def _to_binary_features(regime, direction, delta_div) -> dict:
    """Convert categorical values to deterministic binary columns (one-hot).

    Phase Bridge [F3] — replaces LabelEncoder ordinal encoding.
    Each categorical becomes N binary columns. Mapping is fixed and
    identical across retraining cycles.
    """
    r = str(regime or "").strip().upper()
    d = str(direction or "").strip().lower()
    dd = str(delta_div or "").strip().upper()
    return {
        "is_trending": int(r == "TREND"),
        "is_lateral": int(r == "LATERAL"),
        "is_high_vol": int(r == "HIGH_VOL"),
        "is_bullish": int("bull" in d),
        "is_div_bullish": int(dd in ("BULLISH", "BULLISH_ABSORPTION")),
        "is_div_bearish": int(dd in ("BEARISH", "BEARISH_EXHAUSTION")),
        "is_div_neutral": int(dd not in ("BULLISH", "BULLISH_ABSORPTION", "BEARISH", "BEARISH_EXHAUSTION")),
    }


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
        self._encoders: Dict[str, Dict[str, int]] = {}
        self._training_metrics: Dict[str, Any] | None = None
        self._feature_cols = [
            "vwap_at_retest",
            "obi_10_at_retest",
            "cumulative_delta_at_retest",
            "atr_14",
            # Binary columns (one-hot) — Phase Bridge [F3]
            "is_trending",
            "is_lateral",
            "is_high_vol",
            "is_bullish",
            "is_div_bullish",
            "is_div_bearish",
            "is_div_neutral",
        ]

    @staticmethod
    def _deterministic_encoders() -> Dict[str, Dict[str, int]]:
        return {
            "delta_divergence": {"UNKNOWN": 0, "NEUTRAL": 1, "BULLISH": 2, "BEARISH": 3},
            "regime": {"UNKNOWN": 0, "LATERAL": 1, "TREND": 2, "HIGH_VOL": 3},
            "direction": {"UNKNOWN": 0, "BULLISH": 1, "BEARISH": 2},
        }

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
        _PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
        report_path = _PROJECT_ROOT / "aipha_memory/reports/oracle_quality_latest.json"
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

        # Binary columns are produced by _normalize_sample → _to_binary_features
        # Fill any missing binary cols with 0 (default = unknown/neutral)
        for col in self._feature_cols:
            if col not in df.columns:
                df[col] = 0

        # Preserve deterministic encoders for backward compat (save_to_disk)
        self._encoders = self._deterministic_encoders()

        X = (
            df[self._feature_cols]
            .apply(pd.to_numeric, errors="coerce")
            .fillna(0.0)
        )
        y = (
            df["outcome"]
            .astype(str)
            .str.upper()
            .map({"BOUNCE_STRONG": 1, "BREAKOUT": 0})
        )

        valid_mask = y.notna()
        X = X.loc[valid_mask]
        y = y.loc[valid_mask].astype(int)
        if X.empty:
            raise ValueError("No valid rows with outcome BOUNCE_STRONG/BREAKOUT were found.")

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
        self.model = (
            CalibratedClassifierCV(FrozenEstimator(base_model), method='sigmoid', cv='prefit')
            if FrozenEstimator is not None
            else CalibratedClassifierCV(base_model, method='sigmoid', cv='prefit')
        )
        
        # Primero entrenar base con training set
        base_model.fit(X_train, y_train)
        # Luego calibrar (usando el mismo training set ya que cv='prefit')
        self.model.fit(X_train, y_train)

        # Métricas OOS Reales
        y_test_probs = self.model.predict_proba(X_test)[:, 1]
        test_accuracy = float(self.model.score(X_test, y_test))
        brier_score = float(brier_score_loss(y_test, y_test_probs))
        
        cv_scores = cross_val_score(base_model, X_train, y_train, cv=5, scoring='accuracy')
        cv_mean = float(cv_scores.mean())
        cv_std = float(cv_scores.std())
        class_distribution = (
            y.map({1: "BOUNCE_STRONG", 0: "BREAKOUT"})
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
        
        # Filtrar muestras INCONCLUSIVE/BOUNCE_WEAK
        valid_df = df[df['outcome'].astype(str).str.upper().isin(["BOUNCE_STRONG", "BREAKOUT"])]
        if len(valid_df) < 10:
            return False, {"reason": f"Insufficient valid samples ({len(valid_df)} < 10)", "passed": False}
            
        counts = valid_df['outcome'].astype(str).str.upper().value_counts(normalize=True)
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

    def is_placeholder(self) -> bool:
        """True si el modelo no está entrenado o es el placeholder.

        Fix BUG-4: el sistema puede distinguir predicciones reales
        de confidence=0.85 hardcoded.
        """
        return (
            self.model is None
            or self.model == "placeholder_model_trained"
        )

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

        # Numerical features
        row = {
            "vwap_at_retest": float(self._pick(micro, "vwap", signal_data.get("vwap_at_retest", 0.0))),
            "obi_10_at_retest": float(self._pick(micro, "obi_10", signal_data.get("obi_10_at_retest", 0.0))),
            "cumulative_delta_at_retest": float(
                self._pick(micro, "cumulative_delta", signal_data.get("cumulative_delta_at_retest", 0.0))
            ),
            "atr_14": float(self._pick(micro, "atr_14", signal_data.get("atr_14", 0.0))),
        }
        # Binary features (one-hot) — Phase Bridge [F3]
        binary = _to_binary_features(
            self._pick(micro, "regime", signal_data.get("regime", "LATERAL")),
            signal_data.get("direction", self._pick(micro, "direction", "bullish")),
            self._pick(micro, "delta_divergence", signal_data.get("delta_divergence", "NEUTRAL")),
        )
        row.update(binary)

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
        value_str = str(value).strip().upper()

        # Compatibilidad con modelos antiguos serializados con LabelEncoder
        encoder_obj = self._encoders[field]
        if hasattr(encoder_obj, "classes_") and hasattr(encoder_obj, "transform"):
            known = {str(v) for v in encoder_obj.classes_}
            if value_str not in known:
                return 0
            return int(encoder_obj.transform([value_str])[0])

        mapping = encoder_obj
        if field == "direction":
            if "BULL" in value_str:
                return mapping.get("BULLISH", 1)
            if "BEAR" in value_str:
                return mapping.get("BEARISH", 2)
        elif field == "delta_divergence":
            if "BULL" in value_str:
                return mapping.get("BULLISH", 2)
            if "BEAR" in value_str:
                return mapping.get("BEARISH", 3)
            if "NEUTRAL" in value_str:
                return mapping.get("NEUTRAL", 1)
        elif field == "regime":
            if "LATERAL" in value_str:
                return mapping.get("LATERAL", 1)
            if "HIGH" in value_str and "VOL" in value_str:
                return mapping.get("HIGH_VOL", 3)
            if "TREND" in value_str or "BULL" in value_str or "BEAR" in value_str:
                return mapping.get("TREND", 2)

        return mapping.get(value_str, mapping.get("UNKNOWN", 0))

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
        
        # Schema v2.0 support (ReentrySnapshot)
        if "_meta" in sample and "schema_version" in sample.get("_meta", {}):
            l2 = sample.get("l2_snapshot_at_touch", {})
            zg = sample.get("zone_geometry", {})
            cl = sample.get("clearance", {})
            out = sample.get("outcome", {})
            
            normalized["vwap_at_retest"] = (
                l2.get("vwap_at_retest")
                or l2.get("vwap_session")
                or l2.get("retest_price")
            )
            normalized["obi_10_at_retest"] = l2.get("obi_10")
            normalized["cumulative_delta_at_retest"] = l2.get("cumulative_delta")
            normalized["atr_14"] = cl.get("atr_at_detection")
            normalized["outcome"] = out.get("label")
            # Binary columns — Phase Bridge [F3]
            normalized.update(_to_binary_features(
                cl.get("regime"), zg.get("direction"), l2.get("delta_divergence")
            ))
            return normalized

        # Legacy support
        nested = sample.get("features")
        if isinstance(nested, dict):
            normalized.update(nested)
        for col in self._feature_cols:
            if col in sample:
                normalized[col] = sample[col]
        # Derive binary columns from raw categoricals
        normalized.update(_to_binary_features(
            normalized.get("regime"), normalized.get("direction"),
            normalized.get("delta_divergence")
        ))
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

@dataclass
class MAEPrediction:
    trade_id: str
    predicted_mae_atr: float
    limit_price: float
    is_safe: bool
    reason: str = ""

class OracleRegressor_MAE(BaseComponentV3):
    """
    ╔═══════════════════════════════════════════════════════╗
    ║  ORACLE REGRESSOR MAE — Capa 2 (Fase 13)             ║
    ║  Apunta a estimar el Maximum Adverse Excursion normal-║
    ║  izado por ATR para colocar órdenes Limit dinámicas.  ║
    ╚═══════════════════════════════════════════════════════╝
    """
    def __init__(self, manifest: ComponentManifest):
        super().__init__(manifest)
        self.model: RandomForestRegressor | None = None
        self.training_data: List[Dict[str, Any]] = []
        self._encoders: Dict[str, Dict[str, int]] = {}
        self._training_metrics: Dict[str, Any] | None = None
        self._feature_cols = [
            "vwap_at_retest",
            "obi_10_at_retest",
            "cumulative_delta_at_retest",
            "atr_14",
            # Binary columns (one-hot) — Phase Bridge [F3]
            "is_trending",
            "is_lateral",
            "is_high_vol",
            "is_bullish",
            "is_div_bullish",
            "is_div_bearish",
            "is_div_neutral",
            "zone_width_atr",  # Extra feature available in v2.0
        ]
        self.max_allowable_mae_ratio = 0.90 # 90% of zone width

    @staticmethod
    def _deterministic_encoders() -> Dict[str, Dict[str, int]]:
        return {
            "delta_divergence": {"UNKNOWN": 0, "NEUTRAL": 1, "BULLISH": 2, "BEARISH": 3},
            "regime": {"UNKNOWN": 0, "LATERAL": 1, "TREND": 2, "HIGH_VOL": 3},
            "direction": {"UNKNOWN": 0, "BULLISH": 1, "BEARISH": 2},
        }

    def load_training_dataset(self, training_samples: List[Dict]):
        """Carga el dataset (schema v2.0)."""
        self.training_data = training_samples

    def train_model(self):
        if not self.training_data:
            raise ValueError("No training data loaded. Call load_training_dataset() first.")

        # Filtrar solo BOUNCE_STRONG para la regresión (donde MAE tiene sentido)
        valid_samples = []
        for sample in self.training_data:
            if sample.get("outcome", {}).get("label") in ["BOUNCE_STRONG", "BOUNCE_WEAK"]:
                valid_samples.append(sample)
                
        if len(valid_samples) < 10:
            import logging
            logging.getLogger(__name__).warning("❌ Insufficient BOUNCE samples for MAE Regression (< 10).")
            return False

        records = [self._normalize_sample(s) for s in valid_samples]
        df = pd.DataFrame(records)

        for col in self._feature_cols:
            if col not in df.columns:
                df[col] = np.nan

        # Binary columns are produced by _normalize_sample → _to_binary_features
        for col in self._feature_cols:
            if col not in df.columns:
                df[col] = 0

        self._encoders = self._deterministic_encoders()

        X = df[self._feature_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0)
        y = df["mae_atr"].apply(pd.to_numeric, errors="coerce")

        valid_mask = y.notna()
        X = X.loc[valid_mask]
        y = y.loc[valid_mask]

        if len(X) < 10:
            return False

        if len(X) >= 15:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        else:
            X_train, X_test, y_train, y_test = X, X, y, y

        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=5,
            min_samples_leaf=2,
            random_state=42
        )
        self.model.fit(X_train, y_train)

        from sklearn.metrics import mean_absolute_error, r2_score
        y_pred = self.model.predict(X_test)
        mae_metric = float(mean_absolute_error(y_test, y_pred))
        r2_metric = float(r2_score(y_test, y_pred))

        importances = dict(zip(self._feature_cols, [round(float(v), 4) for v in self.model.feature_importances_]))
        
        self._training_metrics = {
            "n_train": len(X_train),
            "n_test": len(X_test),
            "test_mae_atr": mae_metric,
            "test_r2": r2_metric,
            "feature_importances": importances
        }
        return True

    def _normalize_sample(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        normalized: Dict[str, Any] = {}
        if "_meta" in sample and "schema_version" in sample.get("_meta", {}):
            l2 = sample.get("l2_snapshot_at_touch", {})
            zg = sample.get("zone_geometry", {})
            cl = sample.get("clearance", {})
            out = sample.get("outcome", {})
            
            normalized["vwap_at_retest"] = l2.get("vwap_at_retest")
            normalized["obi_10_at_retest"] = l2.get("obi_10")
            normalized["cumulative_delta_at_retest"] = l2.get("cumulative_delta")
            normalized["atr_14"] = cl.get("atr_at_detection")
            normalized["zone_width_atr"] = zg.get("zone_width_atr", 0.5)
            normalized["mae_atr"] = out.get("mae_atr")
            # Binary columns — Phase Bridge [F3]
            normalized.update(_to_binary_features(
                cl.get("regime"), zg.get("direction"), l2.get("delta_divergence")
            ))
        return normalized

    def predict_mae(self, micro: MicrostructureRecord, signal_data: Dict) -> MAEPrediction:
        if self.model is None:
            # Fallback a penetración moderada (e.g. 0.2 ATR)
            return MAEPrediction(str(signal_data.get("index", "unknown")), 0.2, 0.0, True, "Placeholder model")

        # Numerical features
        row = {
            "vwap_at_retest": float(self._pick(micro, "vwap", signal_data.get("vwap_at_retest", 0.0))),
            "obi_10_at_retest": float(self._pick(micro, "obi_10", signal_data.get("obi_10_at_retest", 0.0))),
            "cumulative_delta_at_retest": float(self._pick(micro, "cumulative_delta", signal_data.get("cumulative_delta_at_retest", 0.0))),
            "atr_14": float(self._pick(micro, "atr_14", signal_data.get("atr_14", 0.0))),
            "zone_width_atr": float(signal_data.get("zone_width_atr", 0.5)),
        }
        # Binary features (one-hot) — Phase Bridge [F3]
        binary = _to_binary_features(
            self._pick(micro, "regime", signal_data.get("regime", "LATERAL")),
            signal_data.get("direction", self._pick(micro, "direction", "bullish")),
            self._pick(micro, "delta_divergence", signal_data.get("delta_divergence", "NEUTRAL")),
        )
        row.update(binary)

        features = pd.DataFrame([row], columns=self._feature_cols).fillna(0.0)
        predicted_mae_atr = float(self.model.predict(features)[0])
        
        retest_price = signal_data.get("zone_top", 0) if row["direction"] == self._safe_encode("direction", "bullish") else signal_data.get("zone_bottom", 0)
        atr_val = row["atr_14"]
        
        # bullish = rebota en zone_top y cae hasta (zone_top - mae_atr*atr) antes de subir
        # bearish = rebota en zone_bottom y sube hasta (zone_bottom + mae_atr*atr) antes de caer
        direction_str = signal_data.get("direction", "bullish")
        
        if direction_str == "bullish":
            limit_price = retest_price - (predicted_mae_atr * atr_val)
        else:
            limit_price = retest_price + (predicted_mae_atr * atr_val)
            
        # Safety check: ¿el MAE predicho es mayor a lo que la zona puede aguantar?
        zone_width_atr = row["zone_width_atr"]
        if predicted_mae_atr > (zone_width_atr * self.max_allowable_mae_ratio):
            is_safe = False
            reason = f"Predicted MAE ({predicted_mae_atr:.2f} ATR) exceeds {self.max_allowable_mae_ratio*100:.0f}% of zone width ({zone_width_atr:.2f} ATR)"
        else:
            is_safe = True
            reason = "OK"

        return MAEPrediction(
            trade_id=str(signal_data.get("index", "unknown")),
            predicted_mae_atr=predicted_mae_atr,
            limit_price=limit_price,
            is_safe=is_safe,
            reason=reason
        )

    def get_training_metrics(self) -> Dict[str, Any] | None:
        """Retorna métricas del último entrenamiento."""
        return self._training_metrics

    def _safe_encode(self, field: str, value: Any) -> int:
        if field not in self._encoders:
            return 0
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return 0
        value_str = str(value).strip().upper()

        # Compatibilidad con modelos antiguos serializados con LabelEncoder
        encoder_obj = self._encoders[field]
        if hasattr(encoder_obj, "classes_") and hasattr(encoder_obj, "transform"):
            known = {str(v) for v in encoder_obj.classes_}
            if value_str not in known:
                return 0
            return int(encoder_obj.transform([value_str])[0])

        mapping = encoder_obj
        if field == "direction":
            if "BULL" in value_str:
                return mapping.get("BULLISH", 1)
            if "BEAR" in value_str:
                return mapping.get("BEARISH", 2)
        elif field == "delta_divergence":
            if "BULL" in value_str:
                return mapping.get("BULLISH", 2)
            if "BEAR" in value_str:
                return mapping.get("BEARISH", 3)
            if "NEUTRAL" in value_str:
                return mapping.get("NEUTRAL", 1)
        elif field == "regime":
            if "LATERAL" in value_str:
                return mapping.get("LATERAL", 1)
            if "HIGH" in value_str and "VOL" in value_str:
                return mapping.get("HIGH_VOL", 3)
            if "TREND" in value_str or "BULL" in value_str or "BEAR" in value_str:
                return mapping.get("TREND", 2)

        return mapping.get(value_str, mapping.get("UNKNOWN", 0))

    def _pick(self, record: Any, field: str, fallback: Any) -> Any:
        if record is None: return fallback
        if isinstance(record, dict): return record.get(field, fallback)
        return getattr(record, field, fallback)

    def save_to_disk(self, path: str):
        import joblib
        joblib.dump({"model": self.model, "encoders": self._encoders, "metrics": self._training_metrics}, path)

    def load_from_disk(self, path: str):
        import joblib
        data = joblib.load(path)
        self.model = data["model"]
        self._encoders = data["encoders"]
        self._training_metrics = data["metrics"]

    @classmethod
    def create_default(cls):
        manifest = ComponentManifest(
            name="OracleRegressor_MAE",
            category="sizing",
            function="Regresor de Maximum Adverse Excursion para Optimización de Entry Points",
            inputs=["MicrostructureRecord", "SignalData"],
            outputs=["MAEPrediction"],
            heritage_source="Capa 2 / Fase 13",
            heritage_contribution="Limit Order Targeting",
            v3_adaptations="",
            causal_score=0.90
        )
        return cls(manifest)
