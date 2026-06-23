"""
Estudio Forense de Time Drift — D-014 Validación Empírica
==========================================================
Conecta al WebSocket de Binance Futures (btcusdt@depth20@100ms),
recibe ≥1000 mensajes, mide local_offset_ms = local_ts_ms - binance_ts_ms
para cada uno, y reporta la distribución estadística.

Objetivo: validar si p95 ≤ 100ms (considerar bajar ε a 100ms)
o si p95 > 200ms (necesario aumentar ε o mejorar NTP).

Valor canónico actual: ε = 200ms (D-014, ADR-ACOPLAMIENTO-TEMPORAL-1).

Uso:
    python cgalpha_v3/scripts/forensic_time_drift_study.py [--messages 1000] [--symbol btcusdt]

No requiere API keys (stream público). No modifica estado del sistema.
"""

import argparse
import asyncio
import json
import statistics
import time
from collections import Counter

import websockets


async def collect_drift_samples(symbol: str, num_messages: int) -> list:
    """
    Conecta al WebSocket de Binance y recolecta muestras de local_offset_ms.
    Retorna lista de floats (offset en milisegundos).
    """
    sym = symbol.lower()
    stream = f"{sym}@depth20@100ms"
    url = f"wss://fstream.binance.com/ws/{stream}"

    samples = []
    connection_attempts = 0

    print(f"🔗 Conectando a {url}")
    print(f"📊 Recolectando {num_messages} muestras de local_offset_ms...")

    while len(samples) < num_messages and connection_attempts < 3:
        connection_attempts += 1
        try:
            async with websockets.connect(url, ping_interval=60, ping_timeout=60) as ws:
                print(
                    f"✅ Conectado (intento {connection_attempts}). Recibiendo mensajes..."
                )
                while len(samples) < num_messages:
                    message = await ws.recv()
                    data = json.loads(message)

                    # Extraer binance_ts_ms (campo E = event time)
                    binance_ts_ms = data.get("E", data.get("T"))
                    if binance_ts_ms is None:
                        continue  # Skip mensajes sin timestamp

                    # Medir local_ts_ms inmediatamente después de recv
                    local_ts_ms = time.time() * 1000
                    local_offset_ms = local_ts_ms - binance_ts_ms

                    samples.append(local_offset_ms)

                    # Progress cada 100 muestras
                    if len(samples) % 100 == 0:
                        print(f"  ... {len(samples)}/{num_messages} muestras")

        except Exception as e:
            print(f"⚠️ Error en conexión (intento {connection_attempts}): {e}")
            if connection_attempts < 3:
                print(f"   Reintentando en 3s...")
                await asyncio.sleep(3)

    return samples


def analyze_drift(samples: list) -> dict:
    """
    Analiza la distribución de local_offset_ms.
    Retorna dict con min, p50, p95, p99, max, mean, std, y histograma.
    """
    if not samples:
        return {"error": "No samples collected"}

    sorted_samples = sorted(samples)
    n = len(sorted_samples)

    def percentile(p):
        idx = int(n * p / 100)
        if idx >= n:
            idx = n - 1
        return sorted_samples[idx]

    # Histograma por buckets
    buckets = [
        (-float("inf"), -500),
        (-500, -200),
        (-200, -100),
        (-100, -50),
        (-50, -10),
        (-10, 10),
        (10, 50),
        (50, 100),
        (100, 200),
        (200, 500),
        (500, float("inf")),
    ]
    bucket_labels = [
        "< -500ms",
        "-500 to -200ms",
        "-200 to -100ms",
        "-100 to -50ms",
        "-50 to -10ms",
        "-10 to +10ms",
        "+10 to +50ms",
        "+50 to +100ms",
        "+100 to +200ms",
        "+200 to +500ms",
        "> +500ms",
    ]
    bucket_counts = [0] * len(buckets)
    for s in samples:
        for i, (lo, hi) in enumerate(buckets):
            if lo <= s < hi:
                bucket_counts[i] += 1
                break

    return {
        "n_samples": n,
        "min_ms": sorted_samples[0],
        "p50_ms": percentile(50),
        "p95_ms": percentile(95),
        "p99_ms": percentile(99),
        "max_ms": sorted_samples[-1],
        "mean_ms": statistics.mean(samples),
        "std_ms": statistics.stdev(samples) if n > 1 else 0.0,
        "histogram": dict(zip(bucket_labels, bucket_counts)),
    }


