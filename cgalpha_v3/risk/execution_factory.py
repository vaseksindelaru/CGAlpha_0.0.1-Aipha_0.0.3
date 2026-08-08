import os
import logging
from typing import Union
from cgalpha_v3.risk.order_manager import DryRunOrderManager

logger = logging.getLogger("execution_factory")

class RealOrderManagerStub:
    """Implementación de respaldo para evitar desastres."""
    def __init__(self, key, secret):
        self.key = key
        self.secret = secret
    
    def execute_signal(self, signal):
        logger.error("🛑 INTENTO DE EJECUCIÓN REAL BLOQUEADO: RealOrderManager aún no implementado.")
        return None
    
    def update_positions(self, price): pass
    def get_exposure_breakdown(self): return {}
    def close_all_positions(self, reason): pass

def create_order_manager() -> Union[DryRunOrderManager, RealOrderManagerStub]:
    """
    Factory que instancia el motor de ejecución según el .env.
    """
    mode = os.getenv("CGV3_EXECUTION_MODE", "0")
    
    if mode == "1":
        key = os.getenv("BINANCE_API_KEY")
        secret = os.getenv("BINANCE_API_SECRET")
        
        if not key or not secret or "your_api" in key:
            logger.critical("❌ ERROR DE SEGURIDAD: CGV3_EXECUTION_MODE=1 pero no hay llaves válidas. Forzando Dry Run.")
            return DryRunOrderManager()
        
        logger.warning("⚠️ MODO LIVE ACTIVADO: Conectando con Binance Futures API...")
        return RealOrderManagerStub(key, secret) # Sustituir por RealOrderManager en Fase 4.4
    
    else:
        logger.info("🎮 MODO DRY RUN ACTIVO: Operando con capital simulado.")
        return DryRunOrderManager()
