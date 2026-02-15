# Documentation Coverage Matrix

## Purpose

Track which legacy documents are covered by the new hub documentation.
This is the audit layer before any future cleanup of old `.md` files.

Status legend:
- `FULL`: key concepts and operating constraints are integrated.
- `PARTIAL`: major ideas covered; some deep detail still only in source doc.
- `REFERENCE`: kept as source-of-truth archive, summarized but not fully duplicated.
- `RETIRED`: legacy source removed after consolidation into canonical docs.

## Coverage Table

| Source Document | Coverage in Hub | Where Covered |
|---|---|---|
| `UNIFIED_CONSTITUTION_v0.0.3.md` | PARTIAL | `docs/CGALPHA_MASTER_DOCUMENTATION.md`, `docs/CONSTITUTION_RELEVANT_COMPANION.md`, `docs/reference/constitution_core.md`, `docs/reference/gates.md`, `docs/reference/parameters.md` |
| `00_QUICKSTART.md` | FULL | Primary quick onboarding file (direct canonical source) |
| `VERSION.md` | FULL | Primary version status file (direct canonical source) |
| `README.md` | FULL | `docs/CGALPHA_SYSTEM_GUIDE.md`, `docs/CGALPHA_MASTER_DOCUMENTATION.md` |
| `SYSTEM_STATUS.md` | RETIRED | Consolidated into `docs/CGALPHA_MASTER_DOCUMENTATION.md` |
| `00_COMIENZA_AQUI.md` | RETIRED | Consolidated into `docs/CGALPHA_MASTER_DOCUMENTATION.md` |
| `AUDIT_REPORT_V2.md` | RETIRED | Consolidated into `docs/CGALPHA_MASTER_DOCUMENTATION.md` |
| `AUDIT_DEEP_CAUSAL_V03.md` | RETIRED | Consolidated into `docs/CGALPHA_MASTER_DOCUMENTATION.md` |
| `bible/codecraft_sage/phase7_ghost_architect.md` | FULL | `docs/CGALPHA_MASTER_DOCUMENTATION.md`, `docs/CGALPHA_SYSTEM_GUIDE.md` |
| `bible/codecraft_sage/phase8_deep_causal_v03.md` | FULL | `docs/CGALPHA_MASTER_DOCUMENTATION.md`, `docs/CGALPHA_SYSTEM_GUIDE.md` |
| `bible/codecraft_sage/chapter10_execution_engine.md` | FULL | `docs/CGALPHA_MASTER_DOCUMENTATION.md`, `docs/CONSTITUTION_RELEVANT_COMPANION.md` |
| `bible/codecraft_sage/phase1_fundamentals.md` | FULL | Merged into `docs/CODECRAFT_PHASES_1_6_COMPANION.md`; archived at `docs/archive/codecraft_sage/phase1_fundamentals.md` |
| `bible/codecraft_sage/phase2_ast_modifier.md` | FULL | Merged into `docs/CODECRAFT_PHASES_1_6_COMPANION.md`; archived at `docs/archive/codecraft_sage/phase2_ast_modifier.md` |
| `bible/codecraft_sage/phase3_test_generator.md` | FULL | Merged into `docs/CODECRAFT_PHASES_1_6_COMPANION.md`; archived at `docs/archive/codecraft_sage/phase3_test_generator.md` |
| `bible/codecraft_sage/phase4_git_automator.md` | FULL | Merged into `docs/CODECRAFT_PHASES_1_6_COMPANION.md`; archived at `docs/archive/codecraft_sage/phase4_git_automator.md` |
| `bible/codecraft_sage/phase5_cli_integration.md` | FULL | Merged into `docs/CODECRAFT_PHASES_1_6_COMPANION.md`; archived at `docs/archive/codecraft_sage/phase5_cli_integration.md` |
| `bible/codecraft_sage/phase6_automatic_proposals.md` | FULL | Merged into `docs/CODECRAFT_PHASES_1_6_COMPANION.md`; archived at `docs/archive/codecraft_sage/phase6_automatic_proposals.md` |
| `data_processor/docs/Documentación  data_system.md` | FULL | Merged into `data_processor/README.md`; archived at `docs/archive/module_guides/data_processor_data_system.md` |
| `data_postprocessor/docs/data_postprocessor_construction_guide.md` | FULL | Merged into `data_postprocessor/README.md`; archived at `docs/archive/module_guides/data_postprocessor_construction_guide.md` |
| `oracle/docs/oracle_construction_guide.md` | FULL | Merged into `oracle/README.md`; archived at `docs/archive/module_guides/oracle_construction_guide.md` |
| `trading_manager/TRIPLE_COINCIDENCIA_GUIDE.md` | FULL | Merged into `trading_manager/README.md`; archived at `docs/archive/module_guides/triple_coincidencia_guide.md` |
| `ROADMAP_v0.1.0_FINAL.md` | RETIRED | Consolidated into `docs/CGALPHA_MASTER_DOCUMENTATION.md` |

## Gap List (Still in Source Docs)

These remain mostly in original files and should be imported later if needed:
- Detailed historical timelines and long-form business narrative.
- Full historical examples of command output from old onboarding docs.
- Large appendix sections not required for daily operation.

## Consolidation Rule

Before deleting any legacy `.md`:
1. Confirm matrix entry as `FULL`.
2. Confirm at least one reviewer can operate only with hub docs.
3. Confirm local LLM quality does not regress when using hub context.

No legacy document should be removed until these checks pass.
