"""
Fix 6: Re-entrenamiento Oracle con 60 días históricos Binance Vision
Versión Hardened & Standardized (Env-Driven).
"""
import requests
import zipfile
import io
import sys
import json
import os
import time
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

sys.path.insert(0, '.')

# Configuración FIX6_ (Standardized Knobs)
SYMBOL = os.environ.get('FIX6_SYMBOL', 'BTCUSDT')
INTERVAL = os.environ.get('FIX6_INTERVAL', '5m')
DAYS = int(os.environ.get('FIX6_DAYS', '60'))
TIMEOUT = int(os.environ.get('FIX6_REQUEST_TIMEOUT', '30'))
MIN_SUCCESS_DAYS = int(os.environ.get('FIX6_MIN_SUCCESS_DAYS', '30'))
MAX_RETRIES = int(os.environ.get('FIX6_MAX_RETRIES', '3'))
# Compatibilidad: FALLBACK a BASE_SECONDS si no existe RETRY_DELAY
RETRY_DELAY = int(os.environ.get('FIX6_RETRY_DELAY', 
                   os.environ.get('FIX6_BACKOFF_BASE_SECONDS', '5')))

# Guardia de Seguridad: FALLBACK a ZIGZAG_THRESHOLD si no existe el nuevo
EXPECTED_THRESHOLD = os.environ.get('FIX6_EXPECTED_THRESHOLD', 
                       os.environ.get('FIX6_EXPECTED_ZIGZAG_THRESHOLD', '0.0025'))
EXPECTED_THRESHOLD_LABEL = os.environ.get('FIX6_EXPECTED_THRESHOLD_LABEL', '0.25%')

OUTPUT_DIR = Path('cgalpha_v3/data/historical_60d')
BASE_URL = f'https://data.binance.vision/data/futures/um/daily/klines/{SYMBOL}/{INTERVAL}'

def download_historical():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.utcnow()
    frames = []
    success_count = 0

    print(f"Iniciando descarga resiliente: {DAYS} días (Mínimo: {MIN_SUCCESS_DAYS})")

    for i in range(1, DAYS + 1):
        date = today - timedelta(days=i)
        filename = f'{SYMBOL}-{INTERVAL}-{date.strftime("%Y-%m-%d")}.zip'
        url = f'{BASE_URL}/{filename}'
        
        for attempt in range(MAX_RETRIES):
            try:
                if attempt > 0:
                    sleep_time = RETRY_DELAY * (2 ** (attempt - 1))
                    time.sleep(sleep_time)

                r = requests.get(url, timeout=TIMEOUT)
                if r.status_code == 200:
                    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                        csv_name = z.namelist()[0]
                        with z.open(csv_name) as f:
                            df = pd.read_csv(f, header=None,
                                names=['open_time','open','high','low','close',
                                       'volume','close_time','quote_vol','trades',
                                       'taker_base','taker_quote','ignore'])
                            frames.append(df)
                    print(f'✓ {date.strftime("%Y-%m-%d")} ({len(df)} velas)')
                    success_count += 1
                    break
                elif r.status_code == 403:
                    print(f'✗ {date.strftime("%Y-%m-%d")} (HTTP 403)')
                    break
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    print(f'✗ {date.strftime("%Y-%m-%d")} (Error: {e})')
        
    if success_count < MIN_SUCCESS_DAYS:
        raise RuntimeError(f'Fracaso crítico: {success_count} días (Mínimo {MIN_SUCCESS_DAYS})')
    
    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values('open_time').reset_index(drop=True)
    for col in ['open','high','low','close','volume']:
        combined[col] = pd.to_numeric(combined[col], errors='coerce')
    return combined.dropna(subset=['open','high','low','close','volume'])

if __name__ == '__main__':
    print('=== FIX 6 STANDARDIZED: HISTORICAL TRAINING ===\n')

    tc_file = Path('cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py')
    if EXPECTED_THRESHOLD not in tc_file.read_text():
        print(f'❌ STOP: threshold {EXPECTED_THRESHOLD_LABEL} no encontrado')
        sys.exit(1)
    print(f'✓ Threshold {EXPECTED_THRESHOLD_LABEL} verificado\n')

    df = download_historical()
    df.to_csv(OUTPUT_DIR / f"combined_{SYMBOL}_{INTERVAL}_{DAYS}d.csv", index=False)
