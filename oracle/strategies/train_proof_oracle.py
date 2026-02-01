import pandas as pd
import duckdb
import logging
import sys
import os
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from trading_manager.building_blocks.detectors.key_candle_detector import SignalDetector
from trading_manager.building_blocks.labelers.potential_capture_engine import get_atr_labels
from oracle.building_blocks.features.feature_engineer import FeatureEngineer
from oracle.building_blocks.oracles.oracle_engine import OracleEngine

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def train_oracle():
    db_path = "data_processor/data/aipha_data.duckdb"
    table_name = "btc_1h_data"
    model_path = "oracle/models/proof_oracle.joblib"
    
    logger.info("--- INICIANDO ENTRENAMIENTO DEL ORÁCULO ---")
    
    # 1. Carga de Datos
    if not os.path.exists(db_path):
        logger.error(f"Base de datos no encontrada en {db_path}")
        return

    conn = duckdb.connect(db_path)
    df = conn.execute(f"SELECT * FROM {table_name}").df()
    conn.close()
    
    df['Open_Time'] = pd.to_datetime(df['Open_Time'])
    df = df.sort_values('Open_Time').set_index('Open_Time')
    
    # 2. Detección de Señales (Layer 3)
    df = SignalDetector.detect_key_candles(df, volume_percentile_threshold=80)
    t_events = df[df['is_key_candle']].index
    
    if len(t_events) < 10:
        logger.error("Insuficientes eventos para entrenar.")
        return

    # 3. Etiquetado (Layer 3)
    labels = get_atr_labels(df, t_events, tp_factor=2.0, sl_factor=1.0, time_limit=24)
    
    # 4. Extracción de Features (Layer 4)
    features = FeatureEngineer.extract_features(df, t_events)
    
    # Unir features y labels
    data = features.copy()
    data['target'] = labels
    
    # Filtrar casos neutrales (0) si se desea entrenar solo TP vs SL
    # data = data[data['target'] != 0]
    
    if data.empty:
        logger.error("No hay datos después del filtrado.")
        return

    X = data.drop(columns=['target'])
    y = data['target']
    
    # 5. Split y Entrenamiento
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    oracle = OracleEngine()
    oracle.train(X_train, y_train)
    
    # 6. Evaluación
    y_pred = oracle.predict(X_test)
    logger.info("--- EVALUACIÓN DEL MODELO ---")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.2f}")
    print(classification_report(y_test, y_pred))
    
    # 7. Guardado
    oracle.save(model_path)
    logger.info("Proceso de entrenamiento completado.")

if __name__ == "__main__":
    train_oracle()
