"""
CGAlpha v3 — Live Data Feed Adapter (Bloqueador 3)
=================================================
Puente asíncrono que conecta el WebSocket Manager con el Signal Detector.
Consolida ticks en velas (klines) y features de microestructura.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from cgalpha_v3.domain.base_component import BaseComponentV3, ComponentManifest
from cgalpha_v3.infrastructure.binance_websocket_manager import BinanceWebSocketManager
from cgalpha_v3.infrastructure.signal_detector.triple_coincidence import TripleCoincidenceDetector

logger = logging.getLogger("live_adapter")

class LiveDataFeedAdapter(BaseComponentV3):
    """
    ╔═══════════════════════════════════════════════════════╗
    ║  APPLICATION — Live Data Feed Adapter                 ║
    ║  Bridge: WebSocket -> Detector -> ShadowTrader        ║
    ╚═══════════════════════════════════════════════════════╝
    """

    def __init__(self, manifest: ComponentManifest, ws_manager: BinanceWebSocketManager, detector: TripleCoincidenceDetector):
        super().__init__(manifest)
        self.ws = ws_manager
        self.detector = detector
        self.current_kline: Dict[str, Any] = {}
        self.interval_s = 60  # Default 1m para el MVP live demo
        self.symbol = "BTCUSDT"
        self._last_kline_close = 0
        
        # Registrar callback en el WebSocket
        self.ws.add_callback(self.on_ws_message)

    async def on_ws_message(self, data: Dict[str, Any]):
        """Callback procesador de mensajes del WebSocket."""
        event_type = data.get('e')
        
        if event_type == 'aggTrade':
            await self._process_trade(data)
        elif 'b' in data:  # bookTicker
            # El OBI se consulta On-Demand del WS manager, 
            # pero aquí podríamos disparar una re-evaluación si es necesario.
            pass

    async def _process_trade(self, trade: Dict[str, Any]):
        """Consolida trades en la vela actual."""
        price = float(trade['p'])
        qty = float(trade['q'])
        ts = int(trade['T'])
        
        # Lógica de apertura de vela
        kline_start = (ts // (self.interval_s * 1000)) * (self.interval_s * 1000)
        
        if kline_start > self._last_kline_close:
            # Emitir vela anterior al detector si existe
            if self.current_kline:
                self._dispatch_kline(self.current_kline)
            
            # Nueva vela
            self.current_kline = {
                "open_time": kline_start,
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume": qty,
                "close_time": kline_start + (self.interval_s * 1000) - 1,
            }
            self._last_kline_close = kline_start
        else:
            # Actualizar vela actual
            self.current_kline["high"] = max(self.current_kline["high"], price)
            self.current_kline["low"] = min(self.current_kline["low"], price)
            self.current_kline["close"] = price
            self.current_kline["volume"] += qty
            
        # Opcional: Monitorizar retests intra-candle
        # En v3, el detector prefiere velas cerradas para estabilidad, 
        # pero para ShadowTrader Live podemos inyectar ticks.

    def _dispatch_kline(self, kline: Dict[str, Any]):
        """Envía la vela consolidada al detector con micro-features."""
        # Obtener OBI y Delta del WS Manager (que mantiene los buffers)
        obi = self.ws.get_current_obi(self.symbol)
        
        # Enriquecer kline para el detector
        # El detector de v3 espera un DataFrame o lista de dicts
        # Aquí inyectamos el pulso de tiempo real
        logger.info(f"🕯️ Vela Live Cerrada: {self.symbol} Close={kline['close']} OBI={obi:.4f}")
        
        # TODO: Integración real con detector.process_stream() para 1 solo registro
        # detector.process_live_tick(kline, micro_data)

    @classmethod
    def create_default(cls, ws_manager, detector):
        manifest = ComponentManifest(
            name="LiveDataFeedAdapter",
            category="application",
            function="Sincronización de WebSocket con Detector de Señales (Puente de Fase 3)",
            inputs=["BinanceWSStream"],
            outputs=["LiveKlines", "MicrostructureFeatures"],
            causal_score=0.90
        )
        return cls(manifest, ws_manager, detector)
