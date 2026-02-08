"""
Script de Verificación Final: El Organismo Completo.
Simula un ciclo de vida completo:
1. Reseteo de Configuración.
2. Inyección de Estrés (Datos de Crisis).
3. Evolución Forzada (RiskBarrierLab -> Nexus -> Inventor).
4. Verificación de Adaptación (Cambio de Configuración).
"""
import sys
import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime

# Setup Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.config_manager import ConfigManager
from cgalpha.nexus.ops import CGAOps
from cgalpha.nexus.coordinator import CGANexus
from cgalpha.nexus.applicator import ActionApplicator
from cgalpha.labs.risk_barrier_lab import RiskBarrierLab

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FullOrganismTest")

CONFIG_PATH = "aipha_config.json"
BRIDGE_PATH = "aipha_memory/testing/stress_test.jsonl"

def setup_environment():
    """Prepara el entorno para la prueba."""
    logger.info("🛠️  Preparando entorno de prueba...")
    
    # 1. Resetear Config a estado inicial
    initial_config = {
        "Trading": {
            "confidence_threshold": 0.60, # Valor bajo, vulnerable
            "tp_factor": 2.0
        }
    }
    with open(CONFIG_PATH, 'w') as f:
        json.dump(initial_config, f, indent=4)
    logger.info("   ✅ Configuración reseteada: confidence_threshold = 0.60")

def inject_stress():
    """Inyecta datos que simulan una crisis de alta volatilidad."""
    logger.info("💉 Inyectando estrés (Datos de Crisis)...")
    
    # Generar 500 eventos de crisis (WR muy bajo)
    with open(BRIDGE_PATH, 'w') as f: # Sobrescribir para aislar la prueba
        for i in range(500):
            evt = {
                "event_id": f"stress_{i}",
                "timestamp": datetime.now().isoformat(),
                "signal_type": "triple_coincidence",
                "side": 1,
                "outcome": {
                    "label_ordinal": -1 if i % 10 != 0 else 3, # 90% Loss rate
                    "mfe_atr": 0.5,
                    "mae_atr": 1.5
                },
                "causal_tags": ["HIGH_VOL_CRISIS"]
            }
            f.write(json.dumps(evt) + "\n")
            
    logger.info("   ✅ 500 eventos de crisis inyectados en el Puente.")

def trigger_evolution():
    """Dispara el proceso evolutivo."""
    logger.info("🧠 Disparando Evolución (The Awakening)...")
    
    # 1. Labs Analysis
    lab = RiskBarrierLab(Path(BRIDGE_PATH))
    findings = lab.run_analysis()
    
    if not findings:
        logger.error("   ❌ El Lab no encontró nada (Fallo inesperado).")
        return False
        
    logger.info(f"   🔎 Hallazgos del Lab: {len(findings)}")
    
    # 2. Nexus Coordination
    ops = CGAOps()
    nexus = CGANexus(ops_manager=ops)
    
    # Simulamos el paso de mensajes
    proposals_to_apply = []
    
    for f in findings:
        # En v0.0.3, Nexus sintetiza. Para la prueba, extraemos la propuesta cruda.
        # En un sistema real, LLM Inventor convertiría síntesis -> código.
        # Aquí, ActionApplicator consume la propuesta estructurada del Lab directament
        # (Asumiendo que el 'Inventor' es un pasamanos en esta versión)
        if f['type'] == 'risk_adjustment':
            proposals_to_apply.append(f['proposal'])
            
    # 3. Action Application (The Inventor)
    applicator = ActionApplicator(CONFIG_PATH)
    
    success_count = 0
    for prop in proposals_to_apply:
        logger.info(f"   💡 Applicator recibiendo propuesta: {prop}")
        if applicator.apply_proposal(prop):
            success_count += 1
            
    return success_count > 0

def verify_adaptation():
    """Verifica si el sistema se adaptó."""
    logger.info("🕵️ Verificando Adaptación...")
    
    cm = ConfigManager(CONFIG_PATH)
    new_val = cm.get("Trading.confidence_threshold")
    
    logger.info(f"   📊 Nuevo confidence_threshold: {new_val}")
    
    if new_val == 0.75:
        logger.info("🚀 ÉXITO TOTAL: El sistema detectó la crisis y subió sus defensas.")
        return True
    else:
        logger.error(f"   ❌ Fallo: El valor es {new_val}, se esperaba 0.75")
        return False

def run_test():
    setup_environment()
    inject_stress()
    if trigger_evolution():
        if verify_adaptation():
            logger.info("\n✅✅✅ ORGANISMO COMPLETAMENTE FUNCIONAL ✅✅✅")
        else:
            logger.error("\n❌❌❌ MEJORA NO APLICADA ❌❌❌")
    else:
        logger.error("\n❌❌❌ FALLO EN EVOLUCIÓN ❌❌❌")

if __name__ == "__main__":
    run_test()
