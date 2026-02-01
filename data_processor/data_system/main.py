import pandas as pd
import os
import logging
from .storage import save_results_to_duckdb

logger = logging.getLogger(__name__)

def upload_csv_to_duckdb(file_path: str, table_name: str, db_path: str = "aipha_data.duckdb"):
    """Lee un CSV y lo carga en DuckDB."""
    if not os.path.exists(file_path):
        logger.warning(f"Archivo no encontrado: {file_path}. Saltando carga.")
        return

    try:
        logger.info(f"Leyendo '{file_path}' para cargar en tabla '{table_name}'...")
        df = pd.read_csv(file_path)
        if df.empty:
            logger.warning(f"El archivo '{file_path}' está vacío.")
            return
        
        save_results_to_duckdb(df, table_name, db_path=db_path)
    except Exception as e:
        logger.error(f"Error al procesar '{file_path}': {e}")

def run_batch_upload(files_mapping: dict, db_path: str = "aipha_data.duckdb"):
    """Carga múltiples archivos según un mapeo {file_path: table_name}."""
    for file_path, table_name in files_mapping.items():
        upload_csv_to_duckdb(file_path, table_name, db_path=db_path)

def main():
    """Punto de entrada para automatización de carga."""
    # Ejemplo de configuración de carga
    files_to_upload = {
        'training_events.csv': 'training_events',
        'oracle_predictions.csv': 'oracle_predictions'
    }
    
    logger.info("Iniciando proceso de carga masiva a DuckDB...")
    run_batch_upload(files_to_upload)
    logger.info("Proceso de carga completado.")

if __name__ == '__main__':
    # Configuración básica de logging si se ejecuta como script
    logging.basicConfig(level=logging.INFO)
    main()
