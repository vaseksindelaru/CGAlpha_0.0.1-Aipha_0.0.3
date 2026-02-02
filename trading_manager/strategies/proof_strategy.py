import pandas as pd
import duckdb
import logging
import sys
import os
import numpy as np
import joblib
from datetime import date, timedelta
from pathlib import Path

# Añadir el directorio raíz al path para poder importar los building blocks
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from trading_manager.building_blocks.detectors.key_candle_detector import SignalDetector
from trading_manager.building_blocks.detectors.accumulation_zone_detector import AccumulationZoneDetector
from trading_manager.building_blocks.detectors.trend_detector import TrendDetector
from trading_manager.building_blocks.signal_combiner import SignalCombiner
from trading_manager.building_blocks.labelers.potential_capture_engine import get_atr_labels
from data_processor.data_system import BinanceKlinesFetcher, KlinesDataRequestTemplate, save_results_to_duckdb, ApiClient
from core.config_manager import ConfigManager
from core.memory_manager import MemoryManager

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Cache global para Oracle
_oracle_cache = None

def get_oracle_model():
    """Carga el modelo Oracle en caché (lazy loading)."""
    global _oracle_cache
    if _oracle_cache is None:
        aipha_root = Path(__file__).parent.parent.parent
        model_path = aipha_root / "oracle" / "models" / "oracle_5m_trained.joblib"
        if model_path.exists():
            try:
                _oracle_cache = joblib.load(str(model_path))
                logger.info("✅ Oracle model cargado en caché")
            except Exception as e:
                logger.warning(f"⚠️  No se pudo cargar Oracle: {e}")
                _oracle_cache = None
        else:
            logger.warning(f"⚠️  Modelo Oracle no encontrado en {model_path}")
    return _oracle_cache

def extract_oracle_features(df_row, df_context):
    """
    Extrae 4 características para Oracle a partir de una vela.
    Features: [body_percentage, volume_ratio, relative_range, hour_of_day]
    """
    try:
        # Body percentage (cuerpo pequeño indica potencial reversión)
        open_price = df_row['Open']
        close_price = df_row['Close']
        high = df_row['High']
        low = df_row['Low']
        
        total_range = high - low
        body = abs(close_price - open_price)
        body_percentage = (body / total_range) if total_range > 0 else 0
        
        # Volume ratio (comparado con promedio de lookback)
        vol_lookback = 50
        avg_volume = df_context.iloc[-vol_lookback:]['Volume'].mean() if len(df_context) >= vol_lookback else df_context['Volume'].mean()
        volume_ratio = df_row['Volume'] / avg_volume if avg_volume > 0 else 1.0
        
        # Relative range (rango relativo al precio)
        relative_range = total_range / open_price if open_price > 0 else 0
        
        # Hour of day (normalizado 0-23 a 0-1)
        hour_of_day = df_row.name.hour / 24.0  # name es el timestamp
        
        # Normalizar valores a rango [0, 1]
        features = np.array([
            min(max(body_percentage, 0), 1),
            min(max(volume_ratio / 10, 0), 1),  # Dividir por 10 para escalar
            min(max(relative_range * 100, 0), 1),  # Multiplicar por 100 para escalar
            hour_of_day
        ], dtype=np.float32)
        
        return features
    except Exception as e:
        logger.warning(f"Error extrayendo características Oracle: {e}")
        return np.zeros(4, dtype=np.float32)

def filter_signals_with_oracle(df, triple_signals_idx, oracle_model, confidence_threshold=0.5):
    """
    Filtra Triple Coincidencias usando predicciones del Oracle.
    Mantiene solo señales predichas como TP (clase 1).
    Retorna: (filtered_idx, predictions, confidences)
    """
    if oracle_model is None:
        logger.warning("Oracle no disponible, retornando todas las señales")
        return triple_signals_idx, None, None
    
    try:
        # Extraer características para cada señal
        features_list = []
        for idx in triple_signals_idx:
            row_pos = df.index.get_loc(idx)
            features = extract_oracle_features(df.iloc[row_pos], df.iloc[max(0, row_pos-100):row_pos])
            features_list.append(features)
        
        X = np.array(features_list, dtype=np.float32)
        
        # Predicciones y confianzas
        predictions = oracle_model.predict(X)
        confidences = np.max(oracle_model.predict_proba(X), axis=1)
        
        # Filtrar: mantener solo TP (clase 1) con confianza > threshold
        mask = (predictions == 1) & (confidences >= confidence_threshold)
        filtered_idx = triple_signals_idx[mask]
        
        tp_count = (predictions == 1).sum()
        sl_count = (predictions == -1).sum()
        
        logger.info(f"   Oracle filtrado: {tp_count} TP predichos, {sl_count} SL predichos")
        logger.info(f"   Mantenidas {len(filtered_idx)} de {len(triple_signals_idx)} señales (filtro por confianza > {confidence_threshold})")
        
        return filtered_idx, predictions, confidences
    except Exception as e:
        logger.error(f"Error filtrando con Oracle: {e}")
        return triple_signals_idx, None, None


