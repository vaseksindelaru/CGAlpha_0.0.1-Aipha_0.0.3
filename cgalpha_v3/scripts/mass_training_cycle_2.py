import asyncio
from datetime import datetime, timedelta
import logging
from cgalpha_v3.application.pipeline import SimpleFoundationPipeline

# Configuración de Logging de Producción
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [LILA_v3_CORE] - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("cgalpha_v3/logs/mass_training.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def mass_training_cycle_2():
    """
    Ejecuta el ENTRENAMIENTO REAL del Ciclo 2.
    Misión: Cosecha Masiva (90 Días) -> Entrenamiento Oracle v3 -> Validación OOS.
    """
    logger.info("💎 INICIANDO ENTRENAMIENTO REAL (CICLO 2): La Inmortalización Causal")
    
    # 1. Pipeline v3.0.0
    pipeline = SimpleFoundationPipeline()
    
    # 2. Definir Período de Cosecha Real (90 Días de histórico masivo)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    symbol = "BTCUSDT"
    
    logger.info(f"🛰️ Cosecha Masiva: {symbol} de {start_date.date()} a {end_date.date()}")
    
    # 3. Lanzar Bucle de Aprendizaje Masivo
    # (Descarga Real -> Trinity Signals -> Shadow Trades -> bridge.jsonl)
    logger.info("⚙️ Procesando Trinity de Microestructura para 90 días...")
    decision = pipeline.run_cycle(symbol, start_date, end_date)
    
    # 4. Entrenamiento Recursivo del Oracle
    logger.info("🧠 Entrenando Oracle v3 (Meta-Labeling) con OutcomeOrdinals capturados...")
    pipeline.oracle.retrain_recursive("aipha_memory/evolutionary/bridge.jsonl")
    
    logger.info(f"🏆 Entrenamiento Real Completado. Estado Nexus: {decision}")
    logger.info("📈 Resultados disponibles en el Vault Evolution Dashboard.")

if __name__ == "__main__":
    asyncio.run(mass_training_cycle_2())
