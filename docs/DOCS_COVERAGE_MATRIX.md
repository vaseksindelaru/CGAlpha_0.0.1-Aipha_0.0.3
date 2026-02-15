# Documentation Coverage Matrix

## Purpose

Track which legacy documents are covered by the new hub documentation.
This is the audit layer before any future cleanup of old `.md` files.

Status legend:
- `FULL`: key concepts and operating constraints are integrated.
- `PARTIAL`: major ideas covered; some deep detail still only in source doc.
- `REFERENCE`: kept as source-of-truth archive, summarized but not fully duplicated.

## Coverage Table

| Source Document | Coverage in Hub | Where Covered |
|---|---|---|
| `UNIFIED_CONSTITUTION_v0.0.3.md` | PARTIAL | `docs/CGALPHA_MASTER_DOCUMENTATION.md`, `docs/CONSTITUTION_RELEVANT_COMPANION.md` |
| `README.md` | FULL | `docs/CGALPHA_SYSTEM_GUIDE.md`, `docs/CGALPHA_MASTER_DOCUMENTATION.md` |
| `SYSTEM_STATUS.md` | FULL | `docs/CGALPHA_SYSTEM_GUIDE.md`, `docs/CGALPHA_MASTER_DOCUMENTATION.md` |
| `00_COMIENZA_AQUI.md` | PARTIAL | `docs/CGALPHA_MASTER_DOCUMENTATION.md` |
| `AUDIT_REPORT_V2.md` | FULL | `docs/CGALPHA_MASTER_DOCUMENTATION.md` |
| `AUDIT_DEEP_CAUSAL_V03.md` | FULL | `docs/CGALPHA_MASTER_DOCUMENTATION.md`, `docs/CONSTITUTION_RELEVANT_COMPANION.md` |
| `bible/codecraft_sage/phase7_ghost_architect.md` | FULL | `docs/CGALPHA_MASTER_DOCUMENTATION.md`, `docs/CGALPHA_SYSTEM_GUIDE.md` |
| `bible/codecraft_sage/phase8_deep_causal_v03.md` | FULL | `docs/CGALPHA_MASTER_DOCUMENTATION.md`, `docs/CGALPHA_SYSTEM_GUIDE.md` |
| `bible/codecraft_sage/chapter10_execution_engine.md` | FULL | `docs/CGALPHA_MASTER_DOCUMENTATION.md`, `docs/CONSTITUTION_RELEVANT_COMPANION.md` |
| `ROADMAP_v0.1.0_FINAL.md` | PARTIAL | `docs/CGALPHA_MASTER_DOCUMENTATION.md` |

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
