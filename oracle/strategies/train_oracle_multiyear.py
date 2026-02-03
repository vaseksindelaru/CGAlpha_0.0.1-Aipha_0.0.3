"""
ENTRENAMIENTO ORACLE v2 - MÚLTIPLES AÑOS (2023-2024)
====================================================

Objetivo: Entrenar con 24 meses en lugar de 12
- Datos 2023: Jan-Dec (12 meses)
- Datos 2024: Jan-Dec (12 meses)
= 24 meses total con VARIEDAD de contextos de mercado

Esto reduce overfitting porque el modelo ve:
✅ 2023: Un año completo diferente
✅ 2024: Otro año completamente diferente
✅ Mix de volatilidades, tendencias, comportamientos

Ejecutar: python oracle/strategies/train_oracle_multiear.py
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
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from trading_manager.building_blocks.detectors.key_candle_detector import SignalDetector
from trading_manager.building_blocks.detectors.accumulation_zone_detector import AccumulationZoneDetector
from trading_manager.building_blocks.detectors.trend_detector import TrendDetector
from trading_manager.building_blocks.signal_combiner import SignalCombiner
from trading_manager.building_blocks.labelers.potential_capture_engine import get_atr_labels
from data_processor.data_system import BinanceKlinesFetcher, KlinesDataRequestTemplate, save_results_to_duckdb, ApiClient
from core.config_manager import ConfigManager
from core.memory_manager import MemoryManager

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def download_year_data(year, force=False):
    """Descarga datos de un año completo"""
    logger.info(f"\n{'='*80}")
    logger.info(f"📥 DESCARGANDO {year} (12 meses)")
    logger.info(f"{'='*80}")
    
    try:
        client = ApiClient(timeout=60)
        fetcher = BinanceKlinesFetcher(
            client,
            download_dir="data_processor/data/test_downloaded_data"
        )
        
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        
        template = KlinesDataRequestTemplate(
            name=f"BTC_5m_{year}",
            symbol="BTCUSDT",
            interval="5m",
            start_date=start_date,
            end_date=end_date,
            description=f"Datos de {year} para entrenamiento Oracle"
        )
        
        df = fetcher.fetch_klines_by_template(template)
        
        if df is not None and not df.empty:
            logger.info(f"✅ {len(df)} velas de {year} descargadas")
            return df
        else:
            logger.warning(f"⚠️ No se pudieron descargar datos de {year}")
            return None
            
    except Exception as e:
        logger.warning(f"⚠️ Error descargando {year}: {e}")
        return None


def load_existing_data(year):
    """Carga datos de DB si existen"""
    logger.info(f"Buscando datos de {year} en DB...")
    
    db_path = "data_processor/data/aipha_data.duckdb"
    try:
        conn = duckdb.connect(db_path)
        
        # Buscar tabla para ese año
        result = conn.execute(
            f"""
            SELECT * FROM btc_5m_data 
            WHERE EXTRACT(YEAR FROM "Open_Time") = {year}
            """
        ).df()
        conn.close()
        
        if not result.empty:
            logger.info(f"✅ {len(result)} velas de {year} encontradas en DB")
            return result
        else:
            logger.warning(f"⚠️ No hay datos de {year} en DB")
            return None
    except Exception as e:
        logger.warning(f"⚠️ Error: {e}")
        return None


def get_year_data(year):
    """Obtiene datos de un año (desde DB o descarga)"""
    # Primero intenta desde DB
    df = load_existing_data(year)
    
    if df is not None and len(df) > 100:
        return df
    
    # Si no, intenta descargar
    logger.warning(f"   Intentando descargar {year}...")
    df = download_year_data(year)
    
    return df


def detect_signals(df, year, name=""):
    """Detecta Triple Coincidencias en un año"""
    logger.info(f"\n--- Detectando Triple Coincidencias en {year} {name} ---")
    
    config = ConfigManager()
    
    try:
        df['Open_Time'] = pd.to_datetime(df['Open_Time'])
        df = df.sort_values('Open_Time').set_index('Open_Time')
        
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


def run_multiyear_training():
    """Entrena Oracle con datos de múltiples años"""
    
    logger.info("=" * 80)
    logger.info("🚀 ENTRENAMIENTO ORACLE v2 - MÚLTIPLES AÑOS")
    logger.info("=" * 80)
    logger.info("Objetivo: Reducir overfitting con 24 meses de datos")
    logger.info("=" * 80)
    
    memory = MemoryManager()
    
    # Descargar/cargar datos
    logger.info("\n📥 RECOLECTANDO DATOS...")
    
    data_2023 = get_year_data(2023)
    data_2024 = get_year_data(2024)
    
    if data_2023 is None or data_2023.empty:
        logger.warning("⚠️ 2023 no disponible, entrenando solo con 2024")
        df_all = data_2024
        years = [2024]
    elif data_2024 is None or data_2024.empty:
        logger.warning("⚠️ 2024 no disponible, entrenando solo con 2023")
        df_all = data_2023
        years = [2023]
    else:
        df_all = pd.concat([data_2023, data_2024], ignore_index=False)
        years = [2023, 2024]
    
    if df_all is None or df_all.empty:
        logger.error("❌ No hay datos para entrenar")
        return
    
    logger.info(f"✅ Datos totales: {len(df_all)} velas")
    logger.info(f"   Años: {years}")
    logger.info(f"   Rango: {df_all['Open_Time'].min()} a {df_all['Open_Time'].max()}")
    
    # Detectar signals
    logger.info(f"\n--- DETECTANDO TRIPLE COINCIDENCIAS EN {len(years)} AÑOS ---")
    
    df_all, total_tc = detect_signals(df_all, years, "COMPLETO")
    
    if total_tc == 0:
        logger.error("❌ No se detectaron Triple Coincidencias")
        return
    
    # Etiquetar
    logger.info(f"\n--- ETIQUETANDO {total_tc} SEÑALES CON TRIPLE BARRIER METHOD ---")
    
    config = ConfigManager()
    triple_signals = df_all[df_all['is_triple_coincidence']]
    t_events = triple_signals.index
    sides = triple_signals['trend_direction'].copy()
    
    try:
        labels = get_atr_labels(
            df_all, t_events, sides=sides,
            atr_period=14, tp_factor=2.0, sl_factor=1.0, time_limit=20
        )
    except Exception as e:
        logger.error(f"❌ Error etiquetando: {e}")
        return
    
    if isinstance(labels, dict):
        labels = labels.get('labels', labels)
    
    logger.info(f"✅ {len(labels)} señales etiquetadas")
    
    tp_count = (labels == 1).sum()
    sl_count = (labels == -1).sum()
    neutral = (labels == 0).sum()
    
    logger.info(f"   TP (ganancia): {tp_count}")
    logger.info(f"   SL (pérdida): {sl_count}")
    logger.info(f"   Neutral: {neutral}")
    
    # Extraer features
    logger.info(f"\n--- EXTRAYENDO 4 CARACTERÍSTICAS PARA CADA SEÑAL ---")
    
    features_list = []
    for idx in t_events:
        row_pos = df_all.index.get_loc(idx)
        row = df_all.iloc[row_pos]
        context = df_all.iloc[max(0, row_pos - 100):row_pos]
        features = extract_features(row, context)
        features_list.append(features)
    
    X = np.array(features_list, dtype=np.float32)
    y = np.array(labels.values)
    
    logger.info(f"✅ Features extraídas: {X.shape}")
    logger.info(f"   Shape: ({len(X)}, 4)")
    
    # Split train/test
    logger.info(f"\n--- SPLIT TRAIN/TEST ---")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    
    logger.info(f"   Train: {len(X_train)} muestras ({len(X_train)/len(X)*100:.1f}%)")
    logger.info(f"   Test: {len(X_test)} muestras ({len(X_test)/len(X)*100:.1f}%)")
    
    tp_train = (y_train == 1).sum()
    sl_train = (y_train == -1).sum()
    logger.info(f"   Train TP/SL: {tp_train}/{sl_train}")
    
    tp_test = (y_test == 1).sum()
    sl_test = (y_test == -1).sum()
    logger.info(f"   Test TP/SL: {tp_test}/{sl_test}")
    
    # Entrenar
    logger.info(f"\n--- ENTRENANDO RANDOM FOREST (100 árboles) ---")
    
    oracle = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    
    oracle.fit(X_train, y_train)
    logger.info(f"✅ Modelo entrenado")
    
    # Evaluar
    logger.info(f"\n--- EVALUACIÓN ---")
    
    y_train_pred = oracle.predict(X_train)
    y_test_pred = oracle.predict(X_test)
    
    acc_train = accuracy_score(y_train, y_train_pred)
    acc_test = accuracy_score(y_test, y_test_pred)
    
    logger.info(f"\n📊 ACCURACY:")
    logger.info(f"   Train: {acc_train*100:.2f}%")
    logger.info(f"   Test: {acc_test*100:.2f}%")
    logger.info(f"   Diferencia: {(acc_train - acc_test)*100:.2f}%")
    
    if (acc_train - acc_test) < 10:
        logger.info(f"   ✅ Generaliza bien (diferencia < 10%)")
    else:
        logger.warning(f"   ⚠️ Posible overfitting (diferencia > 10%)")
    
    # Matriz de confusión
    logger.info(f"\n--- MATRIZ DE CONFUSIÓN (TEST) ---")
    cm = confusion_matrix(y_test, y_test_pred)
    logger.info(f"   TP correct: {cm[1,1]}")
    logger.info(f"   TP incorrect: {cm[1,0]}")
    logger.info(f"   SL correct: {cm[0,0]}")
    logger.info(f"   SL incorrect: {cm[0,1]}")
    
    if cm[1,1] + cm[1,0] > 0:
        precision = cm[1,1] / (cm[1,1] + cm[1,0])
        logger.info(f"   Precision (TP): {precision*100:.2f}%")
    
    # Guardar modelo
    logger.info(f"\n--- GUARDANDO MODELO ---")
    
    aipha_root = Path(__file__).parent.parent.parent
    model_dir = aipha_root / "oracle" / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Versión nueva (v2)
    model_path_v2 = model_dir / "oracle_5m_trained_v2_multiyear.joblib"
    joblib.dump(oracle, str(model_path_v2))
    logger.info(f"✅ Modelo v2 guardado: {model_path_v2}")
    logger.info(f"   Tamaño: {model_path_v2.stat().st_size / 1024:.0f} KB")
    
    # Resumen
    logger.info(f"\n" + "=" * 80)
    logger.info(f"📋 RESUMEN ENTRENAMIENTO MULTIYEAR")
    logger.info(f"=" * 80)
    
    logger.info(f"\n📊 DATASET:")
    logger.info(f"   Años incluidos: {years}")
    logger.info(f"   Total velas: {len(df_all):,}")
    logger.info(f"   Triple Coincidencias: {total_tc}")
    logger.info(f"   Muestras etiquetadas: {len(labels)}")
    
    logger.info(f"\n🎯 PERFORMANCE:")
    logger.info(f"   Training Accuracy: {acc_train*100:.2f}%")
    logger.info(f"   Testing Accuracy: {acc_test*100:.2f}%")
    logger.info(f"   Overfitting Risk: {'LOW ✅' if (acc_train - acc_test) < 10 else 'HIGH ⚠️'}")
    
    logger.info(f"\n📈 COMPARACIÓN VS v1 (2024 solo):")
    logger.info(f"   v1 Train Accuracy: 50.00% (en 29 muestras)")
    logger.info(f"   v1 Test Accuracy: 75.00% (en 10 muestras)")
    logger.info(f"   v2 Test Accuracy: {acc_test*100:.2f}% (en {len(X_test)} muestras)")
    
    if acc_test >= 60:
        logger.info(f"\n✅ V2 APROBADO PARA VALIDACIÓN")
        status = "BETA - VALIDAR EN DATOS NUEVOS"
    else:
        logger.info(f"\n⚠️ V2 REQUIERE MEJORAS")
        status = "EXPERIMENTAL"
    
    logger.info(f"   Status: {status}")
    
    # Registrar en memoria
    logger.info(f"\n--- REGISTRANDO EN MEMORIA ---")
    
    memory.record_metric(
        component="Oracle",
        metric_name="multiyear_training_v2",
        value=float(acc_test),
        metadata={
            "years": years,
            "total_samples": int(len(labels)),
            "train_samples": int(len(X_train)),
            "test_samples": int(len(X_test)),
            "train_accuracy": float(acc_train),
            "test_accuracy": float(acc_test),
            "overfitting_risk": "LOW" if (acc_train - acc_test) < 10 else "HIGH",
            "model_path": str(model_path_v2),
            "status": status
        }
    )
    
    logger.info(f"✅ Métricas registradas")
    logger.info(f"=" * 80)


if __name__ == "__main__":
    run_multiyear_training()
