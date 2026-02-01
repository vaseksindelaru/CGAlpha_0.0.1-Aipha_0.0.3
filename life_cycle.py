import os
import sys
import time
import asyncio
import logging
from pathlib import Path

# Configurar path para importar módulos de Aipha
AIPHA_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(AIPHA_ROOT))

# Importar el Orquestador Reforzado (que maneja señales)
from core.orchestrator_hardened import CentralOrchestratorHardened, CycleType

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
    Punto de entrada principal del sistema (Daemon).
    Inicia el orquestador, guarda el PID y mantiene el bucle de vida.
    """
    # 1. Guardar PID para que el CLI pueda enviar señales (SIGUSR1)
    pid = os.getpid()
    pid_file = AIPHA_ROOT / "memory" / "orchestrator.pid"
    
    # Asegurar que el directorio existe
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(pid_file, "w") as f:
        f.write(str(pid))
    
    logger.info(f"🚀 Sistema Aipha Iniciado (PID: {pid})")
    logger.info("ℹ️  Usa 'aipha proposal create' en otra terminal para enviar comandos.")
    
    try:
        # 2. Inicializar el Orquestador Reforzado
        orchestrator = CentralOrchestratorHardened()
        
        # 3. Bucle Principal
        while True:
            # 0. Verificar prioridad: Procesar tareas de usuario pendientes antes de nada
            orchestrator.process_pending_requests()

            # 1. Ejecutar un ciclo de mejora automático
            asyncio.run(orchestrator.run_improvement_cycle(CycleType.AUTO))
            
            # 2. Espera Inteligente (Interrumpible por CLI)
            logger.info("⏳ Esperando siguiente ciclo...")
            
            # Si wait_for_next_cycle retorna True, es que el usuario envió un comando
            if orchestrator.wait_for_next_cycle(60):
                logger.info("⚡ INTERRUPCIÓN: Despertado por comando de usuario (Prioridad Máxima)")
                # El loop reinicia inmediatamente y va al paso 0
            
    except KeyboardInterrupt:
        logger.info("🛑 Deteniendo sistema por solicitud de usuario...")
    finally:
        if pid_file.exists():
            pid_file.unlink()
        logger.info("👋 Sistema detenido y PID eliminado.")

if __name__ == "__main__":
    main()