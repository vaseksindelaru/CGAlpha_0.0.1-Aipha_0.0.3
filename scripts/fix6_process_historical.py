"""
Fix 6: Procesar datos históricos reales con TripleCoincidenceDetector (threshold 0.18%)
y re-entrenar Oracle con labels corregidos.
"""
import sys
import json
import zipfile
import io
import numpy as np
import pandas as pd
from pathlib import Path
from collections import Counter
import logging

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("fix6")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from cgalpha_v3.infrastructure.signal_detector.triple_coincidence import (
    TripleCoincidenceDetector, TrainingSample
)
from cgalpha_v3.lila.llm.oracle import OracleTrainer_v3

DATA_DIR = Path('cgalpha_v3/data/historical_30d')
BASE_URL = 'https://data.binance.vision/data/futures/um/daily/klines/BTCUSDT/5m'


def download_historical() -> pd.DataFrame:
    """Descargar 30 días de datos históricos de Binance Vision."""
    import requests
    from datetime import datetime, timedelta

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.utcnow()
    frames = []

    for i in range(1, 31):
        date = today - timedelta(days=i)
        filename = f'BTCUSDT-5m-{date.strftime("%Y-%m-%d")}.zip'
        url = f'{BASE_URL}/{filename}'

        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                    csv_name = z.namelist()[0]
                    with z.open(csv_name) as csvf:
                        df = pd.read_csv(csvf, header=None,
                            names=['open_time','open','high','low','close',
                                   'volume','close_time','quote_vol','trades',
                                   'taker_base','taker_quote','ignore'])
                        frames.append(df)
                # Also save to disk
                (DATA_DIR / filename).write_bytes(r.content)
                print(f'  ✓ {date.strftime("%Y-%m-%d")} ({len(df)} velas)')
            else:
                print(f'  ✗ {date.strftime("%Y-%m-%d")} (HTTP {r.status_code})')
        except Exception as e:
            print(f'  ✗ {date.strftime("%Y-%m-%d")} ({e})')

    if not frames:
        raise RuntimeError('No se descargaron datos')

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values('open_time').reset_index(drop=True)
    for col in ['open','high','low','close','volume']:
        combined[col] = pd.to_numeric(combined[col], errors='coerce')
    combined = combined.dropna(subset=['open','high','low','close','volume'])

    logger.info(f"Datos descargados: {len(combined)} velas")
    return combined


def load_historical_data() -> pd.DataFrame:
    """Cargar datos históricos de disco o descargar si no existen."""
    # Try loading from disk first
    zips = list(DATA_DIR.glob('*.zip'))
    if len(zips) >= 25:  # At least 25 days
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
            logger.info(f"Datos cargados de disco: {len(combined)} velas")
            return combined

    # Download if not on disk
    logger.info("Descargando datos de Binance Vision...")
    return download_historical()


def compute_micro_features(df: pd.DataFrame) -> pd.DataFrame:
    """Calcular features de microestructura a partir de OHLCV real."""
    n = len(df)

    # VWAP: media ponderada acumulativa
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    cum_vol = df['volume'].cumsum()
    cum_tp_vol = (typical_price * df['volume']).cumsum()
    vwap = cum_tp_vol / cum_vol

    # ATR 14
    high_low = df['high'] - df['low']
    high_close_prev = abs(df['high'] - df['close'].shift(1))
    low_close_prev = abs(df['low'] - df['close'].shift(1))
    tr = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
    atr_14 = tr.rolling(14, min_periods=1).mean()

    # OBI simulado (no hay datos de order book en klines)
    price_return = df['close'].pct_change().fillna(0)
    rng = np.random.default_rng(42)
    obi_base = price_return * rng.uniform(3, 8, size=n)
    obi = np.clip(obi_base + rng.normal(0, 0.15, n), -1, 1)

    # Cumulative Delta simulado
    delta_per_bar = price_return * df['volume'] * rng.uniform(0.3, 0.7, size=n)
    cum_delta = delta_per_bar.cumsum()

    # Delta divergence
    divergence = []
    for i in range(n):
        if price_return.iloc[i] > 0.002 and obi.iloc[i] > 0.3:
            divergence.append("BULLISH_ABSORPTION")
        elif price_return.iloc[i] < -0.002 and obi.iloc[i] < -0.3:
            divergence.append("BEARISH_EXHAUSTION")
        else:
            divergence.append("NEUTRAL")

    micro_df = pd.DataFrame({
        'vwap': vwap.round(2),
        'obi_10': obi.round(4),
        'cumulative_delta': cum_delta.round(2),
        'delta_divergence': divergence,
        'atr_14': atr_14.round(2),
    })

    logger.info(f"Micro-features calculados: {len(micro_df)} registros")
    return micro_df


