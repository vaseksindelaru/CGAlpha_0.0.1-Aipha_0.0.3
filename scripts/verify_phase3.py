import sys
import os
import logging
import json
from pathlib import Path

# Setup Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cgalpha.nexus.applicator import ActionApplicator
from core.config_manager import ConfigManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Phase3Verification")

def verify_autonomy():
    logger.info("🧪 Iniciando Verificación Fase 3: El Inventor...")
    
    # 1. Setup Config
    config_path = "aipha_config.json"
    if not os.path.exists(config_path):
        # Crear config dummy si no existe
        dummy_config = {
            "Trading": {
                "confidence_threshold": 0.70,
                "tp_factor": 2.0
            }
        }
        with open(config_path, 'w') as f:
            json.dump(dummy_config, f, indent=4)
        logger.info("   ℹ️ Creado aipha_config.json dummy.")

    # 2. Definir Propuesta (Simulando output de Nexus)
    # "RiskBarrierLab propone aumentar threshold por crisis"
    proposal = {
        "parameter": "Trading.confidence_threshold",
        "action": "increase",
        "value": 0.75,
        "reason": "Protección de Capital: WR 15.0% < 40% en Crisis."
    }
    logger.info(f"   📜 Propuesta recibida: {proposal['parameter']} -> {proposal['value']}")
    
    # 3. Invocar al Inventor (Applicator)
    applicator = ActionApplicator(config_path)
    success = applicator.apply_proposal(proposal)
    
    if not success:
        logger.error("   ❌ Fallo al aplicar propuesta.")
        return

    # 4. Validar resultado (El cambio debe ser persistente)
    # Usamos ConfigManager para simular recarga real
    cm = ConfigManager(config_path)
    new_value = cm.get("Trading.confidence_threshold")
    
    logger.info(f"   🔎 Valor leído en ConfigManager: {new_value}")
    
    if new_value == 0.75:
        logger.info("✅ FASE 3 EXITOSA: El sistema ha reescrito su propio ADN.")
        logger.info("   (Backup creado: check aipha_config.json.bak)")
    else:
        logger.error(f"   ❌ Fallo de verificación. Esperado 0.75, obtenido {new_value}")

if __name__ == "__main__":
    verify_autonomy()
