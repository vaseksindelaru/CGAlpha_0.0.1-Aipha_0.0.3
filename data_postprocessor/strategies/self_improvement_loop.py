import logging
import sys
import os

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from data_postprocessor.building_blocks.self_improvement.adaptive_barrier import AdaptiveATRBarrier

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def run_self_improvement_demo():
    logger.info("--- DEMOSTRACIÓN DE AUTO-MEJORA (DATA POSTPROCESSOR) ---")
    
    # Inicializar la barrera adaptativa
    barrier = AdaptiveATRBarrier(multiplier=2.0, sensitivity=0.1)
    
    # Historial de mercado simulado (Paso 1)
    market_history = [100, 101, 102, 99, 103, 104, 100, 105]
    
    logger.info(f"\n--- Paso 1: Análisis Inicial (Multiplicador: {barrier.multiplier}) ---")
    result = barrier.process(market_history[:5])
    logger.info(f"📊 ATR Calculado: {result['atr']:.2f}")
    logger.info(f"🛡️ Barrera colocada en: {result['barrier_price']:.2f}")
    
    # Simulación del Evento (Paso 2)
    logger.info("\n💥 Evento: El precio bajó a 99 (tocó barrera) y luego subió.")
    logger.info("❌ Resultado: Trade cerrado con pérdida innecesaria (Ruido).")
    
    feedback = {'outcome': -1.0, 'reason': 'noise'}
    
    # Aprendizaje (Paso 3)
    logger.info("\n--- Paso 3: Ejecutando Auto-Mejora ---")
    barrier.learn(feedback)
    
    # Verificación (Paso 4)
    logger.info("\n--- Paso 4: Verificación ---")
    result_new = barrier.process(market_history[:5])
    logger.info(f"🛡️ Nueva Barrera (hipotética) sería: {result_new['barrier_price']:.2f}")
    logger.info(f"📈 Multiplicador Actual: {result_new['multiplier_used']:.2f}")
    
    if result_new['multiplier_used'] > 2.0:
        logger.info("\n✅ ÉXITO: El sistema aprendió y se adaptó al ruido.")
        logger.info(f"Diferencia de protección: {abs(result_new['barrier_price'] - result['barrier_price']):.3f} puntos más abajo.")
    else:
        logger.info("\n❌ FALLO: El sistema no se adaptó.")

if __name__ == "__main__":
    run_self_improvement_demo()