def main():
    print("=" * 70)
    print("  FIX 6: Re-entrenamiento Oracle con datos históricos reales")
    print("  ZigZag threshold: 0.18% (post-fix)")
    print("=" * 70)
    print()

    # Verificar threshold
    tc_file = Path('cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py')
    if '0.0018' not in tc_file.read_text():
        print('❌ STOP: threshold 0.18% no encontrado en triple_coincidence.py')
        sys.exit(1)
    print('✓ Threshold 0.18% verificado\n')

    # Paso 1: Cargar datos
    logger.info("PASO 1: Cargando datos históricos...")
    df = load_historical_data()
    print(f"  📊 Datos: {len(df)} velas (5m)")
    print(f"  💰 Precio: ${df['close'].iloc[0]:,.2f} → ${df['close'].iloc[-1]:,.2f}")
    print()

    # Paso 2: Calcular micro features
    logger.info("PASO 2: Calculando features de microestructura...")
    micro_df = compute_micro_features(df)
    print()

    # Paso 3: Detectar zonas + retests
    logger.info("PASO 3: Ejecutando TripleCoincidenceDetector.process_stream()...")
    detector = TripleCoincidenceDetector()
    retest_events = detector.process_stream(df, micro_df)

    print(f"  🎯 Zonas activas detectadas: {len(detector.active_zones)}")
    print(f"  ⏳ Retests detectados: {len(retest_events)}")
    print(f"  📝 Samples de entrenamiento: {len(detector.training_samples)}")
    print()

    # Paso 4: Analizar distribución — NÚMERO 1
    logger.info("PASO 4: Analizando distribución del dataset...")

    if detector.training_samples:
        outcomes = [s.outcome for s in detector.training_samples]
        dist = Counter(outcomes)
        total = len(outcomes)

        print(f"  📊 Distribución de outcomes:")
        for outcome, count in dist.most_common():
            pct = 100 * count / total
            flag = '⚠️ SOSPECHOSO' if abs(pct - 50) < 5 else '✓'
            print(f"     {outcome}: {count} ({pct:.1f}%) {flag}")

        # NÚMERO 2: Total samples
        print(f"\n  📊 Total samples: {total}")
        if total < 100:
            print(f"  ⚠️  Solo {total} samples — considerar más días o ajustar detector")
        elif total >= 200:
            print(f"  ✓ Suficientes samples para entrenamiento")

        # Feature stats
        vwap_vals = [s.features.get('vwap_at_retest', 0) for s in detector.training_samples]
        obi_vals = [s.features.get('obi_10_at_retest', 0) for s in detector.training_samples]
        delta_vals = [s.features.get('cumulative_delta_at_retest', 0) for s in detector.training_samples]

        print(f"\n  📐 Features en retest:")
        print(f"     VWAP:  μ={np.mean(vwap_vals):.2f}, σ={np.std(vwap_vals):.2f}")
        print(f"     OBI:   μ={np.mean(obi_vals):.4f}, σ={np.std(obi_vals):.4f}")
        print(f"     Delta: μ={np.mean(delta_vals):.2f}, σ={np.std(delta_vals):.2f}")
    else:
        print("  ⚠️  No se generaron samples de entrenamiento.")
        print("  Posibles causas: detector muy restrictivo o datos insuficientes")
        return

    print()

    # Paso 5: Entrenar Oracle — NÚMERO 3
    logger.info("PASO 5: Entrenamiento del Oracle...")

    if len(detector.training_samples) < 5:
        print("  ⚠️  Insuficientes samples para entrenar Oracle (<5)")
        return

    oracle = OracleTrainer_v3.create_default()

    # Preparar dataset
    training_data = []
    for sample in detector.training_samples:
        training_data.append({
            'features': sample.features,
            'outcome': sample.outcome,
            'zone_id': sample.zone_id,
        })

    # Guardar dataset limpio
    output_dir = Path('cgalpha_v3/data/phase0_results')
    output_dir.mkdir(parents=True, exist_ok=True)
    dataset_path = output_dir / 'training_dataset.json'
    dataset_path.write_text(json.dumps(training_data, indent=2, default=str))
    logger.info(f"Dataset guardado: {dataset_path}")

    # Entrenar
    oracle.load_training_dataset(training_data)
    oracle.train_model()

    m = oracle._training_metrics
    print(f"\n  ═════════════════════════════════════════════════")
    print(f"  📊 PRIMERA MÉTRICA OOS REAL")
    print(f"  ═════════════════════════════════════════════════")
    print(f"  Samples: {m['n_samples']} (train={m['n_train']}, test={m['n_test']})")
    print(f"  Train accuracy: {m['train_accuracy']}")
    print(f"  TEST ACCURACY:  {m['test_accuracy']}  ← línea base real")
    print(f"  Rebalance: {m.get('rebalance_applied', 'N/A')}")

    dist = m.get('class_distribution', {})
    for cls, count in dist.items():
        print(f"  {cls}: {count}")

    # Interpretación
    ta = m['test_accuracy']
    if ta >= 0.95:
        print("\n  ⚠️  SOSPECHOSO: accuracy > 0.95 con datos reales — verificar leakage")
    elif ta >= 0.70:
        print("\n  ✓ Discriminación útil — activar con supervisión")
    elif ta >= 0.55:
        print("\n  △ Discriminación débil pero real — continuar acumulando datos")
    else:
        print("\n  ✗ Oracle no discrimina — features insuficientes")

    # Guardar modelo
    model_path = Path('aipha_memory/models/oracle_v3_historical.joblib')
    model_path.parent.mkdir(parents=True, exist_ok=True)
    oracle.save_to_disk(str(model_path))
    print(f"\n  💾 Modelo guardado: {model_path}")

    # También reemplazar el modelo activo
    oracle.save_to_disk('aipha_memory/models/oracle_v3.joblib')
    print(f"  💾 Modelo activo actualizado: aipha_memory/models/oracle_v3.joblib")

    print("\n=== FIX 6 COMPLETADO ===")


if __name__ == '__main__':
    main()
