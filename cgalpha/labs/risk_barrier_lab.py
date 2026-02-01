"""
Risk Barrier Lab (Lóbulo Frontal de Riesgo).
Responsable de optimizar SL, TP y Exposure basándose en evidencia causal.
"""
import logging
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class RiskBarrierLab:
    """
    Lab especializado en Gestión de Riesgo Causal.
    Analiza trayectorias (MFE/MAE) para ajustar barreras dinámicamente.
    """
    
    def __init__(self, bridge_path: Path):
        self.bridge_path = bridge_path
        
    def run_analysis(self) -> List[Dict[str, Any]]:
        """
        Ejecuta el análisis principal del Lab.
        Retorna lista de 'findings' (hallazgos).
        """
        logger.info("🧠 RiskBarrierLab: Despertando...")
        
        # 1. Cargar Datos del Puente
        df = self._load_bridge_data()
        if df.empty or len(df) < 100:
            logger.info("   💤 Insuficientes datos para inferencia causal (<100).")
            return []
            
        logger.info(f"   📊 Analizando {len(df)} trayectorias...")
        
        findings = []
        
        # 2. Análisis por Régimen (Simplificación de CATE)
        # Identificamos regímenes basándonos en 'causal_tags'
        # En la simulación usamos: HIGH_VOL_CRISIS, LOW_VOL_RANGING, STRONG_TREND_BULL
        
        regimes = df['regime'].unique()
        
        for regime in regimes:
            regime_df = df[df['regime'] == regime]
            
            # Calcular Win Rate actual (Label > 0)
            win_rate = len(regime_df[regime_df['label_ordinal'] > 0]) / len(regime_df)
            
            # Calcular Esperanza Matemática (Avg Return en R)
            # Asumimos: label 1=1R, label 2=2R, label 3=3R, label -1=-1R
            # Esto es una simplificación; idealmente usaríamos precios reales.
            r_multiples = regime_df['label_ordinal'].replace({0: -0.1}) # Time limit cost
            expectancy = r_multiples.mean()
            
            logger.info(f"      Regime: {regime:<20} | WR: {win_rate:.2%} | Exp: {expectancy:.2f}R")
            
            # 3. Generar Propuesta si detectamos anomalía u oportunidad
            if regime == "HIGH_VOL_CRISIS":
                if win_rate < 0.40:
                    # En crisis, si WR es bajo, sugerimos apretar gestión o reducir exposición
                    findings.append({
                        "type": "risk_adjustment",
                        "regime": regime,
                        "observation": f"Bajo Win Rate ({win_rate:.1%}) en Alta Volatilidad",
                        "proposal": {
                            "parameter": "Trading.confidence_threshold",
                            "action": "increase",
                            "value": 0.75, # Ser más selectivo
                            "reason": f"Protección de Capital: WR {win_rate:.1%} < 40% en Crisis."
                        },
                        "confidence": 0.95,
                        "priority": 10
                    })
            
            elif regime == "STRONG_TREND_BULL":
                if expectancy > 1.5:
                    # Si la esperanza es muy alta, podemos soltar rienda (dejar correr ganancias)
                    findings.append({
                        "type": "opportunity_seizing",
                        "regime": regime,
                        "observation": f"Alta Esperanza ({expectancy:.2f}R) en Tendencia Fuerte",
                        "proposal": {
                            "parameter": "Trading.tp_factor",
                            "action": "increase",
                            "value": 3.0, # Buscar home runs
                            "reason": f"Maximización: Esperanza {expectancy:.2f}R sugiere dejar correr profits."
                        },
                        "confidence": 0.85,
                        "priority": 8
                    })

        return findings

    def _load_bridge_data(self) -> pd.DataFrame:
        """Carga y estructura datos del JSONL."""
        data = []
        if not self.bridge_path.exists():
            return pd.DataFrame()
            
        try:
            with open(self.bridge_path, 'r') as f:
                for line in f:
                    if not line.strip(): continue
                    try:
                        evt = json.loads(line)
                        
                        # Skip metadata lines or malformed events
                        if 'timestamp' not in evt or 'outcome' not in evt:
                            continue

                        # Aplanar estructura para DataFrame
                        row = {
                            'timestamp': evt['timestamp'],
                            'label_ordinal': evt['outcome']['label_ordinal'],
                            'mfe': evt['outcome']['mfe_atr'],
                            'mae': evt['outcome']['mae_atr'],
                            # Extraer regimen del tag (hack para simulación)
                            'regime': evt.get('causal_tags', ['UNKNOWN'])[0] if evt.get('causal_tags') else 'UNKNOWN'
                        }
                        data.append(row)
                    except json.JSONDecodeError:
                        continue
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Error cargando bridge: {e}")
            return pd.DataFrame()
