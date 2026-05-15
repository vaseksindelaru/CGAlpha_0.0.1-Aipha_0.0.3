#!/usr/bin/env python3
"""
Auditoría de captura de retests:
- Capturados: sample_id presentes en training_dataset_v2.jsonl
- Pendientes: sample_id presentes en pending_labels.json
- Integridad forense: snapshot/raw_buffer por sample_id
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Set


def _load_pending(path: Path) -> List[dict]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _load_training_ids(path: Path) -> Set[str]:
    ids: Set[str] = set()
    if not path.exists():
        return ids
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        sid = ((obj.get("_meta") or {}).get("sample_id") or "").strip()
        if sid:
            ids.add(sid)
    return ids


def _fmt_bool(v: bool) -> str:
    return "yes" if v else "no"


def _parse_utc_ts_ms_from_sample_id(sample_id: str) -> int | None:
    # Esperado: re_YYYYMMDD_HHMMSS_...
    parts = sample_id.split("_")
    if len(parts) < 3:
        return None
    ds, ts = parts[1], parts[2]
    if len(ds) != 8 or len(ts) != 6 or not (ds + ts).isdigit():
        return None
    try:
        dt = datetime.strptime(ds + ts, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    except ValueError:
        return None


def _load_training_rows(path: Path) -> List[dict]:
    rows: List[dict] = []
    if not path.exists():
        return rows
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=20, help="Objetivo de retests capturados")
    parser.add_argument("--root", type=str, default=".", help="Raíz del repo")
    parser.add_argument("--show", type=int, default=50, help="Máx. filas de detalle")
    parser.add_argument(
        "--since",
        type=str,
        default="",
        help="Filtra desde fecha UTC ISO8601 (ej: 2026-05-15T00:00:00Z)",
    )
    parser.add_argument(
        "--last-hours",
        type=float,
        default=0.0,
        help="Filtra por últimas N horas (UTC). Prioridad sobre --since.",
    )
    parser.add_argument(
        "--recent-only",
        action="store_true",
        help="Excluye sample_id sin timestamp parseable (histórico legacy).",
    )
    parser.add_argument(
        "--semaforo",
        action="store_true",
        help="Activa salida con código para automatización/cron.",
    )
    parser.add_argument(
        "--require-raw",
        action="store_true",
        help="En modo semáforo, falla si falta raw_buffer en cualquier sample filtrado.",
    )
    parser.add_argument(
        "--allow-pending",
        action="store_true",
        help="En modo semáforo, no falla por pendientes.",
    )
    args = parser.parse_args()

    repo = Path(args.root).resolve()
    op = repo / "aipha_memory" / "operational"
    snapshots_dir = repo / "aipha_memory" / "snapshots"
    raw_dir = repo / "aipha_memory" / "raw_buffers"

    pending_path = op / "pending_labels.json"
    train_path = op / "training_dataset_v2.jsonl"

    pending = _load_pending(pending_path)
    train_rows = _load_training_rows(train_path)

    since_dt: datetime | None = None
    if args.last_hours and args.last_hours > 0:
        since_dt = datetime.now(timezone.utc) - timedelta(hours=args.last_hours)
    elif args.since:
        s = args.since.strip().replace("Z", "+00:00")
        since_dt = datetime.fromisoformat(s)
        if since_dt.tzinfo is None:
            since_dt = since_dt.replace(tzinfo=timezone.utc)
        else:
            since_dt = since_dt.astimezone(timezone.utc)
    since_ms = int(since_dt.timestamp() * 1000) if since_dt else None

    pending_ids: Set[str] = set()
    for x in pending:
        sid = str(x.get("sample_id", "")).strip()
        if not sid:
            continue
        sid_ts = _parse_utc_ts_ms_from_sample_id(sid)
        if args.recent_only and sid_ts is None:
            continue
        if since_ms is not None and sid_ts is not None and sid_ts < since_ms:
            continue
        if since_ms is not None and sid_ts is None and args.recent_only:
            continue
        pending_ids.add(sid)

    train_ids: Set[str] = set()
    for obj in train_rows:
        sid = ((obj.get("_meta") or {}).get("sample_id") or "").strip()
        if not sid:
            continue
        sid_ts = _parse_utc_ts_ms_from_sample_id(sid)
        if args.recent_only and sid_ts is None:
            continue
        if since_ms is not None and sid_ts is not None and sid_ts < since_ms:
            continue
        if since_ms is not None and sid_ts is None and args.recent_only:
            continue
        train_ids.add(sid)

    all_ids = sorted(train_ids | pending_ids)
    rows: List[Dict[str, str]] = []

    for sid in all_ids:
        in_train = sid in train_ids
        in_pending = sid in pending_ids
        snapshot_ok = (snapshots_dir / f"{sid}.json").exists()
        raw_ok = (raw_dir / f"{sid}.json.gz").exists()
        if in_train:
            status = "captured"
        elif in_pending:
            status = "pending"
        else:
            status = "orphan"
        rows.append(
            {
                "sample_id": sid,
                "status": status,
                "in_train": _fmt_bool(in_train),
                "in_pending": _fmt_bool(in_pending),
                "snapshot": _fmt_bool(snapshot_ok),
                "raw": _fmt_bool(raw_ok),
            }
        )

    captured = len(train_ids)
    missing_to_target = max(0, args.target - captured)
    pending_only = sorted(pending_ids - train_ids)
    missing_snapshot = [r["sample_id"] for r in rows if r["snapshot"] == "no"]
    missing_raw = [r["sample_id"] for r in rows if r["raw"] == "no"]

    print("=== RETEST AUDIT ===")
    print(f"repo_root={repo}")
    print(f"filter_since_utc={since_dt.isoformat() if since_dt else 'none'}")
    print(f"recent_only={args.recent_only}")
    print(f"captured={captured}")
    print(f"pending={len(pending_ids)}")
    print(f"union={len(all_ids)}")
    print(f"target={args.target}")
    print(f"missing_to_target={missing_to_target}")
    print(f"pending_only={len(pending_only)}")
    print(f"missing_snapshot={len(missing_snapshot)}")
    print(f"missing_raw={len(missing_raw)}")

    print("\n--- DETAIL ---")
    print("status | in_train | in_pending | snapshot | raw | sample_id")
    for r in rows[: args.show]:
        print(
            f"{r['status']:8} | {r['in_train']:8} | {r['in_pending']:10} | "
            f"{r['snapshot']:8} | {r['raw']:3} | {r['sample_id']}"
        )

    if pending_only:
        print("\n--- PENDING ONLY IDS ---")
        for sid in pending_only:
            print(sid)

    # Semáforo para cron/CI local:
    # 0 = verde (objetivo cumplido y sin fallas requeridas)
    # 1 = amarillo/rojo suave (aún faltan capturas o hay pendientes)
    # 2 = rojo fuerte (integridad forense incumplida si se exige raw)
    if args.semaforo:
        if args.require_raw and missing_raw:
            sys.exit(2)
        if missing_to_target > 0:
            sys.exit(1)
        if (not args.allow_pending) and pending_only:
            sys.exit(1)
        sys.exit(0)


if __name__ == "__main__":
    main()
