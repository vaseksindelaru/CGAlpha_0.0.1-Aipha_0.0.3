"""
Exit Validator - Stop dinámico basado en Cumulative Delta
Detecta reversión automática = salida inteligente
"""

from typing import Optional, Dict
from cgalpha_v2.indicators.cumulative_delta import CumulativeDeltaReversal
from cgalpha_v2.config import EXECUTION_CONFIG


class DynamicStopWithDelta:
    """
    Stop dinámico que ajusta basado en Cumulative Delta.
    No sale a nivel fijo, sino cuando delta indica agotamiento.
    """
    
    def __init__(self):
        self.cumulative_delta = CumulativeDeltaReversal()
        self.entry_price: Optional[float] = None
        self.position_side: Optional[str] = None
        self.entry_cumulative_delta: float = 0.0
        self.max_profitable_delta: Optional[float] = None
        self.is_position_open = False
    
    def on_entry(
        self,
        entry_price: float,
        position_side: str,
        initial_delta: float
    ) -> None:
        """
        Registra entrada y baseline delta.
        
        Args:
            entry_price: Precio de entrada
            position_side: 'LONG' o 'SHORT'
            initial_delta: Cumulative delta en el momento de entrada
        """
        self.entry_price = entry_price
        self.position_side = position_side
        self.entry_cumulative_delta = initial_delta
        self.max_profitable_delta = initial_delta
        self.is_position_open = True
    
    def on_trade_tick(
        self,
        buy_volume: float,
        sell_volume: float,
        timestamp: float,
        current_price: float
    ) -> Optional[Dict]:
        """
        Procesa cada trade tick y evalúa stop.
        
        Args:
            buy_volume: Volumen comprador
            sell_volume: Volumen vendedor
            timestamp: Timestamp
            current_price: Precio actual
        
        Returns:
            {
                'action': 'PARTIAL_EXIT' | 'FULL_EXIT' | None,
                'exit_qty_pct': float,
                'reason': str,
                'delta_metrics': {...}
            }
        """
        
        if not self.is_position_open:
            return None
        
        # Actualizar delta
        self.cumulative_delta.on_trade_tick(buy_volume, sell_volume, timestamp)
        
        current_delta = self.cumulative_delta.cumulative_delta
        
        # Actualizar máximo delta favorable
        if self.position_side == 'LONG':
            if current_delta > self.max_profitable_delta:
                self.max_profitable_delta = current_delta
        else:  # SHORT
            if current_delta < self.max_profitable_delta:
                self.max_profitable_delta = current_delta
        
        # Detectar reversión
        reversal = self.cumulative_delta.detect_reversal(self.position_side)
        
        if reversal is None:
            return None
        
        if reversal['strength'] == 'WEAK':
            return {
                'action': 'PARTIAL_EXIT',
                'exit_qty_pct': EXECUTION_CONFIG['partial_exit_pct'],
                'reason': reversal['reason'],
                'stop_type': 'delta_reversal_weak',
                'delta_metrics': self.cumulative_delta.get_metrics()
            }
        
        elif reversal['strength'] == 'STRONG':
            self.is_position_open = False
            return {
                'action': 'FULL_EXIT',
                'exit_qty_pct': EXECUTION_CONFIG['full_exit_pct'],
                'reason': reversal['reason'],
                'stop_type': 'delta_reversal_strong',
                'delta_metrics': self.cumulative_delta.get_metrics()
            }
        
        return None
    
    def get_exhaustion_level(self) -> float:
        """Retorna nivel de agotamiento 0-1"""
        if not self.is_position_open:
            return 0.0
        return self.cumulative_delta.get_exhaustion_level(self.position_side)
    
    def close_position(self) -> None:
        """Cierra posición y resetea"""
        self.is_position_open = False
        self.cumulative_delta.reset()
        self.entry_price = None
        self.position_side = None
