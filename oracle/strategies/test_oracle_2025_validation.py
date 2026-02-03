"""
VALIDACIÓN DEL ORACLE EN DATOS 2025 (COMPLETAMENTE NUEVOS)
===========================================================

Propósito: Probar si el Oracle entrenado en 2024 sigue funcionando en datos de 2025
que NUNCA vio durante el entrenamiento.

Esto es la prueba REAL de si el modelo generalizó o solo memorizó patrones de 2024.

Ejecutar: python oracle/strategies/test_oracle_2025_validation.py
Fecha: 3 de Febrero de 2026
"""

import pandas as pd
import numpy as np
import duckdb
import joblib
import logging
import sys
import os
from datetime import date, timedelta
from pathlib import Path

# Setup path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from trading_manager.building_blocks.detectors.key_candle_detector import SignalDetector
from trading_manager.building_blocks.detectors.accumulation_zone_detector import AccumulationZoneDetector
from trading_manager.building_blocks.detectors.trend_detector import TrendDetector
from trading_manager.building_blocks.signal_combiner import SignalCombiner
from trading_manager.building_blocks.labelers.potential_capture_engine import get_atr_labels
from data_processor.data_system import BinanceKlinesFetcher, KlinesDataRequestTemplate, save_results_to_duckdb, ApiClient
from core.config_manager import ConfigManager

# Logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def download_2025_data():
    """Descarga datos de 2025 (Jan 1 - Jan 31 de 2025)"""
    logger.info("=" * 80)
    logger.info("DESCARGANDO DATOS DE 2025 (Datos nuevos para validación)")
    logger.info("=" * 80)
    
    try:
        client = ApiClient(timeout=60)
        fetcher = BinanceKlinesFetcher(
            client,
            download_dir="data_processor/data/test_downloaded_data"
        )
        
        # Descargar enero de 2025
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 31)
        
        template = KlinesDataRequestTemplate(
            name="BTC_5m_Jan_2025",
            symbol="BTCUSDT",
            interval="5m",
            start_date=start_date,
            end_date=end_date,
            description="Datos de 2025 para validación del Oracle"
        )
        
        df = fetcher.fetch_klines_by_template(template)
        
        if df is not None and not df.empty:
            logger.info(f"✅ {len(df)} velas de 5m descargadas para 2025")
            return df
        else:
            logger.error("❌ No se pudieron descargar datos de 2025")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error descargando datos 2025: {e}")
        return None


def detect_triple_coincidences_2025(df):
    """Detecta Triple Coincidencias en datos 2025"""
    logger.info("\n" + "=" * 80)
    logger.info("DETECTANDO TRIPLE COINCIDENCIAS EN DATOS 2025")
    logger.info("=" * 80)
    
    config = ConfigManager()
    
    try:
        # 1. Zonas de Acumulación
        logger.info("1️⃣  Detectando zonas de acumulación...")
        df = AccumulationZoneDetector.detect_zones(
            df,
            atr_period=config.get("Trading.atr_period", 14),
            atr_multiplier=1.5,
            min_zone_bars=5,
            volume_threshold_ratio=1.1,
            lookback_bars=20
        )
        zone_count = df['in_accumulation_zone'].sum()
        logger.info(f"   ✅ {zone_count} barras en zona de acumulación")
        
        # 2. Tendencia
        logger.info("2️⃣  Detectando tendencia...")
        df = TrendDetector.analyze_trend(
            df,
            lookback_period=config.get("Trading.trend_lookback", 20),
            zigzag_threshold=0.005
        )
        avg_r_squared = df['trend_r_squared'].mean()
        logger.info(f"   ✅ R² promedio: {avg_r_squared:.3f}")
        
        # 3. Velas Clave
        logger.info("3️⃣  Detectando velas clave...")
        df = SignalDetector.detect_key_candles(
            df,
            volume_lookback=config.get("Trading.volume_lookback", 50),
            volume_percentile_threshold=config.get("Trading.volume_percentile_threshold", 80),
            body_percentile_threshold=config.get("Trading.body_percentile_threshold", 30),
            ema_period=config.get("Trading.ema_period", 200),
            reversal_mode=config.get("Trading.reversal_mode", True)
        )
        key_candle_count = df['is_key_candle'].sum()
        logger.info(f"   ✅ {key_candle_count} velas clave detectadas")
        
        # 4. Combinar (Triple Coincidencia)
        logger.info("4️⃣  Combinando señales (Triple Coincidencia)...")
        df = SignalCombiner.combine_signals(
            df,
            tolerance_bars=config.get("Trading.tolerance_bars", 8),
            min_r_squared=config.get("Trading.min_r_squared", 0.45)
        )
        triple_count = df['is_triple_coincidence'].sum()
        logger.info(f"✅ {triple_count} TRIPLE COINCIDENCIAS detectadas en 2025")
        
        return df, triple_count
        
    except Exception as e:
        logger.error(f"❌ Error en detección: {e}")
        return None, 0


