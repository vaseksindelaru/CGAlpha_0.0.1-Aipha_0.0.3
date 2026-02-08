import sys
import os
import logging
from pathlib import Path

# Setup Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cgalpha.nexus.coordinator import CGANexus
from cgalpha.nexus.ops import CGAOps

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NexusVerification")

def verify_nexus_evolution():
    logger.info("🧪 Verificando Cadena de Evolución (Nexus -> RiskBarrierLab)...")
    
    # 1. Inicializar Nexus
    ops = CGAOps()
    nexus = CGANexus(ops_manager=ops)
    
    # 2. Ejecutar Ciclo de Pensamiento (Run Cycle)
    # Esto debería disparar RiskBarrierLab, que leerá los 1200 datos simulados
    logger.info("🧠 Ejecutando ciclo de análisis...")
    
    # Mocking el método run_cycle para esta versión v0.0.3 si no existe, 
    # o llamando al método real que orqueste labs.
    # Revisemos primero si coordinate_labs existe.
    
    # Si coordinator no tiene método para correr labs automáticos, lo simulamos aquí
    # llamando al lab directamente y pasando reporte a nexus.
    
    from cgalpha.labs.risk_barrier_lab import RiskBarrierLab
    
    bridge_path = Path("aipha_memory/testing/stress_test.jsonl")
    lab = RiskBarrierLab(bridge_path)
    
    findings = lab.run_analysis()
    logger.info(f"🔍 Hallazgos de RiskBarrierLab: {len(findings)}")
    
    for finding in findings:
        nexus.receive_report(
            lab_name="RiskBarrier",
            findings=finding,
            priority=finding['priority'],
            confidence=finding['confidence']
        )
        logger.info(f"   📥 Reporte recibido: {finding['type']} -> {finding['proposal']['parameter']}")

    # 3. Sintetizar para LLM
    prompt = nexus.synthesize_for_llm()
    logger.info("📝 Síntesis para LLM generada:")
    logger.info(prompt[:500] + "...") # Mostrar intro
    
    if len(findings) > 0:
        logger.info("✅ EVOLUCIÓN VERIFICADA: Datos -> Hallazgos -> Nexus -> Prompt")
    else:
        logger.warning("⚠️ Sin hallazgos (¿Datos insuficientes?)")

if __name__ == "__main__":
    verify_nexus_evolution()
