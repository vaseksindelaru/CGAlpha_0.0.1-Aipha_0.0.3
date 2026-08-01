# Prompt para Evaluación de CGAlpha por LLM Externo

> **Para:** LLM evaluador (modelo con acceso completo al repo CGAlpha_0.0.1-Aipha_0.0.3)
> **Desde:** Operador humano + Tutor AI
> **Objetivo:** Evaluación independiente del estado real del proyecto CGAlpha siguiendo el plan P1-P9 del NEXUS_SUPERIOR.md
> **Acceso requerido:** Repo completo en `/home/vaclav/CGAlpha_0.0.1-Aipha_0.0.3/`

---

## Contexto Mínimo Obligatorio (Leer ANTES de evaluar)

### 1. Documento de Gobernanza Principal
**`/documentation/NEXUS_SUPERIOR.md`** — Lee completo. Es el **punto de partida y estado reclamado** para:
- Plan P1-P9 (§4)
- Verdades inmutables (§3, tabla D-XXX)
- Grafo de dependencias (§2)
- Reglas de gobernanza (§9-§10)
- Estado de cada componente (§5)

> **Principio rector:** El código, los tests y el git son la verdad. NEXUS_SUPERIOR.md es el estado *reclamado* — tu trabajo es verificar cada afirmación contra código, tests y git, no confirmar el documento.

### 2. Verificación de Versión (OBLIGATORIO antes de empezar)
```bash
cd /home/vaclav/CGAlpha_0.0.1-Aipha_0.0.3
grep "NEXUS SUPERIOR v" documentation/NEXUS_SUPERIOR.md
git fetch origin && git status
git log origin/main --oneline -5
```
**No evalúes si:**
- La versión en el archivo no coincide con la que el operador dice que es la actual
- `git status` muestra cambios sin commitear en archivos de gobernanza (NEXUS_SUPERIOR.md, EVO_TICKET_LOG.md, constitutional_events.jsonl) que "ya deberían estar sincronizados"

### 3. Documentos de Referencia Críticos
| Archivo | Qué contiene |
|---------|--------------|
| `documentation/NEXUS_SUPERIOR.md` | Plan maestro, verdades inmutables, orden P1-P9 |
| `documentation/EVO_TICKET_LOG.md` | Estado real de cada EVO-TICKET |
| `documentation/constitutional_events.jsonl` | Ledger constitucional (6 eventos) |
| `cgalpha_v4/RECONSTRUCTION_BRIEF.md` | Brief técnico de Oracle v6 (P1) |
| `cgalpha_v4/oracle_v6_skeleton.py` | Esqueleto de Oracle v6 |
| `cgalpha_v4/test_oracle_v6_skeleton.py` | Tests de contrato Oracle v6 |
| `CRB_*.md` en raíz | Component Reconstruction Briefs (P3, P4, P5) |
| `cgalpha_v3/` | Código real de producción |

---

## Tu Tarea: Evaluación Independiente P1-P9

> **Recordatorio:** El NEXUS_SUPERIOR.md es el *estado reclamado*. Cada afirmación en él debe verificarse contra código, tests y git. No des nada por hecho.

### Para CADA prioridad P1-P9, responde:

#### A. Estado Real vs Reportado
| Prioridad | Componente | Estado en NEXUS (§4) | Estado Real (tu hallazgo) | Gap |
|-----------|------------|----------------------|---------------------------|-----|
| P1 | Oracle v6 | 🔴 EN PROGRESO | ? | ? |
| P2 | CodeCraftSage v4 | 🟡 OPERATIVO | ? | ? |
| P3 | L2 Ring Buffer | 🟡 OPERATIVO | ? | ? |
| P4 | DeferredOutcomeMonitor | 🟡 OPERATIVO | ? | ? |
| P5 | TripleCoincidenceDetector | ✅ ESTABLE | ? | ? |
| P6 | EvolutionOrchestrator v5 | 🟡 ACUMULA BACKLOG | ? | ? |
| P6.5 | Chat de Lila (GUI) | 🔴 DESCONECTADO | ? | ? |
| P7 | MemoryPolicyEngine v4.1 | ✅ ESTABLE | ? | ? |
| P8 | LLMSwitcher v2 | ✅ ESTABLE | ? | ? |
| P9 | ShadowTrader | ✅ ESTABLE | ? | ? |
| P10 | Server/GUI | 🟡 MONOLÍTICO | ? | ? |

