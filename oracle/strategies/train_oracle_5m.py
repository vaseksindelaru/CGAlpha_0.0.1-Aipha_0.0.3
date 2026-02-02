"""
Entrenamiento de Oracle con datos de 5 minutos - Cantidad MÍNIMA RECOMENDADA
Genera ~300+ muestras etiquetadas de 6 meses de datos BTCUSDT 5m
"""

import pandas as pd
import duckdb
import logging
import sys
import os
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from datetime import date

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from trading_manager.building_blocks.detectors.key_candle_detector import SignalDetector
from trading_manager.building_blocks.detectors.accumulation_zone_detector import AccumulationZoneDetector
from trading_manager.building_blocks.detectors.trend_detector import TrendDetector
from trading_manager.building_blocks.signal_combiner import SignalCombiner
from trading_manager.building_blocks.labelers.potential_capture_engine import get_atr_labels
from oracle.building_blocks.features.feature_engineer import FeatureEngineer
from oracle.building_blocks.oracles.oracle_engine import OracleEngine
from data_processor.data_system import BinanceKlinesFetcher, KlinesDataRequestTemplate, save_results_to_duckdb, ApiClient
from core.config_manager import ConfigManager
from core.memory_manager import MemoryManager

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def ensure_5m_extended_data(db_path: str):
    """Asegura que existan datos de 5 minutos extendidos (12 meses) para entrenamiento."""
    table_name = "btc_5m_data"
    
    try:
        conn = duckdb.connect(db_path)
        result = conn.execute(f"SELECT COUNT(*) as count FROM {table_name}").fetchall()
        conn.close()
        
        if result[0][0] > 100000:  # Si hay más de 100k velas (12 meses)
            logger.info(f"✅ Tabla '{table_name}' ya existe con {result[0][0]} velas. Usando datos existentes.")
            return table_name
    except Exception:
        pass
    
    logger.info("📥 Descargando 12 meses de datos de 5 minutos desde Binance...")
    logger.info("   Esto puede tomar 10-15 minutos. Por favor, espera...")
    
    try:
        client = ApiClient(timeout=120)
        fetcher = BinanceKlinesFetcher(
            client, 
            download_dir="data_processor/data/test_downloaded_data"
        )
        
        # Descargar 12 meses en 5m (Enero-Diciembre 2024)
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        template = KlinesDataRequestTemplate(
            name="BTC_5m_12M_2024",
            symbol="BTCUSDT",
            interval="5m",
            start_date=start_date,
            end_date=end_date,
            description="12 meses de datos 5m para entrenar Oracle robusto"
        )
        
        df = fetcher.fetch_klines_by_template(template)
        
        if df is not None and not df.empty:
            logger.info(f"✅ Éxito: {len(df)} velas descargadas (12 meses).")
            save_results_to_duckdb(df, table_name, db_path=db_path)
            logger.info(f"✅ Datos guardados en tabla '{table_name}'.")
            return table_name
        else:
            logger.error("❌ No se pudieron descargar los datos.")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error descargando datos: {e}")
        return None

