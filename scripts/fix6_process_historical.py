"""
Fix 6: Procesar datos históricos reales con TripleCoincidenceDetector (threshold 0.25%)
Versión Refactorizada para Testabilidad.
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

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from cgalpha_v3.infrastructure.signal_detector.triple_coincidence import (
    TripleCoincidenceDetector, TrainingSample
)
from cgalpha_v3.lila.llm.oracle import OracleTrainer_v3

def get_config():
    """Configuración unificada y testeable."""
    return {
        'symbol': os.environ.get('FIX6_SYMBOL', 'BTCUSDT'),
        'interval': os.environ.get('FIX6_INTERVAL', '5m'),
        'days': int(os.environ.get('FIX6_DAYS', '60')),
        'min_success_days': int(os.environ.get('FIX6_MIN_SUCCESS_DAYS', '30')),
        'expected_threshold': os.environ.get('FIX6_EXPECTED_THRESHOLD', '0.0018'),
        'expected_threshold_label': os.environ.get('FIX6_EXPECTED_THRESHOLD_LABEL', '0.18%'),
        'data_dir': Path('cgalpha_v3/data/historical_60d')
    }

def verify_threshold_guard(config):
    """Protección contra threshold incorrecto en detector."""
    tc_file = Path('cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py')
    content = tc_file.read_text()
    if config['expected_threshold'] not in content:
        print(f"❌ STOP: threshold {config['expected_threshold_label']} no encontrado.")
        sys.exit(1)
    print(f"✓ Threshold {config['expected_threshold_label']} verificado.")

def load_and_validate_csv(csv_path_or_buf):
    """Carga y valida el formato de un CSV de Binance."""
    # Soporta tanto path como buffer (para tests)
    df = pd.read_csv(csv_path_or_buf, header=None if isinstance(csv_path_or_buf, io.StringIO) else 'infer')
    
    # En crudo de Binance no tiene headers y son 12 columnas
    # Si viene con headers (ya procesado) buscamos columnas clave
    if 'close' in df.columns:
        cols_missing = [c for c in ['open','high','low','close','volume'] if c not in df.columns]
        if cols_missing:
            raise ValueError(f"Faltan columnas críticas: {cols_missing}")
    else:
        if len(df.columns) < 5:
            raise ValueError(f"Formato CSV inválido: se obtuvieron solo {len(df.columns)} columnas")
    return df

def load_historical_data():
    """Carga de datos con múltiples fallbacks."""
    config = get_config()
    combined_csv = config['data_dir'] / f"combined_{config['symbol']}_{config['interval']}_{config['days']}d.csv"
    
    if combined_csv.exists():
        print(f"Cargando dataset combinado: {combined_csv.name}")
        return pd.read_csv(combined_csv)

    zips = list(config['data_dir'].glob('*.zip'))
    if len(zips) >= config['min_success_days']:
        print(f"Integrando {len(zips)} archivos ZIP")
        frames = []
        for f in sorted(zips):
            with zipfile.ZipFile(f) as z:
                csv_name = z.namelist()[0]
                with z.open(csv_name) as csvf:
                    df = pd.read_csv(csvf, header=None,
                        names=['open_time','open','high','low','close',
                               'volume','close_time','quote_vol','trades',
                               'taker_base','taker_quote','ignore'])
                    frames.append(df)
        
        combined = pd.concat(frames, ignore_index=True)
        combined = combined.sort_values('open_time').reset_index(drop=True)
        for col in ['open','high','low','close','volume']:
            combined[col] = pd.to_numeric(combined[col], errors='coerce')
        return combined.dropna(subset=['open','high','low','close','volume'])

    print("Error: No hay suficientes datos históricos.")
    sys.exit(1)

def compute_micro_features(df: pd.DataFrame) -> pd.DataFrame:
    """Features de microestructura (Simuladas para historical)."""
    n = len(df)
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
    
    # ATR Simple
    tr = pd.concat([df['high']-df['low'], abs(df['high']-df['close'].shift(1)), abs(df['low']-df['close'].shift(1))], axis=1).max(axis=1)
    atr = tr.rolling(14, min_periods=1).mean()
    
    rng = np.random.default_rng(42)
    obi = np.clip(df['close'].pct_change().fillna(0) * 5 + rng.normal(0, 0.1, n), -1, 1)
    
    return pd.DataFrame({
        'vwap': vwap.round(2),
        'obi_10': obi.round(4),
        'atr_14': atr.round(2),
        'cumulative_delta': (df['volume'] * rng.uniform(-0.5, 0.5, n)).cumsum().round(2),
        'delta_divergence': ['NEUTRAL'] * n
    })

def main():
    config = get_config()
    verify_threshold_guard(config)
    
    df = load_historical_data()
    micro_df = compute_micro_features(df)
    detector = TripleCoincidenceDetector()
    detector.process_stream(df, micro_df)
    
    oracle = OracleTrainer_v3.create_default()
    training_data = [{'features': s.features, 'outcome': s.outcome} for s in detector.training_samples]
    
    oracle.load_training_dataset(training_data)
    oracle.train_model()
    
    m = oracle._training_metrics
    print(f"\n  TEST ACCURACY: {m.get('test_accuracy', 'FAILED')}")
    print(f"  CV ACCURACY:   {m.get('cv_mean', 'N/A')} +/- {m.get('cv_std', 'N/A')}")
    print(f"  BRIER SCORE:   {m.get('brier_score', 'N/A')}")
    
    oracle.save_to_disk('aipha_memory/models/oracle_v3.joblib')
    
    # Exportar los samples para el análisis posterior de clearance (Fase 8)
    out_path = Path('cgalpha_v3/data/phase0_results/training_dataset.json')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(training_data, indent=2))
    print(f"\n✓ Dataset exportado: {len(training_data)} samples en {out_path.name}")


if __name__ == '__main__':
    main()
