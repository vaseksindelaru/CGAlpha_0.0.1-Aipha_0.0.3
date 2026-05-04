import collections
import time
import numpy as np

class L2RingBuffer:
    """
    Buffer circular de 30 segundos para microestructura L2.
    Almacena ~300 snapshots (100ms cada uno).
    Tamaño en memoria: disperso, despreciable.
    """
    
    def __init__(self, max_seconds: float = 30.0, sample_rate_ms: int = 100):
        self.max_slots = int(max_seconds * 1000 / sample_rate_ms)
        self._buffer = collections.deque(maxlen=self.max_slots)
        self._current_epoch = 0
    
    def mark_reconnection(self, epoch: int):
        self._current_epoch = epoch

    def push(self, binance_ts_ms: float, local_offset_ms: float, obi_1: float, obi_5: float, obi_10: float, obi_20: float,
             cum_delta: float, best_bid_size: float, best_ask_size: float,
             bid_depth_10: float, ask_depth_10: float, spread_bps: float,
             trade_count: int, aggressive_buy_vol: float, aggressive_sell_vol: float):
        """Cada 100ms, el WS Manager empuja un micro-snapshot."""
        self._buffer.append({
            "ts": binance_ts_ms / 1000.0,
            "local_offset_ms": local_offset_ms,
            "epoch": self._current_epoch,
            "obi_1": float(obi_1), "obi_5": float(obi_5), "obi_10": float(obi_10), "obi_20": float(obi_20),
            "cum_delta": float(cum_delta),
            "best_bid_size": float(best_bid_size), "best_ask_size": float(best_ask_size),
            "bid_depth_10": float(bid_depth_10), "ask_depth_10": float(ask_depth_10),
            "spread_bps": float(spread_bps),
            "trade_count": int(trade_count),
            "agg_buy_vol": float(aggressive_buy_vol), "agg_sell_vol": float(aggressive_sell_vol),
        })

    def synthesize_at_retest(self) -> dict:
        """
        Cuando el detector dispara RETEST, condensa snapshots.
        """
        if len(self._buffer) < 10:
            return self._empty_profile()
        
        buf = list(self._buffer)
        now = buf[-1]["ts"]
        
        # Segmentar por ventanas temporales
        def _window(secs):
            cutoff = now - secs
            return [s for s in buf if s["ts"] >= cutoff]
        
        w5 = _window(5.0)
        w15 = _window(15.0)
        w30 = _window(30.0)
        
        obi_10_series = np.array([s["obi_10"] for s in w30])
        delta_series = np.array([s["cum_delta"] for s in w30])
        
        # Check connection quality
        epochs_in_w30 = set(s.get("epoch", 0) for s in w30)
        l2_data_quality = "FULL" if len(epochs_in_w30) == 1 else "PARTIAL"

        # Gradientes OBI (regresión lineal sobre ventanas)
        def _gradient(series, window_slots):
            if len(series) < max(2, window_slots):
                return 0.0
            segment = series[-window_slots:]
            x = np.arange(len(segment), dtype=float)
            if len(x) < 2:
                return 0.0
            # np.polyfit can trigger RankWarning, wrapping in a try is safer but usually okay for 1D.
            slope = float(np.polyfit(x, segment, 1)[0])
            return slope * len(segment)  # Total Delta in the window
        
        # Delta rates (Δ/segundo)
        def _rate(window, field="cum_delta"):
            if len(window) < 2:
                return 0.0
            dt = window[-1]["ts"] - window[0]["ts"]
            if dt <= 0:
                return 0.0
            return float((window[-1][field] - window[0][field]) / dt)
        
        # Trade intensity y aggression
        def _trade_intensity(window):
            return sum(s["trade_count"] for s in window)
        
        def _aggressive_buy_pct(window):
            buy = sum(s["agg_buy_vol"] for s in window)
            sell = sum(s["agg_sell_vol"] for s in window)
            total = buy + sell
            return float(buy / total) if total > 0 else 0.5
        
        latest = buf[-1]
        dr_current = float(latest["obi_1"] / latest["obi_10"]) if latest["obi_10"] != 0 else 1.0
        
        w5_dr = np.mean([(s["obi_1"] / s["obi_10"]) if s["obi_10"] != 0 else 1.0 
                         for s in w5]) if w5 else dr_current
        w5_dr = float(w5_dr)

        return {
            "window_seconds": 30,
            "n_snapshots": len(w30),
            "l2_data_quality": l2_data_quality,
            "obi_10_gradient_5s": _gradient(obi_10_series, len(w5)),
            "obi_10_gradient_15s": _gradient(obi_10_series, len(w15)),
            "obi_10_gradient_30s": _gradient(obi_10_series, len(w30)),
            "obi_10_min_30s": float(np.min(obi_10_series)) if len(obi_10_series) > 0 else 0.0,
            "obi_10_max_30s": float(np.max(obi_10_series)) if len(obi_10_series) > 0 else 0.0,
            "obi_10_std_30s": float(np.std(obi_10_series)) if len(obi_10_series) > 0 else 0.0,
            "obi_10_at_minus_5s": float(w5[0]["obi_10"]) if w5 else 0.0,
            "obi_10_at_minus_15s": float(w15[0]["obi_10"]) if w15 else 0.0,
            "obi_10_at_minus_30s": float(w30[0]["obi_10"]) if w30 else 0.0,
            "delta_rate_5s": _rate(w5),
            "delta_rate_15s": _rate(w15),
            "delta_rate_30s": _rate(w30),
            "delta_acceleration_5s": _rate(w5) - _rate(w15) if w15 else 0.0,
            "delta_acceleration_15s": _rate(w15) - _rate(w30) if w30 else 0.0,
            "depth_ratio_1_10": dr_current,
            "depth_ratio_1_10_gradient_5s": dr_current - w5_dr,
            "trade_intensity_5s": int(_trade_intensity(w5)),
            "trade_intensity_15s": int(_trade_intensity(w15)),
            "aggressive_buy_pct_5s": _aggressive_buy_pct(w5),
            "aggressive_buy_pct_15s": _aggressive_buy_pct(w15),
        }
    
    def get_raw_buffer(self) -> list:
        return list(self._buffer)

    def _empty_profile(self) -> dict:
        return {
            "window_seconds": 30,
            "n_snapshots": 0,
            "l2_data_quality": "EMPTY",
            **{k: 0.0 for k in [
            "obi_10_gradient_5s", "obi_10_gradient_15s", "obi_10_gradient_30s",
            "obi_10_min_30s", "obi_10_max_30s", "obi_10_std_30s",
            "obi_10_at_minus_5s", "obi_10_at_minus_15s", "obi_10_at_minus_30s",
            "delta_rate_5s", "delta_rate_15s", "delta_rate_30s",
            "delta_acceleration_5s", "delta_acceleration_15s",
            "depth_ratio_1_10", "depth_ratio_1_10_gradient_5s",
            "trade_intensity_5s", "trade_intensity_15s",
            "aggressive_buy_pct_5s", "aggressive_buy_pct_15s",
        ]}}
