"""
Script para poblar la memoria con datos históricos simulados.
Esto permite que el ChangeProposer detecte tendencias de inmediato.
"""
import sys
import os
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.memory_manager import MemoryManager

def populate_historical_data():
    memory = MemoryManager()
    
    print("Poblando memoria con datos históricos simulados...")
    
    # Simular degradación en Trading (Sharpe Ratio)
    # 14 días con Sharpe alto (2.0)
    for _ in range(14):
        memory.record_metric("Trading", "sharpe_ratio", 2.0)
    
    # 14 días con Sharpe bajo (1.4) -> Degradación detectada
    for _ in range(14):
        memory.record_metric("Trading", "sharpe_ratio", 1.4)
        
    # Simular mejora en Oracle (Accuracy)
    # 14 días con Accuracy media (0.80)
    for _ in range(14):
        memory.record_metric("Oracle", "accuracy", 0.80)
    
    # 14 días con Accuracy alta (0.88) -> Mejora detectada
    for _ in range(14):
        memory.record_metric("Oracle", "accuracy", 0.88)

    print("✅ Memoria poblada con éxito.")

if __name__ == "__main__":
    populate_historical_data()
