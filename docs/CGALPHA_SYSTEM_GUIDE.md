# CGAlpha System Guide

## Purpose

CGAlpha is an autonomous code-and-analysis platform with two practical pillars:
- **Builder**: changes and validates code (`Code Craft Sage`, phases 1-6).
- **Observer**: analyzes outcomes and proposes direction (`Ghost Architect`, phase 7+).

The current operating model is incremental hardening:
- Keep core stable.
- Add capabilities without rewriting the nucleus.
- Gate every risky decision with tests and quality checks.

Canonical reading order for full detail:
1. `docs/CGALPHA_MASTER_DOCUMENTATION.md`
2. `docs/CONSTITUTION_RELEVANT_COMPANION.md`
3. `UNIFIED_CONSTITUTION_v0.0.3.md`

## Mental Model (Simple)

- **Body**: executable components (CLI, orchestrators, modules, tests).
- **Brain**: analysis and strategy (Ghost Architect, causal insights).
- **Memory**: operational/evolutionary logs and historical context.

If body works but brain is weak -> system executes but learns poorly.
If brain is strong but body is unstable -> system plans but breaks in production.
Goal is balance.

## High-Level Architecture

### 1) CLI Layer (`aiphalab`)

Entry point for daily operations:
- status, cycle, config, history, debug
- codecraft
- auto-analyze
- local LLM interaction (`ask`, `ask-requirements`, `ask-setup`)
- docs navigation (`docs`)

### 2) Execution/Control Layer

- `cgalpha/orchestrator.py`
- `cgalpha/codecraft/orchestrator.py`

Responsibilities:
- Pipeline execution and rollback behavior.
- Coordination between generation, modification, testing, and reporting.

### 3) Analysis Layer (Ghost Architect)

- `cgalpha/ghost_architect/simple_causal_analyzer.py`

Responsibilities:
- Parse historical logs.
- Build snapshots.
- Infer causal hypotheses (with fallback behavior).
- Emit actionable insights with confidence gates.

### 4) Task/Resilience Layer (Nexus + buffers)

- `cgalpha/nexus/task_buffer.py`
- Redis/SQLite fallback patterns for continuity.

Responsibilities:
- Queue handling under partial failure.
- Concurrency safety.
- Minimal service continuity when infra fails.

### 5) Memory Layer

- `aipha_memory/operational/`
- `aipha_memory/evolutionary/`

Responsibilities:
- Operational traceability.
- Evolutionary change log and bridge records.

## Current State Summary

What is solid:
- CLI workflow is functional.
- Local LLM integration exists and is usable.
- Dual-role assistance is available:
  - Mentor mode for orientation.
  - Requirements mode for structured specs.
- Deep causal baseline exists and can process enriched contexts.

What is still the bottleneck:
- Data quality and coverage (especially microstructure depth alignment).
- Real-time depth data continuity.
- Avoiding overconfidence when coverage is low.

## Daily Operator Workflow

1. Validate health.
2. Run targeted tests.
3. Run analysis.
4. Check decision gate.
5. Only then approve execution path.

Minimal command sequence:

```bash
cgalpha ask-health --smoke
python -m pytest -q tests/test_ghost_architect_phase7.py
cgalpha auto-analyze --working-dir .
```

## Decision Gates (Practical)

Typical gates to review:
- `blind_test_ratio`
- order book coverage
- confidence and causal quality flags

Interpretation:
- High blind ratio + low coverage => hold and improve data quality first.
- Repeated pass with stable gates => progress to next phase safely.

## How to Use This Guide with Existing Documents

Use this file as the map, then open details:
- Constitution for non-negotiable constraints.
- Phase docs for implementation intent.
- Audit docs for risk and hardening decisions.

This prevents random navigation across many historical reports.

## Non-Negotiables for Stability

- No massive refactor without explicit approval.
- No synthetic data presented as real market truth.
- No unvalidated writes outside project scope.
- No phase advancement without repeated gate success.

## Next Documentation Targets

- Add a short runbook per role:
  - operator
  - reviewer
  - maintainer
- Add glossary for repeated terms:
  - fakeout
  - trend break
  - blind test
  - gate pass/fail
