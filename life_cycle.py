import os
import sys
import time
import asyncio
import logging
from pathlib import Path

# Configurar path para importar módulos de Aipha
AIPHA_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(AIPHA_ROOT))

# Importar Componentes Core
from core.orchestrator_hardened import CentralOrchestratorHardened, CycleType
from core.trading_engine import TradingEngine

# Importar Componentes CGAlpha
from cgalpha.nexus.ops import CGAOps

# Configurar Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("memory/aipha_lifecycle.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("LifeCycle")

def main():
    """
    Punto de entrada principal Aipha v0.0.3 + CGAlpha Integration.
    Implementa "The Dual Heartbeat":
    1. Fast Loop (Trading Engine)
    2. Slow Loop (Evolutionary Orchestrator)
    """
    pid = os.getpid()
    pid_file = AIPHA_ROOT / "memory" / "orchestrator.pid"
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(pid_file, "w") as f:
        f.write(str(pid))
    
    logger.info(f"🚀 Sistema Aipha v0.0.3 Iniciado (PID: {pid})")
    
    try:
        # 1. Inicializar Motores
        logger.info("🔧 Inicializando Motores...")
        orchestrator = CentralOrchestratorHardened()
        trading_engine = TradingEngine()
        ops = CGAOps()
        
        logger.info("✅ Motores Listos. Entrando en Bucle Operativo Dual.")
        
        # 2. Bucle Principal
        while True:
            cycle_start = time.time()
            
            # --- FASE 0: Prioridad Usuario ---
            orchestrator.process_pending_requests()

            # --- FASE 1: Fast Loop (Trading) ---
            # Ejecuta detección de señales y sensor ordinal
            # Esto siempre corre, a menos que el usuario interrumpa
            trading_result = trading_engine.run_cycle()
            
            if trading_result['status'] == 'error':
                logger.error("❌ Error crítico en Trading Engine. Esperando 10s...")
                orchestrator.wait_for_next_cycle(10)
                continue

            # Señalizar a Ops si estamos operando (para bloquear tareas pesadas si fuera necesario)
            # En v0.0.3, trading_result no bloquea explicitamente, pero si hay señales activas
            # podríamos querer declarar estado crítico.
            # ops.signal_aipha_active(trading_result.get('signals_found', 0) > 0)

            # --- FASE 2: Slow Loop (Evolution) ---
            # Solo corre si hay recursos disponibles (CGA_Ops Green Light)
            resource_snapshot = ops.get_resource_state()
            
            if ops.can_start_heavy_task():
                logger.info(f"🟢 Recursos OK ({resource_snapshot.ram_percent}% RAM). Iniciando ciclo evolutivo.")
                asyncio.run(orchestrator.run_improvement_cycle(CycleType.AUTO))
            else:
                logger.warning(f"🟡 Recursos limitados ({resource_snapshot.ram_percent}% RAM). Postponiendo evolución.")
            
            # --- FASE 3: Espera Inteligente ---
            # Ritmo cardíaco del sistema. 
            # En producción HFT sería < 1s. En v0.0.3 (DuckDB Batch) usamos 60s.
            logger.info("⏳ Ciclo completado. Esperando...")
            if orchestrator.wait_for_next_cycle(60):
                logger.info("⚡ INTERRUPCIÓN: Comando de usuario recibido.")
            
    except KeyboardInterrupt:
        logger.info("🛑 Deteniendo sistema por solicitud de usuario...")
    except Exception as e:
        logger.critical(f"🔥 Error fatal en LifeCycle: {e}", exc_info=True)
    finally:
        if pid_file.exists():
            pid_file.unlink()
        logger.info("👋 Sistema detenido.")

if __name__ == "__main__":
    main()