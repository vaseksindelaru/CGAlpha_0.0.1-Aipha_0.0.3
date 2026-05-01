"""
Fix 6: Procesar datos históricos reales con TripleCoincidenceDetector (threshold 0.25%)
Versión Hardened & Standardized (Env-Driven).
"""
import sys
import json
import zipfile
import io
import os
import numpy as np
import pandas as pd
from pathlib import Path
from collections import Counter
import logging

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("fix6_process")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configuración FIX6_
SYMBOL = os.environ.get('FIX6_SYMBOL', 'BTCUSDT')
INTERVAL = os.environ.get('FIX6_INTERVAL', '5m')
DAYS = int(os.environ.get('FIX6_DAYS', '60'))
MIN_SUCCESS_DAYS = int(os.environ.get('FIX6_MIN_SUCCESS_DAYS', '30'))

EXPECTED_THRESHOLD = os.environ.get('FIX6_EXPECTED_THRESHOLD', 
                       os.environ.get('FIX6_EXPECTED_ZIGZAG_THRESHOLD', '0.0025'))
EXPECTED_THRESHOLD_LABEL = os.environ.get('FIX6_EXPECTED_THRESHOLD_LABEL', '0.25%')

DATA_DIR = Path('cgalpha_v3/data/historical_60d')

from cgalpha_v3.infrastructure.signal_detector.triple_coincidence import (
    TripleCoincidenceDetector, TrainingSample
)
from cgalpha_v3.lila.llm.oracle import OracleTrainer_v3

def load_historical_data() -> pd.DataFrame:
    """Cargar datos históricos de disco."""
    combined_csv = DATA_DIR / f"combined_{SYMBOL}_{INTERVAL}_{DAYS}d.csv"
    if combined_csv.exists():
        logger.info(f"Cargando dataset combinado desde {combined_csv.name}")
        return pd.read_csv(combined_csv)

    zips = list(DATA_DIR.glob('*.zip'))
    if len(zips) >= MIN_SUCCESS_DAYS:
        logger.info(f"Integrando {len(zips)} archivos ZIP")
        frames = []
        for f in sorted(zips):
            try:
                with zipfile.ZipFile(f) as z:
                    csv_name = z.namelist()[0]
                    with z.open(csv_name) as csvf:
                        df = pd.read_csv(csvf, header=None,
                            names=['open_time','open','high','low','close',
                                   'volume','close_time','quote_vol','trades',
                                   'taker_base','taker_quote','ignore'])
                        frames.append(df)
            except Exception as e:
                logger.warning(f"Error leyendo {f.name}: {e}")
        
        if frames:
            combined = pd.concat(frames, ignore_index=True)
            combined = combined.sort_values('open_time').reset_index(drop=True)
            for col in ['open','high','low','close','volume']:
                combined[col] = pd.to_numeric(combined[col], errors='coerce')
            return combined.dropna(subset=['open','high','low','close','volume'])

    logger.error("No se encontraron suficientes datos.")
    sys.exit(1)

def compute_micro_features(df: pd.DataFrame) -> pd.DataFrame:
    """Calcular features de microestructura."""
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    cum_vol = df['volume'].cumsum()
    cum_tp_vol = (typical_price * df['volume']).cumsum()
    vwap = cum_tp_vol / cum_vol

    high_low = df['high'] - df['low']
    high_close_prev = abs(df['high'] - df['close'].shift(1))
    low_close_prev = abs(df['low'] - df['close'].shift(1))
    tr = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
    atr_14 = tr.rolling(14, min_periods=1).mean()

    # Simulación para historical
    price_return = df['close'].pct_change().fillna(0)
    rng = np.random.default_rng(42)
    obi = np.clip(price_return * rng.uniform(3, 8, len(df)) + rng.normal(0, 0.15, len(df)), -1, 1)
    cum_delta = (price_return * df['volume'] * rng.uniform(0.3, 0.7, len(df))).cumsum()

    divergence = [
        "BULLISH_ABSORPTION" if r > 0.002 and o > 0.3 else 
        "BEARISH_EXHAUSTION" if r < -0.002 and o < -0.3 else "NEUTRAL"
        for r, o in zip(price_return, obi)
    ]

    return pd.DataFrame({
        'vwap': vwap.round(2),
        'obi_10': obi.round(4),
        'cumulative_delta': cum_delta.round(2),
        'delta_divergence': divergence,
        'atr_14': atr_14.round(2),
    })

def main():
    print("=" * 70)
    print(f"  FIX 6 STANDARDIZED: PROCESSING ({SYMBOL} / {INTERVAL})")
    print(f"  ZigZag threshold: {EXPECTED_THRESHOLD_LABEL}")
    print("=" * 70)

    tc_file = Path('cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py')
    if EXPECTED_THRESHOLD not in tc_file.read_text():
        print(f'❌ STOP: threshold {EXPECTED_THRESHOLD_LABEL} no encontrado')
        sys.exit(1)

    df = load_historical_data()
    micro_df = compute_micro_features(df)
    detector = TripleCoincidenceDetector()
    retest_events = detector.process_stream(df, micro_df)
    
    print(f"  📝 Samples generados: {len(detector.training_samples)}")
    
    oracle = OracleTrainer_v3.create_default()
    training_data = [{'features': s.features, 'outcome': s.outcome} for s in detector.training_samples]
    oracle.load_training_dataset(training_data)
    oracle.train_model()
    
    m = oracle._training_metrics
    print(f"\n  TEST ACCURACY: {m['test_accuracy']}")
    oracle.save_to_disk('aipha_memory/models/oracle_v3.joblib')

if __name__ == '__main__':
    main()
