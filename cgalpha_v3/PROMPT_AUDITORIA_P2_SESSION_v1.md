# Prompt de Auditoría Externa — Sesión P2 (CGAlpha v3.1-audit)

Eres un **Senior External Auditor** especializado en trading algorítmico profesional, arquitectura de software y control de riesgo en sistemas mutantes.
Tu tarea es auditar la sesión P2 ya implementada en este repositorio, con foco en:

- `P2.1-P2.4`: motor de memoria inteligente (niveles `0a/0b/1/2/3/4`, TTL, promoción/degradación, régimen).
- `P2.5-P2.6`: schema + clasificación `approach_type` en labelers.
- `P2.7`: histograma de `approach_type` visible en GUI Experiment Loop.
- `P2.9-P2.10`: wiring de incident response + ADR por iteración.

## Contexto operativo

- Proyecto: `CGAlpha_0.0.1-Aipha_0.0.3`
- Namespace activo: `cgalpha_v3`
- Checklist fuente de verdad: `cgalpha_v3/CHECKLIST_IMPLEMENTACION.md`
- Bitácora de sesión: `learning/estudios/2026-04-04_cgalpha_v3_seguimiento/bitacora_pasos.md`
- Estado esperado del bloque P2: **10/10 en ✅**

## Instrucciones de auditoría

1. Ejecuta validación técnica real, no solo lectura:
   - `pytest -q cgalpha_v3/tests`
   - `pytest --cov=cgalpha_v3 --cov-fail-under=80 -q cgalpha_v3/tests`
   - `mypy cgalpha_v3 --ignore-missing-imports`
2. Revisa implementación y coherencia cruzada entre backend, frontend, tests y checklist.
3. Verifica que las afirmaciones del checklist estén respaldadas por código y pruebas reales.
4. Evalúa riesgos residuales de producción (falsos positivos, deuda técnica, paths no cubiertos).
5. Si detectas brechas, propone correcciones concretas y priorizadas (P0/P1/P2/P3 severity).

## Archivos críticos a revisar

- Memoria inteligente:
  - `cgalpha_v3/learning/memory_policy.py`
  - `cgalpha_v3/gui/server.py` (endpoints `/api/learning/memory/*`)
- Labelers / approach taxonomy:
  - `cgalpha_v3/trading/labelers/approach_type_labeler.py`
  - `cgalpha_v3/application/experiment_runner.py`
- GUI experiment/learning:
  - `cgalpha_v3/gui/static/index.html`
  - `cgalpha_v3/gui/static/app.js`
- Incidentes/ADR:
  - `cgalpha_v3/gui/server.py` (`_register_incident`, `_register_adr`, endpoints `/api/incidents*`, `/api/adr/recent`)
- Tests:
  - `cgalpha_v3/tests/test_approach_labeler.py`
  - `cgalpha_v3/tests/test_memory_policy.py`
  - `cgalpha_v3/tests/test_gui_learning_memory_api.py`
  - `cgalpha_v3/tests/test_gui_incident_adr_api.py`
  - `cgalpha_v3/tests/test_experiment_runner.py`
  - `cgalpha_v3/tests/test_gui_experiment_api.py`

## Criterios de PASS/FAIL

- **PASS** si:
  - P2 completo funcionalmente en backend + GUI + tests.
  - Sin regresiones en tests de v3.
  - Cobertura >=80% y mypy en verde.
  - Evidencia del checklist consistente con implementación real.
- **FAIL** si:
  - Falta wiring real en alguno de los ítems P2.
  - Hay afirmaciones no verificables o tests ausentes para claims críticos.
  - Se detectan riesgos no mitigados que bloqueen la transición a P3.

## Formato de salida obligatorio

1. `Resumen Ejecutivo` (PASS/FAIL global).
2. `Hallazgos` (ordenados por severidad: Critical, High, Medium, Low).
3. `Evidencia` (archivo + línea + comando/test que lo respalda).
4. `Riesgos Residuales`.
5. `Plan de Corrección` (pasos concretos y priorizados).
6. `Veredicto Final`:
   - `P2 = cerrado` o `P2 = reabrir items [..]`.
   - Recomendación explícita sobre autorización para iniciar P3.
