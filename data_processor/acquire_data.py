import logging
import sys
import os
from datetime import date, timedelta

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_processor.data_system import ApiClient, BinanceKlinesFetcher, KlinesDataRequestTemplate, save_results_to_duckdb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def acquire_historical_data():
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
        description="Datos para proof_strategy"
    )
    
    logger.info(f"Descargando datos para {template.symbol} {template.interval}...")
    df = fetcher.fetch_klines_by_template(template)
    
    if df is not None and not df.empty:
        logger.info(f"Éxito: {len(df)} filas obtenidas.")
        save_results_to_duckdb(df, "btc_1h_data", db_path=db_path)
        logger.info("Datos guardados en la tabla 'btc_1h_data'.")
    else:
        logger.error("No se pudieron obtener los datos.")

if __name__ == "__main__":
    acquire_historical_data()
