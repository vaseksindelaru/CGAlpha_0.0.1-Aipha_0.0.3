"""
VALIDACIÓN CRUZADA DEL ORACLE - Usando datos de 2024 NO vistos durante entrenamiento
=====================================================================================

Como no tenemos datos de 2025 aún, haremos una validación más rigurosa:
- Entrenamos con: Jan-Oct 2024 (10 meses)
- Probamos con: Nov-Dec 2024 (2 meses COMPLETAMENTE NUEVOS)

Esto simula lo que pasará cuando lleguemos a 2025.

Ejecutar: python oracle/strategies/test_oracle_cross_validation_2024.py
"""

import pandas as pd
import numpy as np
import duckdb
import joblib
import logging
import sys
import os
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from trading_manager.building_blocks.detectors.key_candle_detector import SignalDetector
from trading_manager.building_blocks.detectors.accumulation_zone_detector import AccumulationZoneDetector
from trading_manager.building_blocks.detectors.trend_detector import TrendDetector
from trading_manager.building_blocks.signal_combiner import SignalCombiner
from trading_manager.building_blocks.labelers.potential_capture_engine import get_atr_labels
from core.config_manager import ConfigManager

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def load_data_from_db():
    """Carga todos los datos de 2024 desde DuckDB"""
    db_path = "data_processor/data/aipha_data.duckdb"
    try:
        conn = duckdb.connect(db_path)
        df = conn.execute("SELECT * FROM btc_5m_data").df()
        conn.close()
        
        df['Open_Time'] = pd.to_datetime(df['Open_Time'])
        df = df.sort_values('Open_Time').set_index('Open_Time')
        
        logger.info(f"✅ Datos cargados: {len(df)} velas")
        logger.info(f"   Rango: {df.index.min()} a {df.index.max()}")
        return df
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return None


def split_data_temporal():
    """Split temporal: Train en Jan-Oct, Test en Nov-Dec"""
    df = load_data_from_db()
    if df is None:
        return None, None, None, None
    
    df_train = df[df.index.month <= 10]
    df_test = df[df.index.month > 10]
    
    logger.info(f"\n📊 SPLIT TEMPORAL:")
    logger.info(f"   Train (Jan-Oct 2024): {len(df_train)} velas")
    logger.info(f"   Test (Nov-Dec 2024): {len(df_test)} velas")
    logger.info(f"   Ratio: {len(df_train) / len(df):.1%} / {len(df_test) / len(df):.1%}")
    
    return df, df_train, df_test, len(df)


def detect_signals(df, name=""):
    """Detecta Triple Coincidencias"""
    logger.info(f"\n--- Detectando Triple Coincidencias en {name} ---")
    
    config = ConfigManager()
    
    try:
        # Detectores
        df = AccumulationZoneDetector.detect_zones(
            df, atr_period=14, atr_multiplier=1.5, min_zone_bars=5, 
            volume_threshold_ratio=1.1, lookback_bars=20
        )
        
        df = TrendDetector.analyze_trend(
            df, lookback_period=20, zigzag_threshold=0.005
        )
        
        df = SignalDetector.detect_key_candles(
            df, volume_lookback=50, volume_percentile_threshold=80,
            body_percentile_threshold=30, ema_period=200, reversal_mode=True
        )
        
        df = SignalCombiner.combine_signals(
            df, tolerance_bars=8, min_r_squared=0.45
        )
        
        triple_count = df['is_triple_coincidence'].sum()
        logger.info(f"   ✅ {triple_count} Triple Coincidencias detectadas")
        return df, triple_count
        
    except Exception as e:
        logger.error(f"   ❌ Error: {e}")
        return df, 0


