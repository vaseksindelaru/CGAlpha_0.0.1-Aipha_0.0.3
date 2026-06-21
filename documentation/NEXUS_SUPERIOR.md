# NEXUS SUPERIOR — cgAlpha_0.0.1
## Mapa de Reconstrucción por Componentes

```
CLASIFICACIÓN : Documento estratégico de reconstrucción
VERSIÓN       : 0.1 — Esqueleto inicial (2026-06-08)
ESTADO        : ACTIVO — se actualiza tras cada CRB completado
DE            : Operador + Lila (Claude Sonnet 4.6)
PARA          : Modelo LLM que orquestará la mejora ambiciosa
                del sistema completo
PROPÓSITO     : Guiar una reconstrucción parcial y ordenada
                sin el costo ni el riesgo de reescribir todo de golpe
```

---

## §0 — Para el modelo que lee esto

Eres un LLM más potente que el que construyó cgAlpha_0.0.1.
Tienes más contexto, más capacidad de razonamiento, y probablemente
mejor comprensión de microestructura financiera y ML.

Lo que tienes delante NO es una petición de reescritura total.
Es un mapa que te dice: qué existe, qué funciona, qué está roto,
en qué orden atacar, y qué no debes tocar bajo ninguna circunstancia.

**Paso 0 — OBLIGATORIO antes de leer nada más:**

```
Verifica que ESTE archivo es la versión más reciente.
  grep "Nexus Superior v0\." <esta_ruta>
Si la versión que estás leyendo es menor a la última conocida por
el operador humano, DETENTE y pide la versión actualizada antes
de continuar. NO trabajes sobre una copia desactualizada del Nexus
— la numeración D-XXX puede colisionar entre versiones (ocurrió:
sesión Oracle v6 Fase A asignó "D-008" a una decisión nueva sin
saber que D-008 ya existía en la versión autoritativa, causando
renumeración posterior a D-012).
```

**Tu protocolo de lectura antes de actuar:**

```
1. Leer §1 (visión del sistema en 2 minutos)
2. Leer §3 (verdades inmutables — nunca violarlas)
3. Leer §9 (capa de gobernanza constitucional — cómo dejas huellas)
4. Elegir el componente de mayor prioridad según §4
5. Leer la ficha de ese componente en §5
6. Leer el Component Brief (CRB) específico si existe
   y el EVO-TICKET correspondiente en EVO_TICKET_LOG.md
   — verificar que el estado del ticket no esté desactualizado
   (ocurrió: EVO-TICKET-0004 reportado como READY_FOR_CODEX en
   una copia local cuando ya estaba IMPLEMENTED)
7. Solo entonces, comenzar a leer el código de ese componente
```

No leas oracle.py antes de leer esta guía.
No propongas nada antes de entender el grafo de dependencias.
La historia de 8+ meses de decisiones está en este documento y en el Codex.
No la repitas desde cero.

**Antes de cerrar tu sesión de trabajo**, sin excepción:
generar el `RECONSTRUCTION_MAP_UPDATE` correspondiente (§9), incluyendo
el **LLM Readability Check** (§10 / D-010) — tres preguntas respondidas
como si fueras un modelo con 8k de contexto y sin memoria de la sesión.
Una fase sin ese artefacto NO está completa.

---

## §1 — Mapa del sistema (visión de 500 metros)

cgAlpha_0.0.1 es un sistema de trading algorítmico que aprende y se mejora
a sí mismo de forma gobernada. Operar en producción significa:

```
DATOS EN VIVO
BinanceWebSocketManager
  │ velas 5m + book @depth20@100ms
  ▼
DETECCIÓN DE SEÑALES
TripleCoincidenceDetector
  │ zonas de soporte/resistencia + retests
  ▼
CAPTURA DE MICROESTRUCTURA
DeferredOutcomeMonitor
  │ features L2 + label diferido (BOUNCE_STRONG/WEAK/BREAKOUT)
  ▼
PREDICCIÓN
Oracle (OracleTrainer_v3 + OracleRegressor_MAE)
  │ P(BOUNCE_STRONG) >= threshold → EXECUTE
  ▼
EJECUCIÓN PAPER
ShadowTrader → bridge.jsonl
  │ registra trade, MFE, MAE
  ▼
APRENDIZAJE
AutoProposer → EvolutionOrchestrator → CodeCraftSage
  │ detecta drift → clasifica propuesta → parchea código → tests → commit
  ▼
MEMORIA
MemoryPolicyEngine (7 niveles: RAW → IDENTITY)
  │ persiste decisiones, Codex, reflexiones críticas
  ▼
OBSERVABILIDAD
Server/GUI (Flask + Control Room)
```

**Estado actual del ciclo completo:** funcional end-to-end.
bridge.jsonl recibe datos reales. El canal de evolución ejecuta
propuestas Cat.1 automáticamente. El Oracle tiene OOS honesto de 0.68.

**La limitación central:** el Oracle aprende con features estáticas
(snapshot del momento del retest) en lugar de features dinámicas
(perfil temporal de 30 segundos). Eso es el techo actual del sistema.

---

## §2 — Grafo de dependencias

```
                         [Binance WS]
                              │
                    ┌─────────┴──────────┐
                    ▼                    ▼
          [TripleCoincidence]    [BWS L2 Ring Buffer]
                    │                    │
                    └─────────┬──────────┘
                              ▼
                   [DeferredOutcomeMonitor]
                         │          │
                   labels │          │ zone_geometry
                          ▼          ▼
                        [Oracle] ←──────────────
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
        [ShadowTrader] [bridge.jsonl] [MemoryPolicyEngine]
              │                            │
              ▼                            ▼
        [AutoProposer]              [Codex / IDENTITY]
              │
              ▼
     [EvolutionOrchestrator]
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
[Cat.1]    [Cat.2]   [Cat.3]
    │         │         │
    └────┬────┘         │
         ▼              ▼
  [CodeCraftSage]  [Sesión humana]
         │
         ▼
    [LLMSwitcher]
         │
    ┌────┴────┐
    ▼         ▼
 [Ollama] [Cloud LLM]
```

**Reglas del grafo:**

- Cualquier cambio en `DeferredOutcomeMonitor` afecta la calidad de los labels
  del Oracle. Cambiar DeferredOutcomeMonitor invalida el dataset actual.
- Cualquier cambio en `TripleCoincidenceDetector` puede cambiar cuántas zonas
  se detectan y con qué geometría — afecta directo al Oracle.
- `MemoryPolicyEngine` y `signal.py` son la capa más profunda.
  Un error aquí rompe la identidad de Lila.
- `Server/GUI` depende de todos. Cambiar el server es Cat.3 siempre.

---

## §3 — Registro de verdades inmutables

Estas decisiones tienen evidencia verificada. No se cuestionan sin
datos nuevos superiores. Si tu razonamiento contradice alguna,
primero verifica que no hayas pasado por alto el Codex.

