# CGAlpha Master Documentation

## 1. Scope and Intent

This document is the canonical orientation manual for CGAlpha at the current stage.
It consolidates relevant content from:
- `UNIFIED_CONSTITUTION_v0.0.3.md`
- Audit reports (`AUDIT_REPORT_V2.md`, `AUDIT_DEEP_CAUSAL_V03.md`)
- Operating docs (`README.md`, `SYSTEM_STATUS.md`, `00_COMIENZA_AQUI.md`)
- Phase documents under `bible/codecraft_sage/`

Policy in force:
- Existing `.md` files are preserved.
- No historical file is removed in this phase.
- This master document is the operational map to reduce navigation friction.

## 2. Executive State (Current)

### 2.1 What is currently stable

- Modular CLI (`aiphalab/cli_v2.py`) is operational.
- Local LLM assistant is integrated via CLI:
  - Mentor role.
  - Requirements Architect role.
- Ghost Architect is integrated with Deep Causal baseline.
- `cgalpha auto-analyze` remains the stable entrypoint.
- Documentation hub is now accessible from CLI (`cgalpha docs ...`).

### 2.2 What is currently constrained

- Microstructure quality/coverage is still the bottleneck for v0.3 confidence.
- High `blind_test_ratio` limits causal certainty.
- Deep Causal decisions must remain gated by data quality and OOS evidence.

## 3. Identity and System Model

From the unified constitution:
- **Aipha** is the execution body (production mechanics).
- **CGAlpha** is the experimental brain (causal strategy and autonomous improvement).

Working metaphor:
- **Body**: executes.
- **Brain**: reasons.
- **Memory**: preserves evidence and traceability.

Non-negotiable principle:
- Incremental evolution over destructive rewrites.

## 4. Core Architecture (Condensed but Complete)

### 4.1 Body: 5-layer execution architecture

1. **Layer 1: Infrastructure / Nervous System**
   - Runtime, configs, orchestration baseline, health and controls.
2. **Layer 2: Data Preprocessor**
   - Input normalization and feature preparation.
3. **Layer 3: Trading Manager**
   - Signal generation and trade lifecycle logic.
4. **Layer 4: Oracle**
   - Probabilistic filtering with validated model versions.
5. **Layer 5: Data Postprocessor**
   - Outcome analysis and bridge to causal intelligence.

### 4.2 Brain: CGAlpha labs

1. **SignalDetectionLab** (macro map of structure).
2. **ZonePhysicsLab** (micro behavior inside active zones).
3. **ExecutionOptimizerLab** (entry/exit optimization with data quality checks).
4. **RiskBarrierLab** (causal attribution; isolate decision effect vs market effect).

### 4.3 Nexus and Ops

- Nexus coordinates analysis priorities and synthesis.
- Ops supervises resources with deterministic rules:
  - Green/yellow/red modes based on system pressure and signal priority.

## 5. Memory and Evidence Model

Two critical memory zones:
- `aipha_memory/operational/`: runtime and operational logs.
- `aipha_memory/evolutionary/`: evolutionary evidence (bridge, learning trace).

Key files:
- `aipha_memory/evolutionary/bridge.jsonl`: causal/evolutionary bridge.
- `aipha_memory/operational/order_book_features.jsonl`: official microstructure source for Deep Causal.

Constraint:
- Never mix operational and evolutionary responsibilities without explicit bridge logic.

## 6. Constitution Critical Clauses (Operational Digest)

### 6.1 Triple Barrier and ordinal outcomes

The labeling logic must preserve full trajectory evidence:
- no premature truncation of signal path,
- capture MFE/MAE and ordinal outcome,
- preserve learning value for causal layers.

### 6.2 Part 9: Code Craft Sage

Purpose:
- transform approved proposals into code, tests, docs, and validated change paths.

Expected phase discipline:
1. Parser.
2. Generator / modifier.
3. Tests.
4. Documentation update.
5. Validation/quality barrier before merge.

### 6.3 Part 10: Execution Engine (paper-first, live-gated)

Live/Hybrid preconditions:
1. Microstructure source available:
   - `aipha_memory/operational/order_book_features.jsonl`
2. Recent causal report present with:
   - `data_alignment`
   - `causal_metrics`
   - `readiness_gates`
3. Required readiness:
   - `data_quality_pass = true`
   - `causal_quality_pass = true`
   - `proceed_v03 = true`

If any fail:
- block Live and Hybrid,
- allow only Paper mode.

### 6.4 Part 10.1: Deep Causal governance

Mandatory:
- mark missing valid micro-match as `BLIND_TEST`.
- prohibit high confidence when `blind_test_ratio` exceeds threshold.
- keep integration incremental (no core rewrite).

Recommended thresholds:
- `max_blind_test_ratio <= 0.25`
- `max_nearest_match_avg_lag_ms <= 150`
- `min_causal_accuracy >= 0.55`
- `min_efficiency >= 0.40`

### 6.5 Part 11: causal evaluation protocol (OOS)

Approval requires:
- out-of-sample evidence (not only in-sample fit),
- causal quality pass,
- compatibility with `cgalpha auto-analyze`,
- no massive rewrite as shortcut.

## 7. Deep Causal Evolution: v0.2.x to v0.3

### 7.1 Current baseline

