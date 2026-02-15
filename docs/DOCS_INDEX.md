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
4. `docs/LLM_LOCAL_OPERATIONS.md`
5. `UNIFIED_CONSTITUTION_v0.0.3.md`
6. `bible/codecraft_sage/phase7_ghost_architect.md`
7. `bible/codecraft_sage/phase8_deep_causal_v03.md`

## Strategic Source Documents (Still Active)

- `README.md`: project setup and usage baseline.
- `UNIFIED_CONSTITUTION_v0.0.3.md`: policy and constraints.
- `bible/`: phase-by-phase technical evolution.

## New Canonical Hub Files

- `docs/CGALPHA_MASTER_DOCUMENTATION.md`: detailed canonical orientation and runbook.
- `docs/CONSTITUTION_RELEVANT_COMPANION.md`: actionable constitutional checklist.
- `docs/DOCS_COVERAGE_MATRIX.md`: migration audit of old docs into the new hub.

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
