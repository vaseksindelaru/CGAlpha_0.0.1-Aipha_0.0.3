"""
VALIDACIÓN ORACLE v2 EN ENERO 2026
===================================

Prueba del Oracle v2 (entrenado en 2023+2024) con datos completamente nuevos
de enero 2026.

Esto validará si el modelo realmente generalizó bien o si también falla
con datos fuera de su período de entrenamiento.

Ejecutar: python oracle/strategies/validate_oracle_jan_2026.py
"""

import pandas as pd
import numpy as np
import duckdb
import joblib
import logging
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from trading_manager.building_blocks.detectors.key_candle_detector import SignalDetector
from trading_manager.building_blocks.detectors.accumulation_zone_detector import AccumulationZoneDetector
from trading_manager.building_blocks.detectors.trend_detector import TrendDetector
from trading_manager.building_blocks.signal_combiner import SignalCombiner
from trading_manager.building_blocks.labelers.potential_capture_engine import get_atr_labels
from core.config_manager import ConfigManager

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def load_january_2026_data():
    """Carga datos de enero 2026"""
    logger.info("📥 Cargando datos de enero 2026...")
    
    db_path = "data_processor/data/aipha_data.duckdb"
    try:
        conn = duckdb.connect(db_path)
        df = conn.execute("SELECT * FROM btc_5m_data").df()
        conn.close()
        
        df['Open_Time'] = pd.to_datetime(df['Open_Time'])
        df = df.sort_values('Open_Time').set_index('Open_Time')
        
        # January 2026
        df_jan = df[(df.index.year == 2026) & (df.index.month == 1)]
        
        if len(df_jan) == 0:
            logger.warning("⚠️ No hay datos de enero 2026 en la BD")
            logger.info("📊 Datos disponibles:")
            logger.info(f"   Primer: {df.index[0]}")
            logger.info(f"   Último: {df.index[-1]}")
            return None
        
        logger.info(f"✅ {len(df_jan)} velas en enero 2026")
        logger.info(f"   Período: {df_jan.index[0]} a {df_jan.index[-1]}")
        return df_jan
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return None


def detect_signals_and_label(df):
    """Detecta Triple Coincidencias y etiqueta"""
    logger.info("🔍 Detectando Triple Coincidencias en enero 2026...")
    
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
        
        if triple_count == 0:
            logger.warning("⚠️ Sin Triple Coincidencias en enero 2026")
            return df, None, None
        
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
        import traceback
        traceback.print_exc()
        return None, None, None