def print_report(analysis: dict, epsilon_ms: int = 200):
    """Imprime el reporte forense con interpretación."""
    print("\n" + "=" * 70)
    print("REPORTE FORENSE — Time Drift (local_offset_ms)")
    print("=" * 70)
    print(f"Muestras recolectadas: {analysis['n_samples']}")
    print(f"\nDistribución estadística (ms):")
    print(f"  min:  {analysis['min_ms']:+.2f}ms")
    print(f"  p50:  {analysis['p50_ms']:+.2f}ms")
    print(f"  p95:  {analysis['p95_ms']:+.2f}ms")
    print(f"  p99:  {analysis['p99_ms']:+.2f}ms")
    print(f"  max:  {analysis['max_ms']:+.2f}ms")
    print(f"  mean: {analysis['mean_ms']:+.2f}ms")
    print(f"  std:  {analysis['std_ms']:.2f}ms")

    print(f"\nHistograma:")
    for label, count in analysis["histogram"].items():
        pct = (count / analysis["n_samples"]) * 100
        bar = "█" * int(pct / 2)
        print(f"  {label:>20s}: {count:5d} ({pct:5.1f}%) {bar}")

    print(f"\n{'=' * 70}")
    print(f"INTERPRETACIÓN — D-014 (ε = {epsilon_ms}ms)")
    print(f"{'=' * 70}")

    p95 = analysis["p95_ms"]
    max_val = analysis["max_ms"]

    if abs(p95) <= 100:
        print(f"✅ p95 = {p95:+.2f}ms ≤ 100ms")
        print(f"   El drift es mínimo. Se puede considerar bajar ε a 100ms")
        print(f"   (requiere nuevo ADR). ε = 200ms es conservadoramente seguro.")
    elif abs(p95) <= 200:
        print(f"✅ p95 = {p95:+.2f}ms ≤ 200ms (dentro de ε)")
        print(f"   ε = 200ms es adecuado. No se requiere ajuste.")
        print(f"   El drift está dentro del margen de seguridad.")
    else:
        print(f"⚠️  p95 = {p95:+.2f}ms > 200ms (excede ε)")
        print(f"   El drift excede el margen. Opciones:")
        print(f"   (a) Aumentar ε (requiere nuevo ADR + re-entrenamiento)")
        print(f"   (b) Mejorar NTP del servidor")
        print(f"   (c) Investigar si hay latencia de red anómala")

    if abs(max_val) > 200:
        print(f"\n⚠️  max = {max_val:+.2f}ms > 200ms")
        print(f"   Hay outliers que exceden ε. Estos snapshots serán")
        print(f"   marcados como CAUSAL_REJECTED cuando D-014 se implemente.")
        print(f"   Revisar si son spikes puntuales o un patrón recurrente.")

    print(f"\n{'=' * 70}")
    print(f"CONCLUSIÓN")
    print(f"{'=' * 70}")
    if abs(p95) <= 200:
        print(f"ε = {epsilon_ms}ms es VALIDADO empíricamente. p95 = {p95:+.2f}ms.")
        print(f"D-014 puede implementarse con confianza.")
    else:
        print(f"ε = {epsilon_ms}ms puede ser INSUFICIENTE. p95 = {p95:+.2f}ms.")
        print(f"Requiere investigación adicional antes de implementar D-014.")
    print(f"{'=' * 70}")


async def main():
    parser = argparse.ArgumentParser(
        description="Estudio Forense de Time Drift para D-014"
    )
    parser.add_argument(
        "--messages",
        type=int,
        default=1000,
        help="Número de mensajes a recolectar (default: 1000)",
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default="btcusdt",
        help="Símbolo a suscribir (default: btcusdt)",
    )
    parser.add_argument(
        "--epsilon",
        type=int,
        default=200,
        help="Valor de ε en ms para interpretación (default: 200)",
    )
    args = parser.parse_args()

    samples = await collect_drift_samples(args.symbol, args.messages)

    if len(samples) < args.messages:
        print(
            f"\n⚠️ Solo se recolectaron {len(samples)} muestras (objetivo: {args.messages})"
        )

    analysis = analyze_drift(samples)
    print_report(analysis, args.epsilon)


if __name__ == "__main__":
    asyncio.run(main())