| ID | Decisión | Valor | Fuente |
|---|---|---|---|
| D-001 | zigzag_threshold | 0.0018 (0.18%) | P75 real=0.1553%, commit a5ed77a |
| D-002 | outcome_lookahead | 10 velas (→ adaptativo en v6) | Debilidad #5 análisis estructural |
| D-003 | OOS mínimo para A/B | 30 muestras | Set A tenía 7 muestras en 2026-06-01 |
| D-004 | fingerprint dedup | sin zone_direction | B-008 v2, commit c19f7d6 |
| D-005 | INCONCLUSIVE | excluir del training | DeferredOutcomeMonitor decisión |
| D-006 | ATR de detección | capturar cuando se forma la zona, NO en el retest | commit 59b87ab |
| D-007 | OracleRegressor_MAE | MANTENER (no reemplazar en Fase A) | 0% cobertura, decisión conservadora |
| D-008 | Cierre de fase de reconstrucción | requiere RECONSTRUCTION_MAP_UPDATE | Apéndice — Causal Closure, sesión 2026-06-12 |
| D-009 | Historia constitucional | requiere entrada en constitutional_events.jsonl (vocabulario reducido a 6 eventos, ver §9) | Propuesta operador, sesión 2026-06-12, aceptada con ajustes |
| D-010 | Cognitive Portability | toda reconstrucción debe ser inteligible por modelo de capacidad inferior sin acceso a historial de sesión — test de 3 preguntas, ver §10 | Sesión 2026-06-14 |
| D-011 | live_adapter.py interval_s | =300 (5min) es el timeframe calibrado y operativo. Cambiarlo requiere ADR + recalibración de TODOS los thresholds dependientes (lookback_candles, retest_timeout_bars, zigzag_threshold, key_candle thresholds). NUNCA cambiar como ajuste aislado. | EVO-TICKET-0006, sesión 2026-06-20 — origen: default "MVP demo" sin calibrar (12 abr) causó 4 rondas de investigación |
| D-012 | Oracle v6 ENCODING_MAPS | Mapeo determinista fijo: `regime`={UNKNOWN:0, LATERAL:1, TREND:2, HIGH_VOL:3}, `direction`={UNKNOWN:0, BULLISH:1, BEARISH:2}, `delta_divergence`={UNKNOWN:0, NEUTRAL:1, BULLISH:2, BEARISH:3}. UNKNOWN=0 en toda categoría (fallback seguro). Valores uppercase antes del lookup. Inmutable — cambiar requiere nuevo D-ID + ADR + re-entrenamiento de todos los modelos. Implementado en `cgalpha_v4/oracle_v6_skeleton.py`. Renumerado desde "D-008" local (colisión con D-008 canónico = requisito de RMU). | ADR-EVO-TICKET-0001-1-encoding-determinista, EVO-TICKET-0001 Fase A, sesión 2026-06-21 |

**Módulos protegidos — Cat.3 obligatorio para cualquier cambio:**

```python
PROTECTED_MODULES = [
    "cgalpha_v3/learning/memory_policy.py",
    "cgalpha_v3/domain/models/signal.py",        # MemoryLevel enum
    "cgalpha_v3/lila/evolution_orchestrator.py",
    "cgalpha_v3/gui/server.py",
    "cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py",
    "cgalpha_v3/domain/deferred_outcome_monitor.py",
    "LILA_V4_PROMPT_FUNDACIONAL.md",
    "cronica_desarrollo_cgAlpha.md",
]

PROTECTED_FUNCTIONS = {
    # Función → dónde realmente pertenece
    "compute_adaptive_zigzag_threshold": "MiniTrendDetector",
    "adaptive_lookahead":                "DeferredOutcomeMonitor",
}
```

---

## §4 — Orden de ataque recomendado

La prioridad no es arbitraria. Sigue la lógica:
**primero lo que desbloquea más componentes aguas abajo.**

```
PRIORIDAD   COMPONENTE                    ESTADO ACTUAL       BRIEF
─────────────────────────────────────────────────────────────────────
P0 META     Routing System (Nexus)        ✅ OPERATIVO        Este doc
P0 META     Codex (7 entradas)            ✅ INGESTADO        CODEX_ENTRIES_DRAFT.md

P1          Oracle v6                     🔴 EN PROGRESO      RECONSTRUCTION_BRIEF.md
            Razón: mayor impacto medible, OOS 0.68,
                   cobertura 54.77%, bloqueante para P2
            Ticket: EVO-TICKET-0001 (Fase A) / EVO-TICKET-0002 (Fase B)
                   en EVO_TICKET_LOG.md
            Entregable adicional obligatorio al cierre de cada fase:
                   RECONSTRUCTION_MAP_UPDATE (+ ADRs si hubo
                   decisiones con alternativas) — ver §9

P2          CodeCraftSage v4              🟡 OPERATIVO        [CRB PENDIENTE]
            Razón: el canal de evolución tiene techo bajo
                   mientras solo pueda parchear con regex.
                   AST-based patching desbloquea mejoras complejas.

P3          L2 Ring Buffer                🟡 PARCIAL          [CRB PENDIENTE]
            (BinanceWebSocketManager)
            Razón: prerrequisito directo para Oracle Fase B.
                   Sin Ring Buffer de 30s, las features dinámicas
                   del Oracle son imposibles.

P4          DeferredOutcomeMonitor        🟡 OPERATIVO        [CRB PENDIENTE]
            Fase Bridge (etiquetado enriquecido)
            Razón: prerrequisito para Oracle Fase B.
                   Etiquetado terciario + lookahead adaptativo
                   son mejoras de calidad de datos.

P5          TripleCoincidenceDetector     ✅ ESTABLE          [CRB PENDIENTE]
            (integración L2)
            Razón: necesita recibir el Ring Buffer de P3.
                   No se toca antes de que P3 esté estable.

P6          EvolutionOrchestrator v5      🟡 ACUMULA BACKLOG  [CRB PENDIENTE]
            Razón: el backlog de propuestas crece.
                   Mejorar la lógica de escalada Cat.1→2→3.
                   Baja urgencia mientras P1-P4 están activos.

P6.5        Chat de Lila (GUI)             🔴 DESCONECTADO     [CRB PENDIENTE]
            Razón: endpoint /api/assistant/chat usa string estático
                   en lugar de Capa0+Capa1+Harness del Codex.
                   Bloquea el "Eco Eterno" del Harness (B-008 Acto VIII).
                   Prerequisito: Orchestrator v5 estable.

P7          MemoryPolicyEngine v4.1       ✅ ESTABLE          [CRB PENDIENTE]
            Razón: funciona bien. Solo mejoras menores
                   (búsqueda semántica en v4.1 como futura upgrade).

P8          LLMSwitcher v2                ✅ ESTABLE          [CRB PENDIENTE]
            Razón: opera con Ollama + fallback. Bajo riesgo.

P9          ShadowTrader                  ✅ ESTABLE          [CRB PENDIENTE]
            Razón: escribe en bridge.jsonl correctamente.
                   La mejora MAE regressor depende de Oracle P1.

P10         Server/GUI                    🟡 MONOLÍTICO       [CRB PENDIENTE]
            Razón: 2329 líneas en un solo archivo.
                   Funciona. La deuda técnica es real pero
                   no bloquea nada crítico ahora.
```

