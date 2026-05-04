"""
CGAlpha v3 — Binance WebSocket Manager
==============================================================
Ingesta de datos en vivo (Fase 3). Conecta con Binance Futures WS
para obtener bookTicker (OBI) y aggTrades (Cumulative Delta).
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Callable
import websockets
from datetime import datetime, timezone

from cgalpha_v3.domain.base_component import BaseComponentV3, ComponentManifest
from cgalpha_v3.infrastructure.binance_data import MicrostructureRecord
from cgalpha_v3.infrastructure.l2_ring_buffer import L2RingBuffer

logger = logging.getLogger("binance_ws")

class BinanceWebSocketManager(BaseComponentV3):
    """
    ╔═══════════════════════════════════════════════════════╗
    ║  INFRASTRUCTURE — Binance WebSocket Manager           ║
    ║  Live Data Ingestion (Fase 3 Scaffolding)             ║
    ╠══════════════════════════════════════════════════════╣
    ║  - aggTrades  : Feed para Cumulative Delta            ║
    ║  - bookTicker : Feed para Order Book Imbalance (OBI)  ║
    ║  - Klines     : Feed para OHLCV en tiempo real        ║
    ╚═══════════════════════════════════════════════════════╝
    """

    def __init__(self, manifest: ComponentManifest, symbols: List[str] = ["btcusdt"]):
        super().__init__(manifest)
        self.base_url = "wss://fstream.binance.com/ws"
        self.symbols = [s.lower() for s in symbols]
        self.is_running = False
        self._loop_task: Optional[asyncio.Task] = None
        
        # Buffers de tiempo real
        self.order_book_state: Dict[str, Dict] = {}
        self.last_trades: List[Dict] = []
        
        # Integración L2RingBuffer (P0)
        self._connection_epoch = 0
        self.l2_buffers: Dict[str, L2RingBuffer] = {
            sym: L2RingBuffer() for sym in self.symbols
        }
        
        self.callbacks: List[Callable] = []

    def add_callback(self, callback: Callable[[Dict], None]):
        """Registra un callback para procesar nuevos eventos (Detector)."""
        self.callbacks.append(callback)

    async def start(self):
        """Inicia el loop de conexión asíncrona."""
        if self.is_running:
            return
        
        self.is_running = True
        self._loop_task = asyncio.create_task(self._main_loop())
        logger.info(f"📡 WebSocket Manager iniciado: {', '.join(self.symbols)}")

    async def stop(self):
        """Detiene el loop y cierra conexiones."""
        self.is_running = False
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
        logger.info("📡 WebSocket Manager detenido.")

    async def _main_loop(self):
        """Loop principal con reconexión automática."""
        streams = []
        for s in self.symbols:
            streams.append(f"{s.lower()}@depth20@100ms")
            streams.append(f"{s.lower()}@aggTrade")
        
        url = f"{self.base_url.replace('/ws', '/stream')}?streams={'/'.join(streams)}"
        
        while self.is_running:
            try:
                # Connection epoch tracking para huecos en buffer (P2)
                self._connection_epoch += 1
                for buf in self.l2_buffers.values():
                    buf.mark_reconnection(self._connection_epoch)
                
                async with websockets.connect(url) as ws:
                    logger.info(f"✅ Conectado a Binance WS: {url} (Epoch: {self._connection_epoch})")
                    while self.is_running:
                        message = await ws.recv()
                        data = json.loads(message)
                        await self._handle_message(data)
            except Exception as e:
                logger.error(f"⚠️ Error en WebSocket: {str(e)}. Reintentando en 5s...")
                await asyncio.sleep(5)

    async def _handle_message(self, data: Dict):
        """Procesa y enruta los mensajes del WebSocket."""
        event_type = data.get('e')
        
        if 'stream' in data and 'data' in data:
            stream_name = data['stream']
            data = data['data']
            event_type = data.get('e')

        symbol = (data.get('s') or "").upper()
        
        # Clock Drift y Timestamp Inconsistency (P1)
        # Usar siempre el timestamp del evento de Binance ('E' o 'T') antes que time.time()
        binance_ts_ms = data.get('E', data.get('T', time.time() * 1000))

        if ('b' in data and 'a' in data) and isinstance(data['b'], list):
            self.order_book_state[symbol] = {
                "bids": data.get('b', []),
                "asks": data.get('a', []),
                "timestamp": binance_ts_ms
            }
        elif ('b' in data and 'a' in data) or event_type == 'bookTicker':
            self.order_book_state[symbol] = {
                "bids": [[data['b'], data['B']]],
                "asks": [[data['a'], data['A']]],
                "timestamp": binance_ts_ms
            }
        elif event_type == 'aggTrade':
            trade_data = {
                "price": float(data['p']),
                "qty": float(data['q']),
                "is_buyer_maker": data['m'],
                "timestamp": binance_ts_ms
            }
            self.last_trades.append(trade_data)
             
            # Limitar a los trades de los últimos 15 min aprox a 10tps (10000 limit)
            # para no saturar memoria y permitir ventanas rolling correctas
            if len(self.last_trades) > 10000:
                self.last_trades.pop(0)

        # Inyectar L2RingBuffer micro-snapshot (P0)
        # Solo empujar en eventos del order book (depth20/bookTicker) para mantener ~10hz y ventana de 30s
        is_depth_update = ('b' in data and 'a' in data) or event_type == 'bookTicker'
        local_ts_ms = time.time() * 1000
        sym_lower = symbol.lower()
        if is_depth_update and sym_lower in self.l2_buffers:
            buffer = self.l2_buffers[sym_lower]
            local_offset_ms = local_ts_ms - binance_ts_ms
            
            obi_1 = self.get_current_obi(symbol, 1)
            obi_5 = self.get_current_obi(symbol, 5)
            obi_10 = self.get_current_obi(symbol, 10)
            obi_20 = self.get_current_obi(symbol, 20)
            
            # Cumulative Delta rolling window
            cum_delta_300 = self.get_rolling_delta(symbol, window_seconds=300)
            
            # Profundidad de libro
            state = self.order_book_state.get(symbol, {})
            bids = state.get('bids', [])
            asks = state.get('asks', [])
            
            best_bid_size = float(bids[0][1]) if bids else 0.0
            best_ask_size = float(asks[0][1]) if asks else 0.0
            
            bid_depth_10 = sum(float(b[1]) for b in bids[:10])
            ask_depth_10 = sum(float(a[1]) for a in asks[:10])
            
            best_bid = float(bids[0][0]) if bids else 0.0
            best_ask = float(asks[0][0]) if asks else 0.0
            spread_bps = ((best_ask - best_bid) / best_bid * 10000) if best_bid > 0 else 0.0
            
            # Estimación agresiva de MKT trades en el último segundo para intensity/aggression
            recent_1s_cutoff = binance_ts_ms - 1000
            recent_trades_1s = [t for t in self.last_trades if t["timestamp"] >= recent_1s_cutoff]
            trade_count = len(recent_trades_1s)
            agg_buy_vol = sum(t["qty"] for t in recent_trades_1s if not t["is_buyer_maker"])
            agg_sell_vol = sum(t["qty"] for t in recent_trades_1s if t["is_buyer_maker"])
            
            buffer.push(
                binance_ts_ms=binance_ts_ms,
                local_offset_ms=local_offset_ms,
                obi_1=obi_1, obi_5=obi_5, obi_10=obi_10, obi_20=obi_20,
                cum_delta=cum_delta_300,
                best_bid_size=best_bid_size, best_ask_size=best_ask_size,
                bid_depth_10=bid_depth_10, ask_depth_10=ask_depth_10,
                spread_bps=spread_bps,
                trade_count=trade_count,
                agg_buy_vol=agg_buy_vol, agg_sell_vol=agg_sell_vol
            )

        for cb in self.callbacks:
            if asyncio.iscoroutinefunction(cb):
                await cb(data)
            else:
                cb(data)

    def get_current_obi(self, symbol: str, levels: int = 10) -> float:
        """Calcula el OBI actual desde el estado del libro (Multi-nivel)."""
        state = self.order_book_state.get(symbol.upper())
        if not state: return 0.0
        
        bids = state.get('bids', [])[:levels]
        asks = state.get('asks', [])[:levels]
        
        bid_qty = sum(float(b[1]) for b in bids)
        ask_qty = sum(float(a[1]) for a in asks)
        
        total = bid_qty + ask_qty
        if total == 0: return 0.0
        return (bid_qty - ask_qty) / total

    def get_rolling_delta(self, symbol: str, window_seconds: float = 300) -> float:
        """
        Delta acumulado de los últimos N segundos (P0).
        Reemplaza al delta global infinito.
        """
        cutoff_ms = time.time() * 1000 - (window_seconds * 1000)
        recent_trades = [t for t in self.last_trades if t["timestamp"] >= cutoff_ms]
        
        delta = sum(
            t["qty"] if not t["is_buyer_maker"] else -t["qty"]
            for t in recent_trades
        )
        return delta

    @classmethod
    def create_default(cls, symbol: str = "BTCUSDT"):
        manifest = ComponentManifest(
            name="BinanceWebSocketManager",
            category="infrastructure",
            function="Ingesta de datos en tiempo real via Binance Futures WebSocket",
            inputs=["symbol_list"],
            outputs=["LiveStreamEvents", "TickData"],
            causal_score=0.95
        )
        return cls(manifest, symbols=[symbol])
