# CGAlpha Documentation Hub

This folder is the new documentation hub for both:
- Human operators and maintainers.
- Local LLM assistants (mentor and requirements roles).

Important:
- Legacy root reports were consolidated into canonical docs in `docs/`.
- This hub is now the primary documentation source.
- It creates a stable reading order and a single entry point from CLI.

## Quick Start Reading Order

1. `docs/CGALPHA_MASTER_DOCUMENTATION.md`
2. `docs/CONSTITUTION_RELEVANT_COMPANION.md`
3. `docs/CGALPHA_SYSTEM_GUIDE.md`
4. `00_QUICKSTART.md`
5. `VERSION.md`
6. `docs/LLM_LOCAL_OPERATIONS.md`
7. `docs/CODECRAFT_PHASES_1_6_COMPANION.md`
8. `docs/reference/constitution_core.md`
9. `docs/reference/gates.md`
10. `docs/reference/parameters.md`
11. `UNIFIED_CONSTITUTION_v0.0.3.md`
12. `bible/codecraft_sage/phase7_ghost_architect.md`
13. `bible/codecraft_sage/phase8_deep_causal_v03.md`

## Strategic Source Documents (Still Active)

- `README.md`: project setup and usage baseline.
- `UNIFIED_CONSTITUTION_v0.0.3.md`: compact policy and constraints.
- `docs/archive/constitution/UNIFIED_CONSTITUTION_v0.0.3_FULL_LEGACY.md`: full historical constitution snapshot.
- `bible/`: phase-by-phase technical evolution.

## New Canonical Hub Files

- `docs/CGALPHA_MASTER_DOCUMENTATION.md`: detailed canonical orientation and runbook.
- `docs/CONSTITUTION_RELEVANT_COMPANION.md`: actionable constitutional checklist.
- `docs/DOCS_COVERAGE_MATRIX.md`: migration audit of old docs into the new hub.
- `docs/DOCS_RETENTION_TABLE.md`: KEEP/MERGE/ARCHIVE policy and cleanup classification.
- `docs/CODECRAFT_PHASES_1_6_COMPANION.md`: merged operational guide for Code Craft Sage phases 1-6.
- `00_QUICKSTART.md`: first-day onboarding in 5 minutes.
- `VERSION.md`: single source for declared versions.
- `docs/reference/constitution_core.md`: operational constitution core (short form).
- `docs/reference/gates.md`: readiness gates and thresholds for Deep Causal.
- `docs/reference/parameters.md`: critical parameters quick reference.

## CLI Access

Use direct CLI commands:

```bash
cgalpha docs list
cgalpha docs show index
cgalpha docs show master
cgalpha docs show constitution_companion
cgalpha docs show companion
cgalpha docs show guide
cgalpha docs show llm
cgalpha docs show coverage
cgalpha docs show retention
cgalpha docs show codecraft_companion
cgalpha docs show quickstart
cgalpha docs show version
cgalpha docs show constitution_core
cgalpha docs show gates
cgalpha docs show parameters
cgalpha docs show reference
cgalpha docs path constitution
cgalpha d show master
```

## Why This Hub Exists

- Reduce navigation overhead.
- Keep LLM context clean and consistent.
- Provide one stable map while architecture evolves.
- Make onboarding repeatable and less dependent on chat history.

## Maintenance Rule

When major changes are approved:
- Update `docs/CGALPHA_SYSTEM_GUIDE.md` first.
- Update `docs/LLM_LOCAL_OPERATIONS.md` second.
- Keep historical reports unchanged unless there is a factual correction.
