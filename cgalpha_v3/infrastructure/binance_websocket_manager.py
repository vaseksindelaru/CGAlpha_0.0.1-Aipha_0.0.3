"""
CGAlpha v3 — Binance WebSocket Manager (Sección 3 Bloqueador 1)
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
        self.cumulative_delta: Dict[str, float] = {}  # Tracks net taker buy/sell
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
        # Suscribirse a bookTicker y aggTrade (Futures URL format)
        streams = []
        for s in self.symbols:
            streams.append(f"{s.lower()}@bookTicker")
            streams.append(f"{s.lower()}@aggTrade")
        
        # Format: /stream?streams=stream1/stream2/...
        url = f"{self.base_url.replace('/ws', '/stream')}?streams={'/'.join(streams)}"
        
        while self.is_running:
            try:
                async with websockets.connect(url) as ws:
                    logger.info(f"✅ Conectado a Binance WS: {url}")
                    while self.is_running:
                        message = await ws.recv()
                        data = json.loads(message)
                        await self._handle_message(data)
            except Exception as e:
                logger.error(f"⚠️ Error en WebSocket: {str(e)}. Reintentando en 5s...")
                await asyncio.sleep(5)

    async def _handle_message(self, data: Dict):
        """Procesa y enruta los mensajes del WebSocket."""
        # logger.debug(f"WS Msg: {data}")
        event_type = data.get('e')
        
        # Combined stream wraps data in {'stream': '...', 'data': {...}}
        if 'stream' in data and 'data' in data:
            stream_name = data['stream']
            data = data['data']
            event_type = data.get('e')

        symbol = (data.get('s') or "").upper()

        if ('b' in data and 'a' in data) or event_type == 'bookTicker':
            # bookTicker update (OBI)
            self.order_book_state[symbol] = {
                "bid": float(data['b']),
                "bid_qty": float(data['B']),
                "ask": float(data['a']),
                "ask_qty": float(data['A']),
                "timestamp": time.time() * 1000
            }
        elif event_type == 'aggTrade':
            # aggregated trade update (Delta)
            trade_data = {
                "price": float(data['p']),
                "qty": float(data['q']),
                "is_buyer_maker": data['m'],
                "timestamp": data['T']
            }
            self.last_trades.append(trade_data)
            
            # Cumulative Delta calculation:
            delta = trade_data['qty'] if not trade_data['is_buyer_maker'] else -trade_data['qty']
            self.cumulative_delta[symbol] = self.cumulative_delta.get(symbol, 0.0) + delta
             
            if len(self.last_trades) > 1000:
                self.last_trades.pop(0)

        # Disparar callbacks (async-safe)
        for cb in self.callbacks:
            if asyncio.iscoroutinefunction(cb):
                await cb(data)
            else:
                cb(data)

    def get_current_obi(self, symbol: str) -> float:
        """Calcula el OBI actual desde el estado del libro."""
        state = self.order_book_state.get(symbol.upper())
        if not state: return 0.0
        
        total = state['bid_qty'] + state['ask_qty']
        if total == 0: return 0.0
        # OBI = (bid_qty - ask_qty) / (bid_qty + ask_qty)
        return (state['bid_qty'] - state['ask_qty']) / total

    def get_cumulative_delta(self, symbol: str) -> float:
        """Retorna el delta acumulado para el símbolo."""
        return self.cumulative_delta.get(symbol.upper(), 0.0)

    @classmethod
    def create_default(cls, symbol: str = "BTCUSDT"):
        manifest = ComponentManifest(
            name="BinanceWebSocketManager",
            category="infrastructure",
            function="Ingesta de datos en tiempo real via Binance Futures WebSocket",
            inputs=["symbol_list"],
            outputs=["LiveStreamEvents", "TickData"],
            causal_score=0.95 # Alta precisión de datos
        )
        return cls(manifest, symbols=[symbol])