**Regla de inicio:** No empieces P2 hasta que P1 Fase A esté en producción
estable 48h. No empieces P3 hasta que P1 Fase B esté especificada.
El orden existe por dependencias reales, no por preferencia.

---

## §5 — Fichas por componente

### 5.1 Oracle — `cgalpha_v3/lila/llm/oracle.py`

```
PROPÓSITO   : Meta-labeling. Predice si una señal ya detectada
              tendrá éxito (BOUNCE_STRONG/WEAK/BREAKOUT).
              NO detecta señales ni calcula parámetros de otros módulos.

ESTADO      : 🔴 EN RECONSTRUCCIÓN ACTIVA
COBERTURA   : 54.77% (verificado 2026-06-07)
OOS ACTUAL  : 0.68 (Set B champion, 2026-06-01)
DATASET     : 207 filas limpias (post B-008 v2)

INTERFACES
  Recibe de : TripleCoincidenceDetector (zone_geometry, clearance)
               DeferredOutcomeMonitor (outcome labels)
               BinanceWebSocketManager (l2_snapshot_at_touch)
  Entrega a : ShadowTrader (OraclePrediction)
               EvolutionOrchestrator (métricas de drift)

ISSUES CONOCIDOS
  #1 FEATURE_COLS usa nombres legacy (*_at_retest)  → Oracle v6 Fase A
  #2 LabelEncoder no-determinista                   → Oracle v6 Fase A
  #3 OracleRegressor_MAE 0% cobertura               → Oracle v6 Fase A
  #4 save/load/is_placeholder 0% cobertura          → Oracle v6 Fase A
  #5 Sin features dinámicas (Ring Buffer)           → Oracle v6 Fase B
  #6 Sin walk-forward (solo split estático)         → Oracle v6 Fase B

BRIEF EXISTENTE : cgalpha_v4/RECONSTRUCTION_BRIEF.md (v1.1)
SKELETON        : cgalpha_v4/oracle_v6_skeleton.py
TESTS CONTRATO  : cgalpha_v4/test_oracle_v6_skeleton.py
PRIORIDAD       : P1 — ACTIVO
```

---

### 5.2 CodeCraftSage — `cgalpha_v3/lila/codecraft_sage.py`

```
PROPÓSITO   : Motor de ejecución de cambios al código.
              Recibe TechnicalSpec, aplica parche, corre tests,
              hace commit en feature branch o revierte.

ESTADO      : 🟡 OPERATIVO CON LIMITACIONES
COBERTURA   : [NO MEDIDA AÚN — pendiente]
TESTS       : 9/9 passing (test_codecraft_sage.py)

LIMITACIÓN CRÍTICA
  Usa regex para localizar el código a cambiar.
  Archivos > ~100 líneas tienen riesgo de falso positivo.
  Archivos > 8k tokens (Qwen 2.5:3b context) pueden truncarse.
  SOLUCIÓN: AST-based patching (CRB pendiente para v4)

INTERFACES
  Recibe de : EvolutionOrchestrator (TechnicalSpec + aprobación)
               LLMSwitcher (proveedor LLM para análisis)
  Entrega a : EvolutionOrchestrator (ExecutionResult)
               Git (commits en feature branch)

ISSUES CONOCIDOS
  #1 Regex frágil en archivos grandes         → CodeCraftSage v4
  #2 Sin AST-based patching para múltiples    → CodeCraftSage v4
     puntos de cambio simultáneos
  #3 No verifica si el archivo fue truncado   → CodeCraftSage v4
     por el LLM antes de escribir

BRIEF EXISTENTE : NO (pendiente crear CRB)
PRIORIDAD       : P2
```

---

### 5.3 TripleCoincidenceDetector — `cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py`

```
PROPÓSITO   : Detecta zonas de soporte/resistencia usando tres
              confluencias (key candle + accumulation + mini-trend).
              Monitorea retests y captura features en el momento
              exacto del toque.

ESTADO      : ✅ ESTABLE — PROTEGIDO
LÍNEAS      : ~979
COBERTURA   : [NO MEDIDA AÚN — pendiente]

MÓDULO PROTEGIDO: cambios = Cat.3 obligatorio

FUNCIONES CRÍTICAS QUE VIVEN AQUÍ (NO mover al Oracle):
  compute_adaptive_zigzag_threshold()  → parámetro del detector
  _determine_outcome()                 → con zone_top/zone_bottom (BUG-5 ✅)
  _check_retest()                      → captura features en retest

INTERFACES
  Recibe de : BinanceWebSocketManager (velas + ticks)
  Entrega a : DeferredOutcomeMonitor (zone_geometry, clearance)
               Oracle (via training samples)

ISSUES CONOCIDOS
  #1 No recibe el Ring Buffer de 30s todavía   → P3 prerequisito
  #2 zigzag_threshold hardcoded 0.0018         → adaptativo en v6
     (no cambiar sin recalibración con datos frescos)

BRIEF EXISTENTE : ✅ CRB_TripleCoincidenceDetector_P5.md
                  (creado 2026-06-21, sesión de mapeo post-EVO-0005/0006)
PRIORIDAD       : P5 (después de P3 Ring Buffer)
```

---

### 5.4 DeferredOutcomeMonitor — `cgalpha_v3/domain/deferred_outcome_monitor.py`

```
PROPÓSITO   : Asigna labels diferidos a los retests capturados.
              Espera outcome_lookahead_bars antes de clasificar.
              Produce BOUNCE_STRONG / BOUNCE_WEAK / BREAKOUT / INCONCLUSIVE.
              Elimina el fallback "return BOUNCE" por defecto (BUG-5 ✅).

ESTADO      : 🟡 OPERATIVO — PROTEGIDO — PENDIENTE FASE BRIDGE
COBERTURA   : [NO MEDIDA AÚN — pendiente]

MÓDULO PROTEGIDO: cambios = Cat.3 obligatorio

FUNCIONES CRÍTICAS QUE VIVEN AQUÍ (NO mover al Oracle):
  adaptive_lookahead(zone_width_atr)  → lookahead adaptativo
  _causal_fingerprint()               → sin zone_direction (B-008 v2 ✅)
  register_retest()                   → registra para etiquetado diferido
  tick(price, bar_closed)             → evalúa resolución en cada tick

ISSUES CONOCIDOS / FASE BRIDGE PENDIENTE
  #1 Sin buffer temporal L2 (Ring Buffer)       → P3 prerequisito
  #2 lookahead fijo = 10 velas todavía          → adaptativo en Fase Bridge
     (max(5, min(20, int(5 + zone_width_atr*3))))
  #3 Etiquetado terciario implementado pero     → Fase Bridge valida
     sin datos suficientes para calibrar

BRIEF EXISTENTE : NO (pendiente crear CRB)
PRIORIDAD       : P4 (después de P3 Ring Buffer)
```

---

### 5.5 EvolutionOrchestrator — `cgalpha_v3/lila/evolution_orchestrator.py`

