<p align="center">
  <img src="../logo.png" alt="cgAlpha_0.0.1" width="160"/>
</p>

<h1 align="center">cgAlpha_0.0.1 — White Paper</h1>
<p align="center"><em>Causal Graph Alpha · Documento vivo mantenido por Lila</em></p>
<p align="center"><em>Última actualización: 19 de abril de 2026 · Versión: genesis</em></p>

---

## 1. Qué es cgAlpha_0.0.1

cgAlpha (Causal Graph Alpha) es un sistema de trading algorítmico diseñado para operar BTCUSDT en Binance. Su objetivo no es maximizar beneficios a corto plazo — es construir un sistema que **aprenda de sus propios errores y mejore autónomamente** bajo supervisión humana.

### Principios fundacionales

1. **Evidencia sobre opinión:** Cada decisión del sistema se basa en datos Out-of-Sample (OOS), nunca en la "intuición" del LLM.
2. **Autonomía gradual:** El sistema puede proponer mejoras. El humano aprueba o rechaza. Con evidencia acumulada, la autonomía se amplía.
3. **Honestidad radical:** Si algo no funciona, se documenta como bug con número, no se esconde.
4. **Determinismo primero:** Para decisiones factuales se usa código determinista (grep, AST). Los LLMs solo intervienen en análisis cualitativos.

## 2. Arquitectura actual

```
                    ┌─────────────────────────┐
                    │    FUENTE DE DATOS       │
                    │    Binance Vision API    │
                    │    BTCUSDT klines 5m     │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  DETECCIÓN DE SEÑALES    │
                    │  TripleCoincidenceDetector│
                    │  979 líneas             │
                    │                         │
                    │  Zonas de soporte/resis. │
                    │  → Retests monitoreados  │
                    │  → Features de micro-    │
                    │    estructura (VWAP,      │
                    │    OBI, CumDelta)        │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  ORÁCULO (ML)           │
                    │  OracleTrainer_v3        │
                    │  RandomForest            │
                    │  Meta-Labeling           │
                    │                         │
                    │  Estado: ⚠️ Funcional    │
                    │  con defectos (BUG 1-6) │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  EJECUCIÓN              │
                    │  ShadowTrader           │
                    │  DryRunOrderManager     │
                    │                         │
                    │  Modo: paper trading    │
                    │  Registro: bridge.jsonl │
                    └────────────┬────────────┘
                                 │
                                 ▼
              ┌──────────────────────────────────────┐
              │        CANAL DE EVOLUCIÓN            │
              │                                      │
              │  AutoProposer → Orchestrator v4 →    │
              │  CodeCraftSage                       │
              │                                      │
              │  3 categorías de propuestas:          │
              │  Cat.1: Automática (parámetros)      │
              │  Cat.2: Semi-automática (aprobación)  │
              │  Cat.3: Supervisada (sesión humana)   │
              │                                      │
              │  Estado: 🔨 En construcción           │
              └──────────────────────────────────────┘
```

### Componentes y estado

| Componente | Fichero principal | Líneas | Estado |
|---|---|---|---|
| TripleCoincidenceDetector | `infrastructure/signal_detector/triple_coincidence.py` | 979 | ✅ Operativo |
| OracleTrainer_v3 | `lila/llm/oracle.py` | 314 | ⚠️ 6 bugs documentados |
| ShadowTrader | `trading/shadow_trader.py` | ~200 | ✅ Operativo |
| Pipeline | `application/pipeline.py` | 291 | ✅ Operativo (sin retrain) |
| AutoProposer | `lila/llm/proposer.py` | ~140 | ✅ Genera propuestas |
| ChangeProposer | `application/change_proposer.py` | 93 | ⚠️ Desconectado |
| CodeCraftSage | `lila/codecraft_sage.py` | 190 | ⚠️ Desconectado |
| ExperimentRunner | `application/experiment_runner.py` | 507 | ⚠️ Desconectado |
| EvolutionOrchestrator v4 | `lila/evolution_orchestrator.py` | — | 🔨 Por construir |
| MemoryPolicyEngine | `learning/memory_policy.py` | 311 | ⚠️ Sin persistencia |

## 3. La Simple Foundation Strategy

cgAlpha_0.0.1 opera una única estrategia: la **Simple Foundation Strategy**.

### Pipeline operativo

1. **Detección de zonas:** El TripleCoincidenceDetector identifica zonas de soporte/resistencia usando key candles, zonas de acumulación y mini-tendencias.
2. **Monitoreo de retests:** Cuando el precio vuelve a una zona, se capturan features de microestructura en el punto exacto del retest.
3. **Predicción del Oracle:** El modelo RandomForest (meta-labeling) evalúa si el retest será exitoso (BOUNCE o BREAKOUT).
4. **Ejecución shadow:** Si el Oracle aprueba con suficiente confianza, ShadowTrader registra la operación en `bridge.jsonl` (sin ejecución real).

### Parámetros principales