Already present in code and flow:
- snapshot enrichment with external micro features,
- exact trade_id match + nearest timestamp fallback,
- explicit modes (`ENRICHED_EXACT`, `ENRICHED_NEAREST`, `BLIND_TEST`, `LOCAL_ONLY`),
- structured causal prompt path.

### 7.2 Remaining gap to true v0.3

- Native ingestion layer for continuous order book capture.
- Strong schema validation contract for feature rows.
- OOS protocol automation and reporting stability.
- Better gate persistence to avoid accidental progression under low coverage.

## 8. Security and Reliability Posture

From audits, top risk classes and required posture:

1. **File path safety**
   - No writes outside approved repository scope.
   - Strict path confinement and allowlist enforcement.
2. **Text fallback safety**
   - Avoid unsafe blind textual replacements for code changes.
   - Prefer structural modification paths and explicit failure when uncertain.
3. **Concurrency safety**
   - Lock critical DB/queue operations consistently.
   - Avoid partial lock coverage in maintenance/recovery functions.
4. **Rollback completeness**
   - Clear rollback logic when phase 2/3 fail.
   - Preserve traceability for failure cause and cleanup actions.

## 9. Data Quality as the Primary Gate

Current practical truth:
- Model quality is capped by data quality.
- Without reliable microstructure alignment, Deep Causal confidence is mostly limited.

Data quality checklist:
1. Trade IDs present and consistent.
2. Timestamp quality and lag within threshold.
3. Required micro fields not null.
4. Coverage high enough to reduce blind mode.
5. Repeated gate pass before phase promotion.

## 10. Runbooks

### 10.1 Daily runbook

1. Check local LLM and system health.
2. Run critical tests.
3. Run causal analysis.
4. Review gates and blind ratio.
5. Decide hold/proceed.

Commands:
```bash
cgalpha ask-health --smoke
python -m pytest -q tests/test_ghost_architect_phase7.py
cgalpha auto-analyze --working-dir .
```

### 10.2 Weekly runbook

1. Review causal metrics trend.
2. Compare in-sample vs OOS behavior.
3. Review anomalies in `BLIND_TEST`.
4. Update documentation if governance or gates changed.

### 10.3 Change-approval runbook

Approve only when:
- tests pass,
- readiness gates pass repeatedly,
- risk profile remains bounded,
- no constitutional violation.

## 11. Local LLM as Operational Interface

Roles:
- Mentor: explain architecture and operation clearly.
- Requirements Architect: convert ideas into strict scope and acceptance criteria.

Rule:
- Keep the two roles explicit to avoid mixed outputs.

Recommended usage:
```bash
cgalpha ask-setup
cgalpha ask "Explain current gate status and next safe step"
cgalpha ask-requirements "Define acceptance criteria for v0.3 data layer" --response-format json
```

## 12. Phase Progression Policy

Current policy for this repository:
- Do not jump phases based on one successful run.
- Require repeated gate pass with stable data alignment.
- Keep architecture incremental.
- Do not approve total rewrite proposals as “fast fixes.”

## 13. Glossary (Operational)

- **Fakeout:** temporary breakout with fast return, often liquidity-driven.
- **Structural break:** persistent regime/structure change.
- **BLIND_TEST:** no reliable microstructure match for an analyzed trade.
- **Gate:** a hard criterion that controls whether phase progression is allowed.
- **OOS:** out-of-sample validation period.

## 14. Source Map (Canonical Inputs)

Primary governance:
- `UNIFIED_CONSTITUTION_v0.0.3.md`

Phase strategy:
- `bible/codecraft_sage/phase7_ghost_architect.md`
- `bible/codecraft_sage/phase8_deep_causal_v03.md`
- `bible/codecraft_sage/chapter10_execution_engine.md`

Audit and risk:
- `AUDIT_REPORT_V2.md`
- `AUDIT_DEEP_CAUSAL_V03.md`

Operational baseline:
- `README.md`
- `SYSTEM_STATUS.md`
- `00_COMIENZA_AQUI.md`

## 15. Documentation Governance

Update rule:
1. Update this master doc when major logic changes are approved.
2. Update `docs/CONSTITUTION_RELEVANT_COMPANION.md` when governance changes.
3. Update `docs/DOCS_COVERAGE_MATRIX.md` when new strategic documents appear.

This keeps human and LLM orientation synchronized.

## 16. Legacy Baselines and Context Preservation

The following values are preserved as historical context from legacy status docs and may not represent the live current runtime:
- Legacy snapshot reported `96/96` tests passing in `SYSTEM_STATUS.md`.
- Legacy v0.1.0 roadmap described a staged quality plan:
  - extended type hints,
  - static analysis hardening,
  - performance baseline publication,
  - release checklist discipline.

Why keep this:
- It documents the quality posture that shaped the current architecture.
- It helps explain why CGAlpha prioritizes incremental, test-gated evolution.

Operational rule:
- Treat these baseline values as historical references unless reconfirmed by current test runs and current metrics.

## 17. What Was Missing and Added in This Hub

New elements created for stronger orientation:
1. A single canonical master manual (this document).
2. Constitution-to-checklist companion (`docs/CONSTITUTION_RELEVANT_COMPANION.md`).
3. Coverage matrix for legacy markdown migration (`docs/DOCS_COVERAGE_MATRIX.md`).
4. Direct CLI navigation for docs (`cgalpha docs ...`, alias `cgalpha d ...`).

This closes the main navigation gap for:
- human operators,
- requirement engineering workflow,
- local LLM context initialization.
