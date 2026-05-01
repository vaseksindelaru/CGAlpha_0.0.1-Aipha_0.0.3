"""
Fix 6: Re-entrenamiento Oracle con 60 días históricos Binance Vision
Versión Hardened: Reintentos, Backoff y Modo Degradado.
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

# Configuración (Calibración vía Entorno)
SYMBOL = os.environ.get('SYMBOL', 'BTCUSDT')
INTERVAL = os.environ.get('INTERVAL', '5m')
DAYS = int(os.environ.get('DAYS', '60'))
MIN_SUCCESS_DAYS = int(os.environ.get('MIN_SUCCESS_DAYS', '30'))
MAX_RETRIES = int(os.environ.get('MAX_RETRIES', '3'))
RETRY_DELAY = int(os.environ.get('RETRY_DELAY', '5')) # Base delay para backoff

OUTPUT_DIR = Path('cgalpha_v3/data/historical_60d')
BASE_URL = f'https://data.binance.vision/data/futures/um/daily/klines/{SYMBOL}/{INTERVAL}'

def download_historical():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.utcnow()
    frames = []
    success_count = 0

    print(f"Iniciando descarga resiliente: {DAYS} días (Mínimo requerido: {MIN_SUCCESS_DAYS})")

    for i in range(1, DAYS + 1):
        date = today - timedelta(days=i)
        filename = f'{SYMBOL}-{INTERVAL}-{date.strftime("%Y-%m-%d")}.zip'
        url = f'{BASE_URL}/{filename}'
        
        attempt_success = False
        for attempt in range(MAX_RETRIES):
            try:
                # Backoff exponencial simple
                if attempt > 0:
                    sleep_time = RETRY_DELAY * (2 ** (attempt - 1))
                    print(f"   REINTENTO {attempt}/{MAX_RETRIES} en {sleep_time}s para {date.strftime('%Y-%m-%d')}...")
                    time.sleep(sleep_time)

                r = requests.get(url, timeout=30)
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
                    attempt_success = True
                    break
                elif r.status_code == 403:
                    print(f'✗ {date.strftime("%Y-%m-%d")} (HTTP 403 Forbidden - Proxy/IP Block)')
                    # No reintentamos 403 ya que suele ser bloqueo persistente
                    break
                else:
                    print(f'✗ {date.strftime("%Y-%m-%d")} (HTTP {r.status_code})')
            except Exception as e:
                print(f'✗ {date.strftime("%Y-%m-%d")} (Error: {e})')
        
    print(f"\nFinalización de descarga: {success_count}/{DAYS} días exitosos.")
    
    if success_count < MIN_SUCCESS_DAYS:
        print(f"❌ ERROR: Solo se obtuvieron {success_count} días (mínimo requerido: {MIN_SUCCESS_DAYS})")
        raise RuntimeError(f'Fracaso crítico de red: No se alcanzó el umbral mínimo de {MIN_SUCCESS_DAYS} días')
    
    if success_count < DAYS:
        print(f"⚠️  MODO DEGRADADO: Continuando con {success_count} días de datos parciales.")

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values('open_time').reset_index(drop=True)
    for col in ['open','high','low','close','volume']:
        combined[col] = pd.to_numeric(combined[col], errors='coerce')
    combined = combined.dropna(subset=['open','high','low','close','volume'])

    print(f'Total velas procesadas: {len(combined)}')
    return combined

def verify_distribution(training_file: Path):
    if not training_file.exists():
        return 0, {}
    samples = json.loads(training_file.read_text())
    outcomes = Counter(s.get('outcome') for s in samples)
    total = sum(outcomes.values())
    print(f'\nDistribución del dataset:')
    for outcome, count in outcomes.items():
        pct = 100 * count / total
        flag = '⚠️ SOSPECHOSO' if abs(pct - 50) < 5 and total > 50 else ''
        print(f'  {outcome}: {count} ({pct:.1f}%) {flag}')
    return total, outcomes

if __name__ == '__main__':
    print('=== FIX 6 HARDENED: ENTRENAMIENTO HISTÓRICO ===\n')

    # Paso 1: Verificar threshold en código (0.25% oficial)
    tc_file = Path('cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py')
    if '0.0025' not in tc_file.read_text():
        print('❌ STOP: threshold 0.25% no encontrado en triple_coincidence.py')
        sys.exit(1)
    print('✓ Threshold 0.25% verificado en código\n')

    # Paso 2: Descargar datos
    df = download_historical()

    # Paso 3: Guardar para procesamiento
    OUTPUT_PATH = OUTPUT_DIR / f"combined_{SYMBOL}_{INTERVAL}_{DAYS}d.csv"
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\n✅ Datos guardados en {OUTPUT_PATH}")

    print('\n=== LISTO PARA PROCESAMIENTO ===')
    print('Siguiente paso: python3 scripts/fix6_process_historical.py')
