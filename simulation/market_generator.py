import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Tuple

class MarketGenerator:
    """
    Generador de datos de mercado sintéticos para pruebas de ciclo de vida.
    Soporta diferentes regímenes de mercado.
    """
    
    def __init__(self, start_price: float = 100.0):
        self.current_price = start_price
        self.current_time = datetime(2025, 1, 1, 0, 0)
        
    def generate_day(self, regime: str = "NORMAL") -> pd.DataFrame:
        """
        Genera 24 horas de datos OHLC (velas de 1 hora).
        
        Args:
            regime: "NORMAL", "VOLATILE", "FLAT", "TRENDING_UP", "TRENDING_DOWN"
        """
        periods = 24
        dates = [self.current_time + timedelta(hours=i) for i in range(periods)]
        
        # Configurar parámetros según régimen
        volatility = 0.002 # 0.2% por vela base
        trend = 0.0
        
        if regime == "VOLATILE":
            volatility = 0.01 # 1.0% por vela (Muy alto)
        elif regime == "FLAT":
            volatility = 0.0005 # 0.05% por vela (Muy bajo)
        elif regime == "TRENDING_UP":
            trend = 0.005 # +0.5% por vela
        elif regime == "TRENDING_DOWN":
            trend = -0.005 # -0.5% por vela
            
        ohlc_data = []
        
        for _ in range(periods):
            # Random walk con drift
            change = np.random.normal(trend, volatility)
            open_p = self.current_price
            close_p = open_p * (1 + change)
            
            # High/Low basados en volatilidad
            high_p = max(open_p, close_p) * (1 + abs(np.random.normal(0, volatility/2)))
            low_p = min(open_p, close_p) * (1 - abs(np.random.normal(0, volatility/2)))
            
            ohlc_data.append({
                "Open": open_p,
                "High": high_p,
                "Low": low_p,
                "Close": close_p
            })
            
            self.current_price = close_p
            
        self.current_time += timedelta(days=1)
        
        df = pd.DataFrame(ohlc_data, index=dates)
        return df
