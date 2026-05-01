"""
Fix 6: Procesar datos históricos reales con TripleCoincidenceDetector (threshold 0.25%)
Versión Hardened: Alineada con 60 días y validación de red.
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

# Configuración (Alineada con historical_training.py - FIX6_*)
SYMBOL = os.environ.get('FIX6_SYMBOL', 'BTCUSDT')
INTERVAL = os.environ.get('FIX6_INTERVAL', '5m')
DAYS = int(os.environ.get('FIX6_DAYS', '60'))
MIN_SUCCESS_DAYS = int(os.environ.get('FIX6_MIN_SUCCESS_DAYS', '30'))

EXPECTED_THRESHOLD = os.environ.get('FIX6_EXPECTED_THRESHOLD', '0.0025')
EXPECTED_THRESHOLD_LABEL = os.environ.get('FIX6_EXPECTED_THRESHOLD_LABEL', '0.25%')

DATA_DIR = Path('cgalpha_v3/data/historical_60d')

from cgalpha_v3.infrastructure.signal_detector.triple_coincidence import (
    TripleCoincidenceDetector, TrainingSample
)
from cgalpha_v3.lila.llm.oracle import OracleTrainer_v3

def load_historical_data() -> pd.DataFrame:
    """Cargar datos históricos de disco o del CSV combinado."""
    # Prioridad 1: CSV combinado de historical_training.py
    combined_csv = DATA_DIR / f"combined_{SYMBOL}_{INTERVAL}_{DAYS}d.csv"
    if combined_csv.exists():
        logger.info(f"Cargando dataset combinado desde {combined_csv.name}")
        df = pd.read_csv(combined_csv)
        return df

    # Prioridad 2: Zips individuales
    zips = list(DATA_DIR.glob('*.zip'))
    if len(zips) >= MIN_SUCCESS_DAYS:
        logger.info(f"Integrando {len(zips)} archivos ZIP desde {DATA_DIR}")
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
            combined = combined.dropna(subset=['open','high','low','close','volume'])
            return combined

    logger.error(f"No se encontraron suficientes datos (Mínimo: {MIN_SUCCESS_DAYS} días).")
    logger.error("Ejecute 'python3 scripts/fix6_historical_training.py' primero.")
    sys.exit(1)

def compute_micro_features(df: pd.DataFrame) -> pd.DataFrame:
    """Calcular features de microestructura a partir de OHLCV real."""
    n = len(df)
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    cum_vol = df['volume'].cumsum()
    cum_tp_vol = (typical_price * df['volume']).cumsum()
    vwap = cum_tp_vol / cum_vol

    high_low = df['high'] - df['low']
    high_close_prev = abs(df['high'] - df['close'].shift(1))
    low_close_prev = abs(df['low'] - df['close'].shift(1))
    tr = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
    atr_14 = tr.rolling(14, min_periods=1).mean()

    # Microestructura simulada para historical
    price_return = df['close'].pct_change().fillna(0)
    rng = np.random.default_rng(42)
    obi_base = price_return * rng.uniform(3, 8, size=n)
    obi = np.clip(obi_base + rng.normal(0, 0.15, n), -1, 1)
    delta_per_bar = price_return * df['volume'] * rng.uniform(0.3, 0.7, size=n)
    cum_delta = delta_per_bar.cumsum()

    divergence = []
    for i in range(n):
        if price_return.iloc[i] > 0.002 and obi.iloc[i] > 0.3:
            divergence.append("BULLISH_ABSORPTION")
        elif price_return.iloc[i] < -0.002 and obi.iloc[i] < -0.3:
            divergence.append("BEARISH_EXHAUSTION")
        else:
            divergence.append("NEUTRAL")

    return pd.DataFrame({
        'vwap': vwap.round(2),
        'obi_10': obi.round(4),
        'cumulative_delta': cum_delta.round(2),
        'delta_divergence': divergence,
        'atr_14': atr_14.round(2),
    })

def main():
    print("=" * 70)
    print("  FIX 6 HARDENED: Procesamiento Histórico (60 Días)")
    print("  ZigZag threshold: 0.25% (oficial)")
    print("=" * 70)

    tc_file = Path('cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py')
    if EXPECTED_THRESHOLD not in tc_file.read_text():
        print(f'❌ STOP: threshold {EXPECTED_THRESHOLD_LABEL} ({EXPECTED_THRESHOLD}) no encontrado en triple_coincidence.py')
        sys.exit(1)
    print(f'✓ Threshold {EXPECTED_THRESHOLD_LABEL} verificado en código\n')

    logger.info("PASO 1: Cargando datos históricos...")
    df = load_historical_data()
    print(f"  📊 Datos: {len(df)} velas (5m) | {len(df)//288} días")

    logger.info("PASO 2: Calculando features de microestructura...")
    micro_df = compute_micro_features(df)

    logger.info("PASO 3: Ejecutando TripleCoincidenceDetector...")
    detector = TripleCoincidenceDetector()
    retest_events = detector.process_stream(df, micro_df)

    print(f"  ⏳ Retests detectados: {len(retest_events)}")
    print(f"  📝 Samples generados: {len(detector.training_samples)}")

    if not detector.training_samples:
        print("  ⚠️  No se generaron samples.")
        return

    outcomes = [s.outcome for s in detector.training_samples]
    dist = Counter(outcomes)
    print(f"\n  📊 Distribución de outcomes:")
    for outcome, count in dist.most_common():
        print(f"     {outcome}: {count} ({100*count/len(outcomes):.1f}%)")

    logger.info("PASO 4: Entrenamiento del Oracle...")
    oracle = OracleTrainer_v3.create_default()
    training_data = [
        {'features': s.features, 'outcome': s.outcome, 'zone_id': s.zone_id}
        for s in detector.training_samples
    ]
    
    output_dir = Path('cgalpha_v3/data/phase0_results')
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'training_dataset.json').write_text(json.dumps(training_data, indent=2, default=str))

    oracle.load_training_dataset(training_data)
    oracle.train_model()

    m = oracle._training_metrics
    print(f"\n  ═════════════════════════════════════════════════")
    print(f"  📊 MÉTRICA OOS (60 DÍAS)")
    print(f"  ═════════════════════════════════════════════════")
    print(f"  TEST ACCURACY:  {m['test_accuracy']}  (Samples: {m['n_samples']})")

    model_path = Path('aipha_memory/models/oracle_v3.joblib')
    oracle.save_to_disk(str(model_path))
    print(f"\n  💾 Modelo activo actualizado: {model_path}")
    print("\n=== FIX 6 COMPLETADO ===")

if __name__ == '__main__':
    main()
