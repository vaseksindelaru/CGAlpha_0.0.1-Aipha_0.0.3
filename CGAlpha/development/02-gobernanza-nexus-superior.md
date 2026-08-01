—
type: development-note
project: CGAlpha
tags: [proyecto/cgalpha, development, governance, nexus-superior, s2]
created: 2026-07-27
source: verified-live-against-cloned-repo
confidence: alta
---

# 🏛️ Gobernanza Constitucional — NEXUS_SUPERIOR.md

> Documento de gobernanza verificado en vivo contra el repositorio clonado.
> Vivo en: `documentation/NEXUS_SUPERIOR.md`
> **No** es un ADR — los ADRs documentan decisiones puntuales; este documento define el ciclo de vida completo por artefacto.

## Ciclo de vida formal por artefacto

```
ANOMALY → INCUBATION → MATURITY → QUARANTINE_GATE → READY_FOR_CODEX
  → EXECUTING → IMPLEMENTED → EVOLUTIONARY_DEBT → RECONSTRUCTION → LIBRARY
```

## Tabla de prioridades P0-P9 (completa)

| Prioridad | Componente | Estado | Brief |
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

> **Nota de honestidad**: QUARANTINE_GATE y READY_FOR_CODEX están marcados 🟡 SIMULADO en la tabla, pero la verificación en vivo revela que esto va más allá de "parcialmente automatizado".

### QUARANTINE_GATE y READY_FOR_CODEX — verificación en vivo

- **Cero archivos .py** en todo el repo contienen las cadenas `QUARANTINE_GATE` o `READY_FOR_CODEX`. No es que estén parcialmente codificados — no hay código que los implemente.
- Lo que sí existe es el **checklist manual** (§9 de NEXUS_SUPERIOR.md):

Concepto | Cómo se cumple hoy (textual de NEXUS_SUPERIOR.md)
---|---
QUARANTINE_GATE | Ruta C (`LILA_ROUTING_PROMPT.md`) + **checklist manual** contra §3 (verdades inmutables) antes de aprobar ejecución. Sin código que lo enforce.
READY_FOR_CODEX | El orden de §4 (P1→P10) es la cola. No hay colisiones porque solo un componente está `EXECUTING` a la vez (regla de inicio §4). Sin código que lo enforce.

**En la práctica**: no hay ningún código que impida ejecutar algo que contradiga las verdades inmutables de §3, ni ningún código que impida que dos componentes se ejecuten en paralelo violando la regla de "uno a la vez". Ambas protecciones dependen enteramente de que quien abre el ticket (humano o Lila) siga el checklist manualmente. Es una disciplina documentada y bien especificada — no un descuido — pero es disciplina, no enforcement. Si alguien salta el checklist, nada en el código lo detiene.

> El conjunto completo ("AlphaLab", con QUARANTINE_GATE + READY_FOR_CODEX + resurrección automática) está marcado ❌ NO EXISTE — es "arquitectura objetivo, mismo nivel que el 'Eco Eterno' del Harness" (aspiracional, al mismo nivel que otras cosas todavía no construidas).

## ¿Qué significa en la práctica?

P1 (Oracle v6) es la máxima prioridad activa del proyecto. Si el gate de seguridad que debería protegerlo está completamente desenchufado del código (solo checklist manual), esto es información operativa real sobre el riesgo de seguir trabajando en P1 sin saber cuánto de esa protección es disciplina documentada vs. enforcement automático.

## ADRs vs NEXUS_SUPERIOR vs CRBs: qué es qué

| Tipo de doc | Qué documenta | Dónde vive | Ejemplo |
|---|---|---|---|
| ADR | Decisión puntual inmutable | `aipha_memory/identity/` | D-003: threshold 0.70 inmutable |
| NEXUS_SUPERIOR | Ciclo de vida + prioridades P0-P9 + metodología | `documentation/` | Tabla P0-P9, esquema de fases |
| CRB | Component Reconstruction Brief — reconstrucción determinista | `cgalpha_v4/` y raíz | `oracle_v6_skeleton.py`, CRB_BinanceWebSocketManager_P3.md |
| Ticket de gobernanza | Ticket individual con fecha y checksum de verificación de archivos fantasma | `governance_log/` | RMU-EVO-TICKET-0001 |

## Diferencia clave con respecto a lo que yo (Hermes) documentaba

- **ADR**: "decidimos que X es inmutable" — sí, hay 11 ADRs viviendo ahí (más de lo que documentaba)
- **NEXUS_SUPERIOR**: "cómo se clasifica y ejecuta cualquier cambio" — esto es la capa de proceso que faltaba en nuestra documentación
- **CRB**: reconstrucción determinista de cada componente — esto es nuevo y no aparece en la crónica de mayo ni en la evaluación externa

## Lo que ninguno de los dos (ni la evaluación externa ni mi crónica de mayo) contemplaba

1. **Detección de archivos fantasma** — literalmente un mecanismo que verifica si los archivos citados como evidencia existen de verdad en Git antes de aceptar una afirmación (RMU-EVO-TICKET-0001 corrigió una MATURITY_5 a MATURITY_3 por esto)
2. **ciclo ANOMALY → LIBRARY** completo con 10 estados — no existe en ningún doc que yo tuviera
3. **cgalpha_v4/ como directorio raíz hermano de cgalpha_v3/** — el motor de producción coexiste con la capa de especificación/reconstrucción
4. **governance_log/** con tickets fechados hasta 24jun2026 — más reciente que la crónica de mayo (3 de mayo)

## ⚠️ Puntos que aún no he verificado con el mismo rigor

- No leí el 100% del framework de gobernanza (NEXUS_SUPERIOR.md completo, los 11 ADRs uno por uno)
- No tengo coverage % real de la suite completa actual — solo el 54.77% que el propio CRB autoreporta para Oracle
- El `pip install` parcial pudo haber alterado versiones de sklearn respecto a las que se usaron para entrenar los modelos serializados (vi `InconsistentVersionWarning`) — podría introducir falsos positivos/negativos en tests que carguen modelos `.joblib`
- Mi clon fue superficial (`git clone --depth 1`) — mi lectura de "último commit 7 julio" no prueba inactividad real

## Recomendación de almacenamiento en Obsidian

Esto no es código — es un documento de proceso/metodología. Guardarlo en `development/` (no en `learning/`) porque describe cómo se ejecuta el desarrollo, no cómo funciona el sistema en runtime. La relación con `learning/` es que las futuras clases magistrales pueden referenciar aquí el ciclo de vida como contexto de por qué ciertas decisiones de diseño existen.