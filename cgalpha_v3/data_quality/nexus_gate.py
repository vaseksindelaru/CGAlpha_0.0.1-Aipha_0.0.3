import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional

log = logging.getLogger("dq-gates")

class DQResult:
    def __init__(self, check_id: str, success: bool, message: str):
        self.check_id = check_id
        self.success = success
        self.message = message

def check_oos_resilience(retest_df: pd.DataFrame, min_density: int = 25) -> bool:
    """Verifica si el backtest tiene densidad suficiente (Bloqueador 2)."""
    return len(retest_df) >= min_density

class NexusGate:
    """
    NexusGate — Validador de Integridad Causal.
    Mide la ΔCausal (Distancia entre distribución Live vs Training).
    """
    def __init__(self, baseline_signature: Dict[str, Any] = None):
        # Baseline por defecto (basado en Phase 1)
        self.baseline = baseline_signature or {
            "obi_mean": 0.05,
            "obi_std": 0.35,
            "delta_mean": 0.0,
            "delta_std": 100.0
        }
        self.threshold = 0.25  # 25% de deriva permitida

    def calculate_delta_causal(self, live_buffer: List[Dict]) -> float:
        """
        Calcula la deriva causal usando la diferencia de momentos estadísticos.
        """
        if not live_buffer or len(live_buffer) < 10:
             return 0.0 # No hay datos suficientes
             
        # Extraer métricas de OBI
        obi_vals = [d.get('obi_10', 0) for d in live_buffer if d.get('obi_10') is not None]
        if not obi_vals: return 0.0
        
        live_mean = sum(obi_vals) / len(obi_vals)
        live_std = (sum((x - live_mean)**2 for x in obi_vals) / len(obi_vals))**0.5
        
        # Comparar con baseline (Deriva de OBI normalizada)
        mean_drift = abs(live_mean - self.baseline["obi_mean"]) / (self.baseline["obi_std"] + 1e-6)
        std_drift = abs(live_std - self.baseline["obi_std"]) / (self.baseline["obi_std"] + 1e-6)
        
        # ΔCausal ponderada (Momentum Causal)
        delta_causal = (0.7 * mean_drift + 0.3 * std_drift)
        return round(float(min(delta_causal, 1.0)), 4)

    def is_safe(self, delta_causal: float) -> bool:
        """Determina si el gate permite el paso de señales."""
        return delta_causal <= self.threshold
