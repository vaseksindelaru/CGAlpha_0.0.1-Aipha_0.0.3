import logging
import sys
import os
from datetime import date
import pandas as pd

# Añadir el directorio raíz al path para las importaciones
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from data_system import ApiClient, BinanceKlinesFetcher, DataRequestTemplateManager, KlinesDataRequestTemplate, save_results_to_duckdb

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_integration_flow():
    """Prueba el flujo completo con la nueva estructura simplificada y DuckDB."""
    logger.info("=== INICIANDO TEST DE INTEGRACIÓN (ESTRUCTURA SIMPLIFICADA) ===")
    
    db_path = "layer_2/data/test_aipha_data.duckdb"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # 1. Crear componentes
    api_client = ApiClient(timeout=30)
    fetcher = BinanceKlinesFetcher(api_client, download_dir="layer_2/data/test_downloaded_data")
    manager = DataRequestTemplateManager("layer_2/data/test_project_templates.json")
    
    # 2. Crear y guardar template
    target_date = date(2024, 4, 22)
    template = KlinesDataRequestTemplate(
        name="BTC_Daily_Test",
        symbol="BTCUSDT",
        interval="1d",
        start_date=target_date,
        end_date=target_date,
        description="Test de integración simplificado"
    )
    manager.add_template(template, overwrite=True)
    manager.save_templates()
    
    # 3. Descargar datos
    logger.info(f"Descargando datos para {template.symbol}...")
    df = fetcher.fetch_klines_by_template(template)
    
    if df is not None and not df.empty:
        logger.info(f"Éxito: {len(df)} filas obtenidas.")
        
        # 4. Guardar en DuckDB
        logger.info("Guardando en DuckDB...")
        save_results_to_duckdb(df, "klines_test", db_path=db_path)
        
        # 5. Verificar persistencia
        import duckdb
        with duckdb.connect(db_path) as conn:
            count = conn.execute("SELECT count(*) FROM klines_test").fetchone()[0]
            logger.info(f"Verificación DuckDB: {count} filas encontradas en la tabla.")
            assert count == len(df), "El número de filas en DuckDB no coincide con el DataFrame."
        
        logger.info("=== ✅ TEST DE INTEGRACIÓN EXITOSO ===")
    else:
        logger.error("❌ Fallo: No se obtuvieron datos.")
        sys.exit(1)

if __name__ == "__main__":
    test_integration_flow()