| Parámetro | Valor actual | Rango seguro | Efecto |
|---|---|---|---|
| `volume_threshold` | 1.2 | 0.8 – 2.0 | Filtro de zonas por volumen relativo |
| `quality_threshold` | 0.45 | 0.3 – 0.7 | Calidad mínima de señal |
| `min_oracle_confidence` | 0.70 | 0.60 – 0.90 | Confianza mínima para ejecutar |
| `zone_distance_candles` | 10 | 5 – 30 | Distancia entre zonas en velas |

> ⚠️ **Nota honesta:** El Sharpe de 1.13 reportado en documentación anterior (NORTH_STAR) no es verificable con datos OOS reales. No se ha completado un ciclo de validación walk-forward con el Oracle entrenado.

## 4. El canal de evolución

### Estado actual: Bootstrap en progreso

El canal de evolución es el sistema que permite a cgAlpha mejorarse a sí mismo. Está diseñado pero no implementado todavía. La especificación completa está en el [Prompt Fundacional](LILA_V4_PROMPT_FUNDACIONAL.md), secciones §3–§4.

### Las 3 categorías

| Categoría | Supervisión | Ejemplo | Tiempo estimado |
|---|---|---|---|
| **Cat.1 — Automática** | Ninguna (tests como barrera) | Ajustar `volume_threshold` de 1.2 → 1.3 | Segundos |
| **Cat.2 — Semi-automática** | Aprobación vía GUI | Añadir feature al Oracle | Minutos |
| **Cat.3 — Supervisada** | Sesión humana completa | Crear nueva herramienta | Horas |

### Pasos del bootstrap

1. ✅ Prompt Fundacional escrito (§0–§8)
2. 🔨 ACCIÓN 1: IDENTITY memory + disk reload
3. ⬜ ACCIÓN 2: LLM Switcher
4. ⬜ ACCIÓN 3: Orchestrator v4

## 5. Lecciones aprendidas

*Esta sección se actualiza automáticamente después de cada reflexión crítica validada (§6).*

### Genesis — 19 abril 2026

Al construir el Prompt Fundacional, se identificaron y documentaron:
- **8 bugs funcionales** en el Oracle y la GUI (BUG-1 a BUG-8)
- **4 islas desconectadas** (AutoProposer, CodeCraftSage, ChangeProposer, ExperimentRunner)
- **57 correcciones** al propio prompt (C1–C57) — incluyendo 7 métodos fantasma y dependencias de rama no resueltas

La lección principal: **construir componentes capaces no es suficiente. Conectarlos es lo que crea un sistema.**

## 6. Changelog

| Fecha | Cat. | Cambio | Resultado |
|---|---|---|---|
| 2026-04-19 | — | Prompt Fundacional §0–§8 creado | 3113 líneas, 57 correcciones |
| 2026-04-19 | — | White paper genesis | Primera versión |

*Entradas futuras se añaden automáticamente por el Orchestrator.*

## 7. Glosario

| Término | Definición |
|---|---|
| **bridge.jsonl** | Log de trades shadow: señal + ejecución + outcome |
| **Cat.1/2/3** | Categorías de propuesta de evolución (auto/semi/supervisada) |
| **CodeCraftSage** | Motor que parchea código, corre tests, y commitea en git |
| **drift** | Degradación del rendimiento del modelo detectada por AutoProposer |
| **evolution_log.jsonl** | Log de cambios al sistema (propuestas + resultado) |
| **IDENTITY** | Nivel 5 de memoria: inmutable, contiene el mantra |
| **Lila** | IA constructora de cgAlpha. Ejecuta prompts, propone mejoras |
| **mantra** | El Prompt Fundacional guardado en IDENTITY |
| **meta-labeling** | Técnica ML: el Oracle predice si una señal ya detectada tendrá éxito |
| **OOS** | Out-of-Sample: datos no vistos durante entrenamiento |
| **Oracle** | Modelo RandomForest que filtra señales por probabilidad |
| **Orchestrator** | Componente central que clasifica y enruta propuestas de evolución |
| **reflexión crítica** | Observación de Lila que cuestiona una parte del mantra con evidencia |
| **retest** | Cuando el precio vuelve a tocar una zona de soporte/resistencia |
| **ShadowTrader** | Ejecutor de trades en modo papel (sin dinero real) |
| **TechnicalSpec** | Dataclass que define un cambio concreto al código |
| **Triple Coincidence** | Detector de zonas basado en 3 confluencias técnicas |
| **walk-forward** | Validación temporal: entrenar en pasado, evaluar en futuro no visto |
| **zona** | Nivel de precio donde se detectó soporte o resistencia |

---

<p align="center">
  <em>Este documento es mantenido por Lila como parte de la orden permanente §2.6.</em><br/>
  <em>Se actualiza después de cada evolución del sistema.</em><br/>
  <em>cgAlpha_0.0.1 · Causal Graph Alpha</em>
</p>
