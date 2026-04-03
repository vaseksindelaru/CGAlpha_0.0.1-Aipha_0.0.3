"""
Order Book Imbalance Trigger - Confirmación de ruptura VWAP
Detecta desequilibrio BID/ASK = indicador de dirección real
"""

from collections import deque
from typing import Optional, Dict, List, Tuple


class OrderBookImbalanceTrigger:
    """
    Valida ruptura VWAP con Order Book Imbalance.
    OBI = (bid_vol - ask_vol) / (bid_vol + ask_vol)
    
    Rango: -1.0 (extremadamente bajista) a +1.0 (extremadamente alcista)
    """
    
    def __init__(self, depth_levels: int = 10, history_size: int = 5):
        """
        Args:
            depth_levels: Niveles de profundidad a analizar (top 10)
            history_size: Últimas N actualizaciones a considerar
        """
        self.depth_levels = depth_levels
        self.obi_history = deque(maxlen=history_size)
        self.obi_threshold = 0.25  # OBI > ±0.25 es señal fuerte
    
    def on_order_book_update(
        self, 
        bids: List[Tuple[float, float]], 
        asks: List[Tuple[float, float]]
    ) -> Optional[float]:
        """
        Procesa actualización del Order Book.
        
        Args:
            bids: [(price, qty), (price, qty), ...]
            asks: [(price, qty), (price, qty), ...]
        
        Returns:
            OBI value (-1 to +1) o None si no hay datos
        """
        
        # Tomar top N niveles
        top_bids = bids[:self.depth_levels]
        top_asks = asks[:self.depth_levels]
        
        bid_volume = sum(qty for price, qty in top_bids)
        ask_volume = sum(qty for price, qty in top_asks)
        
        total_volume = bid_volume + ask_volume
        
        if total_volume == 0:
            return None
        
        # Cálculo OBI: escala -1 a +1
        obi = (bid_volume - ask_volume) / total_volume
        
        self.obi_history.append(obi)
        
        return obi
    
    def is_confirmed(self, expected_direction: str) -> bool:
        """
        Valida OBI con dirección esperada.
        
        Args:
            expected_direction: 'LONG' o 'SHORT'
        
        Returns:
            Boolean - ¿Es una entrada válida?
        """
        
        if len(self.obi_history) < 1:
            return False
        
        current_obi = self.obi_history[-1]
        
        # Confirmación de señal
        if expected_direction == 'LONG':
            # Para entrada LONG: OBI BULLISH (>0.25)
            is_confirmed = current_obi > self.obi_threshold
            
            # Validación extra: OBI debe CRECER (fortalecerse)
            if len(self.obi_history) >= 2:
                is_strengthening = current_obi > self.obi_history[-2]
            else:
                is_strengthening = True
            
            return is_confirmed and is_strengthening
        
        elif expected_direction == 'SHORT':
            # Para entrada SHORT: OBI BEARISH (<-0.25)
            is_confirmed = current_obi < -self.obi_threshold
            
            # OBI debe DECRECER (hacerse más negativo)
            if len(self.obi_history) >= 2:
                is_strengthening = current_obi < self.obi_history[-2]
            else:
                is_strengthening = True
            
            return is_confirmed and is_strengthening
        
        return False
    
    def get_strength(self) -> float:
        """
        Retorna fuerza de señal 0-1.
        
        Returns:
            Valor absoluto del OBI más reciente
        """
        if not self.obi_history:
            return 0.0
        return abs(self.obi_history[-1])
    
    def get_metrics(self) -> Dict:
        """Para logging/debug"""
        return {
            'current_obi': self.obi_history[-1] if self.obi_history else None,
            'obi_history': list(self.obi_history),
            'signal_strength': self.get_strength(),
        }
    
    def reset(self) -> None:
        """Resetea el histórico"""
        self.obi_history.clear()