```
PROPÓSITO   : Clasifica propuestas de mejora en Cat.1/2/3.
              Cat.1: ejecuta automáticamente.
              Cat.2: encola para aprobación humana.
              Cat.3: requiere sesión humana completa.

ESTADO      : 🟡 OPERATIVO — ACUMULA BACKLOG
COBERTURA   : [NO MEDIDA AÚN — pendiente]
TESTS       : 19/19 passing (test_orchestrator_v4.py)
              (2 tests pre-existentes en Cat.1 fallando — pre-existentes)

MÓDULO PROTEGIDO: cambios = Cat.3 obligatorio

INTERFACES
  Recibe de : AutoProposer (TechnicalSpec)
               ChangeProposer (Proposal via adaptador)
               ExperimentRunner (ExperimentResult)
               GUI (aprobación/rechazo humano)
  Entrega a : CodeCraftSage (TechnicalSpec aprobada)
               MemoryPolicyEngine (proposals pendientes)
               evolution_log.jsonl (historial)

ISSUES CONOCIDOS
  #1 Backlog de propuestas duplicadas crece    → cooldown §4.3 activo
     AutoProposer genera ~10/hora sobre        pero necesita ajuste
     mismo atributo
  #2 _count_recent_modifications() lee         → funcional
     evolution_log.jsonl correctamente
  #3 Island Bridge conecta ChangeProposer y    → funcional
     ExperimentRunner

BRIEF EXISTENTE : NO (pendiente crear CRB)
PRIORIDAD       : P6
```

---

### 5.6 MemoryPolicyEngine — `cgalpha_v3/learning/memory_policy.py`

```
PROPÓSITO   : Persistencia de conocimiento en 7 niveles con TTL,
              aprobadores, y protección de degradación por régimen.
              Nivel 5 (IDENTITY): inmutable sin aprobación humana.

ESTADO      : ✅ ESTABLE — PROTEGIDO
COBERTURA   : [NO MEDIDA AÚN — pendiente]
NIVELES     : RAW(0a) → NORMALIZED(0b) → FACTS(1) → RELATIONS(2)
              → PLAYBOOKS(3) → STRATEGY(4) → IDENTITY(5)

MÓDULO PROTEGIDO: cambios = Cat.3 obligatorio

ESTADO DE MEMORIA ACTUAL
  Entradas Codex (RELATIONS): 7 (D-001 a D-006 + B-008)
  Entradas IDENTITY: 1 (Prompt Fundacional)
  Total en disco: 249+ entradas JSON

ISSUES CONOCIDOS
  #1 Búsqueda solo por substring (no semántica)  → v4.1 futura mejora
  #2 Sin vector embeddings                       → mejora futura

BRIEF EXISTENTE : S5_MEMORIA_INTELIGENTE_V4.md
PRIORIDAD       : P7 (estable, no urgente)
```

---

### 5.7 BinanceWebSocketManager — `cgalpha_v3/infrastructure/binance_websocket_manager.py`

```
PROPÓSITO   : Conexión a Binance. Ingesta de velas 5m + book depth
              @depth20@100ms. Calcula OBI y CumDelta en tiempo real.

ESTADO      : 🟡 OPERATIVO — RING BUFFER PENDIENTE
COBERTURA   : [NO MEDIDA AÚN — pendiente]

IMPLEMENTADO
  ✅ Stream @depth20@100ms activo
  ✅ OBI multi-nivel (obi_1, obi_5, obi_10, obi_20)
  ✅ CumDelta acumulado (⚠️ global, no rolling)

ISSUES CONOCIDOS — CRÍTICOS PARA ORACLE FASE B
  #1 Sin L2RingBuffer (30s, 300 slots)         → P3 — bloquea Oracle Fase B
  #2 CumDelta es acumulado global, no rolling  → contamina feature causal
     (Codex D-pendiente — Punto Ciego #3)
  #3 Timestamps usan time.time() no Binance   → clock drift posible
     event time                                (Punto Ciego #1)
  #4 Reconexiones generan huecos sin marcar   → l2_data_quality="PARTIAL"
     como PARTIAL                              no implementado aún

RING BUFFER A IMPLEMENTAR (P3)
  L2RingBuffer: deque(maxlen=300), push cada 100ms
  synthesize_at_retest(): condensa 300 slots → 25 features
  Costo en memoria: ~19KB por símbolo. Despreciable.

BRIEF EXISTENTE : architectural_analysis.md (§1.4 Ring Buffer)
PRIORIDAD       : P3 (prerrequisito directo para Oracle Fase B)
```

---

### 5.8 LLMSwitcher — `cgalpha_v3/lila/llm/llm_switcher.py`

```
PROPÓSITO   : Selecciona el proveedor LLM según el tipo de tarea.
              Cat.1 → Ollama (coste 0). Cat.2/3 → Cloud LLM.
              Fallback determinista si el proveedor preferido falla.

ESTADO      : ✅ ESTABLE
COBERTURA   : [NO MEDIDA AÚN — pendiente]
TESTS       : 10/10 passing

MATRIZ ACTUAL
  cat_1, reflection      → Ollama (qwen2.5:3b)
  cat_2, cat_3           → Gemini / OpenAI (fallback Ollama)
  whitepaper             → Ollama

ISSUES CONOCIDOS
  #1 Gemini como provider primario requiere     → funcional
     GEMINI_API_KEY (env var)
  #2 Si Ollama está offline, el sistema         → fallback funcional
     cae a cloud LLM correctamente

BRIEF EXISTENTE : NO (pendiente crear CRB)
PRIORIDAD       : P8
```

---

### 5.9 ShadowTrader — `cgalpha_v3/trading/shadow_trader.py`

```
PROPÓSITO   : Ejecuta trades en modo paper (sin dinero real).
              Registra en bridge.jsonl: señal, entrada, MFE, MAE,
              config_snapshot.

ESTADO      : ✅ ESTABLE
COBERTURA   : [NO MEDIDA AÚN — pendiente]

BRIDGE.JSONL ACTUAL
  Directorio: aipha_memory/evolutionary/bridge.jsonl
  Primer registro: sintético (entry_price=100.01, verificación)
  Registros reales: pendientes de ciclos con señales detectadas

ISSUES CONOCIDOS
  #1 MAE Regressor (Fase 13) depende de Oracle  → pendiente P1 Oracle
  #2 Sniper entry (Limit order en profundidad)  → pendiente Oracle Fase B
     requiere OracleRegressor_MAE funcionando

BRIEF EXISTENTE : NO (pendiente crear CRB)
PRIORIDAD       : P9
```

---

### 5.10 Server/GUI — `cgalpha_v3/gui/server.py`

