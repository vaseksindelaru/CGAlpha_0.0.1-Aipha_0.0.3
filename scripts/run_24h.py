#!/usr/bin/env python3
"""
CGAlpha v3 — 24h Continuous Execution Script
=============================================
Runs TripleCoincidencePipeline.run_cycle() periodically against
live Binance data via REST API (klines endpoint).

Usage:
    python3 scripts/run_24h.py --hours 24
    python3 scripts/run_24h.py --hours 1 --interval 120  # 1h test, 2min cycles

Monitoring:
    tail -f execution_24h.log
    watch -n 30 cat execution_24h_heartbeat.json
"""
import argparse
import json
import logging
import os
import signal
import sys
import time
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
import threading
import asyncio

# ── Project root ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

import pandas as pd
import requests

from cgalpha_v3.infrastructure.binance_data import BinanceVisionFetcher_v3
from cgalpha_v3.application.pipeline import TripleCoincidencePipeline
from cgalpha_v3.lila.evolution_orchestrator import EvolutionOrchestratorV4
from cgalpha_v3.lila.codecraft_sage import CodeCraftSage
from cgalpha_v3.learning.memory_policy import MemoryPolicyEngine
from cgalpha_v3.infrastructure.binance_websocket_manager import BinanceWebSocketManager

# ── Logging ──
LOG_FILE = PROJECT_ROOT / "execution_24h.log"
HEARTBEAT_FILE = PROJECT_ROOT / "execution_24h_heartbeat.json"
BRIDGE_FILE = PROJECT_ROOT / "aipha_memory" / "evolutionary" / "bridge.jsonl"
EVOLUTION_LOG = PROJECT_ROOT / "cgalpha_v3" / "memory" / "evolution_log.jsonl"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("run_24h")

# ── Binance REST Klines Fetcher ──
BINANCE_KLINES_URL = "https://fapi.binance.com/fapi/v1/klines"


def fetch_recent_klines(
    symbol: str = "BTCUSDT",
    interval: str = "5m",
    limit: int = 72,  # 6h of 5m candles
) -> pd.DataFrame:
    """Fetch recent klines from Binance Futures REST API."""
    try:
        resp = requests.get(
            BINANCE_KLINES_URL,
            params={"symbol": symbol, "interval": interval, "limit": limit},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error(f"❌ Failed to fetch klines from Binance REST: {e}")
        return pd.DataFrame()

    if not data:
        return pd.DataFrame()

    rows = []
    for k in data:
        rows.append({
            "open_time": int(k[0]),
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5]),
            "close_time": int(k[6]),
        })

    df = pd.DataFrame(rows)
    return df


def enrich_klines_for_pipeline(df: pd.DataFrame, obi: float = 0.0, delta: float = 0.0) -> pd.DataFrame:
    """Add microstructure columns needed by TripleCoincidenceDetector."""
    if df.empty:
        return df

    # VWAP approximation: (H+L+C)/3 * Volume weighted
    df["vwap"] = (df["high"] + df["low"] + df["close"]) / 3.0

    # OBI and Delta (use real values for the LATEST candle)
    df["obi_10"] = 0.0
    df["cumulative_delta"] = 0.0
    
    # Stamp real values on the last row
    df.loc[df.index[-1], "obi_10"] = obi
    df.loc[df.index[-1], "cumulative_delta"] = delta

    # ATR(14)
    if len(df) >= 14:
        tr = pd.concat([
            df["high"] - df["low"],
            (df["high"] - df["close"].shift(1)).abs(),
            (df["low"] - df["close"].shift(1)).abs(),
        ], axis=1).max(axis=1)
        df["atr_14"] = tr.rolling(14).mean()
    else:
        df["atr_14"] = (df["high"] - df["low"]).mean()

    df["atr_14"] = df["atr_14"].bfill().fillna(
        (df["high"] - df["low"]).mean()
    )

    return df


# ── Heartbeat ──
def write_heartbeat(cycle: int, status: str, details: dict):
    """Write a heartbeat JSON for external monitoring."""
    heartbeat = {
        "cycle": cycle,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_minutes": round((time.time() - _start_time) / 60, 1),
        **details,
    }
    HEARTBEAT_FILE.write_text(json.dumps(heartbeat, indent=2), encoding="utf-8")


def count_lines(path: Path) -> int:
    """Count lines in a file (0 if doesn't exist)."""
    if not path.exists():
        return 0
    try:
        return sum(1 for _ in open(path, encoding="utf-8"))
    except Exception:
        return 0


# ── Graceful shutdown ──
_shutdown = False


def _handle_signal(signum, frame):
    global _shutdown
    logger.info(f"🛑 Shutdown signal received ({signum}). Finishing current cycle...")
    _shutdown = True


signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)

_start_time = time.time()


