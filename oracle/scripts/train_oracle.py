import pandas as pd
import duckdb
import logging
import sys
import os
from joblib import dump

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from trading_manager.building_blocks.detectors.key_candle_detector import SignalDetector
from trading_manager.building_blocks.labelers.potential_capture_engine import get_atr_labels
from oracle.building_blocks.features.feature_engineer import FeatureEngineer
from oracle.building_blocks.oracles.oracle_engine import OracleEngine
from core.config_manager import ConfigManager

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def train_new_oracle():
    config = ConfigManager()
    db_path = "data_processor/data/aipha_data.duckdb"
    table_name = "btc_1h_data"
    
    logger.info("--- INICIANDO ENTRENAMIENTO DE ORÁCULO (AUTO-APRENDIZAJE) ---")
    
    # 1. Carga de Datos
    if not os.path.exists(db_path):
        logger.error("No se encontró la base de datos.")
        return

    conn = duckdb.connect(db_path)
    df = conn.execute(f"SELECT * FROM {table_name}").df()
    conn.close()
    
    df['Open_Time'] = pd.to_datetime(df['Open_Time'])
    df = df.sort_values('Open_Time').set_index('Open_Time')

    # 2. Generar Dataset (Usando la lógica de Reversión actual)
    df = SignalDetector.detect_key_candles(
        df, 
        volume_percentile_threshold=config.get("Trading.volume_percentile_threshold", 90),
        body_percentile_threshold=config.get("Trading.body_percentile_threshold", 25),
        reversal_mode=config.get("Trading.reversal_mode", True)
    )
    
    key_candles = df[df['is_key_candle']]
    t_events = key_candles.index
    sides = key_candles['signal_side']
    
    if len(t_events) < 100:
        logger.warning(f"Dataset muy pequeño para entrenar: {len(t_events)} señales.")
        return

    # 3. Obtener Labels (Ground Truth de Reversión)
    labels = get_atr_labels(
        df, 
        t_events, 
        sides=sides,
        tp_factor=config.get("Trading.tp_factor", 1.5), 
        sl_factor=config.get("Trading.sl_factor", 1.0), 
        time_limit=config.get("Trading.time_limit", 24)
    )
    
    # 4. Extraer Features
    features = FeatureEngineer.extract_features(df, t_events)
    
    # 5. Entrenar Modelo
    # Usamos solo señales con label 1 (éxito) o -1 (fracaso) para entrenamiento binario
    valid_idx = labels[labels != 0].index
    X = features.loc[valid_idx]
    y = (labels.loc[valid_idx] == 1).astype(int)
    
    logger.info(f"Entrenando con {len(X)} muestras (Éxitos: {y.sum()}, Fracasos: {len(y)-y.sum()})")
    
    from sklearn.ensemble import RandomForestClassifier
    rf_model = RandomForestClassifier(n_estimators=config.get("Oracle.n_estimators", 100), random_state=42)
    oracle = OracleEngine(model=rf_model)
    oracle.train(X, y)
    
    # 6. Guardar Modelo (Auto-corrección: Nueva versión)
    new_model_path = "oracle/models/oracle_reversal_v1.joblib"
    os.makedirs("oracle/models", exist_ok=True)
    oracle.save(new_model_path)
    
    # 7. Actualizar Configuración (Auto-corrección)
    config.set("Oracle.model_path", new_model_path)
    logger.info(f"✅ Modelo guardado y configuración actualizada: {new_model_path}")

if __name__ == "__main__":
    train_new_oracle()