```
PROPÓSITO   : Servidor Flask. Control Room para el operador.
              Expone todos los endpoints de la API interna.
              Orquesta el startup de todos los componentes.

ESTADO      : 🟡 OPERATIVO — MONOLÍTICO
LÍNEAS      : 2329 (un solo archivo)
COBERTURA   : [NO MEDIDA AÚN — pendiente]

MÓDULO PROTEGIDO: cambios = Cat.3 obligatorio

ENDPOINTS ACTIVOS
  /api/evolution/*          → Canal de evolución Cat.1/2/3
  /api/training/*           → Review de datos del Oracle
  /api/l2-forensics/*       → Panel forense de microestructura
  /learning/operator        → White paper para el operador
  /learning/lila            → Dashboard de aprendizaje de Lila

ISSUES CONOCIDOS
  #1 2329 líneas en un archivo → difícil de testear en aislamiento
  #2 /api/training/approve y   → stubs vacíos (BUG-8 resuelto
     /api/training/reject        pero GUI buttons pendientes)
  #3 Evolution pulse cada 60s → verifica escalaciones Cat.2→Cat.3

BRIEF EXISTENTE : NO (pendiente crear CRB)
PRIORIDAD       : P10 (último — funciona, alto riesgo de rotura)
```

---

### 5.11 Chat de Lila — `cgalpha_v3/gui/server.py:2351`

```
PROPÓSITO   : Interfaz conversacional entre el operador y Lila.
              Envía mensajes al LLM y retorna respuestas en la GUI.
              Punto donde el sistema de rutas A/B/C debería ejecutarse.

ESTADO      : 🔴 DESCONECTADO DEL CODEX
HTML        : <div id="lila-chat" class="lila-collapsed"> (index.html:2318)
ENDPOINT    : /api/assistant/chat (server.py:2351)
JS          : sendLilaMessage() (app.js:1797-1819)
HISTORIAL   : localStorage, 10 entradas — EFÍMERO (BUG-7 del chat)

IMPLEMENTADO
  ✅ Chat desplegable funcional en la GUI
  ✅ LLMAssistant con system_prompt básico (assistant.py:139-148)
  ✅ ContextBuilder con priority_files (context.py)
  ✅ LLMSwitcher con task_types cat_1/2/3 (llm_switcher.py:40-69)
  ✅ harness_inject_when como campo en codex_kernel.py:50
  ✅ Escalada a modelo externo vía _select_best_provider() (assistant.py:64)

NO IMPLEMENTADO — aspiracional en documentación (verificado 2026-06-08)
  ❌ Ensamblado Capa0 + Capa1 + Harness antes de enviar al LLM
     El endpoint usa: f"Contexto: Trading System v3 Audit. Sujeto: {message}"
  ❌ Clasificación automática DIAGNOSTIC/PROPOSAL/EXECUTION del input
  ❌ ContextBuilder real reemplazando el string estático del endpoint
  ❌ Historial de chat persistido en MemoryPolicyEngine (solo localStorage)
  ❌ Harness inyectando leyes activas del Codex en tiempo real

IMPLICACIÓN PARA B-008
  El "Acto VIII — El Eco Eterno" (Harness bloquea EVO-234 automáticamente)
  describe comportamiento deseado. El harness_inject_when existe como campo
  en el schema pero NO se usa para construir prompts. La protección real
  hoy es la ley escrita en el Codex + revisión humana, no inyección automática.

GAPS FORMALES
  G2: Orquestar Capa0 + Capa1 + Harness en endpoint → Cat.3 (server.py protegido)
  G3: Clasificar task_type del input del chat       → Cat.2
  G4: Usar ContextBuilder real en lugar de string   → Cat.2
  G5: Persistir historial en MemoryPolicyEngine     → Cat.2 (BUG-7 del chat)

BRIEF EXISTENTE : NO — pendiente crear CRB
PRIORIDAD       : P6.5
PREREQUISITO    : Orchestrator v5 estable (P6) antes de tocar el endpoint

KNOWLEDGE CARD — File Reader (G4) [añadida 2026-06-21, EVO-TICKET-0004]
  Endpoint implementado : /api/admin/read-file  (NO /api/lila/read-file — desviación de spec documentada)
  Archivo               : cgalpha_v3/gui/server.py
  Verificación          : py_compile (2026-06-14)
  Invariantes           : path resuelto contra _PROJECT_ROOT_READER, solo GET,
                          @require_auth, archivos >100KB sin rango → 413
  Estado G4             : IMPLEMENTADO — G2/G3/G5 siguen pendientes
  RMU                   : governance_log/RMU-EVO-TICKET-0004-2026-06-14.md
  Nota P65_FILE_READER_SPEC.md: ruta en spec (/api/lila/read-file) no actualizada
                          con la ruta real — pendiente correción menor.
```

---

## §6 — Protocolo para crear un Component Brief (CRB)

Cuando un componente sea elegido para reconstrucción, el primer
paso es crear su CRB si no existe. El CRB sigue esta plantilla:

```markdown
# CRB — [Nombre del Componente]
## cgAlpha_0.0.1 — Component Reconstruction Brief

### §1 — Propósito y lugar en el sistema
[Una sola frase + el fragmento del §2 de este Nexus]

### §2 — Estado actual
- Cobertura de tests: X%
- Tests pasando: N/N
- Issues conocidos numerados

### §3 — Schema de interfaces (qué recibe, qué entrega)
[Nombres de parámetros reales, no descripciones]

### §4 — Módulos protegidos dentro de este componente
[Funciones que no se tocan, con justificación]

### §5 — Deuda técnica conocida
[Como el §1.4 del RECONSTRUCTION_BRIEF.md del Oracle]

### §6 — Fases de reconstrucción
Fase A: cambios deterministas de bajo riesgo
Fase B: cambios que requieren nuevos datos o pruebas

### §7 — Criterios de éxito
[Métricas verificables, no "debe funcionar mejor"]

### §8 — Lo que NO se cambia en esta sesión
[Lista explícita]
```

---

## §7 — Lo que ya está hecho — no repetir

