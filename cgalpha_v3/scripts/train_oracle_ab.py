#!/usr/bin/env python3
"""Train Oracle v5 A/B models from the recovered operational dataset.

Set A is the pure FULL-L2 challenger. It includes every FULL row so the
Oracle quality gate sees the true L2 sample volume; OracleTrainer_v3 then
filters to BOUNCE_STRONG/BREAKOUT internally for classification.

Set B is the hybrid bridge baseline: valid legacy/synth rows with neutralized
L2 values plus valid FULL-L2 rows.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from cgalpha_v3.lila.llm.oracle import OracleTrainer_v3

DATASET = PROJECT_ROOT / "aipha_memory" / "operational" / "training_dataset_v2.jsonl"
PREPARED_DIR = PROJECT_ROOT / "aipha_memory" / "operational" / "prepared_sets"
REPORT_DIR = PROJECT_ROOT / "aipha_memory" / "reports"
MODEL_DIR = PROJECT_ROOT / "aipha_memory" / "data" / "models"

SET_A_PATH = PREPARED_DIR / "set_a_full_l2_all_outcomes.jsonl"
SET_B_PATH = PREPARED_DIR / "set_b_hybrid_bridge_trainable.jsonl"
REPORT_PATH = REPORT_DIR / "oracle_v5_ab_training_20260601.json"
SET_A_MODEL = MODEL_DIR / "oracle_v5_set_a_challenger.joblib"
SET_B_MODEL = MODEL_DIR / "oracle_v5_set_b_champion_candidate.joblib"

VALID_OUTCOMES = {"BOUNCE_STRONG", "BREAKOUT"}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"{path}:{lineno}: invalid JSONL row: {exc}") from exc
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, separators=(",", ":"), ensure_ascii=False) + "\n")


def _sample_id(row: dict[str, Any]) -> str:
    meta = row.get("_meta") if isinstance(row.get("_meta"), dict) else {}
    return str(meta.get("sample_id") or row.get("sample_id") or row.get("id") or "")


def _outcome(row: dict[str, Any]) -> str:
    outcome = row.get("outcome")
    if isinstance(outcome, dict):
        return str(outcome.get("label") or "?")
    return str(outcome or "?")


def _quality(row: dict[str, Any]) -> str:
    profile = row.get("l2_temporal_profile")
    if isinstance(profile, dict):
        return str(profile.get("l2_data_quality") or "?")
    return "?"


def _is_valid(row: dict[str, Any]) -> bool:
    return _outcome(row) in VALID_OUTCOMES


def _clone_with_neutral_l2(row: dict[str, Any]) -> dict[str, Any]:
    cloned = json.loads(json.dumps(row))
    l2 = cloned.setdefault("l2_snapshot_at_touch", {})
    for key in [
        "obi_1",
        "obi_5",
        "obi_10",
        "obi_20",
        "cumulative_delta",
        "best_bid_size_btc",
        "best_ask_size_btc",
        "bid_wall_depth_10_btc",
        "ask_wall_depth_10_btc",
        "spread_bps",
        "vwap_session",
    ]:
        if key in l2:
            l2[key] = 0.0
    profile = cloned.setdefault("l2_temporal_profile", {})
    profile["l2_data_quality"] = "LEGACY_NAN_BRIDGE"
    return cloned


def _is_legacy_synth_bridge(row: dict[str, Any]) -> bool:
    quality = _quality(row)
    price = (row.get("l2_snapshot_at_touch") or {}).get("retest_price", 0)
    return (
        quality in {"?", "MISSING", ""}
        and isinstance(price, (int, float))
        and 50000 < price < 70000
    )


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    trainable = [row for row in rows if _is_valid(row)]
    full = [row for row in rows if _quality(row) == "FULL"]
    ids = [_sample_id(row) for row in rows]
    return {
        "rows": len(rows),
        "unique_ids": len(set(ids)),
        "duplicate_ids": len(rows) - len(set(ids)),
        "outcomes": dict(Counter(_outcome(row) for row in rows)),
        "qualities": dict(Counter(_quality(row) for row in rows)),
        "trainable_rows": len(trainable),
        "trainable_outcomes": dict(Counter(_outcome(row) for row in trainable)),
        "full_rows": len(full),
        "full_outcomes": dict(Counter(_outcome(row) for row in full)),
    }


def _assert_unique_sample_ids(rows: list[dict[str, Any]], label: str) -> None:
    ids = [_sample_id(row) for row in rows]
    missing = [idx for idx, sid in enumerate(ids) if not sid]
    if missing:
        raise RuntimeError(f"{label}: rows without sample_id at positions {missing[:5]}")
    duplicates = [sid for sid, count in Counter(ids).items() if count > 1]
    if duplicates:
        raise RuntimeError(f"{label}: duplicate sample_id values: {duplicates[:10]}")


def _prepare_sets(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    set_a = [row for row in rows if _quality(row) == "FULL"]

    set_b: list[dict[str, Any]] = []
    for row in rows:
        if not _is_valid(row):
            continue
        if _is_legacy_synth_bridge(row):
            set_b.append(_clone_with_neutral_l2(row))
        elif _quality(row) == "FULL":
            set_b.append(row)

    _assert_unique_sample_ids(set_a, "Set A")
    _assert_unique_sample_ids(set_b, "Set B")
    return set_a, set_b


def _train_profile(name: str, rows: list[dict[str, Any]], model_path: Path) -> dict[str, Any]:
    oracle = OracleTrainer_v3.create_default()
    oracle.load_training_dataset(rows)
    result = oracle.train_model()
    metrics = oracle.get_training_metrics()

    profile_report = {
        "name": name,
        "model_path": str(model_path),
        "input_summary": _summarize(rows),
        "train_result": result,
        "metrics": metrics,
        "saved": False,
    }
    if not metrics or metrics.get("quality_gate") == "FAILED":
        profile_report["failure"] = metrics
        return profile_report

    model_path.parent.mkdir(parents=True, exist_ok=True)
    oracle.save_to_disk(str(model_path))
    profile_report["saved"] = True
    return profile_report


def _promotion_decision(set_a: dict[str, Any], set_b: dict[str, Any]) -> dict[str, Any]:
    a_metrics = set_a.get("metrics") or {}
    b_metrics = set_b.get("metrics") or {}
    if not set_a.get("saved") or not set_b.get("saved"):
        return {
            "decision": "no_promotion",
            "reason": "one_or_more_profiles_failed_training",
            "champion": "set_b_hybrid_bridge",
            "challenger": "set_a_full_l2",
        }

    a_brier = float(a_metrics["brier_score"])
    b_brier = float(b_metrics["brier_score"])
    a_test = float(a_metrics["test_accuracy"])
    a_train = float(a_metrics["train_accuracy"])
    a_gap = round(a_train - a_test, 4)

    promote = a_brier <= b_brier and a_test >= 0.52 and a_gap <= 0.20
    return {
        "decision": "promote_set_a" if promote else "keep_set_b_champion",
        "champion": "set_a_full_l2" if promote else "set_b_hybrid_bridge",
        "challenger": "set_b_hybrid_bridge" if promote else "set_a_full_l2",
        "criteria": {
            "set_a_brier_lte_set_b": a_brier <= b_brier,
            "set_a_oos_accuracy_gte_52_pct": a_test >= 0.52,
            "set_a_train_oos_gap_lte_20_pct": a_gap <= 0.20,
        },
        "set_a_train_oos_gap": a_gap,
        "note": "oracle_v5.joblib was not overwritten by this runner",
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DATASET)
    parser.add_argument("--report-path", type=Path, default=REPORT_PATH)
    args = parser.parse_args()

    if not args.dataset.exists():
        raise FileNotFoundError(args.dataset)

    rows = _load_jsonl(args.dataset)
    _assert_unique_sample_ids(rows, "source dataset")
    set_a, set_b = _prepare_sets(rows)
    _write_jsonl(SET_A_PATH, set_a)
    _write_jsonl(SET_B_PATH, set_b)

    set_a_report = _train_profile("set_a_full_l2_challenger", set_a, SET_A_MODEL)
    set_b_report = _train_profile("set_b_hybrid_bridge_champion_candidate", set_b, SET_B_MODEL)

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_path": str(args.dataset),
        "dataset_sha256": _sha256(args.dataset),
        "prepared_sets": {
            "set_a_path": str(SET_A_PATH),
            "set_b_path": str(SET_B_PATH),
        },
        "source_summary": _summarize(rows),
        "set_a": set_a_report,
        "set_b": set_b_report,
        "promotion_decision": _promotion_decision(set_a_report, set_b_report),
    }

    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    args.report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
