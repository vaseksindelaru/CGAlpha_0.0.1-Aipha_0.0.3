#!/usr/bin/env python3
"""
VWAP + OBI + Cumulative Delta: Implementación Completa
Código funcional para integración CGAlpha v2
"""

from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple
from collections import deque
import statistics


# ============================================================================
# 1. VWAP REAL-TIME (Barrera Dinámica)
# ============================================================================

@dataclass
class Tick:
    price: float
    quantity: float
    timestamp: float


class RealtimeVWAPBarrier:
    """
    Cálculo VWAP en tiempo real con desviación estándar
    Reemplaza: ATR(14) que requería 14 velas cerradas
    """
    
    def __init__(self, window_ticks: int = 300):
        self.ticks: deque = deque(maxlen=window_ticks)
        self.vwap_value: Optional[float] = None
        self.vwap_std: Optional[float] = None
    
    def on_tick(self, price: float, quantity: float, timestamp: float) -> None:
        """Actualiza VWAP con cada tick del order book"""
        self.ticks.append(Tick(price=price, quantity=quantity, timestamp=timestamp))
        self._update_vwap()
    
    def _update_vwap(self) -> None:
        """Cálculo incremental: VWAP = Σ(price×qty) / Σ(qty)"""
        if not self.ticks:
            return
        
        total_pv = sum(t.price * t.quantity for t in self.ticks)
        total_qty = sum(t.quantity for t in self.ticks)
        
        if total_qty > 0:
            self.vwap_value = total_pv / total_qty
            
            # Desviación estándar para banda de volatilidad
            prices = [t.price for t in self.ticks]
            variance = sum((p - self.vwap_value) ** 2 for p in prices) / len(prices)
            self.vwap_std = variance ** 0.5
    
    def get_barrier(self, std_multiplier: float = 2.0) -> Optional[Dict]:
        """
        Retorna barrera dinámica
        Reemplaza: close > (ATR * 1.5)
        Ahora: close > VWAP + (VWAP_STD * multiplier)
        """
        if self.vwap_value is None or self.vwap_std is None:
            return None
        
        upper = self.vwap_value + (self.vwap_std * std_multiplier)
        lower = self.vwap_value - (self.vwap_std * std_multiplier)
        
        return {
            'vwap': self.vwap_value,
            'upper': upper,
            'lower': lower,
            'bandwidth': upper - lower,
            'std': self.vwap_std
        }


# ============================================================================
# 2. OBI TRIGGER (Order Book Imbalance - Confirmación)
# ============================================================================

class OrderBookImbalanceTrigger:
    """
    Valida ruptura VWAP con desequilibrio del order book
    Confirma: "¿Es ruptura REAL o falsa?"
    """
    
    def __init__(self, depth_levels: int = 10, obi_threshold: float = 0.25):
        self.depth_levels = depth_levels
        self.obi_threshold = obi_threshold
        self.obi_history: deque = deque(maxlen=10)
        self.current_obi: Optional[float] = None
    
    def on_order_book_update(self, bids: List[Tuple[float, float]], 
                            asks: List[Tuple[float, float]]) -> Optional[float]:
        """
        bids: [(price, qty), ...]
        asks: [(price, qty), ...]
        
        OBI = (bid_volume - ask_volume) / total_volume
        Escala: -1 (100% ventas) a +1 (100% compras)
        """
        
        top_bids = bids[:self.depth_levels]
        top_asks = asks[:self.depth_levels]
        
        bid_volume = sum(qty for price, qty in top_bids)
        ask_volume = sum(qty for price, qty in top_asks)
        total_volume = bid_volume + ask_volume
        
        if total_volume == 0:
            return None
        
        obi = (bid_volume - ask_volume) / total_volume
        self.current_obi = obi
        self.obi_history.append(obi)
        
        return obi
    
    def is_confirmed(self, expected_direction: str) -> bool:
        """
        Valida OBI con dirección esperada
        
        Criterios:
        1. OBI > threshold en dirección correcta
        2. OBI debe estar FORTALECIÉNDOSE (no debilitándose)
        """
        
        if not self.obi_history or self.current_obi is None:
            return False
        
        if expected_direction == 'LONG':
            # Necesito OBI BULLISH (>0.25) y creciendo
            is_bullish = self.current_obi > self.obi_threshold
            
            if len(self.obi_history) >= 2:
                is_strengthening = self.current_obi > self.obi_history[-2]
            else:
                is_strengthening = True
            
            return is_bullish and is_strengthening
        
        else:  # SHORT
            # Necesito OBI BEARISH (<-0.25) y decreciendo
            is_bearish = self.current_obi < -self.obi_threshold
            
            if len(self.obi_history) >= 2:
                is_strengthening = self.current_obi < self.obi_history[-2]
            else:
                is_strengthening = True
            
            return is_bearish and is_strengthening
    
    def get_strength(self) -> float:
        """Fuerza de la señal 0-1"""
        return abs(self.current_obi) if self.current_obi else 0
    
    def get_metrics(self) -> Dict:
        return {
            'current_obi': self.current_obi,
            'obi_history': list(self.obi_history),
            'strength': self.get_strength()
        }