```
COMPLETADO          FECHA       COMMIT
────────────────────────────────────────────────────────────
BUG-1: train_test_split           2026-04     d0992d2
BUG-2: save/load Oracle           2026-04     (server.py)
BUG-3: class imbalance SMOTE      2026-04     dd85d21
BUG-4: is_placeholder() método    2026-06     (deuda técnica)
BUG-5: outcome labeling con zona  2026-04     script det.
BUG-6: pipeline retrain           2026-04     509c7b3
BUG-7: load_from_disk startup     2026-04     bootstrap
BUG-8: approve/reject persistence 2026-04     (server.py)
B-008 v1: Spatial Multi-Touch     2026-05     145c455
B-008 v2: Cross-Polarity Clones   2026-06     c19f7d6
Bootstrap: 3 acciones (IDENTITY,  2026-04     múltiples
  LLM Switcher, Orchestrator v4)
ZigZag calibrado a 0.18%          2026-04     a5ed77a
Island Bridge (4 islas conectadas)2026-04     22dd431
Parameter Landscape Map (Cat.2)   2026-04     813b4ab
OOS baseline honesto: 0.68        2026-06     619c6b2
Codex (D-001→D-006, B-008)        2026-06     (memoria)
FrozenEstimator wrapper           2026-06     (deuda técnica)
OOS guard >= 30 en A/B training   2026-06     (deuda técnica)

─── SESIÓN 2026-06-08 ─────────────────────────────────────────
Sistema de Rutas A/B/C            2026-06-08  LILA_ROUTING_PROMPT.md
Nexus Superior v0.1               2026-06-08  NEXUS_SUPERIOR.md
Ruta A detallada                  2026-06-08  LILA_RUTA_A_OBSERVAR.md
Ruta B detallada                  2026-06-08  LILA_RUTA_B_PROPONER.md
B-008 cápsula Nexus               2026-06-08  B008_NEXUS_CAPSULE.md
  (corrección: fingerprint v1 incluía direction,
   v2 canónico lo eliminó — D-004)
Diagnóstico Chat de Lila (GUI)    2026-06-08  §5.11 en este Nexus
  4 gaps confirmados + BUG-7 del chat
  harness_inject_when aspiracional
  (no inyectado en prompts — P6.5)

─── SESIÓN 2026-06-12 ─────────────────────────────────────────
Capa de Gobernanza Constitucional 2026-06-12  §9 en este Nexus
  (adaptación del Apéndice — Constitutional
   Governance of Evolutionary Debt)
RECONSTRUCTION_MAP_UPDATE_TEMPLATE.md          plantilla obligatoria
ARCHITECTURAL_DECISION_RECORD_TEMPLATE.md      plantilla obligatoria
EVO_TICKET_LOG.md                  seed: EVO-TICKET-0001 (Oracle v6
  Fase A, ACTIVE/EXECUTING) y EVO-TICKET-0002
  (Oracle v6 Fase B, DORMANT — bloqueado por P3/P4)
D-008 añadida a §3 (Causal Closure)

─── SESIÓN 2026-06-12 (cont.) ──────────────────────────────────
D-009 añadida a §3 (Constitutional Event Ledger)
constitutional_events.jsonl        seed: 2 eventos ticket_created
  (EVO-TICKET-0001, EVO-TICKET-0002)
CONSTITUTIONAL_EVENT_LEDGER_SPEC.md  vocabulario de 6 eventos
  (reducido desde propuesta original de 8 — eventos de gates
  automáticos eliminados, ver §9)
Regla operativa (§9) extendida con sub-pasos de ledger

─── SESIÓN 2026-06-14 ─────────────────────────────────────────
D-010 añadida a §3 (Cognitive Portability)
§10 añadida a este Nexus (test 3 preguntas + Knowledge Card)
RECONSTRUCTION_MAP_UPDATE_TEMPLATE.md  campo LLM Readability Check
EVO-TICKET-0004 creado (P6.5 File Reader — G4 building block)
P65_FILE_READER_SPEC.md  endpoint + implementación lista para Cat.2
```

---

## §10 — Cognitive Portability (D-010)

> "La reconstrucción no debe producir componentes optimizados para el
> modelo que los reconstruye; debe producir componentes optimizados
> para los modelos menos capaces que deberán operarlos durante los
> próximos años."

### El problema que resuelve

Sin D-010, una reconstrucción técnicamente correcta puede ser
cognitivamente opaca para el modelo que la mantiene. Un modelo con
8k de contexto que ve `calculate_signal()` y no tiene acceso al
historial de la sesión que la escribió no sabe:
- por qué existe esa función
- qué invariante debe preservar
- qué se rompe si la modifica

Los governance artifacts (RMU, ADR, Nexus §5) son la única memoria
que ese modelo tendrá disponible. D-010 convierte eso en un criterio
de completitud verificable.

### El test de 3 preguntas

Al cerrar cualquier sesión de reconstrucción, el modelo que ejecutó
el trabajo responde estas tres preguntas **como si fuera Lila con 8k
de contexto, sin memoria de la sesión, leyendo solo**:

```
(a) el RMU de la fase
(b) la sección §5 del Nexus del componente afectado
(c) las docstrings de las funciones modificadas
```

Las preguntas:

```
P1: ¿Qué hace este cambio y por qué existe?
    (2-3 frases. Sin jerga de sesión. Sin "como discutimos antes...")

P2: ¿Qué invariante debe preservar siempre la función principal?
    (Ejemplo correcto: "INVARIANTE: _heartbeat_candle_close() nunca
     debe llamarse para la misma kline_start dos veces — la guarda
     `if kline_start <= self._last_kline_close: return` es obligatoria.")
    (Ejemplo incorrecto: "la función debe funcionar bien")

P3: ¿Qué componente aguas abajo se rompe si este cambio se revierte?
    (Componente específico del §2 del Nexus + síntoma observable.
     No "algo falla" — qué exactamente y cómo lo detectarías.)
```

Si el modelo no puede responder las tres con fluidez, la fase
está incompleta. Las acciones correctoras en orden de prioridad:

1. Mejorar la docstring de la función (invariante explícito)
2. Ampliar el campo "Logic Introduced" del RMU
3. Ampliar la ficha del componente en §5 del Nexus

### El Knowledge Card como extensión de §5

Cada ficha de componente en §5 debe tener una subsección
`### Knowledge Card` que responde las tres preguntas una vez,
en estado estable, sin depender de ninguna sesión específica.

Formato mínimo:
```
### Knowledge Card (D-010)

PROPÓSITO EN UNA FRASE:
  [qué hace este componente para el sistema, no cómo lo hace]

INVARIANTE CRÍTICO:
  [qué nunca debe romperse, expresado como condición verificable]

DEPENDIENTE AGUAS ABAJO:
  [componente del §2 que consume este, y síntoma observable si falla]

PARA MODIFICAR ESTE COMPONENTE, el modelo operativo necesita saber:
  [1-3 hechos que no están en el código pero sí en los governance artifacts]
```

Las fichas de §5 existentes (5.1-5.11) no tienen Knowledge Card todavía.
Se añaden progresivamente al cierre de cada sesión de reconstrucción
que toque ese componente — no antes, porque el card debe reflejar
el estado real del código, no el aspiracional.

### Implicación para docstrings de código

Toda función reconstruida bajo D-010 debe tener una docstring que
incluya el invariante clave. No para los humanos — para el modelo
operativo con contexto limitado:

```python
# ANTES (opaco para modelo con 8k de contexto):
def _heartbeat_candle_close(self, depth_ts_ms: int):
    """Fallback clock when aggTrade stream is silent."""

# DESPUÉS (D-010 compliant):
def _heartbeat_candle_close(self, depth_ts_ms: int):
    """Fallback clock: close candle using depthUpdate timestamp
    when aggTrade stream has been silent > heartbeat_timeout.

    INVARIANTE: llamar solo cuando kline_start > self._last_kline_close.
    La guarda al inicio del método es obligatoria — sin ella se generan
    múltiples cierres de vela para el mismo periodo a 10 calls/segundo.

    AGUAS ABAJO: DeferredOutcomeMonitor.tick() recibe el cierre vía
    _on_candle_close(). Si este método se elimina, training_dataset_v2.jsonl
    deja de actualizarse cuando aggTrade falla (EVO-TICKET-0003).
    """
```

### Relación con provider switching y censura

D-010 es la respuesta arquitectónica al riesgo de censura de modelos
(ej: modelo avanzado que reconstruye componente financiero y luego es
censurado o reemplazado). Si el componente reconstruido cumple D-010,
un modelo de menor capacidad puede:

