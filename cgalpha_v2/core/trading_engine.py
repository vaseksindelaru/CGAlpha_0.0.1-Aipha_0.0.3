"""
CGAlpha v2 Trading Engine - Core
Integra VWAP + OBI + Cumulative Delta en pipeline único
"""

from typing import Optional, Dict, List, Tuple
from datetime import datetime
import logging

from cgalpha_v2.validators.entry_validator import ScalpingEntryValidator
from cgalpha_v2.validators.exit_validator import DynamicStopWithDelta
from cgalpha_v2.config import (
    VWAP_CONFIG,
    OBI_CONFIG,
    CUMULATIVE_DELTA_CONFIG,
    EXECUTION_CONFIG,
    LOGGING_CONFIG,
    VALIDATION_CONFIG
)


logger = logging.getLogger(__name__)


class CGAlphaScalpingEngine:
    """
    Motor de escalping CGAlpha v2.
    
    Pipeline:
    1. Order Book Update → VWAP recalcula barrera
    2. VWAP ruptura + OBI confirmado → ENTRADA
    3. Trade ticks → Cumulative Delta rastrea reversión
    4. Delta extremo → SALIDA automática
    
    Latencia total: <15ms
    """
    
    def __init__(self, symbol: str = 'EURUSD'):
        self.symbol = symbol
        self.logger = logging.getLogger(f'{__name__}.{symbol}')
        
        # Validadores
        self.entry_validator = ScalpingEntryValidator()
        self.exit_validator = DynamicStopWithDelta()
        
        # Estado de posición
        self.position_open = False
        self.position_side: Optional[str] = None
        self.entry_price: Optional[float] = None
        self.entry_time: Optional[float] = None
        self.entry_qty: float = 0.0
        self.current_price: float = 0.0
        
        # Métricas
        self.trades_opened = 0
        self.trades_closed = 0
        self.partial_exits = 0
        self.full_exits = 0
    
    def on_order_book_update(
        self,
        bids: List[Tuple[float, float]],
        asks: List[Tuple[float, float]],
        timestamp: float
    ) -> Optional[Dict]:
        """
        Procesa actualización de Order Book (WebSocket).
        Llamado cada tick (~100-500ms típicamente).
        
        Retorna: Señal de entrada si es válida, None otherwise
        """
        
        if len(bids) == 0 or len(asks) == 0:
            return None
        
        mid_price = (bids[0][0] + asks[0][0]) / 2
        bid_ask_volume = bids[0][1] + asks[0][1]
        spread = asks[0][0] - bids[0][0]
        
        self.current_price = mid_price
        
        # Revisar si spread es demasiado grande
        if spread > EXECUTION_CONFIG['max_spread_pips'] * 0.0001:  # Convertir pips
            self.logger.debug(f'Spread muy grande: {spread:.6f}, ignorando')
            return None
        
        # Preparar tick
        order_book_tick = {
            'mid_price': mid_price,
            'volume': bid_ask_volume,
            'timestamp': timestamp,
            'spread': spread,
            'bid': bids[0][0],
            'ask': asks[0][0]
        }
        
        # ===== SI NO HAY POSICIÓN: REVISAR ENTRADA =====
        if not self.position_open:
            entry_signal = self._check_entry_signal(
                current_price=mid_price,
                bids=bids,
                asks=asks,
                order_book_tick=order_book_tick
            )
            
            return entry_signal
        
        # ===== SI HAY POSICIÓN: MANTENER ACTUALIZADO =====
        else:
            # Solo actualizar VWAP para tracking
            self.entry_validator.vwap_barrier.on_tick(
                price=mid_price,
                quantity=bid_ask_volume,
                timestamp=timestamp
            )
            return None
    
    def on_trade_tick(
        self,
        buy_volume: float,
        sell_volume: float,
        timestamp: float
    ) -> Optional[Dict]:
        """
        Procesa trade tick (cada ejecución).
        Actualiza Cumulative Delta.
        Evalúa stops.
        
        Retorna: Señal de salida si es válida, None otherwise
        """
        
        if not self.position_open:
            return None
        
        # Evaluar exit
        exit_signal = self.exit_validator.on_trade_tick(
            buy_volume=buy_volume,
            sell_volume=sell_volume,
            timestamp=timestamp,
            current_price=self.current_price
        )
        
        if exit_signal:
            self._execute_exit(exit_signal)
        
        return exit_signal
    
    def _check_entry_signal(
        self,
        current_price: float,
        bids: List[Tuple[float, float]],
        asks: List[Tuple[float, float]],
        order_book_tick: Dict
    ) -> Optional[Dict]:
        """
        Valida señal de entrada: VWAP + OBI.
        Intenta LONG y SHORT.
        
        Retorna mejor oportunidad o None.
        """
        
        best_signal = None
        best_confidence = 0.0
        
        for position_side in ['LONG', 'SHORT']:
            validation = self.entry_validator.validate_entry_signal(
                current_price=current_price,
                position_side=position_side,
                bids=bids,
                asks=asks,
                order_book_tick=order_book_tick
            )
            
            if validation['valid'] and validation['confidence'] > best_confidence:
                best_signal = validation
                best_confidence = validation['confidence']
                best_signal['position_side'] = position_side
        
        if best_signal and best_confidence >= VALIDATION_CONFIG['confidence_threshold']:
            # Ejecutar entrada
            self._execute_entry(best_signal)
            return best_signal
        
        return None
    
    def _execute_entry(self, signal: Dict) -> None:
        """Ejecuta entrada de posición"""
        
        self.position_open = True
        self.position_side = signal['position_side']
        self.entry_price = signal['entry_price']
        self.entry_time = signal['metrics']['barrier']['ticks_count']  # Usar como placeholder
        self.entry_qty = 1.0  # Simplificado
        
        # Inicializar exit validator
        initial_delta = self.exit_validator.cumulative_delta.cumulative_delta
        self.exit_validator.on_entry(
            entry_price=self.entry_price,
            position_side=self.position_side,
            initial_delta=initial_delta
        )
        
        self.trades_opened += 1
        
        log_msg = (
            f"[ENTRY] {self.position_side} @ {self.entry_price:.5f} | "
            f"Confidence: {signal['confidence']:.2%} | "
            f"Reason: {signal['reason']}"
        )
        self.logger.info(log_msg)
        
        if LOGGING_CONFIG['log_entry_signals']:
            print(log_msg)
    
    def _execute_exit(self, signal: Dict) -> None:
        """Ejecuta salida de posición"""
        
        pnl = (self.current_price - self.entry_price) * (1 if self.position_side == 'LONG' else -1)
        
        log_msg = (
            f"[EXIT] {signal['stop_type']} | "
            f"Qty: {signal['exit_qty_pct']:.0%} | "
            f"PnL: {pnl:.5f} | "
            f"Reason: {signal['reason']}"
        )
        self.logger.info(log_msg)
        
        if LOGGING_CONFIG['log_exit_signals']:
            print(log_msg)
        
        if signal['exit_qty_pct'] >= 1.0:
            self.position_open = False
            self.full_exits += 1
            self.exit_validator.close_position()
        else:
            self.partial_exits += 1
        
        self.trades_closed += 1
    
    def get_status(self) -> Dict:
        """Retorna estado actual del engine"""
        return {
            'position_open': self.position_open,
            'position_side': self.position_side,
            'entry_price': self.entry_price,
            'current_price': self.current_price,
            'trades_opened': self.trades_opened,
            'trades_closed': self.trades_closed,
            'partial_exits': self.partial_exits,
            'full_exits': self.full_exits,
            'exhaustion_level': self.exit_validator.get_exhaustion_level() if self.position_open else 0.0
        }
    
    def reset(self) -> None:
        """Resetea para nueva sesión"""
        self.entry_validator.reset()
        self.exit_validator.close_position()
        self.position_open = False
        self.position_side = None
        self.entry_price = None
        self.trades_opened = 0
        self.trades_closed = 0
