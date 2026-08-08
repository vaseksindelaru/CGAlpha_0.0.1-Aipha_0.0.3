"""
CGAlpha v3 — Live Data Feed Adapter (Bloqueador 3)
=================================================
Puente asíncrono que conecta el WebSocket Manager con el Signal Detector.
Consolida ticks en velas (klines) y features de microestructura.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from cgalpha_v3.domain.base_component import BaseComponentV3, ComponentManifest
from cgalpha_v3.infrastructure.binance_websocket_manager import BinanceWebSocketManager
from cgalpha_v3.infrastructure.signal_detector.triple_coincidence import TripleCoincidenceDetector, RetestEvent
from cgalpha_v3.data_quality.nexus_gate import NexusGate
from cgalpha_v3.risk.order_manager import DryRunOrderManager

logger = logging.getLogger("live_adapter")

class LiveDataFeedAdapter(BaseComponentV3):
    """
    ╔═══════════════════════════════════════════════════════╗
    ║  APPLICATION — Live Data Feed Adapter                 ║
    ║  Bridge: WebSocket -> Detector -> ShadowTrader        ║
    ╚═══════════════════════════════════════════════════════╝
    """

    def __init__(self, manifest: ComponentManifest, ws_manager: BinanceWebSocketManager, detector: TripleCoincidenceDetector, order_manager: Optional[DryRunOrderManager] = None):
        super().__init__(manifest)
        self.ws = ws_manager
        self.detector = detector
        self.order_mgr = order_manager or DryRunOrderManager()
        self._oracle = None  # Se inyecta externamente o carga por defecto
        self.current_kline: Dict[str, Any] = {}
        self.interval_s = 60 
        self.symbol = "BTCUSDT"
        self._last_kline_close = 0
        self.live_signals: List[Dict] = []
        
        # NexusGate & Causal Drift
        self.nexus = NexusGate()
        self.micro_buffer: List[Dict] = []
        self.delta_causal = 0.0
        
        # Registrar callback en el WebSocket
        self.ws.add_callback(self.on_ws_message)

    def inject_oracle(self, oracle):
        """Inyecta el modelo entrenado."""
        self._oracle = oracle
        logger.info("🧠 Oracle validado e inyectado en ShadowTrader.")

    async def on_ws_message(self, data: Dict[str, Any]):
        """Callback procesador de mensajes del WebSocket."""
        event_type = data.get('e')
        if event_type == 'aggTrade':
            await self._process_trade(data)

    async def _process_trade(self, trade: Dict[str, Any]):
        """Consolida trades en la vela actual."""
        price = float(trade['p'])
        qty = float(trade['q'])
        ts = int(trade['T'])
        kline_start = (ts // (self.interval_s * 1000)) * (self.interval_s * 1000)
        
        if kline_start > self._last_kline_close and self._last_kline_close > 0:
            if self.current_kline:
                self._dispatch_kline(self.current_kline)
            
            self.current_kline = {
                "open_time": kline_start,
                "open": price, "high": price, "low": price, "close": price,
                "volume": qty,
                "close_time": kline_start + (self.interval_s * 1000) - 1,
            }
            self._last_kline_close = kline_start
        elif self._last_kline_close == 0:
            self._last_kline_close = kline_start
            self.current_kline = {"open_time": kline_start, "open": price, "high": price, "low": price, "close": price, "volume": qty}
        else:
            self.current_kline["high"] = max(self.current_kline["high"], price)
            self.current_kline["low"] = min(self.current_kline["low"], price)
            self.current_kline["close"] = price
            self.current_kline["volume"] += qty

    def _dispatch_kline(self, kline: Dict[str, Any]):
        """Procesa la vela cerrada con el detector y valida con el Oracle."""
        obi = self.ws.get_current_obi(self.symbol)
        micro_data = {
            "vwap": kline["close"], # Simplificado
            "obi_10": obi,
            "cumulative_delta": 0.0, # WIP
            "timestamp": kline["close_time"]
        }
        
        # 1. Actualizar NexusGate y Delta Causal
        self.micro_buffer.append(micro_data)
        if len(self.micro_buffer) > 100:
            self.micro_buffer.pop(0)
            
        self.delta_causal = self.nexus.calculate_delta_causal(self.micro_buffer)
        is_causally_safe = self.nexus.is_safe(self.delta_causal)
        
        # 1.5 Actualizar posiciones abiertas (Dry Run)
        self.order_mgr.update_positions(kline["close"])
        
        logger.info(f"🕯️ Vela Live Cerrada: {self.symbol} Close={kline['close']} OBI={obi:.4f} ΔCausal={self.delta_causal:.2%}")
        
        if not is_causally_safe:
            logger.warning(f"🚨 NEXUSGATE CLOSED: ΔCausal ({self.delta_causal:.4f}) > Threshold ({self.nexus.threshold}). Señales suspendidas.")
            return

        # 2. Detectar Retests
        retests = self.detector.process_live_tick(kline, micro_data)
        
        for rt in retests:
            # 2. Validar con Oracle (Meta-Labeling)
            confidence = 0.5
            prediction = "PENDING"
            
            if self._oracle and self._oracle.model:
                features = [
                    rt.vwap_at_retest, 
                    rt.obi_10_at_retest, 
                    rt.cumulative_delta_at_retest,
                    1.0 if rt.zone.direction == 'bullish' else 0.0
                ]
                # Nota: El Oracle de v3 espera un DataFrame con nombres de columnas.
                # Aquí lo simplificamos para la ejecución live.
                import pandas as pd
                X = pd.DataFrame([features], columns=['vwap', 'obi', 'delta', 'direction'])
                confidence = self._oracle.model.predict_proba(X)[0][1]
                prediction = "BOUNCE" if confidence > 0.7 else "BREAKOUT"

            signal = {
                "id": f"live_sig_{int(time.time())}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "symbol": self.symbol,
                "price": rt.retest_price,
                "direction": rt.zone.direction,
                "oracle_confidence": confidence,
                "prediction": prediction,
                "obi": obi,
                "status": "active"
            }
            self.live_signals.append(signal)
            
            # 3. EJECUCIÓN DRY RUN (Fase 4.1)
            if confidence > 0.70:
                self.order_mgr.execute_signal(signal)
            
            logger.info(f"🚨 SENAL DETECTADA: {rt.zone.direction} | Conf: {confidence:.2f} | Pred: {prediction}")
            
            # Mantener solo las últimas 50 señales
            if len(self.live_signals) > 50:
                self.live_signals.pop(0)

    @classmethod
    def create_default(cls, ws_manager, detector, order_mgr=None):
        import time 
        manifest = ComponentManifest(name="LiveDataFeedAdapter", category="application", function="ShadowTrader Live Pipeline", inputs=["WS"], outputs=["Signals"], causal_score=0.95)
        return cls(manifest, ws_manager, detector, order_mgr)
