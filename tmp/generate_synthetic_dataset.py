import json
import time
import random
import uuid
from pathlib import Path

DATA_PATH = Path("aipha_memory/operational/training_dataset_v2.jsonl")

def generate_synthetic_data():
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Vamos a generar 100 samples
    # - 40 BOUNCE_STRONG (Éxitos) -> OBI y Delta favorables
    # - 15 BOUNCE_WEAK (Ignorados) -> OBI neutral
    # - 35 BREAKOUT (Fracasos) -> OBI y Delta negativos
    # - 10 INCONCLUSIVE (Ignorados) -> Noise
    
    samples = []
    
    components = [
        ("BOUNCE_STRONG", 40),
        ("BOUNCE_WEAK", 15),
        ("BREAKOUT", 35),
        ("INCONCLUSIVE", 10),
    ]
    
    now = time.time()
    for outcome_label, count in components:
        for _ in range(count):
            sample_id = f"re_{random.randint(1000, 9999)}_{uuid.uuid4().hex[:6]}"
            direction = random.choice(["bullish", "bearish"])
            
            # Crear features correlacionadas al outcome
            if label_is_success(outcome_label):
                # OBI alineado a favor
                obi = random.uniform(0.1, 0.4) if direction == "bullish" else random.uniform(-0.4, -0.1)
                cum_delta = random.uniform(10, 500) if direction == "bullish" else random.uniform(-500, -10)
                delta_divergence = "CONFIRMED"
            elif outcome_label == "BREAKOUT":
                # OBI inverso o débil
                obi = random.uniform(-0.3, 0.05) if direction == "bullish" else random.uniform(-0.05, 0.3)
                cum_delta = random.uniform(-400, 50) if direction == "bullish" else random.uniform(-50, 400)
                delta_divergence = "DIVERGENT"
            else:
                obi = random.uniform(-0.1, 0.1)
                cum_delta = random.uniform(-100, 100)
                delta_divergence = "NEUTRAL"
                
            entry_price = 60000.0 + random.uniform(-5000, 5000)
            atr = entry_price * 0.005 # ~300
            
            # Fabricar Snapshot v2.0
            snapshot = {
                "_meta": {
                    "sample_id": sample_id,
                    "capture_ts_unix_ms": (now - random.randint(100, 100000)) * 1000,
                    "symbol": "BTCUSDT",
                    "schema_version": "2.0"
                },
                "zone_geometry": {
                    "direction": direction,
                    "zone_top": entry_price + 20,
                    "zone_bottom": entry_price - 20,
                    "zone_width_atr": 0.5
                },
                "l2_snapshot_at_touch": {
                    "retest_price": entry_price,
                    "vwap_at_retest": entry_price + random.uniform(-10, 10),
                    "obi_10": obi,
                    "cumulative_delta": cum_delta,
                    "delta_divergence": delta_divergence
                },
                "clearance": {
                    "atr_at_detection": atr,
                    "regime": random.choice(["TRENDING", "LATERAL", "VOLATILE"])
                },
                "outcome": {
                    "label": outcome_label,
                    "mfe": atr * random.uniform(0.6, 2.0) if label_is_success(outcome_label) else 0.0,
                    "mae": atr * random.uniform(0.1, 0.4) if outcome_label != "BREAKOUT" else atr * 1.5,
                    "mfe_atr": random.uniform(0.6, 2.0) if label_is_success(outcome_label) else 0.0,
                    "mae_atr": random.uniform(0.1, 0.4) if outcome_label != "BREAKOUT" else 1.5,
                    "bars_to_resolution": random.randint(3, 10)
                }
            }
            samples.append(snapshot)
            
    # Shuffle para no estar ordenados por clase
    random.shuffle(samples)
    
    with open(DATA_PATH, "w") as f:
        for s in samples:
            f.write(json.dumps(s) + "\n")
            
    print(f"✅ Generados {len(samples)} samples sintéticos en {DATA_PATH}")

def label_is_success(l):
    return l in ["BOUNCE_STRONG"]

if __name__ == "__main__":
    generate_synthetic_data()
