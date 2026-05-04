"""
CGAlpha v3 — Live Data Feed Adapter (v2: Two-Speed Architecture)
================================================================
Puente asíncrono que conecta el WebSocket Manager con el Signal Detector.

Arquitectura de dos velocidades:
  - ZONAS:   detectadas al cerrar la vela (cada 1 minuto)
  - RETESTS: detectados a velocidad de tick (cada aggTrade, ~10-50/s)
  - L2 PROFILE: sintetizado SOLO en el ms del toque de zona (~3 veces/día)

Esto garantiza que el perfil temporal L2 de 30s se capture en el instante
exacto del retest, no 45 segundos después al cierre de la vela.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from cgalpha_v3.domain.base_component import BaseComponentV3, ComponentManifest
from cgalpha_v3.domain.deferred_outcome_monitor import DeferredOutcomeMonitor
from cgalpha_v3.infrastructure.binance_websocket_manager import BinanceWebSocketManager
from cgalpha_v3.infrastructure.signal_detector.triple_coincidence import TripleCoincidenceDetector, RetestEvent
from cgalpha_v3.data_quality.nexus_gate import NexusGate
from cgalpha_v3.risk.order_manager import DryRunOrderManager

logger = logging.getLogger("live_adapter")


class LiveDataFeedAdapter(BaseComponentV3):
    """
    ╔═══════════════════════════════════════════════════════════════╗
    ║  APPLICATION — Live Data Feed Adapter (v2)                    ║
    ║  Bridge: WebSocket -> Detector -> ShadowTrader                ║
    ║                                                               ║
    ║  Two-Speed Architecture:                                      ║
    ║    Speed 1 (1min):  Zone detection at candle close            ║
    ║    Speed 2 (tick):  Retest detection at every aggTrade        ║
    ║                     L2 synthesis ONLY on zone touch           ║
    ╚═══════════════════════════════════════════════════════════════╝
    """

    def __init__(self, manifest: ComponentManifest,
                 ws_manager: BinanceWebSocketManager,
                 detector: TripleCoincidenceDetector,
                 order_manager: Optional[DryRunOrderManager] = None):
        super().__init__(manifest)
        self.ws = ws_manager
        self.detector = detector
        self.order_mgr = order_manager or DryRunOrderManager()
        self._oracle = None

        # Candle aggregation
        self.current_kline: Dict[str, Any] = {}
        self.interval_s = 60
        self.symbol = "BTCUSDT"
        self._last_kline_close = 0
        self.live_signals: List[Dict] = []

        # NexusGate & Causal Drift
        self.nexus = NexusGate()
        self.micro_buffer: List[Dict] = []
        self.delta_causal = 0.0
        self._is_causally_safe = True

        # Deferred Labeling (Semana 3)
        self.deferred_monitor = DeferredOutcomeMonitor()

        # Register callback
        self.ws.add_callback(self.on_ws_message)

    def inject_oracle(self, oracle):
        """Inyecta el modelo entrenado."""
        self._oracle = oracle
        logger.info("🧠 Oracle validado e inyectado en LiveAdapter.")

    # ══════════════════════════════════════════════════════════════
    # SPEED 2 (TICK): Entry point for every aggTrade (~10-50/s)
    # ══════════════════════════════════════════════════════════════

    async def on_ws_message(self, data: Dict[str, Any]):
        """Callback procesador de mensajes del WebSocket."""
        event_type = data.get('e')
        if event_type == 'aggTrade':
            await self._process_trade(data)

    async def _process_trade(self, trade: Dict[str, Any]):
        """
        Procesa cada trade individual. Dos responsabilidades:
        1. Agregar al candle actual (OHLCV aggregation)
        2. Check tick-level retest contra zonas activas
        """
        price = float(trade['p'])
        qty = float(trade['q'])
        ts = int(trade.get('T', trade.get('E', time.time() * 1000)))
        kline_start = (ts // (self.interval_s * 1000)) * (self.interval_s * 1000)

        # ── 1. OHLCV Candle Aggregation ──────────────────────────
        if kline_start > self._last_kline_close and self._last_kline_close > 0:
            # New candle → dispatch the previous one
            if self.current_kline:
                self._on_candle_close(self.current_kline)

            self.current_kline = {
                "open_time": kline_start,
                "open": price, "high": price, "low": price, "close": price,
                "volume": qty,
                "close_time": kline_start + (self.interval_s * 1000) - 1,
            }
            self._last_kline_close = kline_start
        elif self._last_kline_close == 0:
            self._last_kline_close = kline_start
            self.current_kline = {
                "open_time": kline_start,
                "open": price, "high": price, "low": price, "close": price,
                "volume": qty,
                "close_time": kline_start + (self.interval_s * 1000) - 1,
            }
        else:
            self.current_kline["high"] = max(self.current_kline["high"], price)
            self.current_kline["low"] = min(self.current_kline["low"], price)
            self.current_kline["close"] = price
            self.current_kline["volume"] += qty

        # ── 2. TICK-LEVEL RETEST CHECK (the critical change) ─────
        # O(n_zones) pure — no I/O, no DataFrame. ~5-10 zones × 30 ticks/s = trivial
        if self._is_causally_safe and self.detector.active_zones:
            hits = self.detector.check_intra_candle_retest(price, ts)

            for hit in hits:
                # THIS IS THE MOMENT — synthesize L2 profile NOW, not 45s later
                self._on_retest_detected(hit, price, ts)

        # ── 3. DEFERRED LABELING: update MFE/MAE on every tick ───
        # Lightweight: just float comparisons per pending label
        self.deferred_monitor.tick(price, bar_closed=False)

        # ── 4. Update open DryRun positions with current price ───
        self.order_mgr.update_positions(price)

    # ══════════════════════════════════════════════════════════════
    # SPEED 1 (1 MIN): Zone detection at candle close
    # ══════════════════════════════════════════════════════════════

    def _on_candle_close(self, kline: Dict[str, Any]):
        """
        Procesa la vela cerrada. Only two jobs:
        1. Feed detector for NEW zone detection (slow, requires DataFrame)
        2. Update NexusGate causal drift
        3. Resolve deferred labels (bar_closed=True)
        """
        obi = self.ws.get_current_obi(self.symbol, levels=10)
        cum_delta = self.ws.get_rolling_delta(self.symbol, window_seconds=300)
        micro_data = {
            "vwap": kline["close"],
            "obi_10": obi,
            "cumulative_delta": cum_delta,
            "timestamp": kline.get("close_time", int(time.time() * 1000))
        }

        # 1. NexusGate & Causal Drift
        self.micro_buffer.append(micro_data)
        if len(self.micro_buffer) > 100:
            self.micro_buffer.pop(0)

        self.delta_causal = self.nexus.calculate_delta_causal(self.micro_buffer)
        self._is_causally_safe = self.nexus.is_safe(self.delta_causal)

        logger.info(
            f"🕯️ Vela Live Cerrada: {self.symbol} "
            f"Close={kline['close']} OBI={obi:.4f} "
            f"ΔCausal={self.delta_causal:.2%} "
            f"Zonas={len(self.detector.active_zones)} "
            f"Pending={self.deferred_monitor.get_pending_count()}"
        )

        if not self._is_causally_safe:
            logger.warning(
                f"🚨 NEXUSGATE CLOSED: ΔCausal ({self.delta_causal:.4f}) > "
                f"Threshold ({self.nexus.threshold}). Señales suspendidas."
            )

        # 2. Feed closed candle to detector for ZONE DETECTION (Speed 1)
        self.detector.feed_kline_for_zone_detection(kline, micro_data)

        # 3. Deferred labeling: mark bar as closed (increment bars_elapsed)
        resolved = self.deferred_monitor.tick(kline["close"], bar_closed=True)
        for r in resolved:
            logger.info(
                f"🏷️ Outcome resolved via candle close: "
                f"{r['sample_id']} → {r['outcome']}"
            )

    # ══════════════════════════════════════════════════════════════
    # RETEST HANDLER: The critical millisecond
    # ══════════════════════════════════════════════════════════════

    def _on_retest_detected(self, hit: dict, price: float, timestamp_ms: int):
        """
        Called the INSTANT a tick touches a zone. This is where we:
        1. Synthesize the L2 temporal profile (30s ring buffer)
        2. Build the full ReentrySnapshot
        3. Run Oracle prediction
        4. Open ShadowTrade if confidence > threshold
        5. Register with DeferredOutcomeMonitor for labeling
        """
        zone = hit["zone"]
        clearance_atr = hit["clearance_atr"]

        # ── 1. SYNTHESIZE L2 PROFILE (the whole point of this refactor) ──
        sym_lower = self.symbol.lower()
        l2_buffer = self.ws.l2_buffers.get(sym_lower)

        if l2_buffer:
            l2_profile = l2_buffer.synthesize_at_retest()
            raw_buffer = l2_buffer.get_raw_buffer()
        else:
            l2_profile = {}
            raw_buffer = []

        # ── 2. CAPTURE L2 SNAPSHOT AT TOUCH ──────────────────────
        obi_10 = self.ws.get_current_obi(self.symbol, levels=10)
        obi_1 = self.ws.get_current_obi(self.symbol, levels=1)
        obi_5 = self.ws.get_current_obi(self.symbol, levels=5)
        obi_20 = self.ws.get_current_obi(self.symbol, levels=20)
        cum_delta = self.ws.get_rolling_delta(self.symbol, window_seconds=300)

        # Book depth
        state = self.ws.order_book_state.get(self.symbol, {})
        bids = state.get('bids', [])
        asks = state.get('asks', [])
        best_bid_size = float(bids[0][1]) if bids else 0.0
        best_ask_size = float(asks[0][1]) if asks else 0.0
        bid_depth_10 = sum(float(b[1]) for b in bids[:10])
        ask_depth_10 = sum(float(a[1]) for a in asks[:10])
        best_bid = float(bids[0][0]) if bids else 0.0
        best_ask = float(asks[0][0]) if asks else 0.0
        spread_bps = ((best_ask - best_bid) / best_bid * 10000) if best_bid > 0 else 0.0

        # ── 3. BUILD REENTRY SNAPSHOT (Schema v2.0) ──────────────
        zone_width = zone.zone_top - zone.zone_bottom
        atr = zone.atr_at_detection if zone.atr_at_detection > 0 else price * 0.001

        sample_id = (
            f"re_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            f"_{self.symbol}_{zone.direction}_{zone.candle_index}"
        )

        snapshot = {
            "_meta": {
                "schema_version": "2.0.0",
                "capture_ts_utc": datetime.now(timezone.utc).isoformat(),
                "capture_ts_unix_ms": timestamp_ms,
                "symbol": self.symbol,
                "sample_id": sample_id,
                "pipeline_version": "v4.2-tick-level",
            },
            "zone_geometry": {
                "zone_id": f"z_{zone.candle_index}_{zone.direction}",
                "direction": zone.direction,
                "zone_top": zone.zone_top,
                "zone_bottom": zone.zone_bottom,
                "zone_width_abs": zone_width,
                "zone_width_atr": round(zone_width / atr, 4),
                "detection_candle_index": zone.candle_index,
                "detection_ts_utc": datetime.fromtimestamp(
                    zone.detection_timestamp / 1000, tz=timezone.utc
                ).isoformat() if zone.detection_timestamp > 1e9 else None,
                "key_candle_volume_ratio": zone.key_candle.get("volume_percentile", 0),
                "key_candle_body_pct": zone.key_candle.get("body_percentage", 0),
                "accumulation_bar_count": (
                    zone.accumulation_zone.get("end_idx", 0)
                    - zone.accumulation_zone.get("start_idx", 0)
                ),
                "mini_trend_r2": zone.mini_trend.get("r2", 0),
                "coincidence_score": zone.accumulation_zone.get("quality_score", 0),
            },
            "clearance": {
                "atr_at_detection": atr,
                "max_clearance_price": (
                    zone.max_price_since_detection if zone.direction == "bullish"
                    else zone.min_price_since_detection
                ),
                "max_clearance_atr": clearance_atr,
                "seconds_since_detection": (
                    (timestamp_ms - zone.detection_timestamp) / 1000
                    if zone.detection_timestamp > 0 else 0
                ),
            },
            "l2_snapshot_at_touch": {
                "retest_price": price,
                "obi_1": obi_1,
                "obi_5": obi_5,
                "obi_10": obi_10,
                "obi_20": obi_20,
                "cumulative_delta": cum_delta,
                "best_bid_size_btc": best_bid_size,
                "best_ask_size_btc": best_ask_size,
                "bid_wall_depth_10_btc": bid_depth_10,
                "ask_wall_depth_10_btc": ask_depth_10,
                "spread_bps": round(spread_bps, 2),
                "vwap_session": self.current_kline.get("close", price),
            },
            "l2_temporal_profile": l2_profile,
            "market_context": {
                "atr_14_current": atr,
                "regime": "LATERAL",  # Will be enriched by detector if kline buffer has data
                "session": self._get_session(timestamp_ms),
                "hour_utc": datetime.fromtimestamp(
                    timestamp_ms / 1000, tz=timezone.utc
                ).hour,
            },
            "outcome": None,  # Filled by DeferredOutcomeMonitor
        }

        # ── 4. ORACLE PREDICTION ─────────────────────────────────
        confidence = 0.5
        prediction = "PENDING"

        if self._oracle and self._oracle.model and self._oracle.model != "placeholder_model_trained":
            try:
                signal_data = {
                    "vwap_at_retest": price,
                    "obi_10_at_retest": obi_10,
                    "cumulative_delta_at_retest": cum_delta,
                    "delta_divergence": (
                        "BULLISH_ABSORPTION" if zone.direction == "bullish"
                        else "BEARISH_EXHAUSTION"
                    ),
                    "atr_14": atr,
                    "regime": "LATERAL",
                    "direction": zone.direction,
                    "index": zone.candle_index,
                }
                oracle_result = self._oracle.predict(micro=None, signal_data=signal_data)
                confidence = oracle_result.confidence
                prediction = oracle_result.suggested_action
            except Exception as e:
                logger.warning(f"⚠️ Oracle prediction failed: {e}")

        # ── 5. BUILD SIGNAL & EXECUTE ────────────────────────────
        signal = {
            "id": sample_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "symbol": self.symbol,
            "price": price,
            "direction": zone.direction,
            "oracle_confidence": confidence,
            "prediction": prediction,
            "obi": obi_10,
            "l2_quality": l2_profile.get("l2_data_quality", "UNKNOWN"),
            "l2_snapshots": l2_profile.get("n_snapshots", 0),
            "clearance_atr": clearance_atr,
            "status": "active",
        }
        self.live_signals.append(signal)

        # Trim signal history
        if len(self.live_signals) > 50:
            self.live_signals.pop(0)

        # Execute DryRun if Oracle approves
        if confidence > 0.70:
            self.order_mgr.execute_signal(signal)

        # ── 6. REGISTER WITH DEFERRED MONITOR ────────────────────
        self.deferred_monitor.register_retest(snapshot, raw_buffer=raw_buffer)

        # ── 7. LOG ───────────────────────────────────────────────
        logger.info(
            f"🚨 RETEST DETECTADO (tick-level): {zone.direction} "
            f"@ {price:.2f} | Zone [{zone.zone_bottom:.2f}-{zone.zone_top:.2f}] "
            f"| Clearance {clearance_atr:.2f} ATR "
            f"| OBI={obi_10:.4f} | CumΔ={cum_delta:.1f} "
            f"| L2 snaps={l2_profile.get('n_snapshots', 0)} "
            f"| Oracle conf={confidence:.2f} ({prediction}) "
            f"| Sample={sample_id}"
        )

    # ══════════════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def _get_session(timestamp_ms: int) -> str:
        """Determina la sesión de trading basada en hora UTC."""
        hour = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).hour
        if 0 <= hour < 8:
            return "ASIA"
        elif 8 <= hour < 14:
            return "EU"
        elif 14 <= hour < 21:
            return "US"
        else:
            return "LATE_US"

    @classmethod
    def create_default(cls, ws_manager, detector, order_mgr=None):
        manifest = ComponentManifest(
            name="LiveDataFeedAdapter",
            category="application",
            function="Two-Speed Live Pipeline: Zones@1min, Retests@tick, L2@retest",
            inputs=["WS"],
            outputs=["Signals", "ReentrySnapshots"],
            causal_score=0.95,
        )
        return cls(manifest, ws_manager, detector, order_mgr)
