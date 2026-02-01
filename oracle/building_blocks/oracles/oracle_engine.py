import joblib
import logging
import os
from sklearn.ensemble import RandomForestClassifier
from typing import Any, Optional

logger = logging.getLogger(__name__)

class OracleEngine:
    """Motor del Oráculo basado en Machine Learning."""

    def __init__(self, model: Optional[Any] = None):
        if model is not None:
            self.model = model
        else:
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)

    def train(self, features: Any, targets: Any):
        """Entrena el modelo con las características y etiquetas proporcionadas."""
        logger.info(f"Entrenando Oráculo con {len(features)} muestras...")
        self.model.fit(features, targets)
        logger.info("Entrenamiento completado.")

    def predict(self, features: Any) -> Any:
        """Realiza predicciones sobre nuevas características."""
        return self.model.predict(features)

    def predict_proba(self, features: Any) -> Any:
        """Devuelve las probabilidades de cada clase."""
        return self.model.predict_proba(features)

    def save(self, filepath: str):
        """Persiste el modelo en un archivo."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(self.model, filepath)
        logger.info(f"Modelo guardado en {filepath}")

    @classmethod
    def load(cls, filepath: str) -> 'OracleEngine':
        """Carga un modelo desde un archivo."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"No se encontró el modelo en {filepath}")
        model = joblib.load(filepath)
        logger.info(f"Modelo cargado desde {filepath}")
        return cls(model=model)
