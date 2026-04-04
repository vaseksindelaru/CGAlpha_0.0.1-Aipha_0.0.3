# Bitácora de Pasos — CGAlpha v3 (seguimiento vivo)

Fecha: 2026-04-04
Objetivo: mantener trazabilidad legible en `learning/` de cada avance técnico.

## Estado general

- Prompt activo: `cgalpha_v3/PROMPT_MAESTRO_v3.1-audit.md`
- Checklist activo: `cgalpha_v3/CHECKLIST_IMPLEMENTACION.md`
- Regla de parada: `P0 + P1 + P2` completados; siguiente gate activo es `P3` + Production Gate cuantitativo.

## Pasos ejecutados (hoy)

1. Revisión de consistencia del prompt v3.1.
2. Corrección de coherencia de gates (`P0/P1/P2`) en reglas de parada.
3. Refuerzo de seguridad de GUI API (`@require_auth` en endpoints API).
4. Cierre `P0.7`: parámetros de riesgo completos en API y GUI.
5. Cierre `P0.8`: rollback protocol validado por tests.
6. Cierre `P0.9`: test automático de SLA rollback `< 60s`.
7. Actualización de checklist con evidencia real de tests.
8. Cierre `P0.10`: artefactos de iteración automáticos por ciclo real GUI.
9. Cierre `P0.12`: coverage formal >=80% (resultado actual consolidado 89.97%).
10. Cierre `P0.13`: mypy v3 en verde (0 issues).
11. Cierre `P0.14`: no-regresión legacy v1/v2 (`tests` + `tests_v2/unit` en verde).
12. Cierre `P0.1`: validación explícita de paneles Mission Control / Market Live / Risk Dashboard.
13. Inicio P1 con cierre `P1.7`: Library MVP en GUI conectada a backend Lila.
14. Cierre `P1.5`: detección runtime de `primary_source_gap` + validación de claims desde API/GUI.
15. Cierre `P1.11`: Theory Live conectado a snapshot real de Lila (`/api/theory/live` + sección GUI).
16. Cierre `P1.6`: motor de backlog adaptativo (impacto-riesgo-evidencia) con priorización y resolución.
17. Cierre `P1.8`: Change Proposer operativo con fricciones por defecto activas.
18. Cierre `P1.9`: pipeline walk-forward con >=3 ventanas y split temporal Train/Val/OOS.
19. Cierre `P1.10`: integración E2E de no-leakage en runner experimental (error explícito si hay contaminación OOS).
20. Cierre `P1.12`: Experiment Loop con métricas netas post-fricción visibles en API y GUI.
21. Auditoría acumulativa: 5 correcciones aplicadas (require_auth tipado, tests _sha256_file, _validate_score_range, resolve_backlog_item). Tests: 81→86. Coverage: 89.97%→90.42%.
22. Cierre `P2.5/P2.6`: schema `ApproachLabel` + clasificación `approach_type` por muestra en labelers (`TOUCH/RETEST/REJECTION/BREAKOUT/OVERSHOOT/FAKE_BREAK`).
23. Cierre `P2.7`: histograma agregado de `approach_type` integrado en backend (`experiment_runner`) y visible en GUI Experiment Loop.
24. Cierre `P2.1/P2.2`: motor de memoria inteligente operativo (`0a/0b/1/2/3/4`) con promoción/degradación y campo `memory_librarian` activo.
25. Cierre `P2.3`: retención TTL operativa y endpoint runtime para ejecutar política.
26. Cierre `P2.4`: detección de cambio de régimen (>2σ sostenido 20 sesiones) con degradación automática de niveles altos.
27. Cierre `P2.9/P2.10`: wiring real de incident response (P0-P3 + post-mortem) y ADR por iteración con endpoints de consulta/resolución.
28. Aplicación de correcciones de auditoría: fix reloj en `regime_shift`, cobertura batch labeler y filtros de memoria.

## Evidencia técnica clave

