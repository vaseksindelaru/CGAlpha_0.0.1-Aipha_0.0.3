import pandas as pd
import duckdb
import logging
import sys
import os

# Añadir el directorio raíz al path para poder importar los building blocks
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from trading_manager.building_blocks.detectors.key_candle_detector import SignalDetector
from trading_manager.building_blocks.labelers.potential_capture_engine import get_atr_labels
from core.config_manager import ConfigManager
from core.memory_manager import MemoryManager

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def run_proof_strategy():
    # Inicializar managers de Capa 1
    config = ConfigManager()
    memory = MemoryManager()
    
    db_path = "data_processor/data/aipha_data.duckdb"
    table_name = "btc_1h_data"
    
    logger.info("--- INICIANDO PROOF STRATEGY ---")
    
    # 1. Carga de Datos desde DuckDB
    if not os.path.exists(db_path):
        logger.error(f"Base de datos no encontrada en {db_path}")
        return

    try:
        conn = duckdb.connect(db_path)
        df = conn.execute(f"SELECT * FROM {table_name}").df()
        conn.close()
        
        # Asegurar que el índice es el tiempo y está ordenado
        df['Open_Time'] = pd.to_datetime(df['Open_Time'])
        df = df.sort_values('Open_Time').set_index('Open_Time')
        
        logger.info(f"Datos cargados: {len(df)} velas de {df.index.min()} a {df.index.max()}")
    except Exception as e:
        logger.error(f"Error al cargar datos: {e}")
        return

    # 2. Detección de Señales (Usando Config)
    logger.info("Detectando velas clave...")
    df = SignalDetector.detect_key_candles(
        df, 
        volume_lookback=50, 
        volume_percentile_threshold=config.get("Trading.volume_percentile_threshold", 90),
        body_percentile_threshold=config.get("Trading.body_percentile_threshold", 25),
        ema_period=config.get("Trading.ema_period", 200),
        reversal_mode=config.get("Trading.reversal_mode", True)
    )
    
    # 3. Filtrado de Eventos
    key_candles = df[df['is_key_candle']]
    t_events = key_candles.index
    sides = key_candles['signal_side']
    logger.info(f"Se detectaron {len(t_events)} eventos de señal.")

    if len(t_events) == 0:
        logger.warning("No se detectaron señales con los parámetros actuales.")
        return

    # 4. Etiquetado (Triple Barrier Method - Usando Config)
    logger.info("Etiquetando eventos con Triple Barrier Method (ATR)...")
    labels = get_atr_labels(
        df, 
        t_events, 
        sides=sides,
        atr_period=config.get("Trading.atr_period", 14), 
        tp_factor=config.get("Trading.tp_factor", 2.0), 
        sl_factor=config.get("Trading.sl_factor", 1.0), 
        time_limit=config.get("Trading.time_limit", 24)
    )

    # 5. Resultados
    logger.info("--- RESULTADOS FINALES ---")
    counts = labels.value_counts().sort_index()
    
    summary = {
        "Total Señales": len(labels),
        "Take Profit (1)": counts.get(1, 0),
        "Stop Loss (-1)": counts.get(-1, 0),
        "Neutral (0)": counts.get(0, 0)
    }
    
    for key, val in summary.items():
        print(f"{key}: {val}")
        
    if len(labels) > 0:
        win_rate = (summary["Take Profit (1)"] / len(labels)) * 100
        print(f"Win Rate (TP vs Total): {win_rate:.2f}%")
        
        # REGISTRAR MÉTRICA EN CAPA 1
        memory.record_metric(
            component="Trading",
            metric_name="win_rate",
            value=win_rate / 100.0,
            metadata={
                "tp_factor": config.get("Trading.tp_factor"),
                "sl_factor": config.get("Trading.sl_factor"),
                "signals": len(labels)
            }
        )

if __name__ == "__main__":
    run_proof_strategy()
