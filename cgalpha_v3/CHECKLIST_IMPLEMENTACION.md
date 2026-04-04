# CHECKLIST_IMPLEMENTACION — CGAlpha v3.1-audit

**Ruta:** `cgalpha_v3/CHECKLIST_IMPLEMENTACION.md`  
**Sincronizado con:** `cgalpha_v3/PROMPT_MAESTRO_v3.1-audit.md`  
**Fecha de sincronización:** 2026-04-04  
**Estado global:** 🟡 P0+P1+P2 COMPLETOS — fase de hardening P3 antes de producción real

> **REGLA DE PARADA ACTIVA (v3.1-audit):**
> No se autoriza operación en mercado real hasta que **P0 + P1 + P2** estén completos y verificados.

---

## Estado base de referencia (snapshot actual)

- `pytest -q cgalpha_v3/tests` ejecutado: **89 passed**.
- Cobertura formal: **91.43%** (`pytest --cov=cgalpha_v3 --cov-fail-under=80 -q cgalpha_v3/tests`).
- Tipado estático: `mypy cgalpha_v3 --ignore-missing-imports` = **Success: no issues found in 35 source files**.
- No-regresión legacy: `pytest -q tests` (**256 passed**) + `pytest -q tests_v2/unit` (**57 passed**).

---

## P0 — CRÍTICO (operabilidad segura mínima)

| # | Ítem | Estado | Evidencia mínima | Verificado por | Fecha |
|---|------|--------|------------------|----------------|-------|
| P0.1 | GUI Mission Control + Market Live + Risk Dashboard visibles | ✅ | `gui/static/index.html` + `tests/test_gui_library_api.py::test_p0_1_dashboard_panels_visible_in_status_and_html` | pytest + LLM | 2026-04-04 |
| P0.2 | API GUI con autenticación básica activa | ✅ | `@require_auth` en endpoints API | LLM | 2026-04-04 |
| P0.3 | Kill-switch 2 pasos operativo y bloqueo de señales | ✅ | `risk/test_risk.py` + endpoints `/api/kill-switch/*` | pytest + LLM | 2026-04-04 |
| P0.4 | Data Quality Gates activos (schema/freshness/order/gaps/outliers) | ✅ | `data_quality/gates.py`, `test_data_quality.py` | pytest | 2026-04-04 |
| P0.5 | Guard de leakage temporal (OOS) activo | ✅ | `TemporalLeakageError` + tests | pytest | 2026-04-04 |
| P0.6 | Risk Management Layer con circuit breakers | ✅ | `risk/risk_manager.py`, `test_risk.py` | pytest | 2026-04-04 |
| P0.7 | Parámetros de riesgo **completos** configurables desde GUI (`max_drawdown`, `max_position_size`, `max_signals_per_hour`, `min_signal_quality`) | ✅ | `gui/server.py` + `gui/static/index.html` + `tests/test_gui_risk_api.py` | pytest + LLM | 2026-04-04 |
| P0.8 | Rollback Protocol (snapshot+restore+hash) implementado | ✅ | `application/rollback_manager.py` + `tests/test_rollback_manager.py` | pytest + LLM | 2026-04-04 |
| P0.9 | Rollback SLA P0 (<60s) validado en test automatizado | ✅ | `tests/test_rollback_manager.py::test_restore_sla_p0_under_60_seconds` | pytest | 2026-04-04 |
| P0.10 | Artefactos de iteración (`memory/iterations/...`) generados por ciclo real | ✅ | `gui/server.py` (`_record_control_cycle` + `_persist_iteration_artifacts`) + `tests/test_gui_iteration_artifacts.py` | pytest + LLM | 2026-04-04 |
| P0.11 | `pytest cgalpha_v3/tests` en verde | ✅ | **86 passed** | pytest | 2026-04-04 |
| P0.12 | Cobertura >=80% para alcance nuevo | ✅ | `pytest --cov=cgalpha_v3 --cov-fail-under=80 -q cgalpha_v3/tests` = **90.42%** (`cgalpha_v3/coverage.xml`, `cgalpha_v3/htmlcov/`) | pytest-cov | 2026-04-04 |
| P0.13 | `mypy` alcance v3 en verde | ✅ | `mypy cgalpha_v3 --ignore-missing-imports` = **Success: no issues found in 35 source files** | mypy | 2026-04-04 |
| P0.14 | `pytest` legacy (v1/v2) en verde (no-regresión) | ✅ | `pytest -q tests` (**256 passed**) + `pytest -q tests_v2/unit` (**57 passed**) | pytest | 2026-04-04 |

