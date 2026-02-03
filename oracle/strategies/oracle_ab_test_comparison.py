"""
COMPARACIÓN DIRECTA A/B - ORACLE v1 vs v2
==========================================

PRUEBA DEFINITIVA:
Mismo test set (Nov-Dec 2024 - datos NUEVOS)
Mismo número de muestras
Dos modelos diferentes

v1: Entrenado en 2024 solamente (39 muestras)
v2: Entrenado en 2023+2024 (725 muestras)

¿Quién predice mejor en Nov-Dec 2024?

Ejecutar: python oracle/strategies/oracle_ab_test_comparison.py
"""

import pandas as pd
import numpy as np
import duckdb
import joblib
import logging
import sys
import os
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


def load_test_data():
    """Carga el mismo test set (Nov-Dec 2024)"""
    logger.info("📥 Cargando datos Nov-Dec 2024 (MISMO TEST SET)...")
    
    db_path = "data_processor/data/aipha_data.duckdb"
    try:
        conn = duckdb.connect(db_path)
        df = conn.execute("SELECT * FROM btc_5m_data").df()
        conn.close()
        
        df['Open_Time'] = pd.to_datetime(df['Open_Time'])
        df = df.sort_values('Open_Time').set_index('Open_Time')
        
        # Nov-Dec 2024
        df_test = df[df.index.month > 10]
        
        logger.info(f"✅ {len(df_test)} velas en Nov-Dec 2024")
        return df_test
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return None


def detect_signals_and_label(df):
    """Detecta Triple Coincidencias y etiqueta"""
    logger.info("🔍 Detectando Triple Coincidencias en test set...")
    
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
        logger.info(f"✅ {triple_count} Triple Coincidencias detectadas")
        
        # Etiquetar
        logger.info("🏷️  Etiquetando con Triple Barrier...")
        
        triple_signals = df[df['is_triple_coincidence']]
        t_events = triple_signals.index
        sides = triple_signals['trend_direction'].copy()
        
        labels = get_atr_labels(
            df, t_events, sides=sides,
            atr_period=14, tp_factor=2.0, sl_factor=1.0, time_limit=20
        )
        
        if isinstance(labels, dict):
            labels = labels.get('labels', labels)
        
        actual_class = np.where(labels.values == 1, 1, -1)
        
        logger.info(f"✅ {len(labels)} señales etiquetadas")
        logger.info(f"   TP real: {(actual_class == 1).sum()}, SL real: {(actual_class == -1).sum()}")
        
        return df, t_events, actual_class
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return None, None, None


def extract_features(df_row, df_context):
    """Extrae 4 características"""
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


def load_models():
    """Carga ambos modelos"""
    logger.info("\n🧠 Cargando modelos...")
    
    aipha_root = Path(__file__).parent.parent.parent
    
    # v1
    v1_path = aipha_root / "oracle" / "models" / "oracle_5m_trained.joblib"
    if v1_path.exists():
        v1 = joblib.load(str(v1_path))
        logger.info(f"✅ v1 cargado (entrenado en 2024 solamente)")
    else:
        logger.warning(f"⚠️ v1 no encontrado")
        v1 = None
    
    # v2
    v2_path = aipha_root / "oracle" / "models" / "oracle_5m_trained_v2_multiyear.joblib"
    if v2_path.exists():
        v2 = joblib.load(str(v2_path))
        logger.info(f"✅ v2 cargado (entrenado en 2023+2024)")
    else:
        logger.warning(f"⚠️ v2 no encontrado")
        v2 = None
    
    return v1, v2