# ============================================================================
# 3. CUMULATIVE DELTA (Reversión Automática)
# ============================================================================

@dataclass
class TradeEvent:
    buy_volume: float
    sell_volume: float
    timestamp: float
    delta: float  # buy_volume - sell_volume


class CumulativeDeltaReversal:
    """
    Detecta reversión cuando flujo de órdenes se agota
    Acumula diferencia BUY - SELL en ventana de tiempo
    """
    
    def __init__(self, window_minutes: float = 1.0):
        self.trades: deque = deque()
        self.window_minutes = window_minutes
        self.cumulative_delta = 0.0
        self.delta_history: deque = deque(maxlen=100)
    
    def on_trade_tick(self, buy_volume: float, sell_volume: float, 
                     timestamp: float) -> float:
        """
        Registra trade y actualiza delta acumulado
        """
        delta = buy_volume - sell_volume
        self.cumulative_delta += delta
        
        trade = TradeEvent(
            buy_volume=buy_volume,
            sell_volume=sell_volume,
            timestamp=timestamp,
            delta=delta
        )
        
        self.trades.append(trade)
        
        # Limpiar trades fuera de ventana
        cutoff_time = timestamp - (self.window_minutes * 60)
        while self.trades and self.trades[0].timestamp < cutoff_time:
            self.trades.popleft()
        
        # Recalcular acumulado (robusto)
        self.cumulative_delta = sum(t.delta for t in self.trades)
        self.delta_history.append(self.cumulative_delta)
        
        return self.cumulative_delta
    
    def detect_reversal(self, position_side: str, 
                       threshold_percentile: int = 75) -> Optional[Dict]:
        """
        Detecta reversión cuando delta alcanza extremo
        
        LONG: Si CumDelta invierte a NEGATIVO → exit
        SHORT: Si CumDelta invierte a POSITIVO → exit
        """
        
        if len(self.delta_history) < 10:
            return None
        
        current_delta = self.delta_history[-1]
        recent_history = list(self.delta_history)[-20:]
        sorted_deltas = sorted(recent_history)
        
        # Percentiles
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
                reversal_signal = {
                    'strength': 'STRONG',
                    'reason': f'CumDelta extremo ({current_delta:.0f})',
                    'exit_pct': 1.0
                }
            elif current_delta < p25:
                reversal_signal = {
                    'strength': 'WEAK',
                    'reason': f'CumDelta bajo ({current_delta:.0f})',
                    'exit_pct': 0.5
                }
        
        else:  # SHORT
            if current_delta > p90:
                reversal_signal = {
                    'strength': 'STRONG',
                    'reason': f'CumDelta extremo ({current_delta:.0f})',
                    'exit_pct': 1.0
                }
            elif current_delta > p75:
                reversal_signal = {
                    'strength': 'WEAK',
                    'reason': f'CumDelta alto ({current_delta:.0f})',
                    'exit_pct': 0.5
                }
        
        return reversal_signal
    
    def get_exhaustion(self, position_side: str) -> float:
        """
        Retorna agotamiento 0-1
        0 = sin agotamiento, 1 = agotamiento extremo
        """
        if len(self.delta_history) < 5:
            return 0.0
        
        current = self.delta_history[-1]
        recent = list(self.delta_history)[-20:]
        
        max_recent = max(recent)
        min_recent = min(recent)
        range_recent = max_recent - min_recent
        
        if range_recent == 0:
            return 0.0
        
        if position_side == 'LONG':
            exhaustion = (max_recent - current) / range_recent
        else:
            exhaustion = (current - min_recent) / range_recent
        
        return min(1.0, exhaustion)
    
    def get_metrics(self) -> Dict:
        return {
            'current_cumulative_delta': self.cumulative_delta,
            'history_length': len(self.delta_history),
            'max_recent': max(self.delta_history) if self.delta_history else None,
            'min_recent': min(self.delta_history) if self.delta_history else None,
        }