def load_oracle_model():
    """Carga el modelo Oracle entrenado en 2024"""
    logger.info("\n🧠 Cargando modelo Oracle entrenado en 2024...")
    
    aipha_root = Path(__file__).parent.parent.parent
    model_path = aipha_root / "oracle" / "models" / "oracle_5m_trained.joblib"
    
    if model_path.exists():
        oracle = joblib.load(str(model_path))
        logger.info(f"✅ Oracle cargado desde: {model_path}")
        logger.info(f"   Tipo: {type(oracle).__name__}")
        logger.info(f"   Árboles: {oracle.n_estimators}")
        return oracle
    else:
        logger.error(f"❌ Modelo no encontrado: {model_path}")
        return None


def extract_features_for_oracle(df_row, df_context):
    """Extrae 4 características normalizadas para Oracle"""
    try:
        open_price = df_row['Open']
        close_price = df_row['Close']
        high = df_row['High']
        low = df_row['Low']
        
        # 1. Body percentage
        total_range = high - low
        body = abs(close_price - open_price)
        body_percentage = (body / total_range) if total_range > 0 else 0
        
        # 2. Volume ratio
        vol_lookback = 50
        avg_volume = df_context.iloc[-vol_lookback:]['Volume'].mean() if len(df_context) >= vol_lookback else df_context['Volume'].mean()
        volume_ratio = df_row['Volume'] / avg_volume if avg_volume > 0 else 1.0
        
        # 3. Relative range
        relative_range = total_range / open_price if open_price > 0 else 0
        
        # 4. Hour of day
        hour_of_day = df_row.name.hour / 24.0
        
        features = np.array([
            np.clip(body_percentage, 0, 1),
            np.clip(volume_ratio / 10, 0, 1),
            np.clip(relative_range * 100, 0, 1),
            hour_of_day
        ], dtype=np.float32)
        
        return features
    except:
        return np.zeros(4, dtype=np.float32)


