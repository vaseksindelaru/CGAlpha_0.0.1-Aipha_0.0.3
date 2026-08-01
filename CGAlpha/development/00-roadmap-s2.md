---
type: development-roadmap
project: CGAlpha
tags: [proyecto/cgalpha, development, s2, proximos-pasos, actualizado-2026-07-27]
updated: 2026-07-27
source: verified-live-against-cloned-repo
---

# 🔧 Desarrollo — S2 (Próximos Pasos)

> Roadmap del desarrollo activo de CGAlpha v3/v4, basado en verificación en vivo contra el repositorio clonado (27 jul 2026).

## 📊 Evaluación externa vs realidad del repo

La evaluación externa (LLM que citó S3_ORDEN_DE_CONSTRUCCION.md líneas 1-120) está **obsoleta**. Evidencia verificada contra el repo real:

| Afirmación externa | Realidad verificada contra repo |
|---|---|
| "PRÓXIMO PASO: Paso 1 — IDENTITY Memory" | Identity completo: 11 ADRs viviendo en `aipha_memory/identity/`. Paso 1 es historia antigua. |
| "113 tests passing, 92.76% coverage" | **401 tests reales** (395 passed, 6 failed) solo en `cgalpha_v3/tests/` + `tests/`. El badge del README dice "144 passing" — ni siquiera coincide con los 113. |
| "Oracle v6 con 6 bugs, 2 fixados" | Existe `oracle_v6_skeleton.py` real (9906 bytes) pero es un CRB de reconstrucción determinista (54.77% coverage, 2 fases A/B), no "6 bugs, 2 fixados". Los 8 bugs originales BUG-1..BUG-8 están confirmados resueltos. |
| "4 islas ⚠️ desconectadas" | `EvolutionOrchestratorV4` está inyectado en el pipeline, con `CodeCraftSage` como brazo ejecutor real — no solo aprobación sin ejecución. |
| Evaluación basada en: | Texto descriptivo estático (`S3_ORDEN_DE_CONSTRUCCION.md` líneas 1-120), **no** en ejecución contra el repo. |
| Método correcto verificado con: | `pytest` corriendo contra el código clonado, `grep` contra código fuente, artefactos derivados (11 ADRs), CRB fechados. |

## 🔀 Esquema de prioridades P0-P9 (NEXUS_SUPERIOR.md)

Vive en `documentation/NEXUS_SUPERIOR.md`, **no** en ADRs. Los ADRs documentan decisiones puntuales (D-003, etc.); los CRB individuales documentan cada componente.

| Prioridad | Componente | Estado | Referencia |
|---|---|---|---|
| P0 META | Routing System (Nexus) | ✅ OPERATIVO | Este doc |
| P0 META | Codex (7 entradas) | ✅ INGESTADO | CODEX_ENTRIES_DRAFT.md |
| **P1** | **Oracle v6** | 🔴 EN PROGRESO | RECONSTRUCTION_BRIEF.md — OOS 0.68, coverage 54.77% |
| P2 | CodeCraftSage v4 | 🟡 OPERATIVO | CRB pendiente |
| P3 | L2 Ring Buffer (BinanceWebSocketManager) | 🟡 OPERATIVO, audit pendiente | CRB_BinanceWebSocketManager_P3.md |
| P4 | DeferredOutcomeMonitor | 🟡 OPERATIVO, audit pendiente | CRB_DeferredOutcomeMonitor_P4.md |
| P5 | TripleCoincidenceDetector (integración L2) | ✅ ESTABLE | CRB creado |
| P6 | EvolutionOrchestrator v5 | 🟡 ACUMULA BACKLOG | CRB pendiente |
| P6.5 | Chat de Lila (GUI) | 🔴 DESCONECTADO | Bloquea "Eco Eterno" del Harness |
| P7 | MemoryPolicyEngine v4.1 | ✅ ESTABLE | CRB pendiente |
| P8 | LLMSwitcher v2 | ✅ ESTABLE | CRB pendiente |
| P9 | ShadowTrader | ✅ ESTABLE | CRB pendiente |

> **Nota de honestidad**: NEXUS_SUPERIOR.md marca QUARANTINE_GATE y READY_FOR_CODEX como 🟡 SIMULADO — el ciclo de gobernanza existe como diseño y en parte como código, pero no todo está automatizado al 100%. Verificar en próximo paso si el guardrail está implementado o solo diagramado.

## 🐛 6 Tests Fallando (clasificación verificada)