- Tests totales v3: `89 passed` (`pytest -q cgalpha_v3/tests`).
- Test SLA rollback: `test_restore_sla_p0_under_60_seconds`.
- Test artefactos de iteración: `test_gui_iteration_artifacts.py` (2 tests).
- Test Library GUI/API: `test_gui_library_api.py` (5 tests).
- Test Theory/Backlog GUI/API: `test_gui_theory_api.py` (4 tests).
- Test Experiment Loop GUI/API: `test_gui_experiment_api.py` (3 tests).
- Test Application Experiment Runner: `test_experiment_runner.py` (4 tests).
- Test Learning Memory GUI/API: `test_gui_learning_memory_api.py` (3 tests).
- Test Incident/ADR GUI/API: `test_gui_incident_adr_api.py` (3 tests).
- Test Labelers `approach_type`: `test_approach_labeler.py` (6 tests).
- Test Motor Memoria Inteligente: `test_memory_policy.py` (8 tests).
- Coverage formal v3: `pytest --cov=cgalpha_v3 --cov-fail-under=80 -q cgalpha_v3/tests` → **91.43%**.
- Salidas coverage:
  - `cgalpha_v3/coverage.xml`
  - `cgalpha_v3/htmlcov/`
- Mypy v3: `mypy cgalpha_v3 --ignore-missing-imports` → **Success: no issues found in 35 source files**.
- Legacy no-regresión:
  - `pytest -q tests` → **256 passed**
  - `pytest -q tests_v2/unit` → **57 passed**
  - Total legacy verificado: **313 passed**
- API riesgo ahora maneja:
  - `max_drawdown_session_pct`
  - `max_position_size_pct`
  - `max_signals_per_hour`
  - `min_signal_quality_score`
- Ciclos mutantes GUI (`kill-switch`, `risk params`) ahora generan automáticamente:
  - `memory/iterations/YYYY-MM-DD_HH-MM*/iteration_summary.md`
  - `memory/iterations/YYYY-MM-DD_HH-MM*/iteration_status.json`
- Library GUI ya no es placeholder:
  - Estado en vivo (`/api/library/status`)
  - Búsqueda/filtro (`/api/library/sources`)
  - Ficha (`/api/library/sources/<source_id>`)
  - Ingesta (`/api/library/ingest`)
- Theory Live conectado a backend real:
  - Snapshot consolidado (`/api/theory/live`)
  - Validación runtime de claims (`/api/library/claims/validate`)
  - Detección explícita de `primary_source_gap`
  - Backlog adaptativo (`/api/lila/backlog`, `/api/lila/backlog/<id>/resolve`)
- Experiment Loop operativo:
  - Propuesta (`/api/experiment/propose`) con fricciones por defecto
  - Ejecución (`/api/experiment/run`) con walk-forward>=3
  - Estado (`/api/experiment/status`) con métricas netas post-fricción
  - Integración E2E de no-leakage vía `check_oos_leakage` en cada ventana
- P2 memoria inteligente operativa:
  - Estado memoria (`/api/learning/memory/status`)
  - Ingesta/promoción (`/api/learning/memory/ingest`, `/api/learning/memory/promote`)
  - Retención TTL (`/api/learning/memory/retention/run`)
  - Cambio de régimen (`/api/learning/memory/regime/check`)
  - Persistencia de entradas en `memory/memory_entries/*.json`
- P2 incident response + ADR:
  - Incidentes (`/api/incidents`, `/api/incidents/<id>/resolve`)
  - ADR recientes (`/api/adr/recent`)
  - Plantillas post-mortem en `docs/post_mortems/*.md`
  - ADR runtime por iteración en `docs/adr/*.md`
- Taxonomía de acercamientos:
  - Schema y clasificación en `trading/labelers/approach_type_labeler.py`
  - Histograma por experimento visible en sección GUI `Experiment Loop`

## Qué falta para próximos bloques

- P0/P1/P2: completos en esta sesión de auditoría.
- Próximo bloque natural: `P3` (hardening producción, observabilidad y criterios de promoción).

## Nota sobre Lila en GUI y Learning

Ya existe sección `Theory Live` conectada al backend de Lila con snapshot, validación de claims y backlog.
La ventana individual completa tipo v1/v2 aún puede expandirse en próximos incrementos de UX.
