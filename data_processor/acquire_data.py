import logging
import sys
import os
from datetime import date, timedelta

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_processor.data_system import ApiClient, BinanceKlinesFetcher, KlinesDataRequestTemplate, save_results_to_duckdb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def acquire_historical_data_1h():
    """Descarga datos de 1 hora para análisis de contexto macro."""
    db_path = "data_processor/data/aipha_data.duckdb"
    
    client = ApiClient(timeout=60)
    fetcher = BinanceKlinesFetcher(client, download_dir="data_processor/data/test_downloaded_data")
    
    # Descargar 3 meses de datos (Enero a Marzo 2024)
    start_date = date(2024, 1, 1)
    end_date = date(2024, 3, 31)
    
    template = KlinesDataRequestTemplate(
        name="BTC_1h_Q1_2024",
        symbol="BTCUSDT",
        interval="1h",
        start_date=start_date,
        end_date=end_date,
        description="Datos para análisis de contexto macro"
    )
    
    logger.info(f"Descargando datos para {template.symbol} {template.interval}...")
    df = fetcher.fetch_klines_by_template(template)
    
    if df is not None and not df.empty:
        logger.info(f"✅ Éxito: {len(df)} filas obtenidas (1H).")
        save_results_to_duckdb(df, "btc_1h_data", db_path=db_path)
        logger.info("✅ Datos guardados en la tabla 'btc_1h_data'.")
    else:
        logger.error("❌ No se pudieron obtener los datos (1H).")

def acquire_historical_data_5m():
    """Descarga datos de 5 minutos para la Triple Coincidencia."""
    db_path = "data_processor/data/aipha_data.duckdb"
    
    client = ApiClient(timeout=60)
    fetcher = BinanceKlinesFetcher(client, download_dir="data_processor/data/test_downloaded_data")
    
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
    
    logger.info(f"Descargando datos para {template.symbol} {template.interval}...")
    df = fetcher.fetch_klines_by_template(template)
    
    if df is not None and not df.empty:
        logger.info(f"✅ Éxito: {len(df)} filas obtenidas (5M).")
        save_results_to_duckdb(df, "btc_5m_data", db_path=db_path)
        logger.info("✅ Datos guardados en la tabla 'btc_5m_data'.")
    else:
        logger.error("❌ No se pudieron obtener los datos (5M).")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Adquirir datos históricos de Binance")
    parser.add_argument(
        "--interval",
        choices=["1h", "5m", "all"],
        default="all",
        help="Intervalo de tiempo: 1h (1 hora), 5m (5 minutos), o all (ambos)"
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("INICIANDO DESCARGA DE DATOS HISTÓRICOS")
    logger.info("=" * 60)
    
    if args.interval in ["1h", "all"]:
        acquire_historical_data_1h()
    
    if args.interval in ["5m", "all"]:
        acquire_historical_data_5m()
    
    logger.info("=" * 60)
    logger.info("✅ DESCARGA COMPLETADA")
    logger.info("=" * 60)
