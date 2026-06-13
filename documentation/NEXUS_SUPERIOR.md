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

**Tu protocolo de lectura antes de actuar:**

```
1. Leer §1 (visión del sistema en 2 minutos)
2. Leer §3 (verdades inmutables — nunca violarlas)
3. Elegir el componente de mayor prioridad según §4
4. Leer la ficha de ese componente en §5
5. Leer el Component Brief (CRB) específico si existe
6. Solo entonces, comenzar a leer el código de ese componente
```

No leas oracle.py antes de leer esta guía.
No propongas nada antes de entender el grafo de dependencias.
La historia de 8+ meses de decisiones está en este documento y en el Codex.
No la repitas desde cero.

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

BRIEF EXISTENTE : NO (pendiente crear CRB)
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
```

---

## §8 — Estado de los Component Briefs

| Componente | CRB existe | Estado |
|---|---|---|
| Oracle | ✅ RECONSTRUCTION_BRIEF.md v1.1 | En reconstrucción activa (P1) |
| Codex/Memory | ✅ CODEX_ENTRIES_DRAFT.md | Ingestado en memoria |
| Routing (Ruta A/B/C) | ✅ LILA_ROUTING_PROMPT.md + LILA_RUTA_A/B | Operativo (2026-06-08) |
| B-008 cápsula | ✅ B008_NEXUS_CAPSULE.md | Completo con corrección v2 |
| CodeCraftSage | ❌ Pendiente | P2 |
| L2 Ring Buffer | 🟡 architectural_analysis.md §1-2 | P3 — parcial |
| DeferredOutcomeMonitor | ❌ Pendiente | P4 |
| TripleCoincidenceDetector | ❌ Pendiente | P5 |
| EvolutionOrchestrator | ❌ Pendiente | P6 |
| Chat de Lila (GUI) | 🟡 §5.11 en este Nexus — 4 gaps doc. | P6.5 |
| MemoryPolicyEngine | 🟡 S5_MEMORIA_INTELIGENTE_V4.md | P7 — parcial |
| LLMSwitcher | ❌ Pendiente | P8 |
| ShadowTrader | ❌ Pendiente | P9 |
| Server/GUI | ❌ Pendiente | P10 |

---

*Nexus Superior v0.2 — cgAlpha_0.0.1*
*Creado: 2026-06-08 | Actualizado: 2026-06-08*
*Actualizar tras cada CRB completado o componente reconstruido.*