# ── Main Loop ──
def main():
    parser = argparse.ArgumentParser(description="CGAlpha 24h Continuous Execution")
    parser.add_argument("--hours", type=float, default=24, help="Duration in hours")
    parser.add_argument("--interval", type=int, default=300, help="Seconds between cycles (default: 300 = 5min)")
    parser.add_argument("--symbol", type=str, default="BTCUSDT", help="Trading symbol")
    parser.add_argument("--klines", type=int, default=72, help="Number of klines to fetch per cycle (default: 72 = 6h)")
    args = parser.parse_args()

    duration_s = args.hours * 3600
    logger.info("=" * 60)
    logger.info(f"🚀 CGAlpha 24h Execution Starting")
    logger.info(f"   Duration: {args.hours}h | Interval: {args.interval}s | Symbol: {args.symbol}")
    logger.info(f"   Klines per cycle: {args.klines} | Log: {LOG_FILE}")
    logger.info("=" * 60)

    # ── Initialize components ──
    try:
        memory = MemoryPolicyEngine()
        memory.load_from_disk()
        sage = CodeCraftSage.create_default()
        orchestrator = EvolutionOrchestratorV4(memory=memory, sage=sage)
        pipeline = TripleCoincidencePipeline(evolution_orchestrator=orchestrator)
        logger.info("✅ Pipeline initialized with Evolution Orchestrator")
    except Exception as e:
        logger.error(f"💥 Failed to initialize pipeline: {e}")
        traceback.print_exc()
        sys.exit(1)

    # ── WebSocket Manager (Hybrid Data) ──
    ws_manager = BinanceWebSocketManager.create_default(symbol=args.symbol)
    
    def run_ws_bridge():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(ws_manager.start())
        loop.run_forever()

    ws_thread = threading.Thread(target=run_ws_bridge, daemon=True)
    ws_thread.start()
    logger.info(f"📡 Hybrid WS Bridge active for {args.symbol}")

    cycle = 0
    total_retests = 0
    total_trades = 0
    errors = 1  # Start at 1 to avoid ZeroDivision if crash (joking, logic below)
    errors = 0
    while time.time() - _start_time < duration_s and not _shutdown:
        cycle += 1
        cycle_start = time.time()

        logger.info(f"\n{'─' * 40}")
        logger.info(f"🔄 Cycle {cycle} starting at {datetime.now(timezone.utc).isoformat()}")

        try:
            # 1. Fetch recent klines from Binance REST API with Retry/Backoff
            def fetch_with_retry(symbol, limit, max_retries=3, backoff=5):
                for attempt in range(max_retries):
                    try:
                        return fetch_recent_klines(symbol, limit=limit)
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise
                        logger.warning(f"⚠️ Fetch failed ({e}), retry {attempt+1}/{max_retries} in {backoff}s...")
                        time.sleep(backoff * (attempt + 1))
                return pd.DataFrame()

            df = fetch_with_retry(
                symbol=args.symbol,
                limit=args.klines,
            )

            if df.empty:
                logger.warning("⚠️ No klines received. Skipping cycle.")
                write_heartbeat(cycle, "NO_DATA", {"errors": errors})
                time.sleep(args.interval)
                continue

            # Real-time snapshots from WS
            current_obi = ws_manager.get_current_obi(args.symbol)
            current_delta = ws_manager.get_cumulative_delta(args.symbol)

            df = enrich_klines_for_pipeline(df, obi=current_obi, delta=current_delta)
            latest_price = df["close"].iloc[-1]
            logger.info(f"📊 Fetched {len(df)} klines. Latest price: {latest_price:.2f} | OBI: {current_obi:.2f} | Δ: {current_delta:.1f}")

            # 2. Drive the detector directly with REST klines
            #    (bypasses BinanceVisionFetcher which only has yesterday's data)
            micro_df = df[["vwap", "obi_10", "cumulative_delta"]].copy()
            retest_events = pipeline.detector.process_stream(df, micro_df)
            logger.info(f"📊 Retests detectados: {len(retest_events)}")
            cycle_retests = len(retest_events)
            cycle_trades = 0

            for event in retest_events:
                # Oracle prediction
                prediction = pipeline.oracle.predict(
                    micro=None,
                    signal_data={
                        "vwap_at_retest": event.vwap_at_retest,
                        "obi_10_at_retest": event.obi_10_at_retest,
                        "cumulative_delta_at_retest": event.cumulative_delta_at_retest,
                        "delta_divergence": event.delta_divergence,
                        "atr_14": event.atr_14,
                        "regime": event.regime,
                        "direction": event.zone.direction,
                        "index": event.retest_index,
                    },
                )

                if prediction.confidence > 0.70:
                    direction = 1 if event.zone.direction == "bullish" else -1
                    trade_id = pipeline.shadow_trader.open_shadow_trade(
                        entry_price=event.retest_price,
                        direction=direction,
                        atr=event.atr_14,
                        config_snapshot={
                            "volume_threshold": pipeline.detector.config.get("volume_threshold"),
                            "oracle_min_confidence": 0.70,
                        },
                        signal_data={
                            "vwap_at_retest": event.vwap_at_retest,
                            "obi_10_at_retest": event.obi_10_at_retest,
                            "oracle_confidence": prediction.confidence,
                            "is_placeholder": prediction.is_placeholder,
                            "regime": event.regime,
                            "direction": event.zone.direction,
                        },
                        causal_tags=[f"regime:{event.regime}", f"live_24h:cycle_{cycle}"],
                    )
                    if trade_id:
                        cycle_trades += 1
                        logger.info(
                            f"📈 Shadow Trade: {trade_id} "
                            f"(conf={prediction.confidence:.2f}, "
                            f"placeholder={prediction.is_placeholder}, "
                            f"price={event.retest_price:.2f})"
                        )

            # 3. Train Oracle with new samples (if any)
            training_samples = pipeline.detector.get_training_dataset()
            if training_samples:
                dataset_dicts = [
                    {**s.features, "outcome": s.outcome}
                    for s in training_samples
                    if s.outcome in ("BOUNCE", "BREAKOUT")
                ]
                if dataset_dicts:
                    pipeline.oracle.load_training_dataset(dataset_dicts)
                    pipeline.oracle.train_model()
                    model_path = PROJECT_ROOT / "aipha_memory" / "models" / "oracle_v3.joblib"
                    model_path.parent.mkdir(parents=True, exist_ok=True)
                    pipeline.oracle.save_to_disk(str(model_path))
                    logger.info(f"🎓 Oracle retrained and persisted with {len(dataset_dicts)} samples")

            # 4. AutoProposer drift detection + evolution routing
            try:
                drift_report = pipeline.proposer.analyze_drift({
                    "sharpe_neto": 0.0,
                    "net_return_pct": 0.0,
                    "retests": cycle_retests,
                    "trades": cycle_trades,
                    "latest_price": latest_price,
                })
                if drift_report and pipeline.evolution_orchestrator:
                    for spec in drift_report:
                        pipeline.evolution_orchestrator.process_proposal(spec)
            except Exception as drift_exc:
                logger.debug(f"AutoProposer drift: {drift_exc}")

            # 5. Collect metrics
            bridge_lines = count_lines(BRIDGE_FILE)
            evo_lines = count_lines(EVOLUTION_LOG)
            oracle_trained = pipeline.oracle.model is not None and pipeline.oracle.model != "placeholder_model_trained"
            active_trades = pipeline.shadow_trader.get_active_trade_count()

            cycle_duration = round(time.time() - cycle_start, 1)

            details = {
                "result": f"retests={cycle_retests},trades={cycle_trades}",
                "klines_fetched": len(df),
                "latest_price": round(latest_price, 2),
                "bridge_entries": bridge_lines,
                "evolution_log_entries": evo_lines,
                "oracle_trained": oracle_trained,
                "active_shadow_trades": active_trades,
                "cycle_duration_s": cycle_duration,
                "total_cycles": cycle,
                "errors": errors,
            }

            write_heartbeat(cycle, "OK", details)
            logger.info(
                f"💓 Heartbeat: retests={cycle_retests}, trades={cycle_trades}, "
                f"bridge={bridge_lines}, evo_log={evo_lines}, "
                f"oracle={'✅' if oracle_trained else '⏳'}, "
                f"cycle_time={cycle_duration}s"
            )

        except Exception as e:
            errors += 1
            logger.error(f"💥 Cycle {cycle} failed: {e}")
            traceback.print_exc()
            write_heartbeat(cycle, "ERROR", {"error": str(e), "errors": errors})

        # 4. Wait for next cycle
        elapsed = time.time() - cycle_start
        sleep_time = max(0, args.interval - elapsed)
        if sleep_time > 0 and not _shutdown:
            logger.info(f"⏳ Sleeping {sleep_time:.0f}s until next cycle...")
            # Sleep in small increments to allow graceful shutdown
            for _ in range(int(sleep_time)):
                if _shutdown:
                    break
                time.sleep(1)

    # ── Summary ──
    total_time = round((time.time() - _start_time) / 3600, 2)
    logger.info("\n" + "=" * 60)
    logger.info(f"🏁 24h Execution Complete")
    logger.info(f"   Total time: {total_time}h | Cycles: {cycle} | Errors: {errors}")
    logger.info(f"   Bridge entries: {count_lines(BRIDGE_FILE)}")
    logger.info(f"   Evolution log: {count_lines(EVOLUTION_LOG)}")
    logger.info("=" * 60)

    write_heartbeat(cycle, "COMPLETED", {
        "total_hours": total_time,
        "total_cycles": cycle,
        "errors": errors,
        "bridge_entries": count_lines(BRIDGE_FILE),
        "evolution_log_entries": count_lines(EVOLUTION_LOG),
    })


if __name__ == "__main__":
    main()