# ============================================================================
# 4. INTEGRACIÓN COMPLETA: Motor Scalping
# ============================================================================

class ScalpingTradingEngine:
    """
    Motor CGAlpha v2 con VWAP + OBI + Cumulative Delta
    Reemplaza ATR completamente
    """
    
    def __init__(self, symbol: str = 'EURUSD'):
        self.symbol = symbol
        
        # Indicadores nuevos
        self.vwap = RealtimeVWAPBarrier(window_ticks=300)
        self.obi = OrderBookImbalanceTrigger(depth_levels=10)
        self.cumulative_delta = CumulativeDeltaReversal(window_minutes=1.0)
        
        # Estado
        self.position_open = False
        self.position_side: Optional[str] = None
        self.entry_price: Optional[float] = None
        self.entry_time: Optional[float] = None
        self.last_entry_time: Optional[float] = None
        self.min_entry_interval = 0.5  # segundos
        
        # Histórico
        self.trades: List[Dict] = []
    
    def on_order_book_update(self, bids: List[Tuple[float, float]],
                            asks: List[Tuple[float, float]], 
                            timestamp: float) -> Optional[Dict]:
        """
        Procesa actualización del order book
        Retorna: acción (ENTRY/HOLD/EXIT) o None
        """
        
        mid_price = (bids[0][0] + asks[0][0]) / 2
        
        # 1. Actualizar VWAP
        total_qty = bids[0][1] + asks[0][1]
        self.vwap.on_tick(price=mid_price, quantity=total_qty, timestamp=timestamp)
        
        # 2. Actualizar OBI
        self.obi.on_order_book_update(bids, asks)
        
        # 3. Validar entrada si no hay posición
        if not self.position_open:
            entry_signal = self._validate_entry(mid_price, timestamp)
            if entry_signal:
                return entry_signal
        
        return None
    
    def on_trade_tick(self, buy_volume: float, sell_volume: float,
                     timestamp: float) -> Optional[Dict]:
        """
        Procesa ejecución de trade
        Actualiza Cumulative Delta y evalúa stops
        """
        
        self.cumulative_delta.on_trade_tick(buy_volume, sell_volume, timestamp)
        
        # Evaluar stop si hay posición
        if self.position_open:
            stop_action = self._evaluate_stop(timestamp)
            if stop_action:
                return stop_action
        
        return None
    
    def _validate_entry(self, mid_price: float, timestamp: float) -> Optional[Dict]:
        """
        Pipeline entrada: VWAP → OBI → Confirmación
        """
        
        # Check anti-bounce
        if self.last_entry_time:
            time_since_last = timestamp - self.last_entry_time
            if time_since_last < self.min_entry_interval:
                return None
        
        barrier = self.vwap.get_barrier(std_multiplier=2.0)
        if not barrier:
            return None
        
        # Detectar breakout VWAP
        long_breakout = mid_price > barrier['upper']
        short_breakout = mid_price < barrier['lower']
        
        if not (long_breakout or short_breakout):
            return None
        
        # Confirmar con OBI
        expected_direction = 'LONG' if long_breakout else 'SHORT'
        
        if not self.obi.is_confirmed(expected_direction):
            return None
        
        # ENTRADA VALIDADA
        self.position_open = True
        self.position_side = expected_direction
        self.entry_price = mid_price
        self.entry_time = timestamp
        self.last_entry_time = timestamp
        
        return {
            'action': 'ENTRY',
            'side': expected_direction,
            'price': mid_price,
            'vwap': barrier['vwap'],
            'obi_strength': self.obi.get_strength(),
            'reason': f'VWAP break + OBI {expected_direction}'
        }
    
    def _evaluate_stop(self, timestamp: float) -> Optional[Dict]:
        """
        Evalúa stops dinámicos basados en Cumulative Delta
        """
        
        reversal = self.cumulative_delta.detect_reversal(self.position_side)
        
        if not reversal:
            return None
        
        exit_pct = reversal['exit_pct']
        
        self.position_open = (exit_pct < 1.0)  # Si es salida parcial, queda abierto
        
        return {
            'action': 'EXIT',
            'exit_pct': exit_pct,
            'reason': reversal['reason'],
            'strength': reversal['strength'],
            'duration_sec': timestamp - self.entry_time
        }
    
    def get_status(self) -> Dict:
        """Status actual del motor"""
        return {
            'position_open': self.position_open,
            'position_side': self.position_side,
            'entry_price': self.entry_price,
            'vwap_metrics': self.vwap.get_barrier(),
            'obi_metrics': self.obi.get_metrics(),
            'cumulative_delta_metrics': self.cumulative_delta.get_metrics(),
            'num_trades': len(self.trades)
        }


