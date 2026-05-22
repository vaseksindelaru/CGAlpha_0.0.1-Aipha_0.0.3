#!/usr/bin/env python3
import json
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATASET = PROJECT_ROOT / "aipha_memory" / "operational" / "training_dataset_v2.jsonl"

MIN_BOUNCE = 8
MIN_BREAKOUT = 16
MIN_FULL_TOTAL = 24


def load_rows(path: Path):
    rows = []
    if not path.exists():
        return rows
    with open(path, "r") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def main():
    rows = load_rows(DATASET)
    full = [r for r in rows if (r.get("l2_temporal_profile") or {}).get("l2_data_quality") == "FULL"]
    no_tag = [r for r in rows if not (r.get("l2_temporal_profile") or {}).get("l2_data_quality")]

    outcomes_full = Counter((r.get("outcome") or {}).get("label", "?") for r in full)
    b_strong = outcomes_full.get("BOUNCE_STRONG", 0)
    breakout = outcomes_full.get("BREAKOUT", 0)

    ready = (
        len(full) >= MIN_FULL_TOTAL
        and b_strong >= MIN_BOUNCE
        and breakout >= MIN_BREAKOUT
    )

    prices = [(r.get("l2_snapshot_at_touch") or {}).get("retest_price", 0) for r in no_tag]
    synth = [p for p in prices if isinstance(p, (int, float)) and 50000 < p < 70000]
    real = [p for p in prices if isinstance(p, (int, float)) and p > 70000]

    print(f"Dataset total: {len(rows)}")
    print(f"FULL total: {len(full)}")
    print(f"FULL outcomes: {dict(outcomes_full)}")
    print(f"Set A criteria: BOUNCE_STRONG>={MIN_BOUNCE}, BREAKOUT>={MIN_BREAKOUT}, FULL>={MIN_FULL_TOTAL}")
    print(f"Set A ready: {ready}")
    print("-")
    print(f"Without quality tag (nested l2_temporal_profile): {len(no_tag)}")
    print(f"  Price range 50k-70k (possible Synth-Bridge): {len(synth)}")
    print(f"  Price >70k (possible real): {len(real)}")


if __name__ == "__main__":
    main()
