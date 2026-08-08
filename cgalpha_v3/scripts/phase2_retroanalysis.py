"""
CGAlpha v3 — FASE 2: Retroanálisis + Mejora Emergente
======================================================

Objetivos:
1. Analizar estructura de datos generados en Fase 1.
2. Identificar features más discriminantes para BOUNCE vs BREAKOUT.
3. Emitir propuesta de mejora con soporte teórico y contradicciones.
4. Decidir promoción nivel 4 (ADN) según Sharpe > 1.5.
5. Si no cumple, producir conclusión crítica + siguiente paso emergente.
"""

from __future__ import annotations

import csv
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.feature_selection import f_classif, mutual_info_classif
from sklearn.preprocessing import LabelEncoder

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from cgalpha_v3.infrastructure.signal_detector.triple_coincidence import TripleCoincidenceDetector
from cgalpha_v3.scripts.phase0_harvest import generate_micro_features, generate_realistic_ohlcv

FEATURES = [
    "vwap_at_retest",
    "obi_10_at_retest",
    "cumulative_delta_at_retest",
    "delta_divergence",
    "atr_14",
    "regime",
    "direction",
]

NUMERIC_FEATURES = [
    "vwap_at_retest",
    "obi_10_at_retest",
    "cumulative_delta_at_retest",
    "atr_14",
]

