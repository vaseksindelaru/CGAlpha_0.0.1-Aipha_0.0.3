import sys
import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock

# Setup Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.trading_engine import TradingEngine
from cgalpha.nexus.ops import CGAOps

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IntegrationTest")

def generate_synthetic_data():
    """Genera datos OHLCV que provocan una Triple Coincidencia."""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1h')
    data = {
        'Open': [], 'High': [], 'Low': [], 'Close': [], 'Volume': []
    }
    
    price = 10000.0
    
    # 1. Generar tendencia moderada y zona de acumulación
    for i in range(100):
        # Volatilidad baja (Acumulación)
        change = np.random.normal(0, 10) 
        price += change
        
        data['Open'].append(price)
        data['High'].append(price + 20)
        data['Low'].append(price - 20)
        data['Close'].append(price + np.random.normal(0, 5))
        data['Volume'].append(1000) # Volumen normal

    # 2. Inyectar VELA CLAVE (Key Candle) en la última barra
    # Alto volumen, cuerpo pequeño
    idx = -1
    data['Volume'][idx] = 5000 # 5x volumen promedio
    data['Open'][idx] = 10050
    data['Close'][idx] = 10055 # Cuerpo pequeño (5 pts)
    data['High'][idx] = 10100
    data['Low'][idx] = 10000   # Rango amplio (100 pts) → Pinbar/Doji
    
    df = pd.DataFrame(data, index=dates)
    df.index.name = 'Open_Time'
    return df

def test_deep_integration():
    logger.info("🧪 Iniciando Test Profundo con Datos Sintéticos...")
    
    engine = TradingEngine()
    
    # 🔢 MOCK: Reemplazar load_data con datos sintéticos
    logger.info("🔧 Inyectando datos sintéticos...")
    df_synthetic = generate_synthetic_data()
    engine.load_data = MagicMock(return_value=df_synthetic)
    
    # 🚀 Ejecutar Ciclo
    result = engine.run_cycle()
    logger.info(f"✅ Ciclo Terminado. Resultado: {result}")
    
    # 🔍 Validaciones
    if result['signals_found'] > 0:
        logger.info("   ✨ ÉXITO: Señales detectadas.")
    else:
        logger.error("   ❌ FALLO: No se detectaron señales (revisar generador).")
        
    if result.get('trajectories_saved', 0) > 0:
        logger.info(f"   ✨ ÉXITO: {result['trajectories_saved']} trayectorias guardadas en Bridge.")
        
        # Verificar contenido del bridge
        bridge_path = Path("aipha_memory/evolutionary/bridge.jsonl")
        last_line = ""
        with open(bridge_path, 'r') as f:
            for line in f:
                last_line = line
        
        if last_line:
            logger.info(f"   📝 Última entrada en Bridge:\n{last_line[:150]}...")
    else:
        logger.warning("   ⚠️ No se guardaron trayectorias.")

if __name__ == "__main__":
    test_deep_integration()