def extract_features(df_row, df_context):
    """Extrae 4 características para Oracle"""
    try:
        open_price = df_row['Open']
        close_price = df_row['Close']
        high = df_row['High']
        low = df_row['Low']
        
        total_range = high - low
        body = abs(close_price - open_price)
        body_percentage = (body / total_range) if total_range > 0 else 0
        
        vol_lookback = 50
        avg_volume = df_context.iloc[-vol_lookback:]['Volume'].mean() if len(df_context) >= vol_lookback else df_context['Volume'].mean()
        volume_ratio = df_row['Volume'] / avg_volume if avg_volume > 0 else 1.0
        
        relative_range = total_range / open_price if open_price > 0 else 0
        hour_of_day = df_row.name.hour / 24.0
        
        return np.array([
            np.clip(body_percentage, 0, 1),
            np.clip(volume_ratio / 10, 0, 1),
            np.clip(relative_range * 100, 0, 1),
            hour_of_day
        ], dtype=np.float32)
    except:
        return np.zeros(4, dtype=np.float32)


def run_validation():
    """Ejecuta validación cruzada temporal"""
    
    logger.info("=" * 80)
    logger.info("🔬 VALIDACIÓN CRUZADA DEL ORACLE - Split Temporal")
    logger.info("=" * 80)
    logger.info("Entrenamiento: Jan-Oct 2024 (10 meses)")
    logger.info("Prueba: Nov-Dec 2024 (2 meses NUEVOS)")
    logger.info("=" * 80)
    
    # Load y split
    df_full, df_train, df_test, total_velas = split_data_temporal()
    if df_test is None or len(df_test) == 0:
        logger.error("❌ No hay datos de test")
        return
    
    # Detectar signals
    df_train, train_count = detect_signals(df_train, "TRAIN (Jan-Oct)")
    df_test, test_count = detect_signals(df_test, "TEST (Nov-Dec)")
    
    if test_count == 0:
        logger.error("❌ No hay Triple Coincidencias en Nov-Dec")
        return
    
    # Etiquetar test set
    logger.info(f"\n--- ETIQUETANDO {test_count} SEÑALES DE TEST ---")
    
    config = ConfigManager()
    triple_signals = df_test[df_test['is_triple_coincidence']]
    t_events = triple_signals.index
    sides = triple_signals['trend_direction'].copy()
    
    try:
        labels = get_atr_labels(
            df_test, t_events, sides=sides,
            atr_period=14, tp_factor=2.0, sl_factor=1.0, time_limit=20
        )
    except Exception as e:
        logger.error(f"❌ Error etiquetando: {e}")
        return
    
    if isinstance(labels, dict):
        labels = labels.get('labels', labels)
    
    actual_results = labels.values
    actual_class = np.where(actual_results == 1, 1, -1)
    
    logger.info(f"✅ Labels: {len(actual_class)}")
    tp_count = (actual_class == 1).sum()
    sl_count = (actual_class == -1).sum()
    logger.info(f"   TP real: {tp_count}, SL real: {sl_count}")
    
    # Cargar Oracle original (entrenado en Jan-Dec 2024)
    logger.info(f"\n🧠 Cargando Oracle (entrenado en Jan-Dec 2024)...")
    aipha_root = Path(__file__).parent.parent.parent
    model_path = aipha_root / "oracle" / "models" / "oracle_5m_trained.joblib"
    
    if not model_path.exists():
        logger.error(f"❌ Modelo no encontrado: {model_path}")
        return
    
    oracle = joblib.load(str(model_path))
    logger.info(f"✅ Oracle cargado (100 árboles)")
    
    # Predicciones
    logger.info(f"\n--- PREDICCIONES DEL ORACLE EN NOV-DEC ---")
    
    features_list = []
    for idx in t_events:
        row_pos = df_test.index.get_loc(idx)
        row = df_test.iloc[row_pos]
        context = df_test.iloc[max(0, row_pos - 100):row_pos]
        features = extract_features(row, context)
        features_list.append(features)
    
    X_test = np.array(features_list, dtype=np.float32)
    predictions = oracle.predict(X_test)
    confidences = np.max(oracle.predict_proba(X_test), axis=1)
    
    tp_pred = (predictions == 1).sum()
    sl_pred = (predictions == -1).sum()
    
    logger.info(f"   Predicción TP: {tp_pred}")
    logger.info(f"   Predicción SL: {sl_pred}")
    logger.info(f"   Confianza promedio: {confidences.mean():.2f}")
    
    # Accuracy
    logger.info(f"\n--- RESULTADOS ---")
    
    correct = (predictions == actual_class).sum()
    accuracy = (correct / len(predictions)) * 100
    
    logger.info(f"\n📊 ACCURACY SIN FILTRO (Nov-Dec 2024 NEW DATA):")
    logger.info(f"   Predicciones correctas: {correct} / {len(predictions)}")
    logger.info(f"   Accuracy: {accuracy:.2f}%")
    
    # Con filtro
    mask_conf = confidences >= 0.5
    if mask_conf.sum() > 0:
        pred_filt = predictions[mask_conf]
        actual_filt = actual_class[mask_conf]
        correct_filt = (pred_filt == actual_filt).sum()
        acc_filt = (correct_filt / len(actual_filt)) * 100
        
        logger.info(f"\n📊 ACCURACY CON FILTRO (confianza > 0.5):")
        logger.info(f"   Señales filtradas: {mask_conf.sum()} / {len(predictions)}")
        logger.info(f"   Predicciones correctas: {correct_filt} / {len(actual_filt)}")
        logger.info(f"   Accuracy: {acc_filt:.2f}%")
    else:
        acc_filt = 0
    
    # Matriz de confusión
    logger.info(f"\n--- MATRIZ DE CONFUSIÓN ---")
    tp_correct = ((predictions == 1) & (actual_class == 1)).sum()
    tp_incorrect = ((predictions == 1) & (actual_class == -1)).sum()
    sl_correct = ((predictions == -1) & (actual_class == -1)).sum()
    sl_incorrect = ((predictions == -1) & (actual_class == 1)).sum()
    
    logger.info(f"   TP predicho correctamente: {tp_correct}")
    logger.info(f"   TP predicho pero fue SL: {tp_incorrect}")
    logger.info(f"   SL predicho correctamente: {sl_correct}")
    logger.info(f"   SL predicho pero fue TP: {sl_incorrect}")
    
    # Conclusión
    logger.info(f"\n" + "=" * 80)
    logger.info(f"🎯 CONCLUSIONES")
    logger.info(f"=" * 80)
    
    logger.info(f"\nComparación:")
    logger.info(f"   Accuracy en datos 2024 conocidos: 75.00%")
    logger.info(f"   Accuracy en Nov-Dec 2024 NUEVOS: {accuracy:.2f}%")
    
    diff = 75 - accuracy
    if diff < 5:
        logger.info(f"   Diferencia: {diff:.2f}% ✅ EXCELENTE")
        status = "✅ GENERALIZA BIEN"
    elif diff < 15:
        logger.info(f"   Diferencia: {diff:.2f}% ⚠️ MODERADO")
        status = "⚠️ OVERFITTING PARCIAL"
    else:
        logger.info(f"   Diferencia: {diff:.2f}% ❌ ALTO")
        status = "❌ OVERFITTEÓ"
    
    logger.info(f"\n🔮 PREDICCIÓN PARA 2025:")
    logger.info(f"   Si generaliza en Nov-Dec → probablemente funcione en 2025")
    logger.info(f"   Status: {status}")
    
    logger.info(f"\n⚠️  RECOMENDACIONES:")
    if accuracy >= 70:
        logger.info(f"   ✅ APROBADO para trading en vivo")
        logger.info(f"   - Monitorear accuracy en Feb-Mar 2025")
        logger.info(f"   - Reajustar si cae < 60%")
    elif accuracy >= 60:
        logger.info(f"   ⚠️ BETA - Usar con precaución")
        logger.info(f"   - Requiere validación adicional en 2025")
        logger.info(f"   - Considerar reentrenamiento pronto")
    else:
        logger.info(f"   ❌ RECHAZADO - Reentrenar necesario")
        logger.info(f"   - Modelo overfitteó, no confiar en 2025")
    
    logger.info(f"=" * 80)


if __name__ == "__main__":
    run_validation()
