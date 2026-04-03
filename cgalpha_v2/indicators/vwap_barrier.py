"""
VWAP Real-time Barrier - Reemplaza ATR(14)
Proporciona barrera dinámica con <10ms latencia
"""

from collections import deque
from typing import Optional, Dict
import statistics


class RealtimeVWAPBarrier:
    """
    Mantiene VWAP actualizado en cada tick del Order Book.
    Reemplaza ATR(14) que requería 70 minutos de datos.
    """
    
    def __init__(self, window_ticks: int = 300):
        """
        Args:
            window_ticks: Buffer de ticks (~5min a 60 ticks/sec)
        """
        self.ticks = deque(maxlen=window_ticks)
        self.window_ticks = window_ticks
        self.vwap_value: Optional[float] = None
        self.vwap_std: Optional[float] = None
        self.last_update_time = None
    
    def on_tick(self, price: float, quantity: float, timestamp: float) -> None:
        """
        Procesa tick del Order Book (WebSocket).
        Llamado en CADA actualización de mercado (<10ms).
        
        Args:
            price: Precio mid (bid + ask) / 2
            quantity: Volumen total (bid_vol + ask_vol)
            timestamp: Timestamp del tick
        """
        
        tick = {
            'price': price,
            'qty': quantity,
            'pv': price * quantity,  # Price × Volume
            'ts': timestamp
        }
        
        self.ticks.append(tick)
        self.last_update_time = timestamp
        
        # Recalcular VWAP incrementalmente
        self._update_vwap()
    
    def _update_vwap(self) -> None:
        """
        Cálculo real-time VWAP = Σ(price × qty) / Σ(qty)
        Complejidad: O(n) pero n es pequeño (~300 ticks)
        """
        
        if not self.ticks:
            self.vwap_value = None
            self.vwap_std = None
            return
        
        total_pv = sum(t['pv'] for t in self.ticks)
        total_qty = sum(t['qty'] for t in self.ticks)
        
        if total_qty > 0:
            self.vwap_value = total_pv / total_qty
            
            # Desviación estándar para banda
            prices = [t['price'] for t in self.ticks]
            
            try:
                self.vwap_std = statistics.stdev(prices)
            except statistics.StatisticsError:
                # Si todos los precios son iguales
                self.vwap_std = 0.0
    
    def get_barrier(self, std_multiplier: float = 2.0) -> Optional[Dict]:
        """
        Retorna barrera dinámica (reemplaza ATR).
        
        Args:
            std_multiplier: Multiplicador de desviación estándar
            
        Returns:
            {
                'vwap': float,        # VWAP actual
                'upper': float,       # Upper band
                'lower': float,       # Lower band
                'bandwidth': float,   # Ancho de banda
                'std': float          # Desviación estándar
            }
        """
        
        if self.vwap_value is None or self.vwap_std is None:
            return None
        
        upper_barrier = self.vwap_value + (self.vwap_std * std_multiplier)
        lower_barrier = self.vwap_value - (self.vwap_std * std_multiplier)
        
        return {
            'vwap': self.vwap_value,
            'upper': upper_barrier,
            'lower': lower_barrier,
            'bandwidth': upper_barrier - lower_barrier,
            'std': self.vwap_std,
            'ticks_count': len(self.ticks)
        }
    
    def get_metrics(self) -> Dict:
        """Para logging/debug"""
        return {
            'vwap': self.vwap_value,
            'std': self.vwap_std,
            'ticks': len(self.ticks),
            'last_update': self.last_update_time
        }
    
    def reset(self) -> None:
        """Resetea el buffer (e.g., nueva sesión de trading)"""
        self.ticks.clear()
        self.vwap_value = None
        self.vwap_std = None