def train_oracle_5m():
    """Entrena Oracle con Triple Coincidencia en 5 minutos (cantidad mínima recomendada)."""
    
    config = ConfigManager()
    memory = MemoryManager()
    
    db_path = "data_processor/data/aipha_data.duckdb"
    model_path = "oracle/models/oracle_5m_trained.joblib"
    
    logger.info("=" * 70)
    logger.info("ENTRENAMIENTO DE ORACLE - DATOS 5M (CANTIDAD MÍNIMA RECOMENDADA)")
    logger.info("=" * 70)
    
    # 1. Asegurar datos extendidos
    table_name = ensure_5m_extended_data(db_path)
    if table_name is None:
        logger.error("❌ No se puede proceder sin datos.")
        return
    
    # 2. Carga de Datos
    logger.info("\n📊 Cargando datos de DuckDB...")
    if not os.path.exists(db_path):
        logger.error(f"❌ Base de datos no encontrada en {db_path}")
        return

    try:
        conn = duckdb.connect(db_path)
        df = conn.execute(f"SELECT * FROM {table_name}").df()
        conn.close()
        
        df['Open_Time'] = pd.to_datetime(df['Open_Time'])
        df = df.sort_values('Open_Time').set_index('Open_Time')
        
        logger.info(f"✅ Datos cargados: {len(df)} velas de 5m")
        logger.info(f"   Período: {df.index.min()} a {df.index.max()}")
    except Exception as e:
        logger.error(f"❌ Error al cargar datos: {e}")
        return

    # 3. Ejecutar los 3 Detectores (Triple Coincidencia)
    logger.info("\n🔍 Ejecutando Detectores (Triple Coincidencia en 5m)...")
    
    try:
        # Acumulación
        df = AccumulationZoneDetector.detect_zones(
            df,
            atr_period=config.get("Trading.atr_period", 14),
            atr_multiplier=1.5,
            min_zone_bars=5,
            volume_threshold_ratio=1.1,
            lookback_bars=20
        )
        logger.info(f"   ✅ Zonas detectadas: {df['in_accumulation_zone'].sum()} barras")
        
        # Tendencia
        df = TrendDetector.analyze_trend(
            df,
            lookback_period=config.get("Trading.trend_lookback", 20),
            zigzag_threshold=0.005
        )
        logger.info(f"   ✅ R² promedio: {df['trend_r_squared'].mean():.3f}")
        
        # Velas Clave
        df = SignalDetector.detect_key_candles(
            df, 
            volume_lookback=config.get("Trading.volume_lookback", 20),
            volume_percentile_threshold=config.get("Trading.volume_percentile_threshold", 90),
            body_percentile_threshold=config.get("Trading.body_percentile_threshold", 30),
            ema_period=config.get("Trading.ema_period", 200),
            reversal_mode=config.get("Trading.reversal_mode", True)
        )
        logger.info(f"   ✅ Velas clave: {df['is_key_candle'].sum()} detectadas")
        
        # Combinar (TRIPLE COINCIDENCIA)
        df = SignalCombiner.combine_signals(
            df,
            tolerance_bars=config.get("Trading.tolerance_bars", 8),
            min_r_squared=config.get("Trading.min_r_squared", 0.45)
        )
        triple_count = df['is_triple_coincidence'].sum()
        logger.info(f"   ✅ TRIPLE COINCIDENCIAS: {triple_count} señales")
        
    except Exception as e:
        logger.error(f"❌ Error en detectores: {e}")
        return

    # 4. Etiquetado (Triple Barrier - ATR dinámico)
    logger.info("\n🏷️  Etiquetando con Triple Barrier Method...")
    
    triple_signals = df[df['is_triple_coincidence']]
    
    if len(triple_signals) == 0:
        logger.error("❌ No se detectaron Triple Coincidencias.")
        return

    t_events = triple_signals.index
    sides = triple_signals['trend_direction'].copy()
    
    try:
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
        
        # Extraer labels del dict retornado
        if isinstance(labels_result, dict):
            labels = labels_result['labels']
        else:
            labels = labels_result
            
        logger.info(f"✅ Etiquetado completado: {len(labels)} muestras")
        
        # Estadísticas de etiquetas
        counts = labels.value_counts().sort_index()
        logger.info(f"   - TP (1): {counts.get(1, 0)} muestras (Ganadores)")
        logger.info(f"   - SL (-1): {counts.get(-1, 0)} muestras (Perdedores)")
        logger.info(f"   - Neutral (0): {counts.get(0, 0)} muestras (Timeout)")
        
    except Exception as e:
        logger.error(f"❌ Error en etiquetado: {e}")
        return

    # 5. Extracción de Features
    logger.info("\n🎯 Extrayendo características (features)...")
    
    try:
        features = FeatureEngineer.extract_features(df, t_events)
        logger.info(f"✅ Features extraídas: {features.shape}")
        logger.info(f"   Columnas: {list(features.columns)}")
    except Exception as e:
        logger.error(f"❌ Error extrayendo features: {e}")
        return

    # 6. Preparar dataset de entrenamiento
    logger.info("\n📦 Preparando dataset...")
    
    data = features.copy()
    data['target'] = labels
    
    # Filtrar neutrales (0) para entrenar solo TP vs SL
    data_filtered = data[data['target'] != 0].copy()
    
    logger.info(f"✅ Dataset preparado:")
    logger.info(f"   Total (con neutrales): {len(data)} muestras")
    logger.info(f"   Filtered (TP vs SL): {len(data_filtered)} muestras")
    logger.info(f"   Relación features/muestras: {len(data_filtered)} / {data_filtered.shape[1]-1} = {len(data_filtered) / (data_filtered.shape[1]-1):.1f}x")
    
    if len(data_filtered) < 30:
        logger.warning(f"⚠️  Solo {len(data_filtered)} muestras TP/SL. Mínimo recomendado: 100.")
        logger.warning("   Usando dataset completo (incluyendo neutrales).")
        data_filtered = data.copy()
    
    X = data_filtered.drop(columns=['target'])
    y = data_filtered['target']
    
    # 7. Split Train/Test
    logger.info("\n🔀 Dividiendo datos (80% train, 20% test)...")
    
    test_size = max(0.2, 10 / len(X))  # Mínimo 10 muestras de test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )
    
    logger.info(f"✅ Split realizado:")
    logger.info(f"   Train: {len(X_train)} muestras ({100*len(X_train)/len(X):.1f}%)")
    logger.info(f"   Test: {len(X_test)} muestras ({100*len(X_test)/len(X):.1f}%)")
    
    # 8. Entrenamiento de Oracle
    logger.info("\n🤖 Entrenando Oracle (Random Forest, 100 árboles)...")
    
    try:
        oracle = OracleEngine()
        oracle.train(X_train, y_train)
        logger.info("✅ Entrenamiento completado.")
    except Exception as e:
        logger.error(f"❌ Error en entrenamiento: {e}")
        return

    # 9. Evaluación
    logger.info("\n📊 EVALUACIÓN DEL MODELO")
    logger.info("=" * 70)
    
    try:
        y_pred = oracle.predict(X_test)
        y_pred_proba = oracle.predict_proba(X_test)
        
        accuracy = accuracy_score(y_test, y_pred)
        logger.info(f"✅ Accuracy: {accuracy:.2%}")
        
        logger.info("\n📋 Reporte de Clasificación:")
        print(classification_report(y_test, y_pred))
        
        logger.info("\n📊 Matriz de Confusión:")
        cm = confusion_matrix(y_test, y_pred)
        print(cm)
        
    except Exception as e:
        logger.error(f"⚠️  Error en evaluación: {e}")

    # 10. Guardado del Modelo
    logger.info("\n💾 Guardando modelo...")
    
    try:
        oracle.save(model_path)
        logger.info(f"✅ Modelo guardado en: {model_path}")
        logger.info(f"   Tamaño: {os.path.getsize(model_path) / 1024:.1f} KB")
    except Exception as e:
        logger.error(f"❌ Error guardando modelo: {e}")
        return

    # 11. Registro en memoria
    logger.info("\n📝 Registrando métricas en memoria del sistema...")
    
    try:
        memory.record_metric(
            component="Oracle",
            metric_name="training_complete",
            value=1.0,
            metadata={
                "timeframe": "5m",
                "data_samples": len(X_train),
                "accuracy": accuracy,
                "test_samples": len(X_test),
                "features": X.shape[1],
                "model_path": model_path,
                "period": "Enero-Junio 2024"
            }
        )
        logger.info("✅ Métrica registrada.")
    except Exception as e:
        logger.warning(f"⚠️  No se pudo registrar métrica: {e}")

    logger.info("\n" + "=" * 70)
    logger.info("✅ ENTRENAMIENTO DE ORACLE COMPLETADO")
    logger.info("=" * 70)
    logger.info(f"\n📌 Próximos pasos:")
    logger.info(f"   1. Usar el modelo para predicciones:")
    logger.info(f"      python3 oracle/strategies/proof_strategy_v2.py")
    logger.info(f"   2. Modelo guardado en: {model_path}")
    logger.info(f"   3. Accuracy alcanzada: {accuracy:.2%}")
    logger.info(f"   4. Muestras de entrenamiento: {len(X_train)}")

if __name__ == "__main__":
    train_oracle_5m()
