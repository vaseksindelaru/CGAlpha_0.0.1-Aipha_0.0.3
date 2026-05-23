#!/usr/bin/env python3
"""Prepare Set A / Set B datasets for Oracle v5 retraining readiness."""

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC = PROJECT_ROOT / "aipha_memory" / "operational" / "training_dataset_v2.jsonl"
OUT_DIR = PROJECT_ROOT / "aipha_memory" / "operational" / "prepared_sets"


def _load_rows(path: Path):
    rows = []
    if not path.exists():
        return rows
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def _is_valid_outcome(row):
    return (row.get("outcome") or {}).get("label") in {"BOUNCE_STRONG", "BREAKOUT"}


def _force_l2_nan(row):
    row = json.loads(json.dumps(row))
    l2 = row.setdefault("l2_snapshot_at_touch", {})
    # Keep geometry/context; neutralize legacy/synth L2 signal values.
    for key in [
        "obi_1", "obi_5", "obi_10", "obi_20",
        "cumulative_delta", "best_bid_size_btc", "best_ask_size_btc",
        "bid_wall_depth_10_btc", "ask_wall_depth_10_btc", "spread_bps", "vwap_session",
    ]:
        if key in l2:
            l2[key] = None
    profile = row.setdefault("l2_temporal_profile", {})
    profile["l2_data_quality"] = "LEGACY_NAN_BRIDGE"
    return row


def main():
    rows = _load_rows(SRC)

    set_a = [
        r for r in rows
        if (r.get("l2_temporal_profile") or {}).get("l2_data_quality") == "FULL"
        and _is_valid_outcome(r)
    ]

    set_b = []
    for r in rows:
        if not _is_valid_outcome(r):
            continue
        quality = (r.get("l2_temporal_profile") or {}).get("l2_data_quality")
        price = (r.get("l2_snapshot_at_touch") or {}).get("retest_price", 0)
        is_legacy_synth = (quality in (None, "MISSING", "")) and isinstance(price, (int, float)) and (50000 < price < 70000)
        if is_legacy_synth:
            set_b.append(_force_l2_nan(r))
        elif quality == "FULL":
            set_b.append(r)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    a_path = OUT_DIR / "set_a_full_only.jsonl"
    b_path = OUT_DIR / "set_b_bridge.jsonl"

    with open(a_path, "w") as f:
        for r in set_a:
            f.write(json.dumps(r) + "\n")

    with open(b_path, "w") as f:
        for r in set_b:
            f.write(json.dumps(r) + "\n")

    out_a = Counter((r.get("outcome") or {}).get("label", "?") for r in set_a)
    out_b = Counter((r.get("outcome") or {}).get("label", "?") for r in set_b)

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": str(SRC),
        "set_a_path": str(a_path),
        "set_b_path": str(b_path),
        "set_a_count": len(set_a),
        "set_a_outcomes": dict(out_a),
        "set_a_ready": (out_a.get("BOUNCE_STRONG", 0) >= 8 and out_a.get("BREAKOUT", 0) >= 16),
        "set_b_count": len(set_b),
        "set_b_outcomes": dict(out_b),
    }

    s_path = OUT_DIR / "set_prep_summary.json"
    s_path.write_text(json.dumps(summary, indent=2))

    print(f"Set A: {a_path} ({len(set_a)} rows)")
    print(f"Set B: {b_path} ({len(set_b)} rows)")
    print(f"Summary: {s_path}")
    print(f"Set A ready: {summary['set_a_ready']}")


if __name__ == "__main__":
    main()
