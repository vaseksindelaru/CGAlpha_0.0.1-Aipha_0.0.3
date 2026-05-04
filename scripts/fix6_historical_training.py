"""
Fix 6: Re-entrenamiento Oracle con 60 días históricos Binance Vision
Versión Refactorizada para Testabilidad.
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

def get_config():
    """Carga configuración desde variables de entorno con defaults seguros."""
    return {
        'symbol': os.environ.get('FIX6_SYMBOL', 'BTCUSDT'),
        'interval': os.environ.get('FIX6_INTERVAL', '5m'),
        'days': int(os.environ.get('FIX6_DAYS', '60')),
        'timeout': int(os.environ.get('FIX6_REQUEST_TIMEOUT', '30')),
        'min_success_days': int(os.environ.get('FIX6_MIN_SUCCESS_DAYS', '30')),
        'max_retries': int(os.environ.get('FIX6_MAX_RETRIES', '3')),
        'retry_delay': int(os.environ.get('FIX6_RETRY_DELAY', 
                       os.environ.get('FIX6_BACKOFF_BASE_SECONDS', '5'))),
        'expected_threshold': os.environ.get('FIX6_EXPECTED_THRESHOLD', 
                               os.environ.get('FIX6_EXPECTED_ZIGZAG_THRESHOLD', '0.0025')),
        'expected_threshold_label': os.environ.get('FIX6_EXPECTED_THRESHOLD_LABEL', '0.25%'),
        'output_dir': Path('cgalpha_v3/data/historical_60d')
    }

def verify_threshold_guard(config):
    """Verifica que el zigzag_threshold en el código coincida con lo esperado."""
    tc_file = Path('cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py')
    content = tc_file.read_text()
    if config['expected_threshold'] not in content:
        print(f"❌ STOP: threshold {config['expected_threshold_label']} no encontrado en detector.")
        sys.exit(1)
    print(f"✓ Threshold {config['expected_threshold_label']} verificado.")

def _download_single_day(url, timeout, max_retries, retry_delay):
    """Encapsula la descarga de un solo archivo para facilitar mockeo en tests."""
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                time.sleep(retry_delay * (2 ** (attempt - 1)))
            r = requests.get(url, timeout=timeout)
            if r.status_code == 200:
                return r.content
            elif r.status_code == 403:
                return None # Bloqueo persistente
        except Exception:
            if attempt == max_retries - 1:
                raise
    return None

def process_csv_zip(content):
    """Procesa el contenido de un ZIP con CSV de Binance."""
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        csv_name = z.namelist()[0]
        with z.open(csv_name) as f:
            df = pd.read_csv(f, header=None)
            if len(df.columns) != 12:
                raise ValueError(f"Formato CSV inválido: se esperaban 12 columnas, se obtuvieron {len(df.columns)}")
            df.columns = ['open_time','open','high','low','close',
                          'volume','close_time','quote_vol','trades',
                          'taker_base','taker_quote','ignore']
            return df

def download_historical():
    """Pipeline de descarga con modo degradado."""
    config = get_config()
    config['output_dir'].mkdir(parents=True, exist_ok=True)
    
    base_url = f'https://data.binance.vision/data/futures/um/daily/klines/{config["symbol"]}/{config["interval"]}'
    today = datetime.utcnow()
    frames = []
    success_count = 0

    print(f"Descargando {config['days']} días (Mínimo: {config['min_success_days']})")

    for i in range(1, config['days'] + 1):
        date = today - timedelta(days=i)
        filename = f'{config["symbol"]}-{config["interval"]}-{date.strftime("%Y-%m-%d")}.zip'
        url = f'{base_url}/{filename}'
        
        try:
            content = _download_single_day(url, config['timeout'], config['max_retries'], config['retry_delay'])
            if content:
                df = process_csv_zip(content)
                frames.append(df)
                success_count += 1
                print(f'✓ {date.strftime("%Y-%m-%d")} ({len(df)} velas)')
            else:
                print(f'✗ {date.strftime("%Y-%m-%d")} (Fallo de descarga)')
        except Exception as e:
            print(f'✗ {date.strftime("%Y-%m-%d")} (Error: {e})')
        
    if success_count < config['min_success_days']:
        raise RuntimeError(f'Fracaso crítico: {success_count} días (Mínimo {config["min_success_days"]})')
    
    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values('open_time').reset_index(drop=True)
    for col in ['open','high','low','close','volume']:
        combined[col] = pd.to_numeric(combined[col], errors='coerce')
    
    output_path = config['output_dir'] / f"combined_{config['symbol']}_{config['interval']}_{config['days']}d.csv"
    combined.to_csv(output_path, index=False)
    print(f"\n✅ Dataset guardado en {output_path}")
    return combined

if __name__ == '__main__':
    cfg = get_config()
    verify_threshold_guard(cfg)
    download_historical()
