"""
Fix 6: Re-entrenamiento Oracle con 30 días históricos Binance Vision
Ejecutar después de confirmar que ZigZag threshold 0.18% está en código.
"""
import requests
import zipfile
import io
import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

sys.path.insert(0, '.')

SYMBOL = 'BTCUSDT'
INTERVAL = '5m'
DAYS = 30
OUTPUT_DIR = Path('cgalpha_v3/data/historical_30d')
BASE_URL = f'https://data.binance.vision/data/futures/um/daily/klines/{SYMBOL}/{INTERVAL}'

def download_historical():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.utcnow()
    frames = []

    for i in range(1, DAYS + 1):
        date = today - timedelta(days=i)
        filename = f'{SYMBOL}-{INTERVAL}-{date.strftime("%Y-%m-%d")}.zip'
        url = f'{BASE_URL}/{filename}'

        try:
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
            else:
                print(f'✗ {date.strftime("%Y-%m-%d")} (HTTP {r.status_code})')
        except Exception as e:
            print(f'✗ {date.strftime("%Y-%m-%d")} ({e})')

    if not frames:
        raise RuntimeError('No se descargaron datos')

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values('open_time').reset_index(drop=True)
    for col in ['open','high','low','close','volume']:
        combined[col] = pd.to_numeric(combined[col], errors='coerce')
    combined = combined.dropna(subset=['open','high','low','close','volume'])

    print(f'\nTotal velas descargadas: {len(combined)}')
    print(f'Rango: {combined["open_time"].iloc[0]} → {combined["open_time"].iloc[-1]}')
    return combined

def verify_distribution(training_file: Path):
    samples = json.loads(training_file.read_text())
    outcomes = Counter(s.get('outcome') for s in samples)
    total = sum(outcomes.values())
    print(f'\nDistribución del dataset:')
    for outcome, count in outcomes.items():
        pct = 100 * count / total
        flag = '⚠️ SOSPECHOSO' if abs(pct - 50) < 5 else ''
        print(f'  {outcome}: {count} ({pct:.1f}%) {flag}')
    return total, outcomes

if __name__ == '__main__':
    print('=== FIX 6: ENTRENAMIENTO HISTÓRICO ===\n')

    # Paso 1: Verificar threshold en código
    tc_file = Path('cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py')
    if '0.0018' not in tc_file.read_text():
        print('❌ STOP: threshold 0.18% no encontrado en triple_coincidence.py')
        print('   Ejecutar Fix 1 antes de continuar')
        sys.exit(1)
    print('✓ Threshold 0.18% verificado en código\n')

    # Paso 2: Descargar datos
    print('Descargando 30 días de datos históricos...')
    df = download_historical()

    # Paso 3: Procesar con detector
    print('\nProcesando con TripleCoincidenceDetector...')
    # [El procesamiento usa el pipeline existente de phase0_harvest.py]
    print('→ Ejecutar: python3 scripts/phase0_harvest.py --use-dataframe')
    print('  (o el equivalente que procese el DataFrame descargado)')

    # Paso 4: Verificar distribución
    td = Path('cgalpha_v3/data/phase0_results/training_dataset.json')
    if td.exists():
        total, outcomes = verify_distribution(td)
        if total < 100:
            print(f'\n⚠️  Solo {total} samples — considera descargar más días')

    print('\n=== LISTO PARA RE-ENTRENAMIENTO ===')
    print('Ejecutar: python3 scripts/phase1_oracle_training.py')
