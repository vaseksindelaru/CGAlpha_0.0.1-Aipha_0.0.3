"""
Cumulative Delta - Detector de reversión automática
Suma acumulada de (Buy Vol - Sell Vol)
Detecta agotamiento de movimiento = Exit automático
"""

from collections import deque
from typing import Optional, Dict
import statistics


class CumulativeDeltaReversal:
    """
    Detecta reversión basada en agotamiento de flujo.
    Reemplaza stops estáticos por dinámicos basados en microestructura.
    """
    
    def __init__(self, window_minutes: int = 1, history_depth: int = 100):
        """
        Args:
            window_minutes: Ventana temporal (1 minuto típico)
            history_depth: Profundidad de histórico (últimas 100 actualizaciones)
        """
        self.ticks = deque()
        self.window_minutes = window_minutes
        self.cumulative_delta = 0.0
        self.cumulative_delta_history = deque(maxlen=history_depth)
        self.history_depth = history_depth
    
    def on_trade_tick(
        self, 
        buy_volume: float, 
        sell_volume: float, 
        timestamp: float
    ) -> None:
        """
        Procesa cada ejecución de trade.
        
        Args:
            buy_volume: Volumen iniciado por comprador
            sell_volume: Volumen iniciado por vendedor
            timestamp: Timestamp del trade
        """
        
        delta = buy_volume - sell_volume
        self.cumulative_delta += delta
        
        tick = {
            'buy_vol': buy_volume,
            'sell_vol': sell_volume,
            'delta': delta,
            'cumulative': self.cumulative_delta,
            'ts': timestamp
        }
        
        self.ticks.append(tick)
        
        # Mantener ventana temporal
        cutoff_time = timestamp - (self.window_minutes * 60)
        while self.ticks and self.ticks[0]['ts'] <= cutoff_time:
            self.ticks.popleft()
        
        # Recalcular acumulado desde ventana (robusto)
        self.cumulative_delta = sum(t['delta'] for t in self.ticks)
        self.cumulative_delta_history.append(self.cumulative_delta)
    
    def detect_reversal(
        self, 
        position_side: str
    ) -> Optional[Dict]:
        """
        Detecta reversión cuando delta alcanza extremo.
        
        Args:
            position_side: 'LONG' o 'SHORT'
        
        Returns:
            {
                'strength': 'WEAK' | 'STRONG',
                'reason': str,
                'exit_level': str
            }
        """
        
        if len(self.cumulative_delta_history) < 10:
            return None
        
        current_delta = self.cumulative_delta_history[-1]
        
        # Percentiles del histórico reciente
        recent_history = list(self.cumulative_delta_history)[-100:]
        sorted_deltas = sorted(recent_history)
        
        # Calcular umbrales
        p10_idx = max(0, int(len(sorted_deltas) * 0.10) - 1)
        p25_idx = max(0, int(len(sorted_deltas) * 0.25) - 1)
        p75_idx = max(0, int(len(sorted_deltas) * 0.75) - 1)
        p90_idx = max(0, int(len(sorted_deltas) * 0.90) - 1)
        
        p10 = sorted_deltas[p10_idx]
        p25 = sorted_deltas[p25_idx]
        p75 = sorted_deltas[p75_idx]
        p90 = sorted_deltas[p90_idx]
        
        reversal_signal = None
        
        if position_side == 'LONG':
            if current_delta < p10:
                # Fuerte reversión: delta en percentil extremo bajo
                reversal_signal = {
                    'strength': 'STRONG',
                    'reason': 'CumDelta extremadamente bajo (p10)',
                    'exit_level': 'FULL (100%)',
                    'percentile': 10
                }
            elif current_delta < p25:
                # Débil reversión: delta cayó significativamente
                reversal_signal = {
                    'strength': 'WEAK',
                    'reason': 'CumDelta bajo percentil 25',
                    'exit_level': 'PARTIAL (50%)',
                    'percentile': 25
                }
        
        elif position_side == 'SHORT':
            if current_delta > p90:
                reversal_signal = {
                    'strength': 'STRONG',
                    'reason': 'CumDelta extremadamente alto (p90)',
                    'exit_level': 'FULL (100%)',
                    'percentile': 90
                }
            elif current_delta > p75:
                reversal_signal = {
                    'strength': 'WEAK',
                    'reason': 'CumDelta alto percentil 75',
                    'exit_level': 'PARTIAL (50%)',
                    'percentile': 75
                }
        
        return reversal_signal
    
    def get_exhaustion_level(self, position_side: str) -> float:
        """
        Retorna nivel de agotamiento del movimiento (0-1).
        
        Args:
            position_side: 'LONG' o 'SHORT'
        
        Returns:
            0 = sin agotamiento, 1 = agotamiento extremo
        """
        
        if len(self.cumulative_delta_history) < 5:
            return 0.0
        
        current = self.cumulative_delta_history[-1]
        recent = list(self.cumulative_delta_history)[-20:]
        
        max_recent = max(recent)
        min_recent = min(recent)
        recent_range = max_recent - min_recent
        
        if recent_range == 0:
            return 0.0
        
        if position_side == 'LONG':
            exhaustion = (max_recent - current) / recent_range
        else:  # SHORT
            exhaustion = (current - min_recent) / recent_range
        
        return min(1.0, max(0.0, exhaustion))
    
    def get_metrics(self) -> Dict:
        """Para logging"""
        recent = list(self.cumulative_delta_history)[-20:] if len(self.cumulative_delta_history) >= 20 else list(self.cumulative_delta_history)
        
        return {
            'current_cumulative_delta': self.cumulative_delta,
            'history_length': len(self.cumulative_delta_history),
            'max_recent': max(recent) if recent else None,
            'min_recent': min(recent) if recent else None,
            'range': (max(recent) - min(recent)) if recent else None,
        }
    
    def reset(self) -> None:
        """Resetea para nueva sesión"""
        self.ticks.clear()
        self.cumulative_delta = 0.0
        self.cumulative_delta_history.clear()