#### B. Verificación de Evidencia (por componente)
Para cada P1-P9, verifica y reporta:

1. **¿Existe el CRB?** (archivo `CRB_<Componente>_P<X>.md` en raíz)
2. **¿Tests de contrato existen y pasan?** (`pytest -xvs` sobre tests relevantes)
3. **¿Cobertura real medida?** (`pytest --cov=<modulo>` — no "no medido aún")
4. **¿EVO-TICKET correspondiente en `EVO_TICKET_LOG.md` coincide con estado real?**
4. **¿Decisiones D-XXX en §3 se respetan en el código actual?** (ej: D-014 acoplamiento temporal, D-011 interval_s=300, D-012 Oracle v6 encoding maps)
5. **¿Dependencias del grafo (§2) respetadas?** (ej: P5 no toca detector antes de P3 Ring Buffer)

> **Nota sobre cobertura:** "No medido aún" en el NEXUS no es una respuesta válida. Debes ejecutar `pytest --cov=<modulo>` y reportar el número real. Si el módulo no tiene tests, reporta 0%.

#### C. Hallazgos de Riesgo
Para cada P1-P9, lista:
- **Riesgo crítico no documentado** (algo que rompe si se toca sin saber)
- **Deuda técnica real** (vs la reportada en §5)
- **Decisiones D-XXX violadas o en riesgo**

---

### Evaluación Transversal (Obligatoria)

#### 1. Orden P1-P9 — ¿Es correcto?
- ¿Las dependencias reales (§2 grafo) soportan este orden?
- ¿Hay alguna P que debería moverse arriba/abajo?
- ¿P6.5 (Chat Lila) realmente requiere P6 Orchestrator v5 primero, o se puede paralelizar?

#### 2. Grafo de Dependencias (§2) — ¿Es fiel al código real?
Verifica aristas clave:
- `DeferredOutcomeMonitor` → `Oracle` (labels + zone_geometry)
- `TripleCoincidenceDetector` → `DeferredOutcomeMonitor` (zone_geometry)
- `BinanceWebSocketManager` Ring Buffer → `TripleCoincidenceDetector` (P3→P5)
- `AutoProposer` → `EvolutionOrchestrator` → `CodeCraftSage` (P2)
- `Server/GUI` depende de todos (P10 último)

#### 3. Verdades Inmutables (§3) — ¿Todas vigentes?
Verifica cada D-XXX contra código actual. Reporta cualquier violación.

#### 3. Cobertura y Tests — Estado Real
| Módulo | Cobertura Reportada | Cobertura Real (tu medición) | Tests Pasando | Tests Faltantes Críticos |
|--------|---------------------|-------------------------------|---------------|--------------------------|
| Oracle | 54.77% | ? | ? | _evaluate, save/load, MAE |
| DeferredOutcomeMonitor | "parcial" | ? | ? | _evaluate, tick, _flush_resolved |
| TripleCoincidenceDetector | "no medido" | ? | ? | |
| CodeCraftSage | "no medido" | ? | 9/9 passing | AST patching |
| L2 Ring Buffer | "no medido" | ? | 0 tests | time drift, Ring Buffer |
| EvolutionOrchestrator | "no medido" | ? | ? | escalation logic |

#### 4. Gobernanza — ¿Se está cumpliendo?
- `constitutional_events.jsonl` trackeado en git? (verificar `git log`)
- `EVO_TICKET_LOG.md` sincronizado con realidad?
- `RECONSTRUCTION_MAP_UPDATE` generado tras cada fase cerrada?
- `LLM Readability Check` (§10) hecho en cada cierre?

#### 5. P6.5 (Chat Lila) — ¿Realmente bloqueado por P6?
El NEXUS dice: "Prerequisito: Orchestrator v5 estable". ¿Es cierto? ¿O se puede conectar el endpoint `/api/assistant/chat` al Codex + Capa 0+1+Harness sin tocar Orchestrator v5?

#### 6. Normalización de métricas — OBLIGATORIO
Si comparas dos métricas de tamaños de muestra distintos (ej. cobertura de un módulo con 50 tests vs uno con 500, o concentración de aristas INFERRED con 341 aristas vs EXTRACTED con 5330), **no reportes el % crudo sin normalizar primero por tamaño de muestra**. La métrica correcta es la razón (promedio del top-N / promedio general) o un bootstrap submuestreando la muestra mayor al tamaño de la menor. Si no normalizas, el % crudo siempre se verá más concentrado en la muestra más chica, creando falsos "artefactos" o falsas "distribuciones uniformes". Reporta ambas: el % crudo y la métrica normalizada.

