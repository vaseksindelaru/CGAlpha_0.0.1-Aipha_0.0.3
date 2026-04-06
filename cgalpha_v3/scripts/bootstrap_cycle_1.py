import asyncio
from datetime import datetime, timedelta
import logging
from cgalpha_v3.application.pipeline import SimpleFoundationPipeline

# Configuración de Logging Maestro
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [LILA_v3] - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def start_cycle_1():
    """
    Inicia el Ciclo 1 de Aprendizaje de Lila v3.
    Misión: Cosecha 2026 -> Trinity Tuning -> Shadow Trade Capture.
    """
    logger.info("💎 Iniciando Bootstrap del CICLO 1: La Inmortalización Causal")
    
    # 1. Inicializar Pipeline v3.0.0
    pipeline = SimpleFoundationPipeline()
    
    # 2. Definir Período de Cosecha (Últimos 7 días para bootstrap rápido)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    symbol = "BTCUSDT"
    
    logger.info(f"🛰️ Cosechando Futuro: {symbol} de {start_date.date()} a {end_date.date()}")
    
    # 3. Ejecutar Ciclo Maestro
    # (Descarga -> Detección -> Shadow -> Oracle -> Gate)
    decision = pipeline.run_cycle(symbol, start_date, end_date)
    
    logger.info(f"🏆 Ciclo 1 Completado. Estado Nexus: {decision}")
    logger.info("📈 Próximo Paso: Entrenamiento Recursivo del Oracle con MFE/MAE capturado.")

if __name__ == "__main__":
    asyncio.run(start_cycle_1())
