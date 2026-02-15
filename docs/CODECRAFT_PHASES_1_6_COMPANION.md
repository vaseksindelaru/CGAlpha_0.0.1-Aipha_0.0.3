# Code Craft Sage Companion (Phases 1-6)

## Purpose

This document consolidates the operationally relevant content from:
- `phase1_fundamentals.md`
- `phase2_ast_modifier.md`
- `phase3_test_generator.md`
- `phase4_git_automator.md`
- `phase5_cli_integration.md`
- `phase6_automatic_proposals.md`

Goal:
- keep one practical reference for daily operation,
- preserve historical phase files in archive,
- avoid fragmented guidance across many large markdown files.

## Phase 1: Proposal Parsing (Foundation)

Core role:
- Convert natural-language proposals into `TechnicalSpec`.

Operational expectations:
- deterministic parsing when possible,
- strict validation before any code mutation,
- cache-first behavior with graceful fallback when LLM/Redis are unavailable.

Key outputs:
- `TechnicalSpec` with validated fields,
- parser metrics (cache hits/misses, fallback usage, errors).

## Phase 2: Safe Code Modification (AST First)

Core role:
- Apply code changes safely, preferring AST transformations.

Safety contract:
- never mutate without backup,
- validate syntax and compile after modification,
- rollback immediately when validation fails.

Risk posture:
- structural edits preferred,
- text fallback only as controlled fallback,
- unsafe or ambiguous edits must fail closed.

## Phase 3: Test Generation and Validation Barrier

Core role:
- generate targeted tests for the change,
- run regression tests,
- enforce quality gates before proceeding.

Constitution alignment:
- supports the Part 9 “triple barrier” intent:
  1. change-specific validation,
  2. regression protection,
  3. coverage/quality checks.

Minimum acceptance:
- no regression failures,
- quality gate outcome explicitly reported (`ready` vs `needs_fix`).

## Phase 4: Git Automation (Controlled Versioning)

Core role:
- isolate changes in feature branches,
- commit with structured metadata.

Non-negotiable controls:
- no automatic push,
- no direct writes to protected branches,
- fail safely on dirty/conflicted repository state.

Expected result:
- reproducible branch + commit trail for human review.

## Phase 5: CLI and Orchestration Integration

Core role:
- expose end-to-end pipeline as CLI workflow.

Operator flow:
1. submit proposal,
2. execute parser -> modifier -> tests -> git,
3. inspect status and report,
4. proceed only on success gates.

Rollback policy:
- failures in validation phases must leave repository in safe recoverable state.

## Phase 6: Automatic Proposal Generation

Core role:
- analyze performance signals and propose improvements.

Boundary:
- proposes only,
- does not auto-apply without explicit approval.

Practical use:
- surface candidate optimizations with confidence and reason,
- feed approved proposals into the same safeguarded Code Craft pipeline.

## End-to-End Contract (Phases 1-6)

The Builder loop must remain:
1. Parse safely.
2. Modify safely.
3. Validate strictly.
4. Version changes safely.
5. Expose clear operator controls.
6. Keep auto-proposals advisory unless approved.

This preserves system integrity while enabling controlled self-improvement.

## Archive Policy

Historical phase files are archived at:
- `docs/archive/codecraft_sage/`

Use archived files only for deep historical context.
For operational guidance, use this companion plus:
- `docs/CGALPHA_MASTER_DOCUMENTATION.md`
- `docs/CONSTITUTION_RELEVANT_COMPANION.md`
- `UNIFIED_CONSTITUTION_v0.0.3.md`
