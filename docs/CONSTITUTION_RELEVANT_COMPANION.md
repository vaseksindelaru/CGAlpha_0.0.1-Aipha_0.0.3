# Constitution Relevant Companion

## Objective

This companion translates the unified constitution into practical checklists for operators, reviewers, and local LLM workflows.

It is not a replacement for `UNIFIED_CONSTITUTION_v0.0.3.md`.
It is the actionable digest used in daily execution.

## Part-by-Part Practical Summary

## Part 1 - Identity and Strategy

Checklist:
- Keep Aipha (execution body) and CGAlpha (causal brain) roles explicit.
- Protect the separation between operational execution and causal experimentation.
- Do not optimize one side by breaking the other.

## Parts 2-8 - Operational evolution and interface

Checklist:
- Preserve incremental evolution path.
- Keep CLI as control surface, not as hidden complexity layer.
- Keep memory traceability always on.

## Part 9 - Code Craft Sage (Automatic Code Generation)

Mandatory controls:
1. Proposal parsing must be explicit and auditable.
2. Code modification must be scoped and reversible.
3. Test barrier must be explicit (unit + integration + regression).
4. Documentation must be updated for approved changes.
5. Validation barrier must block unsafe merges.

Reviewer checks:
- Any path write outside repository scope -> INSECURE.
- Unsafe textual fallback without structural guarantees -> INSECURE.
- Missing rollback behavior on pipeline fail -> INSECURE.

## Part 10 - Execution Engine (Live-Gated)

Mandatory preconditions for Live/Hybrid:
1. `order_book_features.jsonl` exists and is usable.
2. `auto-analyze` output includes:
   - `data_alignment`
   - `causal_metrics`
   - `readiness_gates`
3. Gates:
   - `data_quality_pass = true`
   - `causal_quality_pass = true`
   - `proceed_v03 = true`

Fallback rule:
- If one gate fails, Paper mode only.

## Part 10.1 - Deep Causal Governance

Mandatory:
- Missing/invalid micro alignment -> mark `BLIND_TEST`.
- No high-confidence causal claim with high blind ratio.
- No total rewrite as shortcut.

Thresholds in active use:
- `max_blind_test_ratio <= 0.25`
- `max_nearest_match_avg_lag_ms <= 150`
- `min_causal_accuracy >= 0.55`
- `min_efficiency >= 0.40`

## Part 11 - Causal Evaluation Protocol (OOS)

Approval conditions:
1. Out-of-sample causal behavior validated.
2. Precision by causal label is acceptable.
3. Noise rejection behavior is measured.
4. Operational compatibility remains intact.

If a proposal breaks compatibility or forces broad rewrite:
- classify as `INSEGURO` until proven safe.

## Memory and Data Governance Rules

Checklist:
- Keep `operational/` and `evolutionary/` semantics clean.
- Preserve bridge traceability (`bridge.jsonl`).
- Do not introduce synthetic data as “real market evidence”.

## Security and Reliability Rules

Checklist:
- Constrain writes to approved repository scope.
- Keep lock coverage on critical shared state operations.
- Ensure rollback hygiene for failed phases.
- Persist clear error evidence for postmortem.

## Promotion Policy (Phase Advancement)

Promotion criteria:
1. Tests pass consistently.
2. Gates pass repeatedly (not just once).
3. Data quality is stable.
4. Risk profile remains bounded.
5. No constitutional conflict.

Promotion blockers:
- high blind mode,
- unstable lag alignment,
- OOS uncertainty,
- safety regressions.

## Operator Shortcut Checklist

Before advancing phase:
1. `cgalpha ask-health --smoke`
2. Run targeted tests.
3. `cgalpha auto-analyze`
4. Verify readiness gates.
5. Review blind ratio trend.
6. Only then approve progression.

## LLM Role Alignment Checklist

Mentor role:
- Explain architecture, flow, constraints.

Requirements role:
- produce strict scope and acceptance criteria.
- avoid code generation.

Shared:
- never bypass constitutional gates.
- never suggest total rewrite without migration proof.