---

### 4. Decisiones Técnicas Pendientes (de §5)
Reporta estado real de cada una:
| Issue | Componente | Estado Real | Bloquea a |
|-------|------------|-------------|-----------|
| Fricción económica (labels puros sin slippage) | P4 | ? | P4, P9 |
| Acoplamiento temporal D-014 (ε=200ms) | P4/P3 | ? | P4, P5 |
| OracleRegressor_MAE 0% cobertura | P1 Fase A | ? | P1, P9 |
| LabelEncoder no-determinista | P1 Fase A | ? | P1 |
| Features estáticas vs dinámicas (Ring Buffer) | P1 Fase B / P3 | ? | P1, P5 |
| Server/GUI monolítico 2329 líneas | P10 | ? | — |

---

## Formato de Entrega

Entrega un **único archivo Markdown** estructurado así:

```markdown
# Evaluación Independiente CGAlpha — [Fecha] — [Tu ID/Modelo]

## Resumen Ejecutivo (máx 200 palabras)
- Estado general: [verde/amarillo/rojo]
- Gap mayor entre NEXUS y realidad: [una línea]
- Riesgo #1 no documentado: [una línea]

## Tabla P1-P10 (sección A completa)

## Por Componente — Evidencia y Gaps (sección B)

## Evaluación Transversal (secciones 1-5 completas)

## Veredicto sobre el Plan P1-P9
- [ ] Correcto y accionable
- [ ] Necesita reordenamiento: [detalle]
- [ ] Faltan prioridades: [cuáles]
- [ ] Sobran prioridades: [cuáles]

## Riesgos Críticos No Documentados (mínimo 3)

## Recomendaciones Concretas (accionables, priorizadas)

## Preguntas al Operador (si necesitas aclarar algo para cerrar)
```

---

## Instrucciones de Ejecución

1. **Clona/accede al repo** en `/home/vaclav/CGAlpha_0.0.1-Aipha_0.0.3/`
2. **Ejecuta la verificación de versión** (paso 2 arriba)
3. **Lee NEXUS_SUPERIOR.md completo** antes de tocar código
4. **Ejecuta tests y mide cobertura** para cada módulo P1-P9
5. **Verifica git status + log** para gobernanza
6. **Escribe el reporte** en el formato exacto arriba
7. **Guárdalo como** `EVALUACION_EXTERNA_<fecha>_<tu_id>.md` en la raíz del repo

---

## Notas para el Evaluador

- **No asumas** que lo que dice el NEXUS es verdad. Verifica contra código, tests, git.
- **No propongas soluciones** salvo en "Recomendaciones Concretas". Tu rol es **evaluar**, no arreglar.
- **Si falta evidencia** para cerrar un punto, dilo explícitamente en "Preguntas al Operador".
- **El operador humano** (Vaclav) está disponible para resolver dudas de contexto, pero **tú tienes acceso completo al repo** — úsalo.
- **Tiempo estimado:** 2-4 horas de trabajo real con acceso al repo.

---

## Acceso al Repo

El repo está en: `/home/vaclav/CGAlpha_0.0.1-Aipha_0.0.3/`

Estructura clave:
```
CGAlpha_0.0.1-Aipha_0.0.3/
├── documentation/
│   ├── NEXUS_SUPERIOR.md          # ← LEER PRIMERO
│   ├── EVO_TICKET_LOG.md
│   └── constitutional_events.jsonl
├── cgalpha_v4/
│   ├── RECONSTRUCTION_BRIEF.md
│   ├── oracle_v6_skeleton.py
│   └── test_oracle_v6_skeleton.py
├── CRB_*.md                       # Briefs de componentes
├── cgalpha_v3/                    # Código producción
│   ├── lila/llm/oracle.py
│   ├── lila/codecraft_sage.py
│   ├── lila/evolution_orchestrator.py
│   ├── infrastructure/signal_detector/triple_coincidence.py
│   ├── infrastructure/binance_websocket_manager.py
│   ├── domain/deferred_outcome_monitor.py
│   ├── gui/server.py
│   └── ...
├── tests/                         # Tests raíz + pytest
├── EVO_TICKET_LOG.md
├── constitutional_events.jsonl
└── NEXUS_SUPERIOR.md (copia en raíz también)
```

---

**¡Éxitos! La evaluación honesta e independiente es lo que más valor tiene para este proyecto.**