#!/usr/bin/env python3
"""Generate a daily harvest quality report from training_dataset_v2.jsonl."""

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATASET = PROJECT_ROOT / "aipha_memory" / "operational" / "training_dataset_v2.jsonl"
OUT_DIR = PROJECT_ROOT / "aipha_memory" / "reports"


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


def _pct(n, d):
    return round((100.0 * n / d), 2) if d else 0.0


def main():
    rows = _load_rows(DATASET)

    quality = Counter((r.get("l2_temporal_profile") or {}).get("l2_data_quality", "MISSING") for r in rows)
    outcomes = Counter((r.get("outcome") or {}).get("label", "MISSING") for r in rows)
    rtypes = Counter((r.get("l2_snapshot_at_touch") or {}).get("retest_type", "MISSING") for r in rows)

    full_rows = [r for r in rows if (r.get("l2_temporal_profile") or {}).get("l2_data_quality") == "FULL"]
    full_outcomes = Counter((r.get("outcome") or {}).get("label", "MISSING") for r in full_rows)
    full_rtypes = Counter((r.get("l2_snapshot_at_touch") or {}).get("retest_type", "MISSING") for r in full_rows)

    inconv_ratio_full = _pct(full_outcomes.get("INCONCLUSIVE", 0), len(full_rows))
    drift_flag = inconv_ratio_full > 45.0

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_path": str(DATASET),
        "dataset_total": len(rows),
        "quality_distribution": dict(quality),
        "outcome_distribution": dict(outcomes),
        "retest_type_distribution": dict(rtypes),
        "full_total": len(full_rows),
        "full_outcome_distribution": dict(full_outcomes),
        "full_retest_type_distribution": dict(full_rtypes),
        "set_a_readiness": {
            "min_bounce_strong": 8,
            "min_breakout": 16,
            "min_full_total": 24,
            "bounce_strong": full_outcomes.get("BOUNCE_STRONG", 0),
            "breakout": full_outcomes.get("BREAKOUT", 0),
            "full_total": len(full_rows),
            "ready": (
                full_outcomes.get("BOUNCE_STRONG", 0) >= 8
                and full_outcomes.get("BREAKOUT", 0) >= 16
                and len(full_rows) >= 24
            ),
        },
        "drift_watch": {
            "inconclusive_ratio_full_pct": inconv_ratio_full,
            "flag_high_inconclusive": drift_flag,
            "rule": "flag when INCONCLUSIVE in FULL > 45%",
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    latest = OUT_DIR / "harvest_report_latest.json"
    stamped = OUT_DIR / f"harvest_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    latest.write_text(json.dumps(report, indent=2))
    stamped.write_text(json.dumps(report, indent=2))

    print(f"Report written: {latest}")
    print(f"Snapshot written: {stamped}")
    print(f"Set A ready: {report['set_a_readiness']['ready']}")


if __name__ == "__main__":
    main()