# ============================================================================
# 5. BACKTESTER SIMPLE (para demo)
# ============================================================================

def run_backtest_demo():
    """
    Demo: Simula 10 ticks de mercado
    Muestra cómo funcionan VWAP, OBI, CumDelta
    """
    
    print("=" * 80)
    print("SCALPING ENGINE BACKTEST: VWAP + OBI + Cumulative Delta")
    print("=" * 80)
    
    engine = ScalpingTradingEngine(symbol='EURUSD')
    
    # Simulación de datos
    tick_data = [
        # (timestamp, bids, asks, buy_vol, sell_vol, description)
        (1000, [(1.0850, 50000), (1.0849, 75000)],
               [(1.0851, 30000), (1.0852, 45000)], 45000, 25000, "Inicio"),
        (1001, [(1.0851, 55000), (1.0850, 80000)],
               [(1.0852, 28000), (1.0853, 40000)], 50000, 20000, "Break up 1"),
        (1002, [(1.0852, 60000), (1.0851, 85000)],
               [(1.0853, 25000), (1.0854, 35000)], 55000, 18000, "Break up 2"),
        (1003, [(1.0853, 58000), (1.0852, 82000)],
               [(1.0854, 23000), (1.0855, 32000)], 52000, 19000, "Momentum up"),
        (1004, [(1.0854, 62000), (1.0853, 88000)],
               [(1.0855, 21000), (1.0856, 30000)], 60000, 15000, "Strong momentum"),
        (1005, [(1.0855, 65000), (1.0854, 90000)],
               [(1.0856, 19000), (1.0857, 28000)], 65000, 12000, "Entrada?"),
        (1006, [(1.0851, 40000), (1.0850, 60000)],
               [(1.0852, 55000), (1.0853, 70000)], 30000, 60000, "Reversión 1"),
        (1007, [(1.0850, 35000), (1.0849, 55000)],
               [(1.0851, 60000), (1.0852, 75000)], 25000, 70000, "Reversión 2"),
    ]
    
    for idx, (ts, bids, asks, buy_vol, sell_vol, desc) in enumerate(tick_data, 1):
        print(f"\n--- TICK {idx}: {desc} (t={ts}) ---")
        
        # Order book update
        entry_signal = engine.on_order_book_update(bids, asks, ts)
        
        # Trade tick
        exit_signal = engine.on_trade_tick(buy_vol, sell_vol, ts)
        
        # Mostrar estado
        mid = (bids[0][0] + asks[0][0]) / 2
        print(f"Mid price: {mid:.4f}")
        print(f"OBI: {engine.obi.get_strength():+.2%}")
        print(f"CumDelta: {engine.cumulative_delta.cumulative_delta:+.0f}")
        
        barrier = engine.vwap.get_barrier()
        if barrier:
            print(f"VWAP: {barrier['vwap']:.4f} ± {barrier['std']:.4f}")
        
        if entry_signal:
            print(f">>> ENTRY SIGNAL: {entry_signal['reason']}")
        
        if exit_signal:
            print(f"<<< EXIT SIGNAL: {exit_signal['reason']}")
        
        status = engine.get_status()
        print(f"Position: {status['position_side'] or 'CLOSED'}")


if __name__ == '__main__':
    run_backtest_demo()