def ensure_5m_data_exists(db_path: str, force_redownload: bool = False):
    """Descarga datos de 5 minutos si no existen o si force_redownload es True."""
    table_name = "btc_5m_data"
    
    try:
        conn = duckdb.connect(db_path)
        result = conn.execute(f"SELECT COUNT(*) as count FROM {table_name}").fetchall()
        conn.close()
        
        if result[0][0] > 0 and not force_redownload:
            logger.info(f"Tabla '{table_name}' ya existe con datos. Usando datos existentes.")
            return table_name
    except Exception:
        pass
    
    logger.info("Descargando datos de 5 minutos desde Binance...")
    
    try:
        client = ApiClient(timeout=60)
        fetcher = BinanceKlinesFetcher(
            client, 
            download_dir="data_processor/data/test_downloaded_data"
        )
        
        # Descargar 1 mes de datos en 5m (Enero 2024)
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        template = KlinesDataRequestTemplate(
            name="BTC_5m_Jan_2024",
            symbol="BTCUSDT",
            interval="5m",
            start_date=start_date,
            end_date=end_date,
            description="Datos de 5 minutos para Triple Coincidencia"
        )
        
        df = fetcher.fetch_klines_by_template(template)
        
        if df is not None and not df.empty:
            logger.info(f"✅ Éxito: {len(df)} velas de 5m descargadas.")
            save_results_to_duckdb(df, table_name, db_path=db_path)
            logger.info(f"✅ Datos guardados en tabla '{table_name}'.")
            return table_name
        else:
            logger.error("❌ No se pudieron descargar los datos.")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error descargando datos: {e}")
        return None

