# Codex v4 Migration — Retroanalysis Record

## Scope
Migration of canonical Codex entries to Kernel v4 contract ("Leyes antes que Datos").

Target canonical IDs:
- `D-001`
- `D-008`
- `B-002`
- `L-003`

## Objective
Guarantee that foundational memory entries satisfy mandatory v4 structure required by `CodexKernel`:
- `schema_version = 4.0.0`
- required fields including `harness_inject_when`
- canonical IDs present and accessible in `cgalpha_v3/memory/codex/`

## Implementation
New script:
- `cgalpha_v3/scripts/migrate_codex_to_v4.py`

Behavior:
- dry-run and apply modes
- atomic writes
- automatic backups under `aipha_memory/reports/codex_migration_backups/<timestamp>/`
- JSON reports (`latest` + timestamped)

## Execution Timeline
1. Dry run:
- `python3 cgalpha_v3/scripts/migrate_codex_to_v4.py`
- Found: 3 codex canonical files (`B-002`, `D-008`, `L-003`)
- Missing in codex dir: `D-001`

2. Apply migration:
- `python3 cgalpha_v3/scripts/migrate_codex_to_v4.py --apply`
- Migrated canonical files to v4 schema
- Migrated named canonical `memory_entries` aliases (`D-008.json`, `B-002.json`, `L-003.json`)

3. Canonical completion step:
- Materialized missing `D-001` from existing `memory_entries` evidence into:
  - `cgalpha_v3/memory/codex/decisions/D-001.json`
  - `cgalpha_v3/memory/memory_entries/D-001.json`

4. Re-run apply for consistency check:
- `python3 cgalpha_v3/scripts/migrate_codex_to_v4.py --apply`
- Result: `changes_planned_or_applied = 0` (idempotent)

5. Validation:
- Canonical codex files all in v4 with inject context
- `pytest -q tests/test_codex_integrity.py` => `5 passed`

## Evidence Artifacts
Reports:
- `aipha_memory/reports/codex_migration_latest.json`
- `aipha_memory/reports/codex_migration_20260524_003635.json`
- `aipha_memory/reports/codex_migration_20260524_003636.json`
- `aipha_memory/reports/codex_migration_20260524_003728.json`

Backups:
- `aipha_memory/reports/codex_migration_backups/<timestamp>/...`

## Final Canonical State
- `cgalpha_v3/memory/codex/decisions/D-001.json` → `schema_version: 4.0.0`
- `cgalpha_v3/memory/codex/decisions/D-008.json` → `schema_version: 4.0.0`
- `cgalpha_v3/memory/codex/bugs/B-002.json` → `schema_version: 4.0.0`
- `cgalpha_v3/memory/codex/lessons/L-003.json` → `schema_version: 4.0.0`

## Residual Risks / Notes
- `D-001` had to be materialized from the newest matching memory entry due to missing explicit codex backup.
- Legacy non-canonical entries remain outside this migration scope by design.
- Kernel v4 validation is now aligned with canonical corpus; future writes must follow supersede flow.

## Recommended Next Step
Integrate this migration script into a CI preflight check for memory governance changes:
1. run migration in dry-run,
2. fail if canonical IDs missing or schema drift detected,
3. require approved migration report in PR artifacts.
