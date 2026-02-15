# Documentation Retention Table (KEEP / MERGE / ARCHIVE)

## Purpose of Each Category

- `KEEP`: Document is active, authoritative, or frequently used. Keep it where it is.
- `MERGE`: Content is valuable but should be consolidated into canonical docs to reduce fragmentation.
- `ARCHIVE`: Historical reference only after merge is complete. Keep in archive location, not in daily reading flow.

## Current Classification

| Path | Category | Why | Next Action |
|---|---|---|---|
| `README.md` | KEEP | Main entrypoint for setup and daily commands | Maintain and update on operational changes |
| `00_QUICKSTART.md` | KEEP | First-day operator onboarding in minimal steps | Keep aligned with real CLI workflow |
| `VERSION.md` | KEEP | Single source for declared version status | Update first on version changes |
| `UNIFIED_CONSTITUTION_v0.0.3.md` | KEEP | Primary governance and non-negotiable rules | Keep as source of truth |
| `docs/CGALPHA_MASTER_DOCUMENTATION.md` | KEEP | Canonical operational map | Keep as top reference |
| `docs/CONSTITUTION_RELEVANT_COMPANION.md` | KEEP | Constitution in practical checklist format | Keep aligned with constitution updates |
| `docs/CGALPHA_SYSTEM_GUIDE.md` | KEEP | High-level architecture guide for humans and local LLM | Keep current after architecture changes |
| `docs/LLM_LOCAL_OPERATIONS.md` | KEEP | Local LLM runbook and usage patterns | Keep current with CLI/model changes |
| `docs/DOCS_INDEX.md` | KEEP | Navigation index for documentation hub | Keep and update links/aliases |
| `docs/DOCS_COVERAGE_MATRIX.md` | KEEP | Audit trail for migration completeness | Keep updated during consolidation |
| `docs/DOCS_RETENTION_TABLE.md` | KEEP | Explicit cleanup policy and classification | Use as cleanup control sheet |
| `docs/CODECRAFT_PHASES_1_6_COMPANION.md` | KEEP | Canonical merged guide for Builder phases 1-6 | Keep as canonical source for phases 1-6 |
| `bible/codecraft_sage/phase7_ghost_architect.md` | KEEP | Active Ghost Architect baseline and policies | Keep as active phase reference |
| `bible/codecraft_sage/phase8_deep_causal_v03.md` | KEEP | Active Deep Causal target architecture | Keep as active phase reference |
| `bible/codecraft_sage/chapter10_execution_engine.md` | KEEP | Execution Engine constraints and gates | Keep as active phase reference |
| `bible/infrastructure/redis_integration.md` | KEEP | Critical infra behavior and resilience context | Keep |
| `bible/memory_system.md` | KEEP | Memory model and separation rules | Keep |
| `data_processor/README.md` | KEEP | Module-level operating reference | Keep |
| `data_postprocessor/README.md` | KEEP | Module-level operating reference | Keep |
| `oracle/README.md` | KEEP | Module-level operating reference | Keep |
| `trading_manager/README.md` | KEEP | Module-level operating reference | Keep |
| `docs/archive/codecraft_sage/phase1_fundamentals.md` | ARCHIVE | Historical phase file already merged | Keep archived for historical traceability |
| `docs/archive/codecraft_sage/phase2_ast_modifier.md` | ARCHIVE | Historical phase file already merged | Keep archived for historical traceability |
| `docs/archive/codecraft_sage/phase3_test_generator.md` | ARCHIVE | Historical phase file already merged | Keep archived for historical traceability |
| `docs/archive/codecraft_sage/phase4_git_automator.md` | ARCHIVE | Historical phase file already merged | Keep archived for historical traceability |
| `docs/archive/codecraft_sage/phase5_cli_integration.md` | ARCHIVE | Historical phase file already merged | Keep archived for historical traceability |
| `docs/archive/codecraft_sage/phase6_automatic_proposals.md` | ARCHIVE | Historical phase file already merged | Keep archived for historical traceability |
| `docs/archive/module_guides/data_processor_data_system.md` | ARCHIVE | Historical module guide already merged | Keep archived for historical traceability |
| `docs/archive/module_guides/data_postprocessor_construction_guide.md` | ARCHIVE | Historical module guide already merged | Keep archived for historical traceability |
| `docs/archive/module_guides/oracle_construction_guide.md` | ARCHIVE | Historical module guide already merged | Keep archived for historical traceability |
| `docs/archive/module_guides/triple_coincidencia_guide.md` | ARCHIVE | Historical module guide already merged | Keep archived for historical traceability |

## Cleanup Rule

Do not move any `MERGE` file to `ARCHIVE` until:
1. Content is consolidated into canonical docs.
2. `docs/DOCS_COVERAGE_MATRIX.md` is updated to `FULL`.
3. Core test suite still passes.
