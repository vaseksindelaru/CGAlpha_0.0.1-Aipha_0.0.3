"""
cgalpha_v3/indicators/legacy_signals.py - Legacy Microstructure Indicators (Migrated from v2)
Misión: Análisis de flujo de órdenes (VWAP, Delta, OBI) de alta fidelidad.
"""

import statistics
from collections import deque
from typing import Optional, Dict, List, Tuple

class RealtimeVWAP:
    """VWAP Real-time Barrier (Migrated from v2)."""
    def __init__(self, window_ticks: int = 300):
        self.ticks = deque(maxlen=window_ticks)
        self.vwap_value: Optional[float] = None
        self.vwap_std: Optional[float] = None

    def on_tick(self, price: float, quantity: float):
        self.ticks.append({'price': price, 'qty': quantity, 'pv': price * quantity})
        self._update()

    def _update(self):
        if not self.ticks: return
        total_pv = sum(t['pv'] for t in self.ticks)
        total_qty = sum(t['qty'] for t in self.ticks)
        if total_qty > 0:
            self.vwap_value = total_pv / total_qty
            prices = [t['price'] for t in self.ticks]
            self.vwap_std = statistics.stdev(prices) if len(prices) > 1 else 0.0

class CumulativeDelta:
    """Cumulative Delta Reversal Detector (Migrated from v2)."""
    def __init__(self, history_depth: int = 100):
        self.cumulative_delta = 0.0
        self.history = deque(maxlen=history_depth)

    def on_trade(self, buy_vol: float, sell_vol: float):
        delta = buy_vol - sell_vol
        self.cumulative_delta += delta
        self.history.append(self.cumulative_delta)

    def get_reversal_signal(self, side: str) -> Optional[str]:
        if len(self.history) < 20: return None
        # Lógica simplificada de percentiles
        curr = self.history[-1]
        sorted_h = sorted(list(self.history))
        p10 = sorted_h[int(len(sorted_h)*0.1)]
        p90 = sorted_h[int(len(sorted_h)*0.9)]
        if side == 'LONG' and curr < p10: return "STRONG_REVERSAL"
        if side == 'SHORT' and curr > p90: return "STRONG_REVERSAL"
        return None

class OBITrigger:
    """Order Book Imbalance Trigger (Migrated from v2)."""
    def __init__(self, depth: int = 10):
        self.depth = depth
        self.obi = 0.0

    def update(self, bids: List[Tuple[float, float]], asks: List[Tuple[float, float]]):
        b_vol = sum(q for p, q in bids[:self.depth])
        a_vol = sum(q for p, q in asks[:self.depth])
        if (b_vol + a_vol) > 0:
            self.obi = (b_vol - a_vol) / (b_vol + a_vol)
        return self.obi