- Entender el invariante sin releer la sesión de reconstrucción
- Hacer cambios puntuales (Cat.1) sin romper la lógica crítica
- Detectar si una propuesta viola el invariante antes de ejecutarla

El conocimiento institucional no vive en el modelo que reconstruyó.
Vive en el código (docstrings) + governance artifacts (RMU §10 field
+ Nexus §5 Knowledge Card). Eso es lo que hace el sistema
independiente de cualquier proveedor específico.

---

## §8 — Estado de los Component Briefs

| Componente | CRB existe | Estado |
|---|---|---|
| Oracle | ✅ RECONSTRUCTION_BRIEF.md v1.1 | En reconstrucción activa (P1) |
| Codex/Memory | ✅ CODEX_ENTRIES_DRAFT.md | Ingestado en memoria |
| Routing (Ruta A/B/C) | ✅ LILA_ROUTING_PROMPT.md + LILA_RUTA_A/B | Operativo (2026-06-08) |
| B-008 cápsula | ✅ B008_NEXUS_CAPSULE.md | Completo con corrección v2 |
| Gobernanza constitucional | ✅ §9 + 3 plantillas + EVO_TICKET_LOG.md | Operativo (2026-06-12) |
| D-010 / Cognitive Portability | ✅ §10 + campo RMU + Knowledge Card | Operativo (2026-06-14) |
| Chat de Lila — File Reader (P6.5) | ✅ EVO-TICKET-0004 + P65_FILE_READER_SPEC.md + Knowledge Card §5.11 | G4 IMPLEMENTADO (2026-06-14) — /api/admin/read-file activo; G2/G3/G5 pendientes |
| CodeCraftSage | ❌ Pendiente | P2 |
| L2 Ring Buffer | 🟡 architectural_analysis.md §1-2 | P3 — parcial |
| DeferredOutcomeMonitor | ❌ Pendiente | P4 |
| TripleCoincidenceDetector | ✅ CRB creado — EVO-TICKET-0005 es primera evidencia real | P5 |
| EvolutionOrchestrator | ❌ Pendiente | P6 |
| Chat de Lila (GUI) | 🟡 §5.11 en este Nexus — 4 gaps doc. G4 implementado (2026-06-14) | P6.5 |
| MemoryPolicyEngine | 🟡 S5_MEMORIA_INTELIGENTE_V4.md | P7 — parcial |
| LLMSwitcher | ❌ Pendiente | P8 |
| ShadowTrader | ❌ Pendiente | P9 |
| Server/GUI | ❌ Pendiente | P10 |

---

## §9 — Capa de Gobernanza Constitucional

> Adaptación del Apéndice "Constitutional Governance of Evolutionary
> Debt" a la cgAlpha REAL (no a la cgAlpha aspiracional). Cada
> concepto del Apéndice se mapea aquí a: existe / no existe / cómo
> se simula mientras no existe.

### Mapa Apéndice → cgAlpha real

```
CONCEPTO DEL APÉNDICE       ESTADO EN cgAlpha           CÓMO SE CUMPLE HOY
──────────────────────────────────────────────────────────────────────────
AlphaLab (cámara completa,   ❌ NO EXISTE                Arquitectura objetivo,
QUARANTINE_GATE,                                         mismo nivel que el
READY_FOR_CODEX,                                         "Eco Eterno" del
resurrección automática)                                 Harness (Acto VIII,
                                                          ver B008_NEXUS_CAPSULE)

EVO-TICKET                   ✅ EVO_TICKET_LOG.md         Formato constitucional
(precedente formal)          (seed: 0001, 0002)          desde 2026-06-12.
                                                          Todo trabajo en P1+
                                                          debe tener ticket
                                                          antes de empezar.

Maturity levels (1-5)        ✅ usado en EVO_TICKET_LOG   Asignado manualmente
                                                          por quien abre el
                                                          ticket. Sin gate
                                                          automático.

Vitality states               ✅ usado en EVO_TICKET_LOG   ACTIVE/DORMANT/
(ACTIVE/DORMANT/                                          STALLED/ORPHANED.
STALLED/ORPHANED)                                         Revisión manual al
                                                          cierre de cada sesión
                                                          de trabajo (no
                                                          automática).

QUARANTINE_GATE               🟡 SIMULADO                  Cumplido por: Ruta C
(verificar no-contradicción)                              (LILA_ROUTING_PROMPT.md)
                                                          + checklist contra §3
                                                          (verdades inmutables)
                                                          antes de aprobar
                                                          ejecución.

READY_FOR_CODEX                🟡 SIMULADO                  El orden de §4
(cola de ejecución)                                       (P1→P10) es la cola.
                                                          No hay colisiones
                                                          porque solo un
                                                          componente está
                                                          "EXECUTING" a la vez
                                                          (regla de inicio §4).

[RECONSTRUCTION_MAP_UPDATE]    ✅ PLANTILLA LISTA           RECONSTRUCTION_MAP_
(obligatorio al cerrar                                    UPDATE_TEMPLATE.md.
implementación)                                           D-008: ninguna fase
                                                          de P1+ se considera
                                                          completa sin este
                                                          artefacto.

[ARCHITECTURAL_DECISION_       ✅ PLANTILLA LISTA           ARCHITECTURAL_
RECORD]                                                    DECISION_RECORD_
(decisiones con alternativas)                             TEMPLATE.md. Uno por
                                                          decisión, no por fase.

Debt classification             ✅ usado en EVO_TICKET_LOG   EXPANSION /
(EXPANSION/CONSOLIDATION/                                  CONSOLIDATION /
EMERGENCY/TOXIC)                                          EMERGENCY / TOXIC.
                                                          Estimado al abrir el
                                                          ticket, confirmado en
                                                          el RMU al cerrarlo.

Resurrection Protocol           ✅ documentado en           EVO-TICKET-0002 es
(tickets dormidos →             EVO_TICKET_LOG              el primer caso real:
decisión obligatoria)                                      DORMANT, con
                                                          condición explícita
                                                          de revisión (P3/P4
                                                          con CRB).

Principle of Causal Closure     ✅ ESTA SECCIÓN              Gobernanza
(estado de gobernanza =                                    (EVO_TICKET_LOG +
estado de implementación)                                  governance_log/) y
                                                          código deben
                                                          mencionarse
                                                          mutuamente: el RMU
                                                          referencia archivos
                                                          y líneas; el código
                                                          puede referenciar
                                                          el ticket en
                                                          comentarios si el
                                                          cambio es no-obvio.
```

### Por qué EvolutionOrchestrator (P6) NO se adelanta

Es la pregunta que originó esta sección: ¿hay que construir
EvolutionOrchestrator antes de tocar Oracle, para que documente
los cambios?

**No**, por dos razones:

1. **Dependencia real (§4):** P6 necesita P1-P5 estables. Adelantarlo
   invierte el orden que ya está justificado por el grafo de
   dependencias (§2).