def run_proof_strategy():
    # Inicializar managers de Capa 1
    config = ConfigManager()
    memory = MemoryManager()
    
    db_path = "data_processor/data/aipha_data.duckdb"
    
    logger.info("=" * 60)
    logger.info("INICIANDO PROOF STRATEGY - TRIPLE COINCIDENCIA EN 5 MINUTOS")
    logger.info("=" * 60)
    
    # 1. Asegurar que existen datos de 5 minutos
    table_name = ensure_5m_data_exists(db_path, force_redownload=False)
    
    if table_name is None:
        logger.error("❌ No se puede proceder sin datos de 5 minutos.")
        return

    # 2. Carga de Datos desde DuckDB
    if not os.path.exists(db_path):
        logger.error(f"❌ Base de datos no encontrada en {db_path}")
        return

    try:
        conn = duckdb.connect(db_path)
        df = conn.execute(f"SELECT * FROM {table_name}").df()
        conn.close()
        
        # Asegurar que el índice es el tiempo y está ordenado
        df['Open_Time'] = pd.to_datetime(df['Open_Time'])
        df = df.sort_values('Open_Time').set_index('Open_Time')
        
        logger.info(f"✅ Datos cargados: {len(df)} velas de 5m de {df.index.min()} a {df.index.max()}")
    except Exception as e:
        logger.error(f"❌ Error al cargar datos: {e}")
        return

    # 3. Ejecutar los TRES Detectores (Triple Coincidencia)
    logger.info("\n--- EJECUTANDO DETECTORES DE TRIPLE COINCIDENCIA ---")
    
    # 3a. Detectar Zonas de Acumulación
    logger.info("1️⃣  Detectando zonas de acumulación...")
    try:
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
    except Exception as e:
        logger.error(f"   ❌ Error en AccumulationZoneDetector: {e}")
        return

    # 3b. Detectar Tendencia
    logger.info("2️⃣  Detectando tendencia (R² y Slope)...")
    try:
        df = TrendDetector.analyze_trend(
            df,
            lookback_period=config.get("Trading.trend_lookback", 20),
            zigzag_threshold=0.005
        )
        avg_r_squared = df['trend_r_squared'].mean()
        logger.info(f"   ✅ R² promedio: {avg_r_squared:.3f}")
    except Exception as e:
        logger.error(f"   ❌ Error en TrendDetector: {e}")
        return

    # 3c. Detectar Velas Clave
    logger.info("3️⃣  Detectando velas clave (volumen + cuerpo pequeño)...")
    try:
        df = SignalDetector.detect_key_candles(
            df, 
            volume_lookback=config.get("Trading.volume_lookback", 20),
            volume_percentile_threshold=config.get("Trading.volume_percentile_threshold", 90),
            body_percentile_threshold=config.get("Trading.body_percentile_threshold", 30),
            ema_period=config.get("Trading.ema_period", 200),
            reversal_mode=config.get("Trading.reversal_mode", True)
        )
        key_candle_count = df['is_key_candle'].sum()
        logger.info(f"   ✅ {key_candle_count} velas clave detectadas")
    except Exception as e:
        logger.error(f"   ❌ Error en SignalDetector: {e}")
        return

    # 4. Combinar las Tres Señales (TRIPLE COINCIDENCIA)
    logger.info("\n--- COMBINANDO SEÑALES (TRIPLE COINCIDENCIA) ---")
    try:
        df = SignalCombiner.combine_signals(
            df,
            tolerance_bars=config.get("Trading.tolerance_bars", 8),
            min_r_squared=config.get("Trading.min_r_squared", 0.45)
        )
        triple_count = df['is_triple_coincidence'].sum()
        logger.info(f"✅ {triple_count} TRIPLE COINCIDENCIAS detectadas en 5m")
    except Exception as e:
        logger.error(f"❌ Error en SignalCombiner: {e}")
        return

    # 5. Filtrado de Eventos y Preparación para Etiquetado
    triple_signals = df[df['is_triple_coincidence']]
    
    if len(triple_signals) == 0:
        logger.warning("⚠️  No se detectaron Triple Coincidencias con los parámetros actuales.")
        return

    t_events = triple_signals.index
    
    # Determinar lado de la operación basado en dirección de tendencia
    sides = triple_signals['trend_direction'].copy()
    
    # 5a. FILTRADO CON ORACLE (Nuevo)
    logger.info("\n--- APLICANDO FILTRO ORACLE ---")
    oracle_model = get_oracle_model()
    
    if oracle_model is not None:
        # Filtrar señales con Oracle (mantener solo TP predichos)
        t_events_filtered, oracle_predictions, oracle_confidences = filter_signals_with_oracle(
            df, t_events.values, oracle_model, confidence_threshold=0.5
        )
        sides = sides[sides.index.isin(t_events_filtered)]
        t_events = pd.Index(t_events_filtered)
        logger.info(f"   ✅ Filtro Oracle aplicado: {len(t_events)} de {len(triple_signals)} señales mantienen")
    else:
        logger.info("   ⚠️  Oracle no disponible, usando todas las Triple Coincidencias")
        oracle_predictions = None
        oracle_confidences = None
    
    logger.info(f"\n--- ETIQUETANDO {len(t_events)} SEÑALES CON TRIPLE BARRIER METHOD ---")
    
    # 6. Etiquetado (Triple Barrier Method - ATR dinámico)
    try:
        labels = get_atr_labels(
            df, 
            t_events, 
            sides=sides,
            atr_period=config.get("Trading.atr_period", 14), 
            tp_factor=config.get("Trading.tp_factor", 2.0), 
            sl_factor=config.get("Trading.sl_factor", 1.0), 
            time_limit=config.get("Trading.time_limit", 20)
        )
    except Exception as e:
        logger.error(f"❌ Error en Etiquetado: {e}")
        return

    # 7. Resultados Finales
    logger.info("\n" + "=" * 60)
    logger.info("RESULTADOS FINALES - ESTRATEGIA DE 5 MINUTOS CON ORACLE")
    logger.info("=" * 60)
    
    # Manejar resultado dict o Series
    if isinstance(labels, dict):
        labels = labels.get('labels', labels)
    
    counts = labels.value_counts().sort_index()
    
    summary = {
        "Total Señales Etiquetadas": len(labels),
        "Take Profit (TP hit)": counts.get(1, 0),
        "Stop Loss (SL hit)": counts.get(-1, 0),
        "Neutral (Time Limit)": counts.get(0, 0)
    }
    
    for key, val in summary.items():
        print(f"  {key}: {val}")
        
    if len(labels) > 0:
        win_rate = (summary["Take Profit (TP hit)"] / len(labels)) * 100
        print(f"\n  🎯 Win Rate (TP vs Total): {win_rate:.2f}%")
        
        # Mostrar métricas de Oracle si fue aplicado
        if oracle_model is not None and oracle_predictions is not None:
            oracle_tp_count = (oracle_predictions == 1).sum()
            oracle_sl_count = (oracle_predictions == -1).sum()
            oracle_accuracy = (summary["Take Profit (TP hit)"] / len(labels) if len(labels) > 0 else 0) * 100
            
            print(f"\n📊 ORACLE METRICS:")
            print(f"  - Signals predicted as TP: {oracle_tp_count} / {len(triple_signals)}")
            print(f"  - Signals predicted as SL: {oracle_sl_count} / {len(triple_signals)}")
            print(f"  - Actual TP from filtered: {summary['Take Profit (TP hit)']} / {len(labels)}")
            print(f"  - Oracle-assisted accuracy: {oracle_accuracy:.2f}%")
            if oracle_confidences is not None and len(oracle_confidences) > 0:
                print(f"  - Avg confidence: {oracle_confidences.mean():.2f}")
        
        # REGISTRAR MÉTRICA EN CAPA 1
        memory.record_metric(
            component="Trading",
            metric_name="win_rate_5m_with_oracle",
            value=float(win_rate / 100.0),
            metadata={
                "timeframe": "5m",
                "tp_factor": float(config.get("Trading.tp_factor")),
                "sl_factor": float(config.get("Trading.sl_factor")),
                "signals": int(len(labels)),
                "triple_coincidences": int(triple_count),
                "oracle_filtered": oracle_model is not None,
                "oracle_predictions_tp": int((oracle_predictions == 1).sum()) if oracle_predictions is not None else 0
            }
        )
        logger.info("✅ Métricas registradas en memoria del sistema.")
    
    logger.info("=" * 60)
    logger.info("✅ PROOF STRATEGY COMPLETADA")
    logger.info("=" * 60)

if __name__ == "__main__":
    run_proof_strategy()
