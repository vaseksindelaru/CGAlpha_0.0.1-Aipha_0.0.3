import sys
import os
import json
import random
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, List

# Setup Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.trading_engine import TradingEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Phase2Simulator")

def generate_random_trajectory(
    mean_outcome: float, 
    volatility: str, 
    trend_type: str
) -> Dict:
    """Genera una trayectoria aleatoria pero coherente con el régimen."""
    
    # 1. Definir parámetros según escenario
    if volatility == "HIGH":
        atr_multiplier = 2.0
        noise = 0.5
    else:
        atr_multiplier = 0.8
        noise = 0.2
        
    base_mfe = 2.0 if trend_type == "FRIENDLY" else 0.5
    base_mae = 0.5 if trend_type == "FRIENDLY" else 1.5
    
    # 2. Simular valores
    mfe = max(0.1, np.random.normal(base_mfe, 1.0) * atr_multiplier)
    mae = max(0.1, np.random.normal(base_mae, 0.5))
    
    # 3. Determinar etiqueta
    # Si MFE > 3 ATR -> Label 3
    # Si MFE > 2 ATR -> Label 2
    # Si MAE > 1 ATR (SL) -> Label -1 (a veces)
    
    label = 0
    highest_tp = 0
    
    if mae > 1.2: # SL hit
        label = -1
    else:
        if mfe > 3.0:
            label = 3
            highest_tp = 3
        elif mfe > 2.0:
            label = 2
            highest_tp = 2
        elif mfe > 1.0:
            label = 1
            highest_tp = 1
            
    return {
        "mfe": round(mfe, 2),
        "mae": round(mae, 2),
        "label": label,
        "highest_tp": highest_tp
    }

def simulate_phase2_data(num_events: int = 1200):
    """
    Simula 1200 trades variando escenarios para probar causalidad.
    - 400 trades en High Volatility (Win Rate bajo simulado)
    - 400 trades en Low Volatility (Win Rate medio)
    - 400 trades en Trending Strong (Win Rate alto)
    """
    logger.info(f"🧬 Iniciando Simulación Fase 2: Generando {num_events} trayectorias...")
    
    bridge_path = "aipha_memory/evolutionary_bridge.jsonl"
    
    scenarios = [
        {"name": "HIGH_VOL_CRISIS", "vol": "HIGH", "trend": "HOSTILE", "count": 400},
        {"name": "LOW_VOL_RANGING", "vol": "LOW", "trend": "NEUTRAL", "count": 400},
        {"name": "STRONG_TREND_BULL", "vol": "NORMAL", "trend": "FRIENDLY", "count": 400}
    ]
    
    total_generated = 0
    start_time = datetime.now() - timedelta(days=60) # 2 meses de historia
    
    with open(bridge_path, "a") as f:
        for scen in scenarios:
            logger.info(f"   ⚗️ Generando escenario: {scen['name']}")
            
            for i in range(scen['count']):
                current_time = start_time + timedelta(hours=total_generated)
                
                # Generar trayectoria estocástica
                traj = generate_random_trajectory(
                    mean_outcome=0, 
                    volatility=scen['vol'], 
                    trend_type=scen['trend']
                )
                
                # Crear objeto de evidencia
                evidence = {
                    "event_id": f"sim_{int(current_time.timestamp())}_{i}",
                    "timestamp": current_time.isoformat(),
                    "signal_type": "triple_coincidence",
                    "side": random.choice([1, -1]),
                    "zone_id": random.randint(100, 900),
                    "trend_r2": round(random.uniform(0.4, 0.95), 2),
                    "outcome": {
                        "label_ordinal": traj['label'],
                        "mfe_atr": traj['mfe'],
                        "mae_atr": traj['mae'],
                        "highest_tp": traj['highest_tp']
                    },
                    "causal_tags": [scen['name'], scen['vol'], scen['trend']]
                }
                
                f.write(json.dumps(evidence) + "\n")
                total_generated += 1
                
    logger.info(f"✅ Simulación Completa. {total_generated} eventos inyectados en {bridge_path}")

if __name__ == "__main__":
    simulate_phase2_data()