**Resultado P0:** 14 ✅ / 0 🚧 / 0 ⬜

---

## P1 — BIBLIOTECA, LILA Y LOOP CIENTÍFICO

| # | Ítem | Estado | Evidencia mínima | Verificado por | Fecha |
|---|------|--------|------------------|----------------|-------|
| P1.1 | Lila ingesta con clasificación `primary/secondary/tertiary` | ✅ | `lila/library_manager.py` + GUI Library | pytest + GUI | 2026-04-04 |
| P1.2 | Regla: claim operativo no puede quedar solo con terciarias | ✅ | `validate_claim` + `detect_primary_source_gap` | pytest | 2026-04-04 |
| P1.3 | Trazabilidad por `source_id` en gestión de biblioteca | ✅ | `LibrarySource.source_id` + API | pytest | 2026-04-04 |
| P1.4 | Métrica `primary_ratio` disponible para GUI | ✅ | `library_snapshot()` en API | GUI | 2026-04-04 |
| P1.5 | Manejo explícito de `primary_source_gap` en runtime | ✅ | Endpoint `/api/library/claims/validate` | GUI | 2026-04-04 |
| P1.6 | Backlog adaptativo liderado por Lila (impacto-riesgo-evidencia) | ✅ | `AdaptiveBacklogItem` + API/GUI | GUI | 2026-04-04 |
| P1.7 | Library MVP en GUI (vista/filtro/búsqueda/ficha) conectada | ✅ | Panel Library en `index.html` | GUI | 2026-04-04 |
| P1.8 | Change Proposer con fricciones por defecto activas | ✅ | `ChangeProposer` + `Proposal` | API | 2026-04-04 |
| P1.9 | Walk-forward >=3 ventanas + split temporal Train/Val/OOS | ✅ | `ExperimentRunner` + API | API | 2026-04-04 |
| P1.10 | Integración obligatoria de no-leakage en pipeline | ✅ | `TemporalLeakageError` en `experiment_run` | pytest | 2026-04-04 |
| P1.11 | Theory Live conectado a datos reales de biblioteca | ✅ | Panel Theory Live en GUI | GUI | 2026-04-04 |
| P1.12 | Experiment Loop muestra métricas netas post-fricción | ✅ | Panel Experiment en GUI | GUI | 2026-04-04 |

**Resultado P1:** 12 ✅ / 0 🚧 / 0 ⬜

---

## P2 — MEMORIA INTELIGENTE, ZONA DE INTERÉS, TRAZABILIDAD

| # | Ítem | Estado | Evidencia mínima | Verificado por | Fecha |
|---|------|--------|------------------|----------------|-------|
| P2.1 | Campo `memory_librarian` activo en Learning real (no solo en prompt) | ✅ | `learning/memory_policy.py` + captura runtime en `gui/server.py::_capture_memory_librarian_event` + endpoints `/api/learning/memory/*` + `tests/test_gui_learning_memory_api.py::test_p2_1_to_p2_3_learning_memory_runtime` | pytest + LLM | 2026-04-04 |
| P2.2 | Política de memoria 0a/0b/1/2/3/4 implementada con promoción/degradación | ✅ | `MemoryPolicyEngine` (`ingest_raw/promote/degrade/parse_level`) + `tests/test_memory_policy.py` + API `POST /api/learning/memory/promote` | pytest + LLM | 2026-04-04 |
| P2.3 | TTL por nivel y retención aplicados automáticamente | ✅ | `MemoryPolicyEngine.apply_ttl_retention` + API `POST /api/learning/memory/retention/run` + `tests/test_memory_policy.py` + `tests/test_gui_learning_memory_api.py` | pytest + LLM | 2026-04-04 |
| P2.4 | Degradación por cambio de régimen (>2σ, >20 sesiones) activa | ✅ | `MemoryPolicyEngine.detect_and_apply_regime_shift` + API `POST /api/learning/memory/regime/check` + `tests/test_memory_policy.py` + `tests/test_gui_learning_memory_api.py::test_p2_4_regime_shift_runtime_api` | pytest + LLM | 2026-04-04 |
| P2.5 | Taxonomía de acercamientos a zona (`TOUCH/RETEST/REJECTION/BREAKOUT/OVERSHOOT/FAKE_BREAK`) en schema | ✅ | `trading/labelers/approach_type_labeler.py::ApproachLabel` + `ApproachType` obligatorio en schema + `tests/test_approach_labeler.py` | pytest + LLM | 2026-04-04 |
| P2.6 | `approach_type` clasificado por muestra en labelers | ✅ | `classify_approach_type`, `label_approach_sample(s)` + cobertura de casos en `tests/test_approach_labeler.py` | pytest + LLM | 2026-04-04 |
| P2.7 | Histograma de `approach_type` visible en GUI Experiment Loop | ✅ | Histograma en `application/experiment_runner.py` + render en `gui/static/app.js`/`index.html` + `tests/test_experiment_runner.py` + `tests/test_gui_experiment_api.py` | pytest + LLM | 2026-04-04 |
| P2.8 | Artefactos por iteración (`iteration_summary.md` + `iteration_status.json`) | ✅ | Generación automática por ciclo en `gui/server.py` + `tests/test_gui_iteration_artifacts.py` | pytest + LLM | 2026-04-04 |
| P2.9 | Incident response P0-P3 + plantilla post-mortem en flujo real | ✅ | Wiring runtime `gui/server.py::_register_incident` + endpoints `/api/incidents*` + plantilla en `docs/post_mortems/*` + `tests/test_gui_incident_adr_api.py::test_p2_9_incident_response_runtime_wiring` | pytest + LLM | 2026-04-04 |
| P2.10 | ADR y decisiones críticas registradas por iteración | ✅ | `gui/server.py::_register_adr` + endpoint `/api/adr/recent` + escritura en `docs/adr/*` + `tests/test_gui_incident_adr_api.py::test_p2_10_adr_per_iteration_and_incident_resolution` | pytest + LLM | 2026-04-04 |