2. **No es lo que se necesita.** EvolutionOrchestrator es el motor
   que ejecuta y escala propuestas (Cat.1→2→3) — un componente vivo.
   Lo que pedía la idea original — "huellas claras para seguimiento
   post-reescritura" — es un **formato de artefacto**, no un motor.
   Un formato se puede exigir desde HOY, por disciplina de proceso,
   sin que exista el software que algún día lo consuma.

El patrón es **"escribir ahora, ingerir después"**: los archivos en
`governance_log/` y `EVO_TICKET_LOG.md` ya están en el schema
constitucional. Cuando P6 y P7 (MemoryPolicyEngine) se reconstruyan,
los ingieren tal cual — sin reinterpretación, porque ya son datos
estructurados, no la crónica de desarrollo que el Apéndice (y D-008)
buscan evitar.

### Regla operativa para el LLM que reconstruye Oracle v6

```
1. Abrir/confirmar EVO-TICKET-0001 en EVO_TICKET_LOG.md antes
   de escribir código (ya está abierto, estado EXECUTING).

2. Trabajar la fase normalmente (Ruta C, LILA_RUTA_B_PROPONER.md
   si aplica clasificación Cat.1/2/3 dentro de la fase).

3. Al cerrar la sesión:
   a. Llenar RECONSTRUCTION_MAP_UPDATE_TEMPLATE.md →
      governance_log/RMU-EVO-TICKET-0001-{fecha}.md
      → append a constitutional_events.jsonl:
         {"event":"rmu_generated","ticket":"EVO-TICKET-0001",
          "artifact":"RMU-EVO-TICKET-0001-{fecha}"}
   b. Si hubo decisiones con alternativas (ej: esquema de
      encoding, issue #2 de §5.1) → llenar
      ARCHITECTURAL_DECISION_RECORD_TEMPLATE.md por cada una →
      governance_log/ADR-EVO-TICKET-0001-{n}-{slug}.md
      → append a constitutional_events.jsonl:
         {"event":"adr_created","ticket":"EVO-TICKET-0001",
          "adr":"ADR-EVO-TICKET-0001-{n}-{slug}"}
   c. Si el RMU propone nuevas entradas D-XXX → añadirlas a §3
      de este Nexus directamente (no esperar a P7).
   d. Actualizar la tabla "Registro de cierre" en EVO_TICKET_LOG.md
      → append a constitutional_events.jsonl:
         {"event":"debt_recorded","ticket":"EVO-TICKET-0001",
          "component":"Oracle","debt_class":"<de la RMU>"}
         {"event":"ticket_closed","ticket":"EVO-TICKET-0001",
          "final_state":"IMPLEMENTED"}

4. Solo entonces, la fase está completa (D-008 + D-009).
```

### D-009 — Constitutional Event Ledger

> Propuesta del operador, sesión 2026-06-12. Aceptada con ajustes.
> Archivo: `constitutional_events.jsonl` (especificación completa en
> `CONSTITUTIONAL_EVENT_LEDGER_SPEC.md`, seed inicial en
> `constitutional_events.jsonl`).

**Por qué se acepta:** RMU/ADR/EVO_TICKET_LOG responden "¿por qué
ocurrió?" — son documentos, requieren leer prosa para reconstruir
una cronología. El ledger responde "¿qué ocurrió y cuándo?" en
formato append-only de una línea por evento. Es el mismo principio
de "escribir ahora, ingerir después" que ya aplicamos a RMU/ADR,
llevado a su forma más estructurada posible: JSON plano, sin
interpretación necesaria. No introduce componentes, no altera
P1→P10, no es una base de datos — es un log.

**Ajustes hechos sobre la propuesta original:**

1. **Vocabulario reducido de 8 a 6 tipos de evento.** La propuesta
   original incluía `ticket_entered_quarantine` y
   `ticket_ready_for_codex` — eventos que implican que
   QUARANTINE_GATE y READY_FOR_CODEX son pasos automatizados reales.
   Pero §9 ya documenta ambos como `🟡 SIMULADO` (revisión manual,
   no gates). Registrar esos eventos como si hubieran "ocurrido"
   crearía un falso precedente: un sistema futuro leyendo el ledger
   asumiría que existió un gate automático en 2026-06, cuando en
   realidad fue un humano mirando una tabla. Eso es una violación
   en miniatura del propio Principle of Causal Closure que motiva
   esta propuesta — el evento afirmaría más automatización de la
   que hubo.

   Vocabulario final (7 eventos):
   ```
   ticket_created        — alta de un EVO-TICKET
   ticket_state_changed  — cambio de maturity | vitality |
                            lifecycle_state, con campo
                            decided_by: "human" | "llm_self_assessment"
   rmu_generated         — referencia a un RMU ya escrito
   adr_created           — referencia a un ADR ya escrito
   crb_created           — referencia a un Component Reconstruction Brief
                            ya escrito. Justificación: P1-P10 requieren CRB
                            antes de reconstrucción; registrarlo como evento
                            separado evita que un ticket de bugfix (ej:
                            EVO-0005) tenga que absorber la creación del CRB
                            como si fuera parte de su cierre.
   debt_recorded         — clasificación de deuda confirmada
                            (EXPANSION_DEBT | CONSOLIDATION_DEBT |
                             EMERGENCY_DEBT | TOXIC_DEBT)
   ticket_closed         — cierre con estado final
   ```

   El campo `decided_by` es la pieza nueva más valiosa: en lugar de
   fingir un gate automático, registra HONESTAMENTE quién tomó cada
   decisión de transición. Esa es información causal real que ni
   RMU ni ADR capturan por sí solos.

2. **Naming consistente con EVO_TICKET_LOG.md.** La propuesta usaba
   `EVO-0001`; el log ya usa `EVO-TICKET-0001`. Se mantiene la
   convención existente en todos los ejemplos.

3. **Ubicación bajo `governance_log/`**, junto a los RMU/ADR — un
   solo directorio para todo lo que es gobernanza, separado del
   código.

4. **No es un checklist nuevo y separado.** Se integró como
   sub-pasos de la "Regla operativa" ya existente (arriba). Misma
   sesión, mismo cierre, sin ritual adicional que alguien pueda
   olvidar por estar en otro documento.

5. **Seed retroactivo.** La creación de EVO-TICKET-0001 y
   EVO-TICKET-0002 (sesión 2026-06-12, anterior a esta) se registra
   como los dos primeros eventos del ledger — "escribir historia
   una vez" incluye la historia que ya existe, no solo la futura.

**Relación con `EVO_TICKET_LOG.md`:** no compiten. `EVO_TICKET_LOG.md`
es el **estado actual** (snapshot mutable: maturity, vitality,
estado de ciclo de cada ticket). El ledger es la **historia**
(append-only, nunca se edita). Son la misma relación que entre el
estado de un fichero y `git log` — no se puede que "diverjan" porque
responden preguntas distintas.

---

*Nexus Superior v0.5 — cgAlpha_0.0.1*
*Creado: 2026-06-08 | Actualizado: 2026-06-14*
*Actualizar tras cada CRB completado, componente reconstruido,
o EVO-TICKET cerrado.*
