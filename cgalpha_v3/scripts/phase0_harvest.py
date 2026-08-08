"""
CGAlpha v3 — FASE 0: Cosecha y Observabilidad
===============================================
Script de ejecución que:
1. Genera datos OHLCV sintéticos realistas (o carga CSV si existe)
2. Ejecuta TripleCoincidenceDetector.process_stream()
3. Genera dataset de retests con features de microestructura
4. Entrena Oracle con el dataset
5. Documenta resultados y estadísticas

Ejecutar: PYTHONPATH=. python cgalpha_v3/scripts/phase0_harvest.py
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("phase0")

# Ensure project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from cgalpha_v3.infrastructure.signal_detector.triple_coincidence import (
    TripleCoincidenceDetector, RetestEvent, TrainingSample
)
from cgalpha_v3.application.experiment_runner import ExperimentRunner
from cgalpha_v3.lila.llm.oracle import OracleTrainer_v3


# ═══════════════════════════════════════════════════════════
# 1. GENERACIÓN DE DATOS OHLCV SINTÉTICOS REALISTAS
# ═══════════════════════════════════════════════════════════

def generate_realistic_ohlcv(
    n_candles: int = 2000,
    base_price: float = 65000.0,
    interval_ms: int = 3600000,  # 1h en ms
    seed: int = 42,
) -> pd.DataFrame:
    """
    Genera datos OHLCV sintéticos con propiedades realistas:
    - Movimiento browniano geométrico con drift
    - Periodos de alta/baja volatilidad (régimen)
    - Zonas de acumulación (laterales)
    - Velas de alto volumen (key candles)
    - Mini-tendencias con R² variable
    """
    rng = np.random.default_rng(seed)
    
    # Simular régimen: alternar entre TREND/LATERAL/HIGH_VOL
    regime_segments = []
    remaining = n_candles
    while remaining > 0:
        seg_len = rng.integers(40, 120)
        seg_len = min(seg_len, remaining)
        regime_type = rng.choice(["TREND", "LATERAL", "HIGH_VOL"], p=[0.35, 0.45, 0.20])
        regime_segments.append((regime_type, seg_len))
        remaining -= seg_len
    
    # Generar precios
    prices = [base_price]
    volumes = []
    regimes = []
    timestamps = []
    
    start_ts = int(datetime(2024, 1, 1).timestamp() * 1000)
    candle_idx = 0
    
    for regime_type, seg_len in regime_segments:
        if regime_type == "TREND":
            # Tendencia clara con drift
            drift = rng.choice([-1, 1]) * rng.uniform(0.0003, 0.001)
            vol = rng.uniform(0.003, 0.008)
        elif regime_type == "LATERAL":
            # Acumulación: baja volatilidad, sin drift
            drift = 0.0
            vol = rng.uniform(0.001, 0.004)
        else:  # HIGH_VOL
            # Alta volatilidad: movimientos grandes
            drift = rng.choice([-1, 1]) * rng.uniform(0.0001, 0.0005)
            vol = rng.uniform(0.008, 0.018)
        
        for i in range(seg_len):
            last_price = prices[-1]
            ret = drift + vol * rng.standard_normal()
            new_price = last_price * np.exp(ret)
            prices.append(new_price)
            
            # Volumen: base + spikes aleatorios
            base_vol = rng.uniform(800, 2500)
            if regime_type == "HIGH_VOL":
                base_vol *= 2.5
            # Spike de volumen ocasional (key candle candidata)
            if rng.random() < 0.08:
                base_vol *= rng.uniform(3, 8)
            volumes.append(base_vol)
            
            regimes.append(regime_type)
            timestamps.append(start_ts + candle_idx * interval_ms)
            candle_idx += 1
    
    # Quitar el precio inicial extra
    prices = prices[1:]
    
    # Construir OHLCV desde precios
    rows = []
    for i in range(len(prices)):
        close = prices[i]
        open_price = prices[i - 1] if i > 0 else close * (1 + rng.uniform(-0.002, 0.002))
        
        # High/Low realistas
        spread = abs(close - open_price) + close * rng.uniform(0.001, 0.005)
        high = max(open_price, close) + spread * rng.uniform(0.3, 1.0)
        low = min(open_price, close) - spread * rng.uniform(0.3, 1.0)
        
        rows.append({
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': round(volumes[i], 2),
            'close_time': timestamps[i],
            'regime': regimes[i],
        })
    
    df = pd.DataFrame(rows)
    logger.info(f"Datos OHLCV generados: {len(df)} velas, "
                f"precio rango [{df['low'].min():.2f}, {df['high'].max():.2f}]")
    return df


def generate_micro_features(df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """
    Genera features de microestructura sintéticos alineados con OHLCV.
    Simula VWAP, OBI, CumDelta, ATR de forma realista.
    """
    rng = np.random.default_rng(seed)
    n = len(df)
    
    # VWAP: media ponderada acumulativa (simplificada)
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    cum_vol = df['volume'].cumsum()
    cum_tp_vol = (typical_price * df['volume']).cumsum()
    vwap = cum_tp_vol / cum_vol
    
    # OBI (Order Book Imbalance): correlacionado con dirección del precio
    price_return = df['close'].pct_change().fillna(0)
    obi_base = price_return * rng.uniform(3, 8, size=n)
    obi = np.clip(obi_base + rng.normal(0, 0.15, n), -1, 1)
    
    # Cumulative Delta: acumulación de presión compradora/vendedora
    delta_per_bar = price_return * df['volume'] * rng.uniform(0.3, 0.7, size=n)
    cum_delta = delta_per_bar.cumsum()
    
    # ATR 14
    high_low = df['high'] - df['low']
    high_close_prev = abs(df['high'] - df['close'].shift(1))
    low_close_prev = abs(df['low'] - df['close'].shift(1))
    tr = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
    atr_14 = tr.rolling(14, min_periods=1).mean()
    
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
    
    logger.info(f"Micro-features generados: {len(micro_df)} registros, "
                f"VWAP rango [{micro_df['vwap'].min():.2f}, {micro_df['vwap'].max():.2f}]")
    return micro_df


# ═══════════════════════════════════════════════════════════
# 2. EJECUCIÓN DEL PIPELINE
# ═══════════════════════════════════════════════════════════

def run_phase0():
    """Ejecuta la Fase 0 completa."""
    
    print("=" * 70)
    print("  CGAlpha v3 — FASE 0: Cosecha y Observabilidad")
    print("  Triple Coincidence Strategy")
    print("=" * 70)
    print()
    
    # ── PASO 1: Generar datos ───────────────────────────────
    logger.info("PASO 1: Generando datos OHLCV sintéticos...")
    df = generate_realistic_ohlcv(n_candles=500, seed=42)
    micro_df = generate_micro_features(df, seed=42)
    
    print(f"  📊 Datos: {len(df)} velas (1h)")
    print(f"  💰 Precio: {df['close'].iloc[0]:.2f} → {df['close'].iloc[-1]:.2f}")
    print(f"  📈 Rango: [{df['low'].min():.2f}, {df['high'].max():.2f}]")
    print(f"  📊 Regímenes: {df['regime'].value_counts().to_dict()}")
    print()
    
    # ── PASO 2: Detectar zonas + retests ────────────────────
    logger.info("PASO 2: Ejecutando TripleCoincidenceDetector.process_stream()...")
    detector = TripleCoincidenceDetector()
    retest_events = detector.process_stream(df, micro_df)
    
    print(f"  🎯 Zonas activas detectadas: {len(detector.active_zones)}")
    print(f"  ⏳ Retests detectados: {len(retest_events)}")
    print(f"  📝 Samples de entrenamiento: {len(detector.training_samples)}")
    print()
    
    # ── PASO 3: Analizar dataset ────────────────────────────
    logger.info("PASO 3: Analizando dataset de retests...")
    
    if detector.training_samples:
        outcomes = [s.outcome for s in detector.training_samples]
        bounce_count = outcomes.count("BOUNCE")
        breakout_count = outcomes.count("BREAKOUT")
        unknown_count = len(outcomes) - bounce_count - breakout_count
        
        print(f"  📊 Distribución de outcomes:")
        print(f"     BOUNCE:   {bounce_count} ({bounce_count/len(outcomes)*100:.1f}%)")
        print(f"     BREAKOUT: {breakout_count} ({breakout_count/len(outcomes)*100:.1f}%)")
        if unknown_count > 0:
            print(f"     UNKNOWN:  {unknown_count} ({unknown_count/len(outcomes)*100:.1f}%)")
        
        # Estadísticas de features
        vwap_vals = [s.features.get('vwap_at_retest', 0) for s in detector.training_samples]
        obi_vals = [s.features.get('obi_10_at_retest', 0) for s in detector.training_samples]
        delta_vals = [s.features.get('cumulative_delta_at_retest', 0) for s in detector.training_samples]
        
        print()
        print(f"  📐 Features en retest:")
        print(f"     VWAP:  μ={np.mean(vwap_vals):.2f}, σ={np.std(vwap_vals):.2f}")
        print(f"     OBI:   μ={np.mean(obi_vals):.4f}, σ={np.std(obi_vals):.4f}")
        print(f"     Delta: μ={np.mean(delta_vals):.2f}, σ={np.std(delta_vals):.2f}")
        
        # Direcciones
        directions = [s.features.get('direction', 'UNKNOWN') for s in detector.training_samples]
        direction_counts = {}
        for d in directions:
            direction_counts[d] = direction_counts.get(d, 0) + 1
        print(f"     Directions: {direction_counts}")
        
    else:
        print("  ⚠️  No se generaron samples de entrenamiento.")
    
    print()
    
    # ── PASO 4: Entrenar Oracle (si hay suficientes datos) ──
    logger.info("PASO 4: Entrenamiento del Oracle...")
    
    if len(detector.training_samples) >= 5:
        oracle = OracleTrainer_v3.create_default()
        
        # Preparar dataset para Oracle
        training_data = []
        for sample in detector.training_samples:
            training_data.append({
                'features': sample.features,
                'outcome': sample.outcome,
                'zone_id': sample.zone_id,
            })
        
        # Por ahora Oracle es placeholder — documentamos los datos
        print(f"  🧠 Oracle: {len(training_data)} samples listos para entrenamiento")
        print(f"  ⚠️  Oracle actual es placeholder (confidence fija 0.85)")
        print(f"  📋 Próximo paso: implementar RandomForestClassifier")
    else:
        print(f"  ⚠️  Insuficientes samples para entrenar ({len(detector.training_samples)})")
        print(f"  📋 Necesarios: ≥30 para entrenamiento significativo")
    
    print()
    
    # ── PASO 5: Ejecutar experiment_runner.process_retests() ─
    logger.info("PASO 5: Validando flujo completo via ExperimentRunner...")
    
    runner = ExperimentRunner()
    runner.set_signal_detector()
    
    rows_dict = df.to_dict('records')
    micro_dict = micro_df.to_dict('records') if micro_df is not None else None
    retests = runner.process_retests(rows_dict, micro_dict)
    dataset = runner.get_training_dataset()
    
    print(f"  🔄 ExperimentRunner.process_retests(): {len(retests)} retests")
    print(f"  📦 ExperimentRunner.get_training_dataset(): {len(dataset)} samples")
    print()
    
    # ── PASO 6: Guardar resultados ──────────────────────────
    logger.info("PASO 6: Guardando resultados...")
    
    output_dir = PROJECT_ROOT / "cgalpha_v3" / "data" / "phase0_results"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Guardar retests
    if retests:
        retests_path = output_dir / "retests_dataset.json"
        with open(retests_path, 'w') as f:
            json.dump(retests, f, indent=2, default=str)
        print(f"  💾 Retests guardados: {retests_path}")
    
    # Guardar training samples
    if dataset:
        dataset_path = output_dir / "training_dataset.json"
        with open(dataset_path, 'w') as f:
            json.dump(dataset, f, indent=2, default=str)
        print(f"  💾 Dataset guardado: {dataset_path}")
    
    # Guardar OHLCV sintético
    ohlcv_path = output_dir / "synthetic_ohlcv_2000.csv"
    df.to_csv(ohlcv_path, index=False)
    print(f"  💾 OHLCV guardado: {ohlcv_path}")
    
    # Guardar resumen
    summary = {
        "phase": "0 — Cosecha y Observabilidad",
        "strategy": "Triple Coincidence v3",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "n_candles": len(df),
            "interval": "1h",
            "price_range": [float(df['low'].min()), float(df['high'].max())],
            "regime_distribution": df['regime'].value_counts().to_dict(),
        },
        "detection": {
            "active_zones": len(detector.active_zones),
            "retest_events": len(retest_events),
            "training_samples": len(detector.training_samples),
        },
        "outcomes": {
            "BOUNCE": bounce_count if detector.training_samples else 0,
            "BREAKOUT": breakout_count if detector.training_samples else 0,
        },
        "oracle": {
            "status": "placeholder",
            "confidence_fixed": 0.85,
            "next_step": "Implementar RandomForestClassifier con dataset real",
        },
        "experiment_runner": {
            "retests_via_runner": len(retests),
            "dataset_via_runner": len(dataset),
        },
    }
    
    summary_path = output_dir / "phase0_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"  💾 Resumen guardado: {summary_path}")
    
    print()
    print("=" * 70)
    print("  FASE 0 COMPLETADA")
    print("=" * 70)
    print()
    print("  Próximos pasos:")
    print("  ┌─────────────────────────────────────────────────────────┐")
    print("  │ 1. Analizar distribución de features en retests        │")
    print("  │ 2. Implementar RandomForestClassifier en Oracle        │")
    print("  │ 3. Descargar CSVs reales de Binance Vision             │")
    print("  │ 4. Ejecutar process_retests() con datos reales         │")
    print("  │ 5. Walk-Forward 3 ventanas → medir Sharpe             │")
    print("  └─────────────────────────────────────────────────────────┘")
    
    return summary


if __name__ == "__main__":
    run_phase0()
