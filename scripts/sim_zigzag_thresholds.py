import sys
import pandas as pd
import numpy as np
from pathlib import Path
import zipfile
import io
import logging

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from cgalpha_v3.infrastructure.signal_detector.triple_coincidence import (
    TripleCoincidenceDetector
)

logging.basicConfig(level=logging.WARNING)

def load_data():
    data_dir = Path('cgalpha_v3/data/historical_60d')
    frames = []
    for zf in sorted(data_dir.glob('*.zip')):
        try:
            with zipfile.ZipFile(zf) as z:
                csv_name = z.namelist()[0]
                with z.open(csv_name) as f:
                    df = pd.read_csv(f, header=None)
                    if len(df.columns) >= 5:
                        frames.append(df)
        except:
            continue
    
    if not frames:
        return None
        
    combined = pd.concat(frames, ignore_index=True)
    # Ensure numeric and drop headers if any
    for col in [1, 2, 3, 4, 5]: # open, high, low, close, volume
        combined[col] = pd.to_numeric(combined[col], errors='coerce')
    combined = combined.dropna(subset=[1, 2, 3, 4])
    # Rename columns to standard 5m futures format
    combined.columns = ['open_time','open','high','low','close','volume',
                       'close_time','quote_vol','trades','taker_base','taker_quote','ignore'][:len(combined.columns)]
    return combined

def compute_micro_sim(df):
    # Minimal micro features for detector
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    cum_vol = df['volume'].cumsum()
    cum_tp_vol = (typical_price * df['volume']).cumsum()
    vwap = cum_tp_vol / cum_vol
    
    return pd.DataFrame({
        'vwap': vwap,
        'obi_10': 0.0,
        'cumulative_delta': 0.0,
        'atr_14': (df['high'] - df['low']).rolling(14).mean()
    })

def run_sim():
    print("Loading data...")
    df = load_data()
    if df is None:
        print("Error: No data found")
        return
    
    print(f"Total velas: {len(df)}")
    micro_df = compute_micro_sim(df)
    
    thresholds = [0.0018, 0.0025, 0.0030, 0.0035]
    results = []
    
    for t in thresholds:
        print(f"Simulating threshold: {t*100:.2f}% ...")
        # Creamos detector con config custom
        detector = TripleCoincidenceDetector()
        # FIX: Modificar el config del sub-detector de tendencia
        detector.trend_detector.config['zigzag_threshold'] = t
        # También el del detector principal por si acaso (algunos lo usan para logging)
        detector.config['zigzag_threshold'] = t
        
        # Procesar
        retests = detector.process_stream(df, micro_df)
        samples = len(detector.training_samples)
        
        # Distribución
        outcomes = [s.outcome for s in detector.training_samples]
        from collections import Counter
        dist = Counter(outcomes)
        
        results.append({
            'threshold': t,
            'samples': samples,
            'distribution': dict(dist)
        })

    print("\n" + "="*50)
    print("SIMULATION RESULTS (60 DAYS)")
    print("="*50)
    for res in results:
        t = res['threshold']
        s = res['samples']
        d = res['distribution']
        total = sum(d.values())
        bounce_pct = (d.get('BOUNCE', 0) / total * 100) if total > 0 else 0
        print(f"Threshold {t*100:.2f}%:")
        print(f"  Total Samples: {s}")
        print(f"  Distribution: {d}")
        print(f"  Bounce Rate: {bounce_pct:.1f}%")
        print("-" * 20)

if __name__ == '__main__':
    run_sim()