**Resultado P2:** 10 ✅ / 0 🚧 / 0 ⬜

---

## P3 — HARDENING Y PRODUCCIÓN

| # | Ítem | Estado | Evidencia mínima | Verificado por | Fecha |
|---|------|--------|------------------|----------------|-------|
| P3.1 | Tests por bounded context completos | 🚧 | Existen tests DQ/Risk/Lila; faltan otros contextos | LLM | 2026-04-04 |
| P3.2 | Suite de datos temporal y consistencia ampliada | 🚧 | Base DQ existe, faltan casos avanzados | LLM | 2026-04-04 |
| P3.3 | Criterios de promoción de labs/simulation a producción documentados | ⬜ | Falta documento operativo final | — | — |
| P3.4 | `bible/` indexada y conectada semánticamente a Lila/Library | ⬜ | Falta integración semántica | — | — |
| P3.5 | SLOs + alerting + health checks cerrados | ⬜ | Falta capa de observabilidad formal | — | — |
| P3.6 | Production Gate firmada en `docs/promotions/` | ⬜ | No aplica aún (gates incompletos) | — | — |

**Resultado P3:** 0 ✅ / 2 🚧 / 4 ⬜

---

## Production Gate (v3.1-audit)

> Requiere **P0 + P1 + P2** completos antes de evaluar despliegue real.

| Gate | Criterio | Estado |
|------|----------|--------|
| Sharpe OOS | >= 0.8 neto post-fricción | ⬜ |
| Max Drawdown OOS | <= 15% | ⬜ |
| Cobertura tests | >= 80% del alcance nuevo | ✅ |
| Data Quality | 0 errores en DQ suite | 🚧 |
| Risk Assessment | completado y aprobado | ⬜ |
| Code Review | aprobado con justificación | ⬜ |
| Rollback testado | verificado en SLA | ✅ |
| Post-mortems P0/P1 | todos cerrados | ⬜ |

**Estado de producción:** 🔴 NO LISTO

---

## Acciones inmediatas recomendadas (siguiente iteración)

1. Subir cobertura por bounded context P3.1 (especialmente `gui/server.py` paths de error y filtros).
2. Ampliar suite avanzada de consistencia temporal para P3.2 (casos borde de orden/gaps/outliers/leakage).
3. Documentar criterios formales de promoción Labs/Simulation->Producción para P3.3.
4. Definir SLOs/alerting/health checks operativos para P3.5.

---

## Leyenda

| Símbolo | Significado |
|---------|-------------|
| ⬜ | Pendiente |
| 🚧 | Implementado parcial / falta validación end-to-end |
| ✅ | Completado y verificado con evidencia |
| ❌ | Fallido — requiere corrección |
| ⚠️ | Riesgo o desviación detectada |