def run_ab_test():
    """Ejecuta prueba A/B con mismo test set"""
    
    logger.info("=" * 80)
    logger.info("🆚 COMPARACIÓN DIRECTA A/B: Oracle v1 vs v2")
    logger.info("=" * 80)
    logger.info("Test Set: Nov-Dec 2024 (MISMO para ambos modelos)")
    logger.info("=" * 80)
    
    # Load test data
    df_test = load_test_data()
    if df_test is None:
        return
    
    # Detect & label
    df_test, t_events, actual_class = detect_signals_and_label(df_test)
    if df_test is None:
        return
    
    # Load models
    v1, v2 = load_models()
    if v1 is None or v2 is None:
        logger.error("❌ No se pueden cargar ambos modelos")
        return
    
    # Extract features
    logger.info("\n📊 Extrayendo características...")
    features_list = []
    for idx in t_events:
        row_pos = df_test.index.get_loc(idx)
        row = df_test.iloc[row_pos]
        context = df_test.iloc[max(0, row_pos - 100):row_pos]
        features = extract_features(row, context)
        features_list.append(features)
    
    X_test = np.array(features_list, dtype=np.float32)
    logger.info(f"✅ Features: {X_test.shape}")
    
    # COMPARACIÓN A/B
    logger.info("\n" + "=" * 80)
    logger.info("⚡ PREDICCIONES")
    logger.info("=" * 80)
    
    # v1 predictions
    logger.info("\n📌 ORACLE v1 (Entrenado en 2024 solamente):")
    pred_v1 = v1.predict(X_test)
    conf_v1 = np.max(v1.predict_proba(X_test), axis=1)
    
    tp_v1 = (pred_v1 == 1).sum()
    sl_v1 = (pred_v1 == -1).sum()
    
    logger.info(f"   Predice TP: {tp_v1}")
    logger.info(f"   Predice SL: {sl_v1}")
    logger.info(f"   Confianza promedio: {conf_v1.mean():.2f}")
    
    correct_v1 = (pred_v1 == actual_class).sum()
    acc_v1 = (correct_v1 / len(pred_v1)) * 100
    logger.info(f"   ✅ ACCURACY: {acc_v1:.2f}%")
    
    # v2 predictions
    logger.info("\n📌 ORACLE v2 (Entrenado en 2023+2024):")
    pred_v2 = v2.predict(X_test)
    conf_v2 = np.max(v2.predict_proba(X_test), axis=1)
    
    tp_v2 = (pred_v2 == 1).sum()
    sl_v2 = (pred_v2 == -1).sum()
    
    logger.info(f"   Predice TP: {tp_v2}")
    logger.info(f"   Predice SL: {sl_v2}")
    logger.info(f"   Confianza promedio: {conf_v2.mean():.2f}")
    
    correct_v2 = (pred_v2 == actual_class).sum()
    acc_v2 = (correct_v2 / len(pred_v2)) * 100
    logger.info(f"   ✅ ACCURACY: {acc_v2:.2f}%")
    
    # RESULTADO FINAL
    logger.info("\n" + "=" * 80)
    logger.info("🏆 RESULTADO FINAL")
    logger.info("=" * 80)
    
    logger.info(f"\nTest Set (Nov-Dec 2024 - Datos NUEVOS):")
    logger.info(f"   Muestras: {len(X_test)}")
    logger.info(f"   TP reales: {(actual_class == 1).sum()}")
    logger.info(f"   SL reales: {(actual_class == -1).sum()}")
    
    logger.info(f"\n📊 COMPARACIÓN ACCURACY:")
    logger.info(f"   v1 (2024 solo): {acc_v1:.2f}%")
    logger.info(f"   v2 (2023+2024): {acc_v2:.2f}%")
    
    diff = acc_v2 - acc_v1
    logger.info(f"   Diferencia: {diff:+.2f}%")
    
    if diff > 5:
        logger.info(f"   🏆 v2 GANA decisivamente")
        verdict = "✅ v2 ES MEJOR"
    elif diff > -5:
        logger.info(f"   ≈ Similar")
        verdict = "≈ EMPATE"
    else:
        logger.info(f"   v1 mejor (¡pero aún bajo!)")
        verdict = "⚠️ v1 mejor"
    
    # Matriz de confusión
    logger.info(f"\n--- MATRIZ DE CONFUSIÓN v1 ---")
    tp_correct_v1 = ((pred_v1 == 1) & (actual_class == 1)).sum()
    tp_incorrect_v1 = ((pred_v1 == 1) & (actual_class == -1)).sum()
    sl_correct_v1 = ((pred_v1 == -1) & (actual_class == -1)).sum()
    sl_incorrect_v1 = ((pred_v1 == -1) & (actual_class == 1)).sum()
    
    logger.info(f"   TP correct: {tp_correct_v1}, TP incorrect: {tp_incorrect_v1}")
    logger.info(f"   SL correct: {sl_correct_v1}, SL incorrect: {sl_incorrect_v1}")
    
    logger.info(f"\n--- MATRIZ DE CONFUSIÓN v2 ---")
    tp_correct_v2 = ((pred_v2 == 1) & (actual_class == 1)).sum()
    tp_incorrect_v2 = ((pred_v2 == 1) & (actual_class == -1)).sum()
    sl_correct_v2 = ((pred_v2 == -1) & (actual_class == -1)).sum()
    sl_incorrect_v2 = ((pred_v2 == -1) & (actual_class == 1)).sum()
    
    logger.info(f"   TP correct: {tp_correct_v2}, TP incorrect: {tp_incorrect_v2}")
    logger.info(f"   SL correct: {sl_correct_v2}, SL incorrect: {sl_incorrect_v2}")
    
    # Conclusión
    logger.info(f"\n" + "=" * 80)
    logger.info(f"📌 CONCLUSIÓN")
    logger.info(f"=" * 80)
    
    logger.info(f"\n{verdict}")
    logger.info(f"\nEntrenamiento con MÁS DATOS (2023+2024 vs 2024):")
    logger.info(f"  Resultado: {acc_v2:.2f}% vs {acc_v1:.2f}%")
    
    if acc_v2 > acc_v1:
        logger.info(f"  ✅ SÍ, más datos ayudó (+{diff:.2f}%)")
    elif acc_v2 < acc_v1:
        logger.info(f"  ⚠️ No, menos datos fue mejor ({diff:.2f}%)")
    else:
        logger.info(f"  ≈ Sin cambio significativo")
    
    logger.info(f"\n" + "=" * 80)


if __name__ == "__main__":
    run_ab_test()