CATEGORICAL_FEATURES = [
    "delta_divergence",
    "regime",
    "direction",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _flatten_training_samples(samples: list[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sample in samples:
        features = dict(getattr(sample, "features", {}) or {})
        outcome = getattr(sample, "outcome", None)
        if outcome not in ("BOUNCE", "BREAKOUT"):
            continue

        row = {
            "outcome": outcome,
            "zone_id": getattr(sample, "zone_id", "unknown"),
            "retest_timestamp": getattr(sample, "retest_timestamp", None),
        }
        for feat in FEATURES:
            row[feat] = features.get(feat)
        rows.append(row)
    return rows


def _build_phase2_dataset() -> pd.DataFrame:
    df = generate_realistic_ohlcv(n_candles=2000, seed=42)
    micro_df = generate_micro_features(df, seed=42)
    detector = TripleCoincidenceDetector()
    detector.process_stream(df, micro_df)

    rows = _flatten_training_samples(detector.get_training_dataset())
    out = pd.DataFrame(rows)
    return out


def _analyze_structure(df: pd.DataFrame) -> dict[str, Any]:
    class_dist = df["outcome"].value_counts().to_dict()
    missing = {col: int(df[col].isna().sum()) for col in FEATURES}
    duplicates = int(df.duplicated(subset=["zone_id", "retest_timestamp"]).sum())

    numeric_summary = {}
    for col in NUMERIC_FEATURES:
        s = pd.to_numeric(df[col], errors="coerce")
        numeric_summary[col] = {
            "mean": round(float(s.mean()), 6),
            "std": round(float(s.std(ddof=0)), 6),
            "min": round(float(s.min()), 6),
            "max": round(float(s.max()), 6),
        }

    categorical_cardinality = {
        col: int(df[col].astype(str).nunique()) for col in CATEGORICAL_FEATURES
    }

    return {
        "n_samples": int(len(df)),
        "class_distribution": class_dist,
        "missing_by_feature": missing,
        "duplicate_zone_timestamp_rows": duplicates,
        "numeric_summary": numeric_summary,
        "categorical_cardinality": categorical_cardinality,
    }


def _encode_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, dict[str, list[str]]]:
    work = df.copy()
    label_maps: dict[str, list[str]] = {}

    for col in CATEGORICAL_FEATURES:
        enc = LabelEncoder()
        values = work[col].fillna("UNKNOWN").astype(str)
        work[col] = enc.fit_transform(values)
        label_maps[col] = list(enc.classes_)

    for col in NUMERIC_FEATURES:
        work[col] = pd.to_numeric(work[col], errors="coerce").fillna(0.0)

    X = work[FEATURES].fillna(0.0)
    y = work["outcome"].map({"BOUNCE": 1, "BREAKOUT": 0}).astype(int)
    return X, y, label_maps


def _effect_size(mean_a: float, mean_b: float, std_a: float, std_b: float) -> float:
    pooled = ((std_a ** 2) + (std_b ** 2)) / 2.0
    if pooled <= 0:
        return 0.0
    return float((mean_a - mean_b) / np.sqrt(pooled))


def _analyze_discrimination(df: pd.DataFrame) -> dict[str, Any]:
    X, y, label_maps = _encode_features(df)

    mi = mutual_info_classif(X, y, random_state=42)
    f_scores, p_values = f_classif(X, y)

    rankings: list[dict[str, Any]] = []
    for idx, feat in enumerate(FEATURES):
        rankings.append(
            {
                "feature": feat,
                "mutual_information": round(float(mi[idx]), 6),
                "f_score": round(float(f_scores[idx]), 6),
                "p_value": round(float(p_values[idx]), 8),
            }
        )

    # Effect sizes for numeric features
    bounce = df[df["outcome"] == "BOUNCE"]
    breakout = df[df["outcome"] == "BREAKOUT"]
    effects: list[dict[str, Any]] = []
    for feat in NUMERIC_FEATURES:
        a = pd.to_numeric(bounce[feat], errors="coerce").dropna()
        b = pd.to_numeric(breakout[feat], errors="coerce").dropna()

        if len(a) == 0 or len(b) == 0:
            eff = 0.0
            a_mean = 0.0
            b_mean = 0.0
            a_std = 0.0
            b_std = 0.0
        else:
            a_mean = float(a.mean())
            b_mean = float(b.mean())
            a_std = float(a.std(ddof=0))
            b_std = float(b.std(ddof=0))
            eff = _effect_size(a_mean, b_mean, a_std, b_std)

        effects.append(
            {
                "feature": feat,
                "bounce_mean": round(a_mean, 6),
                "breakout_mean": round(b_mean, 6),
                "effect_size": round(float(eff), 6),
            }
        )

    rankings_sorted = sorted(rankings, key=lambda x: x["mutual_information"], reverse=True)
    effects_sorted = sorted(effects, key=lambda x: abs(x["effect_size"]), reverse=True)

    return {
        "ranking_by_mutual_information": rankings_sorted,
        "numeric_effect_sizes": effects_sorted,
        "label_maps": label_maps,
    }


def _phase3_readiness() -> dict[str, Any]:
    ws_hits = []
    for path in (PROJECT_ROOT / "cgalpha_v3").rglob("*.py"):
        if path.name == "phase2_retroanalysis.py":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "websocket" in text.lower() or "ws://" in text.lower() or "wss://" in text.lower():
            ws_hits.append(str(path.relative_to(PROJECT_ROOT)))

    has_shadow = (PROJECT_ROOT / "cgalpha_v3" / "trading" / "shadow_trader.py").exists()
    has_nexus = (PROJECT_ROOT / "cgalpha_v3" / "lila" / "nexus" / "gate.py").exists()

    return {
        "websocket_binance_detected": len(ws_hits) > 0,
        "websocket_references": ws_hits[:20],
        "shadow_trader_module_present": has_shadow,
        "nexus_gate_module_present": has_nexus,
    }


def run_phase2() -> dict[str, Any]:
    phase1_dir = PROJECT_ROOT / "cgalpha_v3" / "data" / "phase1_results"
    phase2_dir = PROJECT_ROOT / "cgalpha_v3" / "data" / "phase2_results"
    phase2_dir.mkdir(parents=True, exist_ok=True)

    phase1_summary = json.loads((phase1_dir / "phase1_summary.json").read_text(encoding="utf-8"))
    walk_forward = json.loads((phase1_dir / "walk_forward_results.json").read_text(encoding="utf-8"))

    df = _build_phase2_dataset()
    structure = _analyze_structure(df)
    discrimination = _analyze_discrimination(df)

    sharpe = float(walk_forward["aggregated"]["sharpe_neto_avg"])
    promote_level4 = sharpe > 1.5

    top_mi = discrimination["ranking_by_mutual_information"][:3]
    weakest_mi = discrimination["ranking_by_mutual_information"][-3:]

    improvement_proposal = {
        "title": "P2-Proposal: CodeCraft-Sage-guided feature refactor + robust OOS gates",
        "technical_specs": [
            {
                "change_type": "feature",
                "target": "cgalpha_v3/lila/llm/oracle.py",
                "action": "Add engineered features: vwap_distance_bps, delta_over_atr, abs_obi",
                "reason": "Current MI concentration suggests signal compression in ATR/VWAP/delta interactions.",
            },
            {
                "change_type": "validation",
                "target": "cgalpha_v3/scripts/phase1_oracle_training.py",
                "action": "Enforce min OOS events per window and fallback adaptive windowing",
                "reason": "Two WF windows had very low OOS event count; reduce optimistic bias.",
            },
            {
                "change_type": "architecture",
                "target": "cgalpha_v3/lila/codecraft_sage.py",
                "action": "Introduce CodeCraft Sage pipeline: parse->modify->test barrier->git commit",
                "reason": "AutoProposer currently produces specs but lacks automatic execution channel.",
            },
        ],
        "theoretical_support": [
            {
                "source": "Advances in Financial Machine Learning (2018)",
                "supports": "Meta-labeling secondary filter architecture for execution gating.",
            },
            {
                "source": "VWAP benchmark literature (Journal of Finance)",
                "supports": "VWAP-relative context as robust execution signal under institutional flow.",
            },
            {
                "source": "Probability of Backtest Overfitting (2014)",
                "contradicts_or_warns": "High in-sample/OOS metrics can still be inflated with low-event windows.",
            },
        ],
    }

    if promote_level4:
        phase2_decision = {
            "promote_to_level4": True,
            "reason": f"Sharpe neto avg={sharpe:.4f} > 1.5",
            "action": "Promote validated playbook to strategy DNA level 4",
        }
    else:
        phase2_decision = {
            "promote_to_level4": False,
            "reason": f"Sharpe neto avg={sharpe:.4f} <= 1.5",
            "critical_conclusion": (
                "Fase 1 es positiva pero insuficiente para ADN nivel 4. "
                "Existe riesgo de sobreajuste por bajo recuento de eventos OOS en ventanas 1 y 3."
            ),
            "next_emergent_step": (
                "Implementar CodeCraft Sage (parse->modify->tests->git), ampliar OOS "
                "a ventanas con mínimo 25 retests y activar Fase 3 live-data scaffolding."
            ),
        }

    readiness = _phase3_readiness()

    result = {
        "phase": "2 — Retroanalysis + Emergent Improvement",
        "generated_at": _now_iso(),
        "phase1_reference": {
            "summary_path": str(phase1_dir / "phase1_summary.json"),
            "walk_forward_path": str(phase1_dir / "walk_forward_results.json"),
            "phase1_training_samples": int(phase1_summary["detection"]["training_samples"]),
            "phase1_retests": int(phase1_summary["detection"]["retest_events"]),
        },
        "dataset_structure": structure,
        "feature_discrimination": discrimination,
        "improvement_proposal": improvement_proposal,
        "phase2_decision": phase2_decision,
        "phase3_readiness": readiness,
    }

    # Outputs
    (phase2_dir / "phase2_retroanalysis.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    with (phase2_dir / "feature_discrimination.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["feature", "mutual_information", "f_score", "p_value"],
        )
        writer.writeheader()
        for row in discrimination["ranking_by_mutual_information"]:
            writer.writerow(row)

    md = [
        "# Fase 2 — Retroanálisis + Mejora Emergente",
        "",
        f"- Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"- Sharpe neto Fase 1: {sharpe:.4f}",
        "",
        "## Features más discriminantes (MI)",
    ]
    for row in top_mi:
        md.append(f"- {row['feature']}: MI={row['mutual_information']:.6f}, F={row['f_score']:.4f}")

    md.append("")
    md.append("## Features más débiles (MI)")
    for row in weakest_mi:
        md.append(f"- {row['feature']}: MI={row['mutual_information']:.6f}")

    md.extend(
        [
            "",
            "## Decisión",
            f"- promote_to_level4: {phase2_decision['promote_to_level4']}",
            f"- razón: {phase2_decision['reason']}",
        ]
    )

    if not phase2_decision["promote_to_level4"]:
        md.append(f"- conclusión crítica: {phase2_decision['critical_conclusion']}")
        md.append(f"- siguiente paso emergente: {phase2_decision['next_emergent_step']}")

    md.extend(
        [
            "",
            "## Propuesta clave",
            "- Implementar `CodeCraft Sage` operativo para ejecutar `TechnicalSpec` aprobadas con barrera de tests y commit versionado.",
            "",
            "## Readiness Fase 3",
            f"- WebSocket Binance detectado: {readiness['websocket_binance_detected']}",
            f"- ShadowTrader presente: {readiness['shadow_trader_module_present']}",
            f"- NexusGate presente: {readiness['nexus_gate_module_present']}",
        ]
    )

    (phase2_dir / "phase2_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    iteration_root = PROJECT_ROOT / "cgalpha_v3" / "memory" / "iterations"
    iteration_root.mkdir(parents=True, exist_ok=True)
    iteration_dir = iteration_root / datetime.now().strftime("%Y-%m-%d_%H-%M_phase2")
    if iteration_dir.exists():
        suffix = 1
        while True:
            candidate = iteration_root / f"{iteration_dir.name}_{suffix:02d}"
            if not candidate.exists():
                iteration_dir = candidate
                break
            suffix += 1
    iteration_dir.mkdir(parents=True, exist_ok=True)

    iteration_status = {
        "phase": "2",
        "task": "Retroanalysis + Emergent Improvement",
        "status": "completed",
        "timestamp": _now_iso(),
        "sharpe_neto_avg": round(sharpe, 4),
        "promote_to_level4": promote_level4,
        "top_feature_by_mi": top_mi[0]["feature"] if top_mi else None,
        "artifacts": {
            "phase2_retroanalysis": str(phase2_dir / "phase2_retroanalysis.json"),
            "phase2_summary": str(phase2_dir / "phase2_summary.md"),
            "feature_discrimination_csv": str(phase2_dir / "feature_discrimination.csv"),
        },
    }
    (iteration_dir / "iteration_status.json").write_text(
        json.dumps(iteration_status, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (iteration_dir / "iteration_summary.md").write_text(
        (phase2_dir / "phase2_summary.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    return result


if __name__ == "__main__":
    out = run_phase2()
    print("FASE 2 completada")
    print("Sharpe fase1:", out["phase2_decision"]["reason"])