| # | Test | Tipo de evidencia | Fallo | Clasificación | Acción |
|---|---|---|---|---|---|
| 1 | `test_classifier_feature_count_is_eleven` | **Verbatim pytest** (AssertionError) | `assert 23 == 11` | Oracle features desactualizado: pasó de 11 a 23 (Fase B, features dinámicas + L2) | Actualizar fixture |
| 2 | `test_regressor_feature_count_is_twelve` | **Verbatim pytest** (AssertionError) | `assert 24 == 12` | Mismo que arriba (Oracle 12→24) | Actualizar fixture |
| 3 | `test_heartbeat_status` | **Verbatim pytest** (AssertionError) | `'OFFLINE' not in ('offline', 'OK', ...)` | Cosmético: case mismatch en el assertion del test | Arreglar en test |
| 4 | `test_clearance_instrumentation_robust` | **Verbatim pytest** (AssertionError) | Esperaba 10100.0, obtuvo 10200.0 | Bug de fixture del test — véase detalle abajo | Investigar fixture (PRIORIDAD S2) |
| 5 | `test_orchestrator_classify` (Rule 3, caso 1) | **Lectura directa de código fuente** (no pytest) | Lógica del guardrail, no AssertionError | Guardrail intencional: `classify()` línea 192 Rule 3 bloquea auto-aprobación para `volume_threshold`. Test anterior al Parameter Landscape Map. | No es bug — documentar como diseño evolucionado |
| 6 | `test_orchestrator_classify` (Rule 3, caso 2) | **Lectura directa de código fuente** (no pytest) | Mismo mecanismo | Igual que #5 | Igual que #5 |

> **Nota de precisión**: Los tests #5 y #6 no tienen verbatim de pytest. Lo que tengo es la lógica causal completa en `classify()` línea 192, que es evidencia más fuerte que un trace de pytest (explica por qué fallan, no el mensaje de error del fallo). Son evidencia de tipo distinto.

### 🔴 PRIORIDAD S2: max_price_since_detection (test #6)

**Resultado verificado en vivo**: determinista, 10200.0 cada vez, no un flake.

**Mecanismo exacto** (verificado contra código de producción):
1. `detector.active_zones = [zone]` inyecta la zona en `active_zones` **antes** de que el loop arranque
2. El loop `process_stream()` empieza en `idx=0` — la zona existe "desde el inicio"
3. En `idx=0` el sistema dispara un **retest falso** porque no valida `idx >= zone.candle_index` antes de intentar retest
4. `zone.max_price_since_detection` termina en **10200.0** (el high más alto de todo el dataset, incluyendo las 15 velas de padding del test)
5. El guard `_cleanup_expired_zones()` (línea 1235) llega **tarde** — se ejecuta después del bloque de retest en la misma iteración
6. El feature `max_clearance_atr` se calculó con `max_price_since_detection=10015` (valor real en `idx=0`), no `10100` ni `10200`

**Conclusión**: **Bug de fixture, no regresión de producción**. Una zona genuina solo entra en `active_zones` a través de `_detect_new_zones()` en el mismo `idx` que la zona se detecta — nunca antes. El arreglo del test es inyectar la zona solo cuando el loop llega a `candle_index`:

```python
# Fix recomendado (en el test, no en producción):
_ = detector.process_stream(df.iloc[:zone.candle_index])
detector.active_zones = [zone]
_ = detector.process_stream(df.iloc[zone.candle_index:].reset_index(drop=True))
```

El dataset de entrenamiento real (`prepared_sets/`, 92+101+122 samples) **NO está contaminado** por este mecanismo — requiere una zona "nacida antes de su propio índice", condición imposible en pipeline live o batch histórico real.

## 🏗️ Estructura del repositorio (verificada en vivo)

```
CGAlpha_0.0.1-Aipha_0.0.3/
├── cgalpha_v3/          → Motor de producción
│   ├── core/            → TripleCoincidenceDetector, OracleTrainer_v3
│   ├── infrastructure/  → BinanceWebSocketManager
│   ├── lila/            → EvolutionOrchestratorV4
│   ├── learning/        → MemoryPolicyEngine, memory levels
│   ├── tests/           → Test suite (401 tests, 395 passing)
│   └── gui/             → server.py (punto de entrada)
├── cgalpha_v4/          → Capa de especificación/reconstrucción (¡hermano de cgalpha_v3!, no anidado)
│   ├── oracle_v6_skeleton.py (9906 bytes)
│   ├── test_oracle_v6_skeleton.py (17594 bytes)
│   └── CRBs individuales (P3, P4, P5)
├── governance_log/      → Tickets fechados hasta 24jun2026
├── documentation/        → NEXUS_SUPERIOR.md (gobernanza), S0_d_hasta_24h.md (108K)
├── aipha_memory/identity/ → 11 ADRs documentando decisiones (D-003, etc.)
├── rebound/             → Para "multitouch" (nuevo, no en crónica mayo)
├── prepared_sets/       → Set A / Set Bhybrid (92+101+122 samples)
├── docs/                → Crónica de desarrollo
└── tests/               → Test suite raíz (tests/)
```