def extract_features(df_row, df_context):
    """Extrae 4 características normalizadas"""
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
    """Ejecuta validación de Oracle v2 en enero 2026"""
    
    logger.info("=" * 80)
    logger.info("🔬 VALIDACIÓN ORACLE v2 EN ENERO 2026")
    logger.info("=" * 80)
    logger.info("Modelo: Entrenado en 2023+2024")
    logger.info("Datos nuevos: Enero 2026 (completamente fuera del rango de entrenamiento)")
    logger.info("=" * 80)
    
    # Load test data
    df_jan = load_january_2026_data()
    if df_jan is None:
        return
    
    # Detect & label
    df_jan, t_events, actual_class = detect_signals_and_label(df_jan)
    if df_jan is None or t_events is None:
        return
    
    if len(t_events) == 0:
        logger.warning("⚠️ No hay señales para validar")
        return
    
    # Load v2 model
    logger.info("\n🧠 Cargando modelo v2...")
    aipha_root = Path(__file__).parent.parent.parent
    v2_path = aipha_root / "oracle" / "models" / "oracle_5m_trained_v2_multiyear.joblib"
    
    if not v2_path.exists():
        logger.error(f"❌ Modelo v2 no encontrado en {v2_path}")
        return
    
    v2 = joblib.load(str(v2_path))
    logger.info(f"✅ v2 cargado correctamente")
    
    # Extract features
    logger.info("\n📊 Extrayendo características...")
    features_list = []
    for idx in t_events:
        row_pos = df_jan.index.get_loc(idx)
        row = df_jan.iloc[row_pos]
        context = df_jan.iloc[max(0, row_pos - 100):row_pos]
        features = extract_features(row, context)
        features_list.append(features)
    
    X_test = np.array(features_list, dtype=np.float32)
    logger.info(f"✅ Features: {X_test.shape}")
    
    # Predictions
    logger.info("\n" + "=" * 80)
    logger.info("⚡ PREDICCIONES EN ENERO 2026")
    logger.info("=" * 80)
    
    pred_v2 = v2.predict(X_test)
    conf_v2 = np.max(v2.predict_proba(X_test), axis=1)
    
    tp_pred = (pred_v2 == 1).sum()
    sl_pred = (pred_v2 == -1).sum()
    tp_actual = (actual_class == 1).sum()
    sl_actual = (actual_class == -1).sum()
    
    logger.info(f"\n📌 Predicciones de Oracle v2:")
    logger.info(f"   TP predichos: {tp_pred}")
    logger.info(f"   SL predichos: {sl_pred}")
    logger.info(f"   Total: {len(pred_v2)}")
    
    logger.info(f"\n📌 Resultados reales:")
    logger.info(f"   TP reales: {tp_actual}")
    logger.info(f"   SL reales: {sl_actual}")
    logger.info(f"   Total: {len(actual_class)}")
    
    # Accuracy
    correct = (pred_v2 == actual_class).sum()
    accuracy = (correct / len(pred_v2)) * 100
    
    logger.info(f"\n✅ ACCURACY EN ENERO 2026: {accuracy:.2f}%")
    logger.info(f"   Correctas: {correct}/{len(pred_v2)}")
    
    # Confusion matrix
    logger.info(f"\n--- MATRIZ DE CONFUSIÓN ---")
    tp_correct = ((pred_v2 == 1) & (actual_class == 1)).sum()
    tp_incorrect = ((pred_v2 == 1) & (actual_class == -1)).sum()
    sl_correct = ((pred_v2 == -1) & (actual_class == -1)).sum()
    sl_incorrect = ((pred_v2 == -1) & (actual_class == 1)).sum()
    
    logger.info(f"   TP predicho, TP real (correcto): {tp_correct}")
    logger.info(f"   TP predicho, SL real (falso positivo): {tp_incorrect}")
    logger.info(f"   SL predicho, SL real (correcto): {sl_correct}")
    logger.info(f"   SL predicho, TP real (falso negativo): {sl_incorrect}")
    
    # Confianza
    logger.info(f"\n--- CONFIANZA ---")
    logger.info(f"   Promedio: {conf_v2.mean():.2f}")
    logger.info(f"   Mínima: {conf_v2.min():.2f}")
    logger.info(f"   Máxima: {conf_v2.max():.2f}")
    
    # Conclusión
    logger.info(f"\n" + "=" * 80)
    logger.info(f"📌 CONCLUSIÓN - VALIDACIÓN ENERO 2026")
    logger.info(f"=" * 80)
    
    logger.info(f"\nAccuracy en Enero 2026: {accuracy:.2f}%")
    
    if accuracy >= 70:
        logger.info(f"✅ EXCELENTE - Modelo generaliza bien a datos 2026")
        logger.info(f"   El Oracle v2 ES CONFIABLE para producción")
    elif accuracy >= 65:
        logger.info(f"✅ BUENO - Modelo funciona aceptablemente en 2026")
        logger.info(f"   Posible para producción con monitoreo")
    elif accuracy >= 55:
        logger.info(f"⚠️ ACEPTABLE - Mejor que azar pero con riesgo")
        logger.info(f"   Requiere más validación antes de producción")
    else:
        logger.info(f"❌ DEFICIENTE - Modelo falló en enero 2026")
        logger.info(f"   NO LISTO para producción. Necesita reentrenamiento.")
    
    logger.info(f"\nDatos de entrenamiento: 2023+2024")
    logger.info(f"Datos de validación: Enero 2026 (13 meses DESPUÉS del entrenamiento)")
    logger.info(f"Período de validación: {df_jan.index[0].date()} a {df_jan.index[-1].date()}")
    
    logger.info(f"\n" + "=" * 80)


if __name__ == "__main__":
    run_validation()
