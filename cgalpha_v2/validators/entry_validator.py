"""
Entry Validator - Pipeline completo de validación
Integra VWAP → OBI → Entrada segura
"""

from typing import Optional, Dict, List, Tuple
from cgalpha_v2.indicators.vwap_barrier import RealtimeVWAPBarrier
from cgalpha_v2.indicators.obi_trigger import OrderBookImbalanceTrigger
from cgalpha_v2.config import EXECUTION_CONFIG


class ScalpingEntryValidator:
    """
    Pipeline completo: VWAP → OBI → Entrada
    Flujo sincronizado de validación en <15ms
    """
    
    def __init__(self):
        self.vwap_barrier = RealtimeVWAPBarrier()
        self.obi_trigger = OrderBookImbalanceTrigger()
        self.last_entry_time = None
        self.min_entry_interval = EXECUTION_CONFIG['min_entry_interval_ms'] / 1000.0
    
    def validate_entry_signal(
        self,
        current_price: float,
        position_side: str,
        bids: List[Tuple[float, float]],
        asks: List[Tuple[float, float]],
        order_book_tick: Dict
    ) -> Dict:
        """
        Pipeline completo: VWAP → OBI → Entrada.
        
        Args:
            current_price: Precio de mercado actual
            position_side: 'LONG' o 'SHORT'
            bids: [(price, qty), ...]
            asks: [(price, qty), ...]
            order_book_tick: {'mid_price', 'volume', 'timestamp', ...}
        
        Returns:
            {
                'valid': Boolean,
                'reason': str,
                'confidence': 0-1,
                'entry_price': float,
                'metrics': {...}
            }
        """
        
        now = order_book_tick['timestamp']
        
        # 1. REVISAR anti-bounce
        if self.last_entry_time:
            time_since_last = now - self.last_entry_time
            if time_since_last < self.min_entry_interval:
                return {
                    'valid': False,
                    'reason': f'Anti-bounce cooldown ({time_since_last:.3f}s)',
                    'confidence': 0.0,
                    'entry_price': None,
                    'metrics': {}
                }
        
        # 2. EVALUAR barrera VWAP
        self.vwap_barrier.on_tick(
            price=order_book_tick['mid_price'],
            quantity=order_book_tick['volume'],
            timestamp=now
        )
        
        barrier = self.vwap_barrier.get_barrier()
        
        if barrier is None:
            return {
                'valid': False,
                'reason': 'VWAP aún no calculado (sin datos)',
                'confidence': 0.0,
                'entry_price': None,
                'metrics': {}
            }
        
        # Detectar ruptura
        if position_side == 'LONG':
            is_breakout = current_price > barrier['upper']
            barrier_name = 'upper'
        else:  # SHORT
            is_breakout = current_price < barrier['lower']
            barrier_name = 'lower'
        
        if not is_breakout:
            return {
                'valid': False,
                'reason': f'Sin ruptura VWAP (precio no toca {barrier_name})',
                'confidence': 0.0,
                'entry_price': None,
                'metrics': {'barrier': barrier}
            }
        
        # 3. CONFIRMAR con OBI
        self.obi_trigger.on_order_book_update(bids, asks)
        
        is_obi_confirmed = self.obi_trigger.is_confirmed(position_side)
        obi_strength = self.obi_trigger.get_strength()
        
        if not is_obi_confirmed:
            return {
                'valid': False,
                'reason': f'OBI sin confirmación (fuerza: {obi_strength:.2f})',
                'confidence': obi_strength * 0.5,
                'entry_price': None,
                'metrics': {
                    'barrier': barrier,
                    'obi': self.obi_trigger.get_metrics()
                }
            }
        
        # 4. ENTRADA VALIDADA ✓
        self.last_entry_time = now
        
        distance_to_barrier = abs(current_price - barrier[barrier_name])
        confidence = min(1.0, obi_strength * (distance_to_barrier / barrier['bandwidth']))
        
        return {
            'valid': True,
            'reason': f'Ruptura VWAP + OBI confirmado ({obi_strength:.2f})',
            'confidence': confidence,
            'entry_price': current_price,
            'metrics': {
                'barrier': barrier,
                'obi': self.obi_trigger.get_metrics(),
                'distance_to_barrier': distance_to_barrier,
                'vwap_value': barrier['vwap'],
                'bandwidth': barrier['bandwidth']
            }
        }
    
    def reset(self) -> None:
        """Resetea validador para nueva sesión"""
        self.vwap_barrier.reset()
        self.obi_trigger.reset()
        self.last_entry_time = None