def run_oracle_validation():
    """Ejecuta validación completa del Oracle en 2025"""
    
    logger.info("\n" + "=" * 80)
    logger.info("🔬 VALIDACIÓN DEL ORACLE EN DATOS 2025 (COMPLETAMENTE NUEVOS)")
    logger.info("=" * 80)
    logger.info(f"Objetivo: Probar si el Oracle generaliza más allá de datos 2024")
    logger.info(f"Fecha prueba: {date.today()}")
    logger.info("=" * 80)
    
    # Paso 1: Descargar datos 2025
    df_2025 = download_2025_data()
    if df_2025 is None or df_2025.empty:
        logger.error("❌ No hay datos para validar")
        return
    
    df_2025['Open_Time'] = pd.to_datetime(df_2025['Open_Time'])
    df_2025 = df_2025.sort_values('Open_Time').set_index('Open_Time')
    logger.info(f"✅ Rango de datos: {df_2025.index.min()} a {df_2025.index.max()}")
    logger.info(f"   Total velas: {len(df_2025)}")
    
    # Paso 2: Detectar Triple Coincidencias en 2025
    df_2025, triple_count = detect_triple_coincidences_2025(df_2025)
    if df_2025 is None or triple_count == 0:
        logger.error("❌ No se detectaron Triple Coincidencias")
        return
    
    # Paso 3: Etiquetar con Triple Barrier
    logger.info(f"\n--- ETIQUETANDO {triple_count} SEÑALES CON TRIPLE BARRIER METHOD ---")
    
    config = ConfigManager()
    triple_signals = df_2025[df_2025['is_triple_coincidence']]
    t_events = triple_signals.index
    sides = triple_signals['trend_direction'].copy()
    
    try:
        labels = get_atr_labels(
            df_2025,
            t_events,
            sides=sides,
            atr_period=config.get("Trading.atr_period", 14),
            tp_factor=config.get("Trading.tp_factor", 2.0),
            sl_factor=config.get("Trading.sl_factor", 1.0),
            time_limit=config.get("Trading.time_limit", 20)
        )
    except Exception as e:
        logger.error(f"❌ Error en etiquetado: {e}")
        return
    
    # Manejar dict o Series
    if isinstance(labels, dict):
        labels = labels.get('labels', labels)
    
    actual_results = labels.values
    logger.info(f"✅ {len(labels)} señales etiquetadas")
    
    # Paso 4: Cargar Oracle
    oracle = load_oracle_model()
    if oracle is None:
        logger.error("❌ No se puede continuar sin Oracle")
        return
    
    # Paso 5: Hacer predicciones con Oracle
    logger.info(f"\n--- EJECUTANDO PREDICCIONES DEL ORACLE EN {len(t_events)} SEÑALES 2025 ---")
    
    features_list = []
    for idx in t_events:
        row_pos = df_2025.index.get_loc(idx)
        row = df_2025.iloc[row_pos]
        context = df_2025.iloc[max(0, row_pos - 100):row_pos]
        features = extract_features_for_oracle(row, context)
        features_list.append(features)
    
    X_2025 = np.array(features_list, dtype=np.float32)
    
    predictions_2025 = oracle.predict(X_2025)
    confidences_2025 = np.max(oracle.predict_proba(X_2025), axis=1)
    
    tp_predicted = (predictions_2025 == 1).sum()
    sl_predicted = (predictions_2025 == -1).sum()
    
    logger.info(f"✅ Oracle predicciones en 2025:")
    logger.info(f"   Predichas como TP: {tp_predicted} / {len(t_events)}")
    logger.info(f"   Predichas como SL: {sl_predicted} / {len(t_events)}")
    logger.info(f"   Confianza promedio: {confidences_2025.mean():.2f}")
    
    # Paso 6: Calcular accuracy
    logger.info(f"\n--- COMPARANDO PREDICCIONES VS RESULTADOS REALES ---")
    
    # Convertir actual results a clase (1 para TP, -1 para SL, 0 para neutral)
    actual_class = np.where(actual_results == 1, 1, -1)
    
    # Accuracy general
    correct = (predictions_2025 == actual_class).sum()
    accuracy_general = (correct / len(predictions_2025)) * 100
    
    logger.info(f"\n📊 ACCURACY SIN FILTRO:")
    logger.info(f"   Predicciones correctas: {correct} / {len(predictions_2025)}")
    logger.info(f"   Accuracy: {accuracy_general:.2f}%")
    
    # Accuracy con filtro de confianza
    mask_confident = confidences_2025 >= 0.5
    if mask_confident.sum() > 0:
        predictions_filtered = predictions_2025[mask_confident]
        actual_filtered = actual_class[mask_confident]
        correct_filtered = (predictions_filtered == actual_filtered).sum()
        accuracy_filtered = (correct_filtered / len(actual_filtered)) * 100
        
        logger.info(f"\n📊 ACCURACY CON FILTRO (confianza > 0.5):")
        logger.info(f"   Señales filtradas: {mask_confident.sum()} / {len(predictions_2025)}")
        logger.info(f"   Predicciones correctas: {correct_filtered} / {len(actual_filtered)}")
        logger.info(f"   Accuracy: {accuracy_filtered:.2f}%")
    else:
        accuracy_filtered = 0
    
    # Métricas detalladas
    logger.info(f"\n--- MÉTRICAS DETALLADAS ---")
    
    # Confusion matrix
    tp_correct = ((predictions_2025 == 1) & (actual_class == 1)).sum()
    tp_incorrect = ((predictions_2025 == 1) & (actual_class == -1)).sum()
    sl_correct = ((predictions_2025 == -1) & (actual_class == -1)).sum()
    sl_incorrect = ((predictions_2025 == -1) & (actual_class == 1)).sum()
    
    logger.info(f"Matriz de Confusión:")
    logger.info(f"  Predicha TP, Real TP (True Positive): {tp_correct}")
    logger.info(f"  Predicha TP, Real SL (False Positive): {tp_incorrect}")
    logger.info(f"  Predicha SL, Real SL (True Negative): {sl_correct}")
    logger.info(f"  Predicha SL, Real TP (False Negative): {sl_incorrect}")
    
    if (tp_correct + tp_incorrect) > 0:
        precision_tp = (tp_correct / (tp_correct + tp_incorrect)) * 100
        logger.info(f"  Precisión (cuando predice TP): {precision_tp:.2f}%")
    
    if (tp_correct + sl_incorrect) > 0:
        recall_tp = (tp_correct / (tp_correct + sl_incorrect)) * 100
        logger.info(f"  Recall (detectar TP real): {recall_tp:.2f}%")
    
    # Resultados finales
    logger.info(f"\n" + "=" * 80)
    logger.info(f"📋 RESULTADOS FINALES - VALIDACIÓN 2025")
    logger.info(f"=" * 80)
    
    logger.info(f"\n🎯 CONCLUSIÓN:")
    if accuracy_general >= 70:
        logger.info(f"✅ GENERALIZÓ BIEN - El Oracle mantiene accuracy > 70% en datos 2025")
        logger.info(f"   El modelo NO overfitteó, funciona en datos nuevos")
    elif accuracy_general >= 60:
        logger.info(f"⚠️  RENDIMIENTO MODERADO - Accuracy entre 60-70%")
        logger.info(f"   Funciona pero probablemente overfitteó parcialmente")
    else:
        logger.info(f"❌ FALLÓ - Accuracy < 60%")
        logger.info(f"   El modelo overfitteó completamente en 2024")
    
    logger.info(f"\n📊 Comparación 2024 vs 2025:")
    logger.info(f"   2024 (Entrenamiento + Test): 75.00% accuracy")
    logger.info(f"   2025 (Datos completamente nuevos): {accuracy_general:.2f}% accuracy")
    
    if accuracy_general >= 70:
        logger.info(f"   ✅ Diferencia: -5% o menos (ACEPTABLE)")
    elif accuracy_general >= 60:
        logger.info(f"   ⚠️  Diferencia: 5-15% (PREOCUPANTE)")
    else:
        logger.info(f"   ❌ Diferencia: > 15% (NO CONFIABLE)")
    
    logger.info(f"\n" + "=" * 80)
    logger.info(f"Status para Live Trading: ", end="")
    
    if accuracy_general >= 65:
        logger.info(f"✅ APROBADO (Con monitoreo)")
    else:
        logger.info(f"❌ RECHAZADO (Necesita reentrenamiento)")
    
    logger.info(f"=" * 80)


if __name__ == "__main__":
    run_oracle_validation()