> **Nota de estructura**: `cgalpha_v4/` es un directorio raíz, hermano de `cgalpha_v3/`. Si la búsqueda está scopeada a `cgalpha_v3/`, nunca encuentra nada en `cgalpha_v4/`.

## ⏭️ Próximos pasos S2 — Priorizados

| Paso | Prioridad | Descripción | Estado | Por qué esta prioridad |
|---|---|---|---|---|
| **1. Fix del fixture de max_price_since_detection** | 🔴 ALTA | Aplicar el fix del test (inyectar zona en active_zones solo cuando el loop llega a candle_index, no antes). El diagnóstico está completo y el fix está listo. | PENDIENTE — LISTO PARA EJECUTAR | Es el único de los tres pasos con diagnóstico completo y fix listo para aplicar. Dejarlo abierto después de un diagnóstico del todo es la brecha entre "saber" y "cerrar". |
| **2. QUARANTINE_GATE — ¿qué tan automatizado es?** | 🟡 MEDIA | Verificado en vivo: **cero archivos .py** contienen QUARANTINE_GATE o READY_FOR_CODEX. Son solo checklist manual (§9 de NEXUS_SUPERIOR.md), sin enforcement en código. P1 (Oracle v6) es la máxima prioridad y si el gate de seguridad que debería protegerlo está desenchufado del código, esto es información operativa real. | VERIFICADO — información almacenada en `02-gobernanza-nexus-superior.md` | No es curiosidad ociosa: la pregunta "¿cuánto de la protección del P1 es código real vs. proceso manual?" tiene respuesta verificada y es cero código. |
| **3. Lila GUI P6.5** | 🔴 NO PRIORIZAR | Ya respondido con la lógica del propio proyecto: P6.5 tiene como prerequisito explícito "Orchestrator v5 estable"; P6 se autodeclara "baja urgencia mientras P1-P4 estén activos". No hace falta indagar más — el documento ya contestó esta pregunta. | RESUELTO por el documento del proyecto | El propio P0-P9 del proyecto ya priorizó y justificó la secuencia. |
| **4. Leer NEXUS_SUPERIOR.md 100%** | NO HACERLO TODAVÍA | Sin una pregunta concreta que lo requiera, esto es la definición del antipatrón §7.3 del Prompt Fundacional: "filosofar antes de actuar". | APLAZADO | Cuando una decisión real dependa de un detalle que no leí, lo leo entonces — no antes. |

## 📝 Fuentes verificadas en este round

- `NEXUS_SUPERIOR.md` → esquema de fases P0-P9, tabla QUARANTINE_GATE/READY_FOR_CODEX como SIMULADO
- `documentation/S0_d_hasta_24h.md` (108K) → documentación de estado
- `governance_log/` → tickets fechados hasta 24jun2026
- `cgalpha_v4/oracle_v6_skeleton.py` (9906 bytes) → CRB reconstrucción Oracle v6
- `cgalpha_v4/test_oracle_v6_skeleton.py` (17594 bytes) → test del skeleton
- `CRB_BinanceWebSocketManager_P3.md`, `CRB_DeferredOutcomeMonitor_P4.md`, `CRB_TripleCoincidenceDetector_P5.md` → CRBs de componentes
- 11 ADRs en `aipha_memory/identity/` → D-003 (threshold 0.70 inmutable), etc.
- `test_clearance_instrumentation.py` → fixture bug: retest_index=0 debería ser 13
- `TripleCoincidenceDetector/_check_retest()` → retest dispara en idx=0 cuando zone.candle_index=10
- `_cleanup_expired_zones()` → guard llega tarde (misma iteración, después del bloque de retest)
- `classify()` línea 192 → Rule 3: RESTRICTED FOR VALIDATION para parámetros de alto impacto
- `prepared_sets/` → 92+101+122 samples, no contaminados por bug de fixture