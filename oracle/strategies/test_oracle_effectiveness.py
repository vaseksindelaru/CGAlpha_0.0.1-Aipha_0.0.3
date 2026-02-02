"""
🧪 TEST DE EFECTIVIDAD DEL ORACLE
Valida si el modelo entrenado mejora las predicciones del PotentialCaptureEngine
"""

import pandas as pd
import duckdb
import numpy as np
import joblib
import logging
import sys
import os
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from trading_manager.building_blocks.detectors.key_candle_detector import SignalDetector
from trading_manager.building_blocks.detectors.accumulation_zone_detector import AccumulationZoneDetector
from trading_manager.building_blocks.detectors.trend_detector import TrendDetector
from trading_manager.building_blocks.signal_combiner import SignalCombiner
from trading_manager.building_blocks.labelers.potential_capture_engine import get_atr_labels
from oracle.building_blocks.features.feature_engineer import FeatureEngineer
from core.config_manager import ConfigManager
from core.memory_manager import MemoryManager

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_oracle_effectiveness():
    """Prueba la efectividad del Oracle comparando predicciones con/sin filtro"""
    
    print("\n" + "=" * 80)
    print("🧪 PRUEBA DE EFECTIVIDAD DEL ORACLE")
    print("=" * 80)
    
    config = ConfigManager()
    memory = MemoryManager()
    
    # 1. Cargar datos
    logger.info("\n📊 Cargando datos de DuckDB...")
    db_path = "data_processor/data/aipha_data.duckdb"
    if not os.path.exists(db_path):
        logger.error(f"❌ Base de datos no encontrada: {db_path}")
        return
    
    conn = duckdb.connect(db_path)
    df = conn.execute("SELECT * FROM btc_5m_data ORDER BY Open_Time").df()
    # Renombrar columnas a mayúsculas para consistencia con detectores
    df.columns = df.columns.str.capitalize()
    df['Open_time'] = pd.to_datetime(df['Open_time'])
    df = df.set_index('Open_time')
    
    # Asegurar que tenemos las columnas esperadas
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    for col in required_cols:
        if col not in df.columns:
            logger.error(f"❌ Columna faltante: {col}")
            return
    
    logger.info(f"✅ {len(df)} velas cargadas")
    logger.info(f"   Período: {df.index.min()} a {df.index.max()}")
    
    # 2. Ejecutar detectores
    logger.info("\n🔍 Ejecutando detectores (Triple Coincidencia)...")
    
    df = AccumulationZoneDetector.detect_zones(
        df,
        atr_period=config.get("Trading.atr_period", 14),
        atr_multiplier=1.5,
        min_zone_bars=5,
        volume_threshold_ratio=1.1,
        lookback_bars=20
    )
    
    df = TrendDetector.analyze_trend(
        df,
        lookback_period=config.get("Trading.trend_lookback", 20),
        zigzag_threshold=0.005
    )
    
    df = SignalDetector.detect_key_candles(
        df,
        volume_lookback=config.get("Trading.volume_lookback", 50),
        volume_percentile_threshold=config.get("Trading.volume_percentile_threshold", 80),
        body_percentile_threshold=config.get("Trading.body_percentile_threshold", 30),
        ema_period=config.get("Trading.ema_period", 200),
        reversal_mode=config.get("Trading.reversal_mode", True)
    )
    
    df = SignalCombiner.combine_signals(
        df,
        tolerance_bars=config.get("Trading.tolerance_bars", 8),
        min_r_squared=config.get("Trading.min_r_squared", 0.45)
    )
    
    triple_signals = df[df['is_triple_coincidence']].copy()
    logger.info(f"✅ {len(triple_signals)} Triple Coincidencias detectadas")
    
    if len(triple_signals) == 0:
        logger.warning("⚠️ No hay Triple Coincidencias en los datos")
        return
    
    # 3. Obtener etiquetas
    logger.info("\n🏷️ Etiquetando señales con Triple Barrier Method...")
    
    t_events = triple_signals.index
    sides = triple_signals['trend_direction'].copy()
    
    labels_result = get_atr_labels(
        df,
        t_events,
        sides=sides,
        atr_period=config.get("Trading.atr_period", 14),
        tp_factor=config.get("Trading.tp_factor", 2.0),
        sl_factor=config.get("Trading.sl_factor", 1.0),
        time_limit=config.get("Trading.time_limit", 20),
        return_trajectories=True
    )
    
    if isinstance(labels_result, dict):
        labels = labels_result.get('labels', labels_result)
    else:
        labels = labels_result
    
    logger.info(f"✅ {len(labels)} señales etiquetadas")
    logger.info(f"   TP: {(labels == 1).sum()}, SL: {(labels == -1).sum()}, Neutral: {(labels == 0).sum()}")
    
    # 4. Extraer features
    logger.info("\n🎯 Extrayendo características...")
    
    features_df = FeatureEngineer.extract_features(df, t_events)
    logger.info(f"✅ Features extraídas: {features_df.shape}")
    
    # 5. Cargar Oracle
    logger.info("\n🤖 Cargando modelo Oracle...")
    
    model_path = "oracle/models/oracle_5m_trained.joblib"
    if not os.path.exists(model_path):
        logger.error(f"❌ Modelo no encontrado: {model_path}")
        return
    
    oracle = joblib.load(model_path)
    logger.info(f"✅ Modelo cargado: {model_path}")
    
    # 6. Realizar predicciones
    logger.info("\n🔮 Realizando predicciones del Oracle...")
    
    try:
        predictions = oracle.predict(features_df)
        prediction_probs = oracle.predict_proba(features_df)
        logger.info(f"✅ Predicciones obtenidas: {len(predictions)}")
    except Exception as e:
        logger.error(f"❌ Error en predicciones: {e}")
        return
    
    # 7. Comparar efectividad
    logger.info("\n" + "=" * 80)
    logger.info("📊 ANÁLISIS DE EFECTIVIDAD")
    logger.info("=" * 80)
    
    # SIN FILTRO (todas las señales)
    all_correct = (predictions == labels).sum()
    all_accuracy = all_correct / len(labels) * 100
    
    logger.info(f"\n❌ SIN FILTRO ORACLE (Todas las {len(labels)} señales):")
    logger.info(f"   Predicciones correctas: {all_correct}/{len(labels)}")
    logger.info(f"   Accuracy: {all_accuracy:.2f}%")
    
    # CON FILTRO (solo señales de alta confianza: TP predicho)
    high_confidence_mask = predictions == 1
    if high_confidence_mask.sum() > 0:
        filtered_labels = labels[high_confidence_mask]
        filtered_predictions = predictions[high_confidence_mask]
        filtered_correct = (filtered_predictions == filtered_labels).sum()
        filtered_accuracy = filtered_correct / len(filtered_labels) * 100
        
        logger.info(f"\n✅ CON FILTRO ORACLE (Señales predichas como TP):")
        logger.info(f"   Señales filtradas: {high_confidence_mask.sum()}/{len(labels)} ({high_confidence_mask.sum()/len(labels)*100:.1f}%)")
        logger.info(f"   Predicciones correctas: {filtered_correct}/{len(filtered_labels)}")
        logger.info(f"   Accuracy en filtradas: {filtered_accuracy:.2f}%")
        
        # Ganancia de efectividad
        improvement = filtered_accuracy - all_accuracy
        logger.info(f"\n🎯 MEJORA CON FILTRO: {improvement:+.2f}%")
        
        if filtered_accuracy > all_accuracy:
            logger.info("   ✅ El Oracle MEJORA la efectividad")
        else:
            logger.info("   ⚠️ El Oracle NO mejora en este dataset")
    else:
        logger.info(f"\n⚠️ El Oracle no predijo ninguna señal como TP")
    
    # CON FILTRO (solo señales de alta confianza: cualquier predicción)
    high_prob_threshold = 0.6
    high_prob_mask = prediction_probs.max(axis=1) > high_prob_threshold
    
    if high_prob_mask.sum() > 0:
        filtered_labels_prob = labels[high_prob_mask]
        filtered_predictions_prob = predictions[high_prob_mask]
        filtered_correct_prob = (filtered_predictions_prob == filtered_labels_prob).sum()
        filtered_accuracy_prob = filtered_correct_prob / len(filtered_labels_prob) * 100
        
        logger.info(f"\n✅ CON FILTRO DE CONFIANZA (prob > {high_prob_threshold}):")
        logger.info(f"   Señales filtradas: {high_prob_mask.sum()}/{len(labels)} ({high_prob_mask.sum()/len(labels)*100:.1f}%)")
        logger.info(f"   Predicciones correctas: {filtered_correct_prob}/{len(filtered_labels_prob)}")
        logger.info(f"   Accuracy en confiables: {filtered_accuracy_prob:.2f}%")
        
        improvement_prob = filtered_accuracy_prob - all_accuracy
        logger.info(f"\n🎯 MEJORA CON CONFIANZA: {improvement_prob:+.2f}%")
    
    # 8. Matriz de confusión detallada
    logger.info(f"\n" + "=" * 80)
    logger.info("📋 MATRIZ DE CONFUSIÓN DETALLADA (SIN FILTRO)")
    logger.info("=" * 80)
    
    from sklearn.metrics import confusion_matrix, classification_report
    
    cm = confusion_matrix(labels, predictions)
    logger.info(f"\nMatriz de Confusión:\n{cm}")
    logger.info(f"\nReporte de Clasificación:\n{classification_report(labels, predictions, target_names=['SL (-1)', 'TP (1)'])}")
    
    # 9. Registrar resultados
    logger.info(f"\n💾 Registrando métricas...")
    
    memory.record_metric(
        component="Oracle",
        metric_name="test_accuracy_no_filter",
        value=float(all_accuracy / 100.0),
        metadata={
            "signals": int(len(labels)),
            "correct": int(all_correct),
            "timeframe": "5m"
        }
    )
    
    if high_confidence_mask.sum() > 0:
        memory.record_metric(
            component="Oracle",
            metric_name="test_accuracy_with_filter",
            value=float(filtered_accuracy / 100.0),
            metadata={
                "signals": int(len(labels)),
                "filtered": int(high_confidence_mask.sum()),
                "correct": int(filtered_correct),
                "timeframe": "5m"
            }
        )
    
    logger.info("✅ Métricas registradas")
    
    # 10. Resumen final
    logger.info(f"\n" + "=" * 80)
    logger.info("✅ PRUEBA COMPLETADA EXITOSAMENTE")
    logger.info("=" * 80)
    
    summary = {
        "Total Señales": len(labels),
        "Accuracy SIN filtro": f"{all_accuracy:.2f}%",
        "Accuracy CON filtro": f"{filtered_accuracy:.2f}%" if high_confidence_mask.sum() > 0 else "N/A",
        "Señales filtradas": f"{high_confidence_mask.sum()}/{len(labels)}" if high_confidence_mask.sum() > 0 else "0/0",
        "Mejora": f"{improvement:+.2f}%" if high_confidence_mask.sum() > 0 else "N/A"
    }
    
    for key, value in summary.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    test_oracle_effectiveness()
