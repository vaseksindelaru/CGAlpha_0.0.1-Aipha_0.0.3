#!/usr/bin/env python3
"""Migrate canonical Codex entries from legacy schema to v4 contract.

- Preserves historical substance (statement/rationale).
- Writes atomic backups before mutation.
- Emits machine-readable report for retroanalysis.
"""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODEX_DIR = PROJECT_ROOT / "cgalpha_v3" / "memory" / "codex"
MEMORY_ENTRIES_DIR = PROJECT_ROOT / "cgalpha_v3" / "memory" / "memory_entries"
REPORT_DIR = PROJECT_ROOT / "aipha_memory" / "reports"
BACKUP_ROOT = PROJECT_ROOT / "aipha_memory" / "reports" / "codex_migration_backups"

TARGET_SCHEMA = "4.0.0"
CANONICAL_IDS = ["D-001", "D-008", "B-002", "L-003"]

DEFAULT_INJECT = {
    "D-001": ["feature_proposal", "oracle_modification", "memory_governance"],
    "D-008": ["signal_detector", "live_pipeline"],
    "B-002": ["model_training", "server_setup"],
    "L-003": ["optimizer", "backtest_config", "feature_proposal"],
}

TYPE_TO_SUBDIR = {
    "DECISION": "decisions",
    "BUG": "bugs",
    "LESSON": "lessons",
    "FEATURE": "features",
    "RULE": "rules",
    "PATTERN": "patterns",
}


@dataclass
class MigrationItem:
    codex_id: str
    source_path: str
    destination_path: str
    changed: bool
    notes: str



def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())



def _save_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(path)



def _normalize_v4(entry: dict[str, Any], codex_id: str) -> tuple[dict[str, Any], bool, list[str]]:
    before = deepcopy(entry)
    notes: list[str] = []

    entry["codex_id"] = codex_id
    entry["schema_version"] = TARGET_SCHEMA

    # normalize required strings
    entry["type"] = str(entry.get("type", "DECISION")).upper()
    entry["status"] = str(entry.get("status", "ACTIVE")).upper()
    entry["statement"] = str(entry.get("statement", "")).strip()
    entry["rationale"] = str(entry.get("rationale", "")).strip()

    if not entry["rationale"]:
        entry["rationale"] = "Legacy migration: rationale preserved from available context."
        notes.append("Filled missing rationale")

    inject = entry.get("harness_inject_when")
    if not isinstance(inject, list) or not inject or not all(isinstance(x, str) and x.strip() for x in inject):
        entry["harness_inject_when"] = DEFAULT_INJECT.get(codex_id, ["memory_governance"])
        notes.append("Normalized harness_inject_when")

    # normalize optional governance fields to keep stable v4 shape
    entry.setdefault("supersedes", None)
    entry.setdefault("superseded_by", None)
    entry.setdefault("related_entries", [])
    entry.setdefault("affects_files", [])
    entry.setdefault("affects_components", [])
    entry.setdefault("categories_applicable", [])
    entry.setdefault("evidence_ids", [])

    changed = entry != before
    return entry, changed, notes



def _backup_file(src: Path, backup_root: Path) -> Path:
    rel = src.relative_to(PROJECT_ROOT)
    dst = backup_root / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src.read_text())
    return dst



def _locate_codex_file(codex_id: str) -> Path | None:
    for sub in ("decisions", "bugs", "lessons", "features", "rules", "patterns", "other"):
        p = CODEX_DIR / sub / f"{codex_id}.json"
        if p.exists():
            return p
    return None



def _migrate_codex_backups(apply: bool, backup_root: Path) -> tuple[list[MigrationItem], list[str]]:
    items: list[MigrationItem] = []
    missing: list[str] = []

    for codex_id in CANONICAL_IDS:
        src = _locate_codex_file(codex_id)
        if src is None:
            missing.append(codex_id)
            continue

        data = _load_json(src)
        data, changed, notes = _normalize_v4(data, codex_id)

        entry_type = str(data.get("type", "")).upper()
        sub = TYPE_TO_SUBDIR.get(entry_type, "other")
        dst = CODEX_DIR / sub / f"{codex_id}.json"

        if apply and changed:
            _backup_file(src, backup_root)
            _save_json(dst, data)

        items.append(
            MigrationItem(
                codex_id=codex_id,
                source_path=str(src),
                destination_path=str(dst),
                changed=changed,
                notes=("; ".join(notes) if notes else "No structural changes needed"),
            )
        )

    return items, missing



def _migrate_memory_entries_named_ids(apply: bool, backup_root: Path) -> list[MigrationItem]:
    items: list[MigrationItem] = []
    # Only canonical-id named files (D-008.json, B-002.json, L-003.json)
    for codex_id in CANONICAL_IDS:
        p = MEMORY_ENTRIES_DIR / f"{codex_id}.json"
        if not p.exists():
            continue

        outer = _load_json(p)
        content = outer.get("content")
        if not isinstance(content, str):
            continue

        try:
            inner = json.loads(content)
        except json.JSONDecodeError:
            continue

        inner, changed, notes = _normalize_v4(inner, codex_id)
        if apply and changed:
            _backup_file(p, backup_root)
            outer["content"] = json.dumps(inner, ensure_ascii=False)
            _save_json(p, outer)

        items.append(
            MigrationItem(
                codex_id=codex_id,
                source_path=str(p),
                destination_path=str(p),
                changed=changed,
                notes=("; ".join(notes) if notes else "No structural changes needed"),
            )
        )

    return items



def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate canonical Codex entries to schema v4")
    parser.add_argument("--apply", action="store_true", help="Write changes (default is dry-run)")
    args = parser.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_root = BACKUP_ROOT / ts

    codex_items, missing_canonical = _migrate_codex_backups(args.apply, backup_root)
    memory_items = _migrate_memory_entries_named_ids(args.apply, backup_root)

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "apply" if args.apply else "dry_run",
        "target_schema": TARGET_SCHEMA,
        "canonical_ids": CANONICAL_IDS,
        "missing_canonical_in_codex_dir": missing_canonical,
        "codex_backup_items": [asdict(x) for x in codex_items],
        "memory_entry_items": [asdict(x) for x in memory_items],
        "backup_root": str(backup_root) if args.apply else None,
        "summary": {
            "codex_files_seen": len(codex_items),
            "memory_entry_files_seen": len(memory_items),
            "changes_planned_or_applied": sum(1 for x in [*codex_items, *memory_items] if x.changed),
        },
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    latest = REPORT_DIR / "codex_migration_latest.json"
    stamped = REPORT_DIR / f"codex_migration_{ts}.json"
    latest.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    stamped.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    print(f"Report: {stamped}")
    print(f"Latest: {latest}")
    print(json.dumps(report["summary"], indent=2))
    if missing_canonical:
        print(f"Missing canonical IDs in codex dir: {missing_canonical}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
