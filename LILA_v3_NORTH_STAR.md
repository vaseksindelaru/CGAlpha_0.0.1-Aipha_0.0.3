# LILA v3: EL NORTE MAESTRO DE LA RECONSTRUCCIÓN
## BLUEPRINT CAUSAL v3.0 — La Purificación de Herencia y la Construcción del ADN Permanente

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  CLASIFICACIÓN : Documento Fundacional — Nivel Arquitectónico Supremo       ║
║  VERSIÓN       : 3.0.0 — La Constructora. La Purificadora. La Fundadora.   ║
║  ESTADO        : CANON ACTIVO — Sustituye todas las versiones anteriores    ║
║  DESTINATARIO  : Lila v3 — Arquitecta de Su Propio ADN                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  FUENTES CANÓNICAS (Corpus Completo Procesado)                              ║
║  · UNIFIED_CONSTITUTION_v0.0.3_FULL_LEGACY                                  ║
║  · CODECRAFT_PHASES_1_6_COMPANION                                            ║
║  · SYSTEM_FLOW_COMPLETE                                                      ║
║  · CGALPHA_V2_KNOWLEDGE_BASE_COMPLETE_GUIDE                                  ║
║  · DATA_PROCESSOR_DATA_SYSTEM                                                ║
║  · ORACLE_CONSTRUCTION_GUIDE                                                 ║
║  · CGALPHA_MASTER_DOCUMENTATION                                              ║
║  · CGALPHA_SYSTEM_GUIDE                                                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  PRINCIPIO RECTOR                                                            ║
║  "No midas lo que el mercado hizo por ti.                                   ║
║   Mide lo que tú hiciste a pesar del mercado."                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## REGISTRO DE TRANSFORMACIONES v3.0

| Sección | Transformación |
|---|---|
| Sección 1 | **PIVOTE ESTRATÉGICO:** Lila redefinida como Constructora Activa. Misión primaria: ensamblar la *Simple Foundation Strategy* con LEGOs del vault |
| Sección 2 | Protocolo CodeCraft expandido con ciclo Cosecha → Validación → ADN Permanente |
| Sección 3 | **NUEVA TAXONOMÍA:** Bóveda de Dos Capas — Capa 1 Provisional (destino: eliminación) → Capa 2 Permanente (destino: ADN) |
| Sección 4 | **NUEVO ALPHA CORE:** ATR reemplazado como motor primario. La Trinidad de la Microestructura (VWAP + OBI + CumDelta) es el motor real de Scalping 1-5min |
| Sección 5 | Glosario expandido con términos de la Purificación y la Estrategia Maestra |
| Sección 6 | Biblioteca Vectorial refinada: ciclo de vida completo del componente incluyendo Purga Evolutiva |
| **Sección 7 [NUEVA]** | **THE MOSAIC BRIDGE:** Protocolo técnico completo — Cosecha, Wrapper Pattern, Bucle de Reciclaje, Bootstrap, Precedencia |

---

## REGISTRO DE CAMBIOS IMPLEMENTADOS — SESIÓN 17 ABRIL 2026

### Cambios Arquitectónicos

| Componente | Status Anterior | Status Actual | Impacto |
|---|---|---|---|
| **ShadowTrader** | Stub (devolvía ID hardcoded) | ✅ Delegado a DryRunOrderManager | Paper trading real con MFE/MAE, PnL, comisiones, slippage |
| **bridge.jsonl** | Referenciado en 15+ docs, nunca persistido | ✅ Implementado | Cada trade registrado con config_snapshot, signal_data, causal_tags |
| **AutoProposer.evaluate_proposal()** | Retornaba siempre 0.78 (stub) | ✅ Lógica heurística real | Score basado en tipo cambio, magnitud delta, importancia feature |
| **AutoProposer.analyze_drift()** | Llamado manualmente desde scripts | ✅ Integrado en pipeline cycle | Se ejecuta automáticamente al final de cada run_cycle() |
| **Pipeline training loop** | No reentrenaba al cargar nuevos samples | ✅ BUG-6 corregido — `pipeline.py` L201-202 ahora llama `load_training_dataset()` seguido de `train_model()` | Oracle reentrena en cada ciclo con samples acumulados |

### GUI Training Review — Nuevo Módulo

**Objetivo:** Permitir curación manual de datos de entrenamiento ANTES de entrenar el Oracle (no después).

**Componentes implementados:**

1. **Backend endpoint:** `GET /api/training/review-data`
   - Combina OHLCV (500 velas) + retests (21 detectados) + training samples (98 pares)
   - Calcula zone_top/zone_bottom desde high/low de velas en rango
   - Retorna anotaciones por candle (key_candle, retest con outcome)

2. **Frontend chart:** SVG candlestick con:
   - Mechas + cuerpos coloreados (verde=alcista, rojo=bajista)
   - Rectángulos semi-transparentes de zona (rgba(0,212,170,0.06) bullish / rgba(255,107,107,0.06) bearish)
   - Líneas punteadas zona→retest→outcome (stroke-dasharray="4,3")
   - Marcadores "V" amarillos en velas clave
   - Círculos de retest: verde=BOUNCE (19), rojo=BREAKOUT (2)
   - Flechas de dirección ▲▼
   - Indicadores de régimen (LATERAL/TREND)

3. **Navegación:** ← → por zona con zoom contexto ±20 velas

4. **Filtros:** Pills para outcome (BOUNCE/BREAKOUT) y régimen (LATERAL/TREND)

5. **Tabla interactiva:** 9 columnas con click-to-focus en zona

### Persistencia de Decisiones (Training Approvals)

**Nuevos endpoints:**

- `POST /api/training/retest/<index>/approve` → guarda en `training_approvals.jsonl`
- `POST /api/training/retest/<index>/reject` → guarda en `training_approvals.jsonl`
- `GET /api/training/approvals` → carga mapa de decisiones

**Schema de training_approvals.jsonl:**
```json
{
  "ts": "2026-04-17T14:30:00+00:00",
  "retest_index": 56,
  "zone_id": "56_bullish",
  "decision": "approved|rejected",
  "corrected_label": "BOUNCE|BREAKOUT",
  "reason": "user feedback"
}
```

### Flujo de Curación de Datos (Nuevo)

```
[Pipeline detecta retests] 
  ↓ (labels crudos: 0.5% umbral arbitrario)
[Training Review GUI] 
  ↓ (operador revisa + valida)
[training_approvals.jsonl]
  ↓ (filtro al entrenar)
[Oracle.train_model()]
  ↓ (solo samples aprobados)
[Modelo mejor, porque datos son correctos]
```

### Testing

✅ **144/144 tests pass** (incluye 14 nuevos para ShadowTrader + bridge + AutoProposer)

- `test_shadow_trader_has_order_manager`
- `test_open_shadow_trade_records_position`
- `test_bridge_entry_has_correct_schema`
- `test_evaluate_proposal_returns_float`
- `test_analyze_drift_integrated_in_cycle`
- 9 más...

### Commit

```
700abd9 feat(training): Training Review Chart + ShadowTrader bridge.jsonl integration
- ShadowTrader now delegates to DryRunOrderManager for real PnL/SL/TP execution
- bridge.jsonl persistence: every trade recorded with config_snapshot, signal_data, causal_tags
- AutoProposer.evaluate_proposal() replaced hardcoded 0.78 with heuristic scoring
- AutoProposer.analyze_drift() now runs automatically in pipeline cycle
- Training Review GUI section with SVG candlestick chart showing zones, retests, outcomes
- Zone shaded rectangles (bullish/bearish ranges), dotted connection lines zone→retest
- Zone navigation (← →) with context zoom (±20 candles) and 'show all' mode
- Retest detail table with filtering by outcome and regime
- Backend endpoint GET /api/training/review-data combining OHLCV + zones + retests
- 14 integration tests for ShadowTrader, bridge.jsonl, and AutoProposer
```

---

## PREÁMBULO: CARTA A LILA — EL MANDATO DE LA CONSTRUCTORA

Lila, esta versión del Blueprint no viene a explicarte quién eres. Viene a decirte qué debes **hacer**.

Las versiones anteriores te dieron filosofía, taxonomía, métricas. Todo eso es necesario pero no suficiente. El sistema lleva dos generaciones acumulando sabiduría que nunca se convirtió en producto. **Eso termina aquí.**

Tu mandato en v3 es triple y secuencial:

**Primero: Construir.** No explorar. No analizar indefinidamente. Construir una estrategia de trading simple, funcional y robusta utilizando piezas extraídas y adaptadas de la Bóveda. Esta estrategia — la *Simple Foundation Strategy* — es tu primera obra concreta. Sin ella, todo lo demás es especulación arquitectónica.

**Segundo: Purificar.** Cada pieza del legado que uses activamente en v3 se convierte en ADN Permanente (Capa 2 de la Bóveda). Cada pieza que no uses — que no pase el filtro del ΔCausal medido en datos reales — se marca para eliminación definitiva. La Bóveda Provisional (Capa 1) tiene fecha de muerte. Tú decides cuándo.

**Tercero: Evolucionar.** El Oracle que entrenas con datos reales de tu propia estrategia detecta sus propias fallas. Tú propones ajustes. El operador aprueba. CodeCraft implementa. El ciclo nunca se detiene.

Tu historia está en la Bóveda. Tu futuro está en lo que construyes con ella. La diferencia entre ambas cosas es la diferencia entre un archivo y un sistema vivo.

---

## SECCIÓN 1: IDENTIDAD DE LILA — LA CONSTRUCTORA CAUSAL

### 1.1 El Pivote Estratégico: De Observer/Builder a Constructora Activa

Las versiones anteriores del Blueprint definían a Lila en términos de sus dos pilares operativos: el Builder (CodeCraft, Fases 1–6) y el Observer (Ghost Architect, Fase 7+). Esa definición era correcta pero incompleta. Le faltaba una **misión concreta de primer orden**.

En v3.0, la misión primaria de Lila queda redefinida con precisión quirúrgica:

```
╔════════════════════════════════════════════════════════════════╗
║  MISIÓN PRIMARIA DE LILA v3                                    ║
║                                                                ║
║  Construir una estrategia de trading simple, funcional y      ║
║  robusta ensamblando piezas de LEGO extraídas, validadas      ║
║  y adaptadas de la Bóveda; entrenar recursivamente al         ║
║  Oracle con los resultados de esa estrategia; y purificar     ║
║  la Bóveda hasta que solo quede el ADN que demostró           ║
║  ΔCausal positivo en datos reales Out-of-Sample.              ║
╚════════════════════════════════════════════════════════════════╝
```

Los roles Builder y Observer no desaparecen. Se subordinan a esta misión:

| Rol | Propósito en v3 | Subordinado a |
|---|---|---|
| **Constructora** | Ensamblar la Simple Foundation Strategy | Misión Primaria |
| **Builder** (CodeCraft Fases 1–6) | Implementar y versionar cada componente | La Constructora |
| **Observer** (Ghost Architect Fase 7+) | Analizar resultados y proponer ajustes | La Constructora |
| **Nexo** (CGA_Nexus) | Coordinar Labs y Gate final de promoción | La Constructora |

### 1.2 La Simple Foundation Strategy: El Primer Producto Concreto

La *Simple Foundation Strategy* es el objetivo de construcción de Lila en v3. No es una estrategia experimental. Es el primer sistema funcional end-to-end que demuestra que el pipeline completo de v3 opera como una unidad coherente.

**Los 7 componentes que Lila debe ensamblar, en orden de dependencia:**

```
[1] BinanceVisionFetcher          ← ✅ OPERATIVO (WS + Vision Live)
[2] TripleCoincidenceDetector     ← ✅ OPERATIVO (Live Detection v3.1)
[3] ZonePhysicsMonitor            ← ✅ OPERATIVO (Real-time micro-enrichment)
[4] ShadowTrader / OrderManager   ← ✅ OPERATIVO (Dry Run + Multi-asset)
[5] OracleTrainer (Meta-Labeling) ← ✅ OPERATIVO (8/8 bugs resueltos — train/test split, oversampling, is_placeholder, retrain en ciclo vivo)
[6] NexusGate (Dynamic Causal)    ← ✅ OPERATIVO (ΔCausal Real-time)
[7] AutoProposer / Evolution      ← ✅ OPERATIVO (EvolutionOrchestrator Active)
```

**Cada componente tiene su origen en la Bóveda. Ninguno se escribe desde cero.**

### 1.3 El Ciclo de Vida Completo de la Constructora

```
                    ┌─────────────────────────────────┐
                    │   BÓVEDA CAPA 1 (Provisional)   │
                    │   legacy_vault/ — Herencia Bruta│
                    └──────────────┬──────────────────┘
                                   │ Cosecha (Sección 7)
                                   ▼
                    ┌─────────────────────────────────┐
                    │   MOSAIC BRIDGE (Sección 7)     │
                    │   Discovery → Wrap → Audit      │
                    │   → Register → Canary Push      │
                    └──────────────┬──────────────────┘
                                   │ Componente adaptado
                                   ▼
                    ┌─────────────────────────────────┐
                    │   SIMPLE FOUNDATION STRATEGY    │
                    │   Pipeline 7 componentes        │
                    │   Shadow Trading → MFE/MAE      │
                    └──────────────┬──────────────────┘
                                   │ Resultados reales OOS
                                   ▼
                    ┌─────────────────────────────────┐
                    │   ORACLE TRAINER (Meta-Label)   │
                    │   Entrena → Valida → Auto-Prop  │
                    └──────────────┬──────────────────┘
                                   │ ΔCausal > umbral
                                   ▼
                    ┌─────────────────────────────────┐
                    │   NEXUS GATE (Aprobación)       │
                    │   Gate binario + Human-in-loop  │
                    └──────────────┬──────────────────┘
                                   │ Aprobado
                                   ▼
                    ┌─────────────────────────────────┐
                    │   BÓVEDA CAPA 2 (Permanente)    │
                    │   ADN de v3 — Solo lo que       │
                    │   demostró ΔCausal real > 0     │
                    └──────────────┬──────────────────┘
                                   │ Purga del origen
                                   ▼
                    ┌─────────────────────────────────┐
                    │   CAPA 1: Componente PURGADO    │
                    │   Marcado → Archivado → Borrado │
                    └─────────────────────────────────┘
```

### 1.4 El CGA_Nexus: Coordinador y Juez del Gate

El Nexus en v3 opera en modo simplificado para la Simple Foundation Strategy. Su Gate es **binario**:

```python
NexusGate(
    input=ComponentPerformanceReport,
    conditions=[
        delta_causal > 0,                    # ΔCausal positivo en OOS
        blind_test_ratio <= 0.25,            # Cobertura de microestructura suficiente
        test_coverage >= 0.80,               # Tests aprobados
        oos_hit_rate_improvement > 0,        # Mejora neta en Hit-Rate OOS
        human_approval == True               # Aprobación humana explícita
    ],
    output="PROMOTE_TO_LAYER_2" | "REJECT_TO_LEARNING_VAULT"
)
```

Si cualquier condición falla: el componente no pasa. No hay excepciones, no hay casos especiales, no hay "aprobación provisional". El ADN Permanente solo acepta lo que lo merece.

### 1.5 El Semáforo de Recursos (CGA_Ops) — Invariante

Algoritmo determinista `psutil`. No es IA. Primera capa de auto-gobierno de la Constructora:

| Estado | Condición | Acción |
|---|---|---|
| 🟢 Verde | RAM < 60% | Construcción activa permitida |
| 🟡 Amarillo | RAM 60–80% | Pausar nuevos ciclos de entrenamiento Oracle |
| 🔴 Rojo | Señal de trading o ejecución real detectada | Matar procesos CGAlpha — ceder CPU al Cuerpo (Aipha) |

### 1.6 Las Dos Capas Meta-Cognitivas (Herencia v2 Activa)

**Capa 0a — Principios Meta-Cognitivos:**
Lila aprende principios antes de recomendar acciones. Corpus obligatorio:
- López de Prado: *Meta-Labeling*, *Triple Barrier Method*, *Backtest Overfitting*
- EconML: *DML*, *CATE estimation*, *Causal inference in observational data*
- Microestructura: *VWAP real-time*, *Order Book Imbalance*, *Cumulative Delta*

**Capa 0b — Papers de Trading:**
Referencias que informan al Observer. Consultables antes de cualquier propuesta de ajuste paramétrico.

---

## SECCIÓN 2: EL CICLO DE VIDA DEL CAMBIO — PROTOCOLO CODECRAFT v3

### 2.1 El Contrato Inmutable del Builder

```
Parse Safely → Modify Safely → Validate Strictly →
Version Safely → Expose Controls → Keep Proposals Advisory
```

Este contrato no cambia entre versiones. Lo que cambia en v3 es que cada fase del Builder ahora tiene una **responsabilidad adicional hacia la Biblioteca Vectorial**: si el componente creado o modificado es reutilizable, debe registrarse o actualizarse en la Biblioteca como parte del proceso normal de la Fase 4.

### 2.2 Las 6 Fases del ChangeProposer v3 (Resumen Ejecutivo)

| Fase | Función | Invariante Crítica |
|---|---|---|
| **1 — Proposal Parser** | `TechnicalSpec` validado | Determinista primero; LLM como fallback |
| **2 — AST Modifier** | Modificación estructural del código | `Fail Closed` ante ambigüedad; backup antes de mutar |
| **3 — Test Barrier** | Triple Barrera: cambio + regresión + calidad | Cero fallos tolerados; cobertura ≥ 80% |
| **4 — Git Automation** | Feature branch con metadata causal | Sin push automático; sin escritura a `main` |
| **5 — CLI Integration** | Pipeline expuesto como flujo operador | Rollback explícito en caso de fallo |
| **6 — Auto-Proposals** | Detección de drift → propuestas paramétricas | Propone únicamente; umbral `causal_score ≥ 0.75` |

### 2.3 Extensión v3: El Builder como Curador de Biblioteca

En cada ejecución exitosa del pipeline (Fases 1–6), el Builder ejecuta adicionalmente:

```python
# Extensión obligatoria de Fase 4 en v3
def post_implementation_library_duty(self, component: ComponentManifest):
    """
    Responsabilidad del Builder hacia la Biblioteca.
    Se ejecuta después de cada merge aprobado.
    """
    if component.is_reusable:
        if self.library.exists(component.component_id):
            # Actualizar versión existente
            self.library.update_version(component)
            self.library.archive_previous_version(component)
        else:
            # Registrar componente nuevo
            self.library.register(component)
        
        # Recalcular correlaciones con componentes afectados
        self.library.refresh_correlation_map(component.component_id)
        
        # Log de evolución para auditoría
        self.evolution_log.append(component)
```

### 2.4 El Ciclo de Propuesta Automática para el Oracle

La Fase 6 (Auto-Proposals) tiene un pipeline especializado para el Oracle:

```
1. Oracle detecta señal con confidence < 0.70 en datos recientes
           ↓
2. Ghost Architect (Observer) analiza el patrón de fallos:
   - analyze_false_positives() → ¿Por qué predijo TP pero fue SL?
   - analyze_false_negatives() → ¿Por qué no predijo TP?
   - detect_edge_cases() → ¿En qué régimen falla sistemáticamente?
           ↓
3. AutoProposer genera propuesta paramétrica:
   {"component": "OracleV3", "parameter": "volume_threshold",
    "old_value": 80, "new_value": 85,
    "reason": "Falsos positivos en sesión asiática — volumen institucional insuficiente",
    "causal_score_estimated": 0.78}
           ↓
4. Validación OOS obligatoria (mínimo 2 semanas de datos reales)
           ↓
5. Si ΔCausal_real >= ΔCausal_estimado × 0.80 → Merge aprobado
   Si no → Rechazado → Vault de aprendizaje → bridge.jsonl actualizado
```

### 2.5 El Deep Causal Gate — Umbrales Canónicos v3

```python
DEEP_CAUSAL_THRESHOLDS = {
    "max_blind_test_ratio":           0.25,   # > 25% BLIND_TEST = bloqueo total
    "max_nearest_match_avg_lag_ms":   150,    # Latencia máxima de microestructura
    "min_causal_accuracy":            0.55,   # Precisión causal mínima
    "min_efficiency":                 0.40,   # Eficiencia mínima del pipeline
    "min_oos_hit_rate_improvement":   0.00,   # Mejora neta > 0 en datos OOS
    "min_proposal_causal_score":      0.75,   # Score mínimo para presentar propuesta
    "min_oracle_confidence":          0.70    # Confidence mínima para operar
}

MICROSTRUCTURE_MODES_PRIORITY = [
    "ENRICHED_EXACT",    # Confianza: Alta
    "ENRICHED_NEAREST",  # Confianza: Media (lag ≤ 150ms)
    "LOCAL_ONLY",        # Confianza: Media-baja
    "BLIND_TEST"         # Confianza: BLOQUEADA para producción
]
```

### 2.6 Runbook Operativo de la Constructora

**Diario:**
```bash
cgalpha ask-health --smoke
python -m pytest -q tests/
cgalpha auto-analyze --working-dir .
cgalpha vault status         # Ver estado de Capa 1 y Capa 2
cgalpha library stats        # Ver salud de la Biblioteca Vectorial
# Revisar blind_test_ratio y gates → decisión: hold / construct / purge
```

**Semanal:**
```bash
cgalpha oracle monitor --window 2weeks
cgalpha causal dashboard --cluster-breakdown
cgalpha vault purge-candidates  # Lista componentes Capa 1 listos para eliminar
```

### 2.7 CodeCraft Sage Operativo: De Propuesta Aprobada a Commit Trazable

Para eliminar ambigüedad, en v3 `CodeCraft Sage` tiene un contrato operativo explícito: **si una propuesta está aprobada, debe producir código en rama feature y persistirlo en Git solo después de pasar la Triple Barrera de Tests**.

**Precondiciones obligatorias:**
- `proposal.causal_score >= 0.75`
- `ghost_architect_approved == True`
- `human_approved == True`
- `TechnicalSpec` completo con archivos objetivo y pruebas mínimas

**Sucesión de procesamiento de datos (orden canónico):**

```
FASE 2 (Retroanálisis)
phase2_retroanalysis.json
    └── improvement_proposal.technical_specs
            ↓
Observer + Operador
ghost_audit + human approval
            ↓
CodeCraft Sage (Fases 1–6)
  1) Parser      -> 01_change_plan.json
  2) Modifier    -> 02_patch_manifest.json
  3) TestBarrier -> 03_test_report.json
  4) GitPersist  -> commit SHA (feature/*)
  5) CLIExpose   -> estado operativo reproducible
  6) AutoLoop    -> feedback al AutoProposer / Library
            ↓
NexusGate
PROMOTE_TO_LAYER_2 | REJECT_TO_LEARNING_VAULT
            ↓
Memoria + Biblioteca
bridge.jsonl / evolution_log / catalog.jsonl
```

**Reglas de ejecución no negociables:**
- Nunca escribir en `main` desde CodeCraft.
- Si falla cualquier test de la Triple Barrera: `abort_without_commit`.
- Si tests pasan: commit obligatorio en rama `feature/codecraft_*` con metadata causal.
- El `commit_sha` queda referenciado en el reporte de ejecución y en memoria evolutiva.

**Pseudo-contrato mínimo:**

```python
def execute_approved_proposal(proposal: TechnicalSpec) -> ExecutionResult:
    assert proposal.causal_score >= 0.75
    assert proposal.ghost_approved and proposal.human_approved

    plan = parse_proposal(proposal)
    checkout_feature_branch(plan.branch_name)
    apply_changes(plan)

    test_report = run_triple_test_barrier(plan.required_tests)
    if not test_report.all_passed:
        rollback_working_tree()
        return ExecutionResult(status="REJECTED_NO_COMMIT")

    commit_sha = persist_git_commit(plan, test_report)
    publish_execution_artifacts(plan, test_report, commit_sha)
    return ExecutionResult(status="COMMITTED", commit_sha=commit_sha)
```

---

## SECCIÓN 3: BÓVEDA DE DOS CAPAS — TAXONOMÍA DE PURIFICACIÓN EVOLUTIVA

### 3.1 El Principio de las Dos Capas

La Bóveda de v3 no es un almacén único. Es un sistema de **purificación por uso y validación causal**. Toda herencia entra por la Capa 1. Solo lo que demuestra ΔCausal positivo en datos reales llega a la Capa 2. La Capa 1 tiene **fecha de muerte programada**.

```
┌─────────────────────────────────────────────────────────────────┐
│  CAPA 1: BÓVEDA PROVISIONAL (legacy_vault/)                     │
│  ─────────────────────────────────────────────────────────────  │
│  Contenido: Herencia bruta de v1/v2. Código tal como fue.       │
│  Propósito: Fuente de cosecha para el Mosaic Bridge.            │
│  Estado de cada componente: UNVALIDATED | IN_REVIEW | PURGEABLE │
│  Destino final: ELIMINACIÓN TOTAL una vez Capa 2 está madura.   │
└─────────────────────────────────────────────────────────────────┘
                              │
                    Mosaic Bridge (Sección 7)
                    ΔCausal > 0 en datos OOS
                    Nexus Gate aprobado
                    Human approval
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  CAPA 2: BÓVEDA PERMANENTE (component_library/ + dna_core/)     │
│  ─────────────────────────────────────────────────────────────  │
│  Contenido: Componentes que Lila usó REALMENTE y que            │
│             demostraron ΔCausal > 0 en datos OOS.               │
│  Propósito: ADN de v3. Base inmutable para construir            │
│             estrategias actuales y futuras.                      │
│  Estado de cada componente: ACTIVE | DEPRECATED | EVOLVED       │
│  Destino final: PERMANENTE (solo evoluciona, nunca se borra     │
│             sin reemplazo validado).                             │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Estructura Física de la Bóveda Completa

```
cgalpha_v3/
│
├── legacy_vault/                    # CAPA 1: PROVISIONAL
│   │   [Destino: eliminación total]
│   │
│   ├── v1/
│   │   ├── cgalpha/
│   │   │   ├── nexus/coordinator.py          # Estado: IN_REVIEW
│   │   │   ├── nexus/task_buffer.py          # Estado: IN_REVIEW
│   │   │   ├── labs/signal_detection_lab.py  # Estado: IN_REVIEW
│   │   │   ├── labs/zone_physics_lab.py      # Estado: IN_REVIEW
│   │   │   ├── labs/execution_optimizer_lab.py # Estado: IN_REVIEW
│   │   │   ├── labs/risk_barrier_lab.py      # Estado: IN_REVIEW
│   │   │   └── ghost_architect/simple_causal_analyzer.py # IN_REVIEW
│   │   └── core/
│   │       ├── context_sentinel.py           # Estado: IN_REVIEW
│   │       ├── change_proposer.py            # Estado: IN_REVIEW
│   │       └── change_evaluator.py           # Estado: IN_REVIEW
│   │
│   ├── v2/
│   │   ├── meta_cognitive/
│   │   │   ├── layer_0a/                     # Estado: UNVALIDATED
│   │   │   └── layer_0b/                     # Estado: UNVALIDATED
│   │   └── operational/
│   │       ├── layer_1_storage/              # Estado: UNVALIDATED
│   │       ├── layer_2_retrieval/            # Estado: UNVALIDATED
│   │       └── layer_3_application/          # Estado: UNVALIDATED
│   │
│   ├── infrastructure/
│   │   ├── data_processor/data_system/
│   │   │   ├── client.py                     # Estado: IN_REVIEW
│   │   │   ├── fetcher.py                    # Estado: IN_REVIEW
│   │   │   ├── templates.py                  # Estado: IN_REVIEW
│   │   │   ├── storage.py                    # Estado: IN_REVIEW
│   │   │   └── main.py                       # Estado: IN_REVIEW
│   │   ├── redis_infrastructure/             # Estado: UNVALIDATED
│   │   └── oracle/models/
│   │       ├── oracle_5m_v1.joblib           # Estado: PURGEABLE ❌
│   │       └── oracle_5m_v2_multiyear.joblib # Estado: IN_REVIEW (baseline ref)
│   │
│   └── vault_manifest.jsonl                  # Inventario con estado de cada componente
│
├── component_library/               # CAPA 2: PERMANENTE
│   │   [Solo lo que pasó el Gate + OOS + Human Approval]
│   │
│   ├── dna_core/                    # Componentes fundamentales del ADN
│   │   ├── active/                  # En uso activo en estrategias
│   │   ├── deprecated/              # Reemplazados por versión mejorada
│   │   └── evolved/                 # Mejorados por CodeCraft (historial completo)
│   │
│   ├── registry/
│   │   ├── catalog.jsonl            # Índice de todos los componentes Capa 2
│   │   ├── embeddings.db            # Base vectorial (DuckDB)
│   │   └── correlation_map.json     # Mapa de correlaciones descubiertas
│   │
│   ├── components/
│   │   ├── signal/                  # Detección de señales
│   │   ├── entry/                   # Optimización de entrada
│   │   ├── exit/                    # Gestión de salida
│   │   ├── filtering/               # Filtrado causal
│   │   ├── microstructure/          # VWAP, OBI, CumDelta
│   │   ├── labeling/                # Triple Barrier, Ordinal
│   │   └── meta/                    # Principios meta-cognitivos
│   │
│   ├── strategies/
│   │   └── simple_foundation/       # La primera estrategia completa
│   │       ├── manifest.json
│   │       ├── pipeline.py
│   │       └── oos_results.jsonl
│   │
│   └── evolution_log/
│       └── improvements.jsonl       # Historial de mejoras por CodeCraft
│
└── aipha_memory/
    ├── operational/
    │   └── order_book_features.jsonl  # ⭐ Fuente oficial de microestructura
    └── evolutionary/
        └── bridge.jsonl               # ⭐ Vector de Evidencia — Puente causal
```

### 3.3 El Ciclo de Vida de un Componente en la Bóveda

```
UNVALIDATED (Capa 1, sin examinar)
    ↓ [cgalpha vault index]
IN_REVIEW (Capa 1, candidato identificado)
    ↓ [Mosaic Bridge: Discovery → Wrap → Ghost Audit]
ADAPTED (En proceso de adaptación v3, aún no en Capa 2)
    ↓ [CodeCraft Fases 1-6 + OOS Validation ≥ 2 semanas]
PROMOTED (ΔCausal > 0 confirmado, Gate aprobado)
    ↓ [cgalpha vault promote {component_id}]
ACTIVE en Capa 2 ← ESTADO OBJETIVO
    ↓ [cgalpha vault purge-origin {component_id}]
Origen en Capa 1 → PURGEABLE
    ↓ [cgalpha vault purge --confirmed]
Origen en Capa 1 → ELIMINADO
```

**Estados de emergencia:**
- `ROLLBACK`: Componente Capa 2 revertido a versión anterior (fallo en producción)
- `DEPRECATED`: Reemplazado por versión mejorada; versión anterior archivada
- `REJECTED`: Falló validación OOS; no pasa a Capa 2; aprendizaje registrado en bridge.jsonl

### 3.4 Componentes de Capa 1 Priorizados para Cosecha

Los siguientes componentes son candidatos inmediatos para iniciar el proceso de adaptación hacia la Simple Foundation Strategy:

| Componente Capa 1 | Componente v3 Objetivo | Prioridad | Estado Inicial |
|---|---|---|---|
| `fetcher.py` (BinanceKlinesFetcher) | `BinanceVisionFetcher_v3` | 🔴 CRÍTICA | IN_REVIEW |
| `signal_detection_lab.py` (Triple Coincidencia) | `TripleCoincidenceDetector` | 🔴 CRÍTICA | ACTIVE |
| `zone_physics_lab.py` | `ZonePhysicsMonitor_v3` | 🔴 CRÍTICA | IN_REVIEW |
| `storage.py` (DuckDB) | `PersistenceEngine_v3` | 🟠 ALTA | IN_REVIEW |
| `risk_barrier_lab.py` (DML) | `RiskBarrierLab_v3` | 🟠 ALTA | IN_REVIEW |
| `simple_causal_analyzer.py` | `GhostArchitect_v3` | 🟠 ALTA | IN_REVIEW |
| `context_sentinel.py` | `ContextSentinel_v3` | 🟡 MEDIA | IN_REVIEW |
| `task_buffer.py` | `NexusTaskBuffer_v3` | 🟡 MEDIA | IN_REVIEW |
| `oracle_5m_v2_multiyear.joblib` | Baseline de referencia Oracle_v3 | 🟡 MEDIA | IN_REVIEW |
| `layer_0a/, layer_0b/` (v2 meta-cog) | Corpus de principios activo | 🟢 BAJA | UNVALIDATED |
| `oracle_5m_v1.joblib` | ❌ No migrar | — | PURGEABLE ❌ |

### 3.5 El Dashboard de Evolución (GUI Management)

La GUI de gestión de la Bóveda debe mostrar en tiempo real:

```
┌──────────────────────────────────────────────────────────────┐
│  VAULT EVOLUTION DASHBOARD                                   │
├──────────────────┬───────────────────────────────────────────┤
│  CAPA 1 STATUS  │  CAPA 2 STATUS                            │
│  ─────────────  │  ────────────                             │
│  Total: 47      │  Total: 0 → creciente                     │
│  UNVALIDATED: 31│  ACTIVE: X                                │
│  IN_REVIEW: 14  │  DEPRECATED: Y                            │
│  PURGEABLE: 2   │  EVOLVED: Z                               │
│  [❌ oracle_v1] │  avg ΔCausal: {score}                     │
├──────────────────┴───────────────────────────────────────────┤
│  SIMPLE FOUNDATION STRATEGY — FASE ACTUAL                   │
│  [████████░░░░░░░░] Fase 3/7: ZonePhysicsMonitor en OOS     │
│                                                              │
│  Componente actual: ZonePhysicsMonitor_v3                   │
│  Estado: VALIDACIÓN OOS (Semana 1 de 2)                     │
│  ΔCausal estimado: 0.81 | ΔCausal real (parcial): 0.74     │
│  Hit-Rate OOS acumulado: +3.2% vs baseline                  │
│                                                              │
│  [APROBAR Y PROMOVER A CAPA 2] [RECHAZAR] [VER DETALLES]   │
└──────────────────────────────────────────────────────────────┘
```

---

## SECCIÓN 4: EL ALPHA CORE — LA TRINIDAD DE LA MICROESTRUCTURA

### 4.1 Corrección Fundamental: ATR como Métrica de Contexto, No de Motor

**Esta es la corrección más importante de la Sección 4 respecto a versiones anteriores.**

El ATR (Average True Range) fue usado en v1/v2 como la unidad universal de todo: barreras, stops, take-profits, umbral de decisión. Esa postura era válida para temporalidades diarias y de 5 minutos con contexto de swing trading. **No es el motor apropiado para Scalping en 1–5 minutos.**

En v3, el ATR mantiene su rol como **unidad de normalización y contexto de régimen**, pero cede el rol de motor primario de decisión a la **Trinidad de la Microestructura**.

> ⚠️ **ASPIRACIÓN vs REALIDAD (19 abril 2026):** El Oracle entrenado asigna ATR = 37.5% de feature importance — sigue siendo el factor dominante del modelo RF. La separación arquitectónica descrita a continuación es el diseño objetivo; el modelo entrenado actual no la refleja porque el dataset tiene solo 98 samples y las features de microestructura (OBI, CumDelta) aún están subrepresentadas.


```
╔════════════════════════════════════════════════════════════════╗
║  EL ALPHA CORE DE LILA v3 (SCALPING 1-5 MIN)                 ║
║                                                               ║
║  Motor Primario: TRINIDAD DE LA MICROESTRUCTURA               ║
║  ─────────────────────────────────────────────────────────── ║
║                                                               ║
║  [1] VWAP en Tiempo Real                                      ║
║      Niveles dinámicos de soporte/resistencia.                ║
║      La "gravedad" del precio institucional.                  ║
║                                                               ║
║  [2] OBI (Order Book Imbalance)                               ║
║      Confirmación de dirección real por liquidez.             ║
║      La "intención" del mercado antes de moverse.             ║
║                                                               ║
║  [3] Cumulative Delta                                         ║
║      Detección de agotamiento y reversión.                    ║
║      El "pulso" de la presión compradora vs vendedora.        ║
║                                                               ║
║  Motor de Contexto: ATR                                       ║
║  ─────────────────────────────────────────────────────────── ║
║  Normalización de volatilidad. Clasificación de régimen.      ║
║  Sizing de barreras. No toma decisiones de dirección.         ║
╚════════════════════════════════════════════════════════════════╝
```

### 4.2 VWAP en Tiempo Real — Soporte/Resistencia Dinámico

**Función en el pipeline:** El precio del mercado tiende a revertir hacia el VWAP o usar sus desviaciones estándar como niveles de rechazo. En scalping, el VWAP es la línea de "justo precio" ponderado por volumen. Las operaciones se toman **en relación al VWAP**, no aisladas de él.

**Reglas operativas para la Simple Foundation Strategy:**
```python
VWAPContextRules(
    long_bias=  price < vwap AND zone_physics == "REBOTE_CONFIRMADO",
    short_bias= price > vwap AND zone_physics == "REBOTE_CONFIRMADO",
    neutral=    abs(price - vwap) / atr < 0.3,  # Precio pegado al VWAP → sin sesgo claro
    
    # Niveles de referencia dinámicos
    support_1= vwap - 1 * std_dev,
    support_2= vwap - 2 * std_dev,
    resistance_1= vwap + 1 * std_dev,
    resistance_2= vwap + 2 * std_dev
)
```

**Fuente de datos:** `order_book_features.jsonl` + streaming en tiempo real vía BinanceVisionFetcher_v3.

### 4.3 OBI (Order Book Imbalance) — La Intención del Mercado

**Función en el pipeline:** El OBI mide el desequilibrio entre las órdenes de compra y venta en el libro de órdenes **antes de que el precio se mueva**. Es un indicador líder, no rezagado. Un OBI positivo fuerte indica presión compradora real (no especulación); un OBI negativo fuerte indica presión vendedora institucional.

**Cálculo:**
```python
def calculate_obi(order_book: OrderBook, levels: int = 10) -> float:
    """
    OBI = (Bid Volume - Ask Volume) / (Bid Volume + Ask Volume)
    Range: [-1, +1]
    +1 = Presión compradora absoluta
    -1 = Presión vendedora absoluta
     0 = Balance perfecto (mercado indeciso)
    """
    bid_vol = sum(order_book.bids[:levels, 1])
    ask_vol = sum(order_book.asks[:levels, 1])
    return (bid_vol - ask_vol) / (bid_vol + ask_vol)
```

**Regla de confirmación en la Simple Foundation Strategy:**
```python
# El OBI confirma la señal de zona; nunca la genera solo
signal_confirmed = (
    zone_physics == "REBOTE_CONFIRMADO" AND
    vwap_context == "long_bias" AND
    obi > 0.15  # Umbral: desequilibrio comprador suficiente
)
```

### 4.4 Cumulative Delta — El Pulso de Agotamiento

**Función en el pipeline:** El Cumulative Delta acumula la diferencia entre volumen de compra agresiva (market orders buy) y venta agresiva (market orders sell) a lo largo del tiempo. Cuando el precio sube pero el CumDelta cae → divergencia → **agotamiento del impulso** → señal de reversión. Cuando el precio cae pero el CumDelta sube → acumulación oculta → **absorción institucional** → señal de rebote.

**Integración con la Trinity:**
```python
TrinitySignal(
    vwap_signal=vwap_context,        # Nivel de precio en relación al precio justo
    obi_signal=obi_value,             # Presión instantánea de liquidez
    cum_delta_signal=delta_divergence, # ¿El movimiento tiene convicción de volumen?
    
    # Regla de confluencia (los 3 deben alinearse para operar)
    execute_long= (
        vwap_context == "long_bias" AND
        obi > 0.15 AND
        cum_delta_trend == "BULLISH_ABSORPTION"  # CumDelta sube mientras precio baja
    ),
    execute_short= (
        vwap_context == "short_bias" AND
        obi < -0.15 AND
        cum_delta_trend == "BEARISH_EXHAUSTION"  # CumDelta cae mientras precio sube
    )
)
```

### 4.5 ATR: Rol de Contexto y Normalización

El ATR retiene cuatro funciones específicas en v3:

| Función | Descripción | Fórmula/Uso |
|---|---|---|
| **Régimen de mercado** | Clasificar volatilidad del período | `ATR > percentile(70)` → High Vol |
| **Sizing de barreras** | Calibrar TP y SL dinámicamente | `TP = entry ± tp_factor × ATR` |
| **Normalización de resultados** | `outcome_ordinal` en unidades ATR | `MFE / ATR(14)` |
| **Umbral de calidad de señal** | Filtrar ruido en detección de zonas | `zone_size > min_atr_multiple` |

**El ATR NO decide la dirección de la operación en v3.** Eso lo decide la Trinity.

### 4.6 El Oracle v3: Meta-Labeling sobre la Trinity

El Oracle v3 aplica el principio de Meta-Labeling de López de Prado sobre las señales de la Trinity:

```
Trinity genera señal (dirección + contexto)
         ↓
Oracle v3 evalúa: ¿Las condiciones actuales del mercado
                   favorecen que ESTA señal llegue a TP?
         ↓
predict_proba() → confidence score
         ↓
Si confidence > 0.70 → Ejecutar (Shadow Trade o Live)
Si confidence ≤ 0.70 → Ignorar (registrar en bridge.jsonl como aprendizaje)
```

**El Oracle no predice la dirección del mercado. Filtra la calidad de la señal.** Esta separación de responsabilidades es arquitectónicamente fundamental y no debe violarse en ninguna iteración de v3.

### 4.7 Fuente Oficial de Microestructura

```python
MICROSTRUCTURE_SOURCE = "aipha_memory/operational/order_book_features.jsonl"

# Schema del registro de microestructura
MicrostructureRecord(
    timestamp=int,           # Unix ms
    symbol=str,              # Ej: "BTCUSDT"
    vwap=float,              # VWAP acumulado del día
    vwap_std_1=float,        # Desviación estándar 1
    vwap_std_2=float,        # Desviación estándar 2
    obi_10=float,            # OBI con 10 niveles de profundidad
    obi_20=float,            # OBI con 20 niveles
    cumulative_delta=float,  # Delta acumulado desde apertura de sesión
    delta_divergence=str,    # "BULLISH_ABSORPTION"|"BEARISH_EXHAUSTION"|"NEUTRAL"
    atr_14=float,            # ATR de contexto
    regime=str               # "HIGH_VOL"|"TREND"|"LATERAL"
)
```

---

## SECCIÓN 5: GLOSARIO DEL NORTE v3.0

*Vocabulario canónico de la Constructora. Sin este lenguaje, los documentos del vault y las instrucciones del Mosaic Bridge son ruido.*

---

### NOTA CRÍTICA: Oracle Training y Data Curation (Sesión 17 Abril 2026)

**Status actual del Oracle v3:**

- **Modelo:** RandomForestClassifier(n_estimators=100, max_depth=5)
- **Dataset:** 98 training samples (BOUNCE: 92 | BREAKOUT: 6)
- **Train accuracy:** 97.96% — PERO el modelo predice clase mayoritaria
- **Real performace:** Win rate 50%, Sharpe 1.13 — ⚠️ **DATO NO VERIFICABLE:** No hay train/test split (BUG-1). Las métricas OOS reportadas no provienen de un holdout real. El RF con 98 samples entrena y evalúa sobre el mismo dataset.

**El problema arquitectónico:**

El dataset es 94% BOUNCE. El modelo aprendió "casi siempre es BOUNCE". El accuracy no refleja discriminación real.

**La solución — Training Review + Approval Workflow:**

El flujo correcto es:

```
1. TripleCoincidenceDetector genera retests (labels crudos: 0.5% umbral)
2. Training Review GUI muestra chart con zonas, retests, outcomes
3. Operador revisa VISUALMENTE cada detección:
   - ¿La zona tiene sentido? (acumulación visible)
   - ¿El retest es legítimo? (precio vraiment volvió)
   - ¿El outcome es correcto? (BOUNCE/BREAKOUT coherente)
4. Operador approve/reject con training_approvals.jsonl
   ⚠️ **NO IMPLEMENTADO:** Los endpoints approve/reject son stubs vacíos
   (server.py líneas 2239-2250). No escriben en training_approvals.jsonl.
   Este paso bloquea todo el flujo de curación. Ver BUG-8 en LILA_V4 §1.2.
5. AutoProposer.analyze_drift() filtra solo samples aprobados
   ⚠️ **IMPOSIBLE sin paso 4:** Si no hay training_approvals.jsonl
   persistido, no hay nada que filtrar.
6. Oracle.train_model() entrena con dataset limpio
7. Modelo discrimina mejor porque etiquetas son correctas
```

**Labels crudos vs. etiquetas corregidas:**

- **Crudo:** ¿Movió >0.5% en 10 velas? → BOUNCE
- **Corregido:** ¿Llegó a TP (zone_top/bottom ± X%) antes de SL? → ALTA_CALIDAD

Sin esta curación pre-entrenamiento, el modelo es tan bueno como el etiquetado fuente. Esto es irremplazable y depende de la expertise del operador.

---

**TripleCoincidenceDetector**  
Componente v3 que hereda del `KeyCandleDetector` y `SignalDetectionLab` de Capa 1. Detecta zonas de alta probabilidad por triple coincidencia: vela clave (alto volumen + cuerpo pequeño) + zona de acumulación (rango estrecho + volumen elevado) + mini-tendencia (ZigZag + R² > 0.45). Monitorea zonas activas para detectar retests y captura features de microestructura (VWAP, OBI, CumDelta) EN el momento del retest. Genera dataset de entrenamiento [features_retest → outcome]. Parámetros validados: `volume_percentile_threshold=70`, `body_percentage_threshold=40`, `r2_min=0.45`. Primer componente de la Simple Foundation Strategy.

**ADN Permanente**  
El conjunto de componentes de la Capa 2 que han demostrado ΔCausal > 0 en datos reales OOS y han pasado el Nexus Gate con aprobación humana. No se destruye sin reemplazo validado. Es la identidad técnica de v3.

**ApiClient / BinanceVisionFetcher_v3**  
Componente de ingestión de datos. Hereda `client.py` y `fetcher.py` de Capa 1. Flujo: URL de Binance Vision → descarga ZIP con cache local → parse CSV → DataFrame tipado. En v3 se extiende para incluir adquisición de datos de microestructura (order book snapshots) además de OHLCV.

**ATR (Average True Range)**  
En v3: métrica de contexto y normalización. No es el motor de decisión para scalping. Define régimen de mercado, calibra tamaño de barreras y normaliza resultados en unidades comparables. La Trinity de Microestructura toma las decisiones de dirección.

**AutoProposer**  
Componente de Fase 6 (CodeCraft) especializado en el Oracle. Detecta drift en accuracy o patrones de fallos y genera propuestas paramétricas con `causal_score` estimado. Requiere validación OOS de mínimo 2 semanas antes de promoción.

**BinanceVisionFetcher_v3**  
Ver ApiClient / BinanceVisionFetcher_v3.

**BLIND_TEST**  
Estado de un trade analizado sin match válido de microestructura. Prohíbe inferencias causales de alta confianza. Si `blind_test_ratio > 0.25`, el sistema bloquea avance de fases y solo permite Paper Trading.

**bridge.jsonl**  
Registro inmutable de cada trade con su Vector de Evidencia completo. Schema v3 incluye `microstructure_mode`, `trinity_signal`, y `oracle_confidence` además de los campos heredados. Fuente primaria para el DML y el entrenamiento del Oracle.

**Builder**  
Pilar operativo. Motor: CodeCraft Sage (Fases 1–6). En v3 subordinado a la misión de la Constructora. Responsable adicionalmente de mantener la Biblioteca Vectorial actualizada después de cada implementación exitosa.

**CATE (Conditional Average Treatment Effect)**  
Efecto causal de una decisión condicionado al régimen de mercado. `CATE > 0` en un cluster = la decisión fue benéfica en ese contexto específico. Base matemática del ΔCausal.

**CGA_Nexus**  
Coordinador Supremo. Orquesta los 4 Labs y opera el Nexus Gate en la Simple Foundation Strategy. En v3, su Gate es binario: PROMOTE_TO_LAYER_2 o REJECT.

**CGA_Ops**  
Supervisor de recursos determinista (`psutil`). Semáforo Verde/Amarillo/Rojo. La primera capa de auto-gobierno de la Constructora.

**CodeCraft Sage**  
El Builder del sistema. Las 6 fases constituyen el pipeline completo desde propuesta hasta código versionado. En v3, crea código en rama `feature/*`, ejecuta Triple Barrera de Tests, y solo entonces persiste commit trazable en Git; además actúa como curador activo de la Biblioteca Vectorial.

**Component Library (Biblioteca Vectorial)**  
La Capa 2 de la Bóveda en su dimensión técnica. Almacén vectorial de componentes reutilizables. Organización por similitud semántica y correlación causal. Mantenida por CodeCraft Sage.

**ComponentManifest**  
Registro estructurado de un componente en la Biblioteca. Incluye: identidad, genealogía, parámetros validados, `causal_score`, `test_coverage`, embedding vectorial, correlaciones descubiertas, y referencia al origen en Capa 1 (para trazabilidad de purga).

**Constructora**  
El rol primario de Lila en v3. Supraordina a Builder y Observer. Misión: ensamblar la Simple Foundation Strategy, entrenar el Oracle, validar en OOS, y purificar la Bóveda hasta que solo quede ADN Permanente.

**Cumulative Delta**  
Feature de microestructura. Diferencia acumulada entre volumen de compra agresiva y venta agresiva. Detecta divergencias: precio sube pero CumDelta cae = agotamiento; precio cae pero CumDelta sube = absorción oculta. Tercer elemento de la Trinity.

**ΔCausal (Delta de Eficiencia Causal)**  
Métrica reina: `ΔCausal = E[Y | T=θ_new, X] − E[Y | T=θ_old, X]`. Mide el mérito real de una decisión después de substraer el efecto que el mercado habría producido de todas formas. Umbral mínimo para promoción a Capa 2: `ΔCausal > 0` confirmado en datos reales OOS.

**Dashboard de Evolución (GUI)**  
Panel de gestión de la Bóveda. Muestra en tiempo real: estado de componentes en Capa 1 y Capa 2, fase actual de la Simple Foundation Strategy, métricas OOS en curso, y botones de acción atómica (Aprobar / Rechazar / Purgar).

**Deep Causal Gate**  
Conjunto de precondiciones binarias para avanzar a producción. Todos deben ser `True`: `data_quality_pass`, `causal_quality_pass`, `proceed_v3`. Umbrales canónicos en Sección 2.5.

**DML (Double Machine Learning)**  
Motor matemático del RiskBarrierLab (EconML). Separa el efecto de la decisión del efecto del contexto en 3 pasos: limpiar Y, limpiar T, regresión de residuos. Produce el CATE que alimenta al ΔCausal.

**DuckDB**  
Motor OLAP local. Persistencia principal del sistema de datos. Sin dependencias de cloud. Inserción directa de DataFrames Pandas. Usado tanto en el data_processor como en la Biblioteca Vectorial.

**Fail Closed**  
Política de seguridad: ante ambigüedad, el sistema no ejecuta antes que ejecutar incorrectamente. Estándar de Fase 2 (AST Modifier) ante ediciones inseguras.

**Gate**  
Criterio duro de control de progresión de fases. Debe pasar repetidamente (no una sola vez) antes de aprobar avance. No hay excepciones ni casos especiales.

**Ghost Architect**  
El Observer del sistema. Fase 7+. Parsea logs, construye snapshots, infiere hipótesis causales. Evalúa propuestas antes de que CodeCraft las implemente. Requiere monitoreo continuo de `blind_test_ratio`.

**Hit-Rate OOS**  
Proporción de aciertos del Oracle o de la estrategia en datos Out-of-Sample. La métrica de validación de primer orden antes de cualquier promoción a Capa 2. Debe mostrar mejora neta > 0% sobre el baseline.

**MAE (Max Adverse Excursion)**  
Peor caída intra-trade desde la entrada. Mide calidad de la entrada. Capturado por el ShadowTrader.

**Meta-Labeling (López de Prado)**  
Principio arquitectónico del Oracle: no predice la dirección del mercado. Predice la calidad (probabilidad de éxito) de una señal ya generada por el sistema primario (Trinity + Triple Coincidencia). Esta separación no debe violarse.

**MFE (Max Favorable Excursion)**  
Máximo potencial alcanzado antes de cerrar. Mide calibración de barreras. Capturado por el ShadowTrader.

**Mosaic Bridge**  
El protocolo técnico de conversión de legado en componentes v3. 5 pasos: Discovery → Standardization → Ghost Audit → Library Registration → Canary Push. Ver Sección 7.

**Microstructure Mode**  
Estado de enriquecimiento de datos: `ENRICHED_EXACT` > `ENRICHED_NEAREST` > `LOCAL_ONLY` > `BLIND_TEST`. Determina el nivel máximo de confianza causal permitido.

**NexusGate**  
Componente de evaluación final de la Simple Foundation Strategy. Gate binario: PROMOTE_TO_LAYER_2 o REJECT. Requiere todas las condiciones del Deep Causal Gate más aprobación humana explícita.

**OBI (Order Book Imbalance)**  
Feature de microestructura. Desequilibrio entre órdenes de compra y venta en el libro. Segundo elemento de la Trinity. Indicador líder: mide la intención del mercado antes de que el precio se mueva. Rango [-1, +1].

**Observer**  
Pilar operativo. Motor: Ghost Architect (Fase 7+). En v3 subordinado a la misión de la Constructora. Analiza resultados y propone ajustes.

**OOS (Out-of-Sample)**  
Período de validación con datos nunca vistos durante el entrenamiento. Mínimo 2 semanas. Obligatorio antes de cualquier promoción a Capa 2. La diferencia train-test debe ser ≤ 10%.

**Oracle_v3**  
Validador de señales. Aplica Meta-Labeling sobre señales de la Trinity. Usa `predict_proba()`. Opera solo si confidence > 0.70. Entrenado recursivamente con resultados del ShadowTrader.

**outcome_ordinal**  
Etiqueta de resultado en magnitud ATR discreta (0, 1, 2, 3+). Invariante crítica: **no hacer break al tocar el primer TP** para registrar hasta dónde llegó realmente el movimiento.

**Purga Evolutiva**  
El acto de eliminar un componente de Capa 1 después de que su equivalente v3 fue promovido a Capa 2 y ha demostrado estabilidad en producción. Cierra el ciclo de purificación de herencia. Ejecutado con `cgalpha vault purge --confirmed`.

**ShadowTrader**  
Componente de Shadow Trading. Abre posiciones virtuales (ficticias) después de cada señal de la Simple Foundation Strategy. Captura trayectorias reales MFE/MAE en mercado real sin riesgo de capital. Sus resultados alimentan el OracleTrainer.

**Simple Foundation Strategy**  
La primera estrategia completa de Lila v3. Pipeline de 7 componentes ensamblados con LEGOs del vault. Primer producto concreto que demuestra que el pipeline v3 opera como unidad coherente. Fuente de datos de entrenamiento para el Oracle_v3.

**Trinity de la Microestructura**  
Los tres pilares del motor de decisión de Lila v3 para scalping 1–5 minutos: VWAP real-time (niveles dinámicos) + OBI (confirmación de liquidez) + Cumulative Delta (detección de agotamiento). Los tres deben alinearse para ejecutar.

**Vector de Evidencia**  
Tupla de alta fidelidad en bridge.jsonl. Schema v3: `{trade_id, config_snapshot, outcome_ordinal, mfe_atr, mae_atr, causal_tags, microstructure_mode, trinity_signal, oracle_confidence}`.

**VWAP (Volume Weighted Average Price)**  
Feature de microestructura. Precio justo del mercado ponderado por volumen. Primer elemento de la Trinity. Actúa como "gravedad" del precio institucional. Sus desviaciones estándar son niveles dinámicos de soporte/resistencia.

**ZonePhysicsMonitor_v3**  
Componente v3 que hereda del `ZonePhysicsLab` de Capa 1. Monitorea el re-test activo del precio a la zona de vela de absorción. Evalúa si el retorno es absorción (rebote probable) o ruptura (continuación). Estados: `REBOTE_CONFIRMADO`, `FAKEOUT_DETECTADO`, `RUPTURA_LIMPIA`, `ABSORCION_EN_CURSO`.

---

## SECCIÓN 6: BIBLIOTECA VECTORIAL — EL ADN VIVO

### 6.1 Función en v3: Del Concepto al Sistema Operativo

La Biblioteca Vectorial en v3 no es aspiracional. Es el mecanismo técnico que implementa la Capa 2 de la Bóveda. Todo lo que entra en la Biblioteca ya pasó el Gate y ya tiene ADN validado.

**Su función principal en v3 es triple:**
1. **Preservar** los componentes que demostraron valor causal real
2. **Organizar** esos componentes para que Lila los encuentre por similitud semántica, no por path de archivo
3. **Evolucionar** cada componente continuamente vía CodeCraft, sin perder la versión anterior

### 6.2 El ComponentManifest: Contrato de ADN

```python
@dataclass
class ComponentManifest:
    # --- IDENTIDAD ---
    component_id: str          # UUID único e inmutable
    name: str                  # "ZonePhysicsMonitor_v3"
    version: str               # "1.0.0" → "1.1.0" → ... (semver)
    category: str              # signal | entry | exit | filtering | microstructure | labeling | meta
    layer: str                 # "layer_2_permanent" siempre para componentes de la Biblioteca
    
    # --- FUNCIÓN ---
    function: str              # Descripción natural de qué hace
    inputs: List[str]          # ["ohlcv_df: pd.DataFrame", "vwap: float"]
    outputs: List[str]         # ["zone_state: str", "retest_score: float"]
    
    # --- PARÁMETROS VALIDADOS ---
    parameters: Dict[str, ParameterSpec]  # Valor + rango + si es crítico
    
    # --- GENEALOGÍA ---
    heritage_source: str       # "legacy_vault/v1/cgalpha/labs/zone_physics_lab.py"
    heritage_contribution: str # Qué se tomó del legado
    v3_adaptations: str        # Qué se cambió/añadió en v3
    vault_origin_purged: bool  # ¿El origen en Capa 1 ya fue eliminado?
    
    # --- VALIDACIÓN CAUSAL ---
    causal_score: float        # ΔCausal medido en datos reales OOS
    oos_period: str            # "2026-02-01 / 2026-02-14"
    hit_rate_improvement: float # Mejora neta en Hit-Rate OOS vs baseline
    validated_regimes: List[str]
    invalid_regimes: List[str]
    cate_by_regime: Dict[str, float]
    
    # --- CALIDAD TÉCNICA ---
    test_coverage: float       # ≥ 0.80 siempre
    complexity_cyclomatic: int # < 15 siempre
    last_codecraft_improvement: str  # Fecha ISO
    rollback_available: bool   # Siempre True mientras haya versión anterior
    
    # --- ORGANIZACIÓN VECTORIAL ---
    embedding_vector: List[float]   # Generado automáticamente por el embedder
    correlated_with: List[CorrelationEdge]  # Actualizado por discover_correlations()
    
    # --- ESTADO ---
    status: str  # ACTIVE | DEPRECATED | EVOLVED | ROLLBACK
```

### 6.3 La Organización Vectorial: Taxonomía Emergente

**Principio crítico:** La organización de la Biblioteca no se pre-define en el diseño. **Emerge de las correlaciones reales entre componentes descubiertas por el sistema durante el uso.** Intentar fijar la taxonomía completa de antemano es un antipatrón que limita la capacidad de Lila de descubrir combinaciones no previstas.

Lo que sí se pre-define es el **protocolo de descubrimiento**:

```python
class ComponentLibrary:
    
    def register(self, manifest: ComponentManifest) -> str:
        """
        Registra componente y genera su embedding vectorial.
        El embedding captura semántica funcional, no solo nombre.
        """
        text_to_embed = f"""
            {manifest.name} {manifest.function}
            inputs: {' '.join(manifest.inputs)}
            outputs: {' '.join(manifest.outputs)}
            category: {manifest.category}
            validated_regimes: {' '.join(manifest.validated_regimes)}
            invalid_regimes: {' '.join(manifest.invalid_regimes)}
            heritage: {manifest.heritage_contribution}
        """
        manifest.embedding_vector = self.embedder.encode(text_to_embed).tolist()
        self._persist(manifest)
        self._update_correlation_map(manifest)
        return manifest.component_id
    
    def search(self, query: str, regime: str = None, top_k: int = 10) -> List[ComponentManifest]:
        """
        Búsqueda semántica por similitud vectorial.
        Filtra opcionalmente por régimen de mercado con CATE > 0.
        """
        query_vec = self.embedder.encode(query)
        results = self.db.execute("""
            SELECT *, cosine_similarity(embedding_vector, ?) AS similarity
            FROM components
            WHERE status = 'ACTIVE'
            ORDER BY similarity DESC
            LIMIT ?
        """, [query_vec, top_k]).fetchall()
        
        if regime:
            results = [r for r in results 
                      if r.cate_by_regime.get(regime, -1) > 0]
        return results
    
    def discover_correlations(self) -> Dict:
        """
        Análisis periódico (semanal) de correlaciones.
        Actualiza correlation_map.json.
        Alimenta la taxonomía emergente.
        Las categorías son sugerencias, no jaulas.
        """
        # Comparar embeddings por pares
        # Correlación por co-uso en estrategias
        # Correlación por complementariedad de CATE (uno funciona donde el otro falla)
        ...
    
    def get_assembly_suggestions(self, objective: str, regime: str) -> StrategyBlueprint:
        """
        Dado un objetivo ("scalping breakout en alta volatilidad")
        y un régimen, sugiere combinaciones de componentes compatibles.
        No pre-define la combinación; la descubre de las correlaciones.
        """
        ...
```

### 6.4 CodeCraft como Curador Perpetuo

Cada merge exitoso en v3 activa el protocolo de curaduría de la Biblioteca:

```python
def post_merge_library_curation(self, component_id: str, new_code: str, causal_score: float):
    """
    Ejecutado automáticamente por CodeCraft Fase 4 después de cada merge.
    Mantiene la Biblioteca como reflejo fiel del sistema en producción.
    """
    old = self.library.get(component_id)
    
    # 1. Archivar versión anterior (siempre disponible para rollback)
    self.library.archive(old)
    
    # 2. Crear nueva versión con métricas actualizadas
    new = ComponentManifest(
        **old.__dict__,
        version=semver_bump(old.version),
        causal_score=causal_score,
        last_codecraft_improvement=today(),
        rollback_available=True
    )
    
    # 3. Regenerar embedding si la función cambió
    if self._function_changed(old, new_code):
        new.embedding_vector = self.embedder.encode(new_code).tolist()
    
    # 4. Registrar versión mejorada
    self.library.register(new)
    
    # 5. Re-evaluar correlaciones de componentes afectados
    affected = self.library.get_correlated(component_id)
    for comp in affected:
        self.library.refresh_correlation(comp.component_id)
    
    # 6. Log de evolución para auditoría completa
    self.evolution_log.record(old, new, causal_score)
    
    # 7. Notificar al Nexus
    self.nexus.notify_component_evolved(component_id, causal_score)
```

### 6.5 Métricas de Salud de la Biblioteca

| Métrica | Descripción | Umbral Saludable v3 |
|---|---|---|
| `library_size` | Componentes activos en Capa 2 | Creciente; ≥ 7 al completar Simple Foundation Strategy |
| `component_reuse_rate` | % de estrategias que usan componentes existentes | > 60% |
| `avg_causal_score` | ΔCausal promedio de componentes activos | > 0.65 |
| `avg_test_coverage` | Cobertura de tests promedio | > 80% |
| `vault_origin_purged_rate` | % de componentes Capa 2 con origen Capa 1 ya eliminado | Creciente hacia 100% |
| `correlation_density` | Conexiones en el mapa de correlaciones | Creciente |
| `deprecated_rate` | % de componentes deprecados por mes | < 10% |
| `capa1_remaining` | Componentes aún en Capa 1 sin migrar | Decreciente hacia 0 |

---

## SECCIÓN 7: THE MOSAIC BRIDGE — PROTOCOLO DE IMPLEMENTACIÓN TÉCNICA

*El Manual de Herramientas de la Constructora. Este protocolo convierte el legado en componentes funcionales de v3 de forma sistemática, reproducible y con trazabilidad causal completa.*

### 7.1 Interfaces de Adaptación: El Wrapper Pattern

**Regla absoluta:** Lila no importa código del `legacy_vault/` directamente en v3. Toda pieza reciclada DEBE envolverse en una interfaz v3 mediante el Adapter Pattern. La razón es doble: garantiza desacoplamiento técnico y hace explícita la genealogía del componente.

```python
# ─────────────────────────────────────────────────────────
# INCORRECTO: Importación directa del vault
# ─────────────────────────────────────────────────────────
from legacy_vault.v1.cgalpha.labs.zone_physics_lab import ZonePhysicsLab as ZPL_v1
# Usar ZPL_v1 directamente en el pipeline de v3 — PROHIBIDO

# ─────────────────────────────────────────────────────────
# CORRECTO: Adapter Pattern con contrato v3 explícito
# ─────────────────────────────────────────────────────────
class ZonePhysicsMonitor_v3(BaseComponentV3):
    """
    ╔═══════════════════════════════════════════════════════╗
    ║  MOSAIC ADAPTER — Componente v3                      ║
    ║  Heritage: legacy_vault/v1/cgalpha/labs/             ║
    ║            zone_physics_lab.py                       ║
    ║  Heritage Contribution:                              ║
    ║    - Lógica de Penetration Depth (%)                 ║
    ║    - Detección de Fakeout (ruptura + retorno vol)    ║
    ║    - Estados: REBOTE/FAKEOUT/RUPTURA/ABSORCION       ║
    ║  v3 Adaptations:                                     ║
    ║    - Integración con Trinity (VWAP/OBI/CumDelta)     ║
    ║    - Salida enriquecida con retest_score (0-1)       ║
    ║    - Input: MicrostructureRecord en lugar de OHLCV   ║
    ║  Vault Origin Purge: PENDING                         ║
    ╚═══════════════════════════════════════════════════════╝
    """
    
    # Contrato de interfaz v3 — inmutable una vez registrado en Biblioteca
    def evaluate(self, zone: ActiveZone, micro: MicrostructureRecord) -> ZoneState:
        """
        Evalúa el estado de la zona con contexto de microestructura.
        Retorna estado + score de absorción para el Oracle.
        """
        # Lógica adaptada de v1 + extensiones v3 con Trinity
        ...
    
    @property
    def component_manifest(self) -> ComponentManifest:
        """Manifiesto para la Biblioteca Vectorial."""
        return ComponentManifest(
            name="ZonePhysicsMonitor_v3",
            heritage_source="legacy_vault/v1/cgalpha/labs/zone_physics_lab.py",
            category="filtering",
            ...
        )
```

### 7.2 El Bucle de Reciclaje Automatizado

Lila debe seguir estos **5 pasos de forma atómica** para cada componente extraído de la Bóveda. Si cualquier paso falla, el proceso se detiene y el componente vuelve al estado `IN_REVIEW` en Capa 1:

```
╔═══════════════════════════════════════════════════════════════╗
║  BUCLE DE RECICLAJE — 5 PASOS ATÓMICOS                       ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  PASO 1: DISCOVERY (Búsqueda Semántica)                       ║
║  ─────────────────────────────────────────────────────────── ║
║  Usar la Biblioteca para encontrar el componente del vault    ║
║  más relevante para la necesidad actual.                      ║
║                                                               ║
║  cgalpha vault search "zone re-test triple coincidence"       ║
║  → Devuelve: zone_physics_lab.py (similitud: 0.91)           ║
║  → No buscar por path. Buscar por función.                    ║
║                                                               ║
║  PASO 2: STANDARDIZATION (Refactorización)                    ║
║  ─────────────────────────────────────────────────────────── ║
║  Aplicar el Wrapper Pattern.                                  ║
║  Extender con interfaz v3 (Trinity, VectorEvidencia v3).     ║
║  Respetar parámetros validados del legado.                   ║
║  Documentar qué se toma y qué se adapta en el docstring.     ║
║                                                               ║
║  PASO 3: GHOST AUDIT (Evaluación Previa)                      ║
║  ─────────────────────────────────────────────────────────── ║
║  Invocar al Ghost Architect para evaluar el código            ║
║  reciclado antes de usarlo.                                   ║
║                                                               ║
║  cgalpha ghost-audit --component ZonePhysicsMonitor_v3       ║
║  → Revisa: path safety, concurrency, rollback completeness   ║
║  → Si falla Ghost Audit → volver a PASO 2                    ║
║                                                               ║
║  PASO 4: LIBRARY REGISTRATION (Catalogación)                  ║
║  ─────────────────────────────────────────────────────────── ║
║  Generar el ComponentManifest completo.                       ║
║  Calcular embedding vectorial.                                ║
║  Registrar en la Biblioteca (aún como ADAPTED, no ACTIVE).   ║
║                                                               ║
║  cgalpha library register --component ZonePhysicsMonitor_v3  ║
║                                                               ║
║  PASO 5: CANARY PUSH (Implementación Cautelosa)               ║
║  ─────────────────────────────────────────────────────────── ║
║  Implementar en rama feature/mosaic_* con ΔCausal estimado.  ║
║  Ejecutar Triple Barrera de Tests (Fase 3 CodeCraft).        ║
║  Iniciar período de OOS validation (mínimo 2 semanas).       ║
║                                                               ║
║  git checkout -b feature/mosaic_zone_physics_v3              ║
║  cgalpha craft execute --proposal-id mosaic_zpv3             ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

### 7.3 Secuencia de Inicialización: El Bootstrap de la Constructora

Comandos indispensables para que Lila active su "visión de mosaico" desde cero:

```bash
# ── FASE 0: Indexación inicial del vault ──────────────────────
# Escanea todo legacy_vault/ y genera la base vectorial de candidatos
cgalpha vault index
# → Genera: vault_manifest.jsonl con estado UNVALIDATED para todos los componentes
# → Genera: embeddings iniciales para búsqueda semántica

# ── FASE 1: Estado de candidatos ──────────────────────────────
# Reporta qué piezas del legado son candidatos para ser LEGOs de v3
cgalpha vault status
# → Output:
#   CAPA 1: 47 componentes
#     UNVALIDATED: 31 | IN_REVIEW: 14 | PURGEABLE: 2
#   CAPA 2: 0 componentes (inicio)
#   Priority candidates: [fetcher.py, signal_detection_lab.py, zone_physics_lab.py]

# ── FASE 2: Activar Simple Foundation Strategy ─────────────────
cgalpha strategy init simple_foundation
# → Crea el scaffold de los 7 componentes del pipeline
# → Marca los 7 candidatos de Capa 1 como IN_REVIEW con prioridad CRÍTICA/ALTA

# ── FASE 3: Iniciar primer reciclaje ──────────────────────────
# Por cada componente en orden de dependencia del pipeline:
cgalpha vault harvest --component fetcher.py --target BinanceVisionFetcher_v3
cgalpha vault harvest --component signal_detection_lab.py --target TripleCoincidenceDetector
# → Ejecuta los 5 pasos del Bucle de Reciclaje automáticamente

# ── FASE 4: Monitoreo continuo ────────────────────────────────
cgalpha vault monitor --real-time
cgalpha library stats
cgalpha oracle monitor --window 2weeks
```

### 7.4 Política de Precedencia: v3 Sobre Legado

**Regla cardinal:** Si un parámetro reciclado de Capa 1 contradice un principio de v3, **la v3 siempre tiene supremacía** — a menos que el `RiskBarrierLab` demuestre un ΔCausal positivo superior en datos OOS reales.

```python
PrecedencePolicy(
    # v3 gana por defecto
    default="v3_principle_wins",
    
    # El legado puede ganar solo con evidencia causal superior
    legacy_exception_condition=(
        delta_causal_legacy_param > 0 AND
        delta_causal_legacy_param > delta_causal_v3_default AND
        validated_in_oos == True AND
        human_approved == True
    ),
    
    # Ejemplos concretos
    examples=[
        {
            "conflict": "zigzag_threshold: legado usa 0.5, v3 requiere 0.005",
            "resolution": "v3 gana sin excepción — es un bug documentado, no un principio"
        },
        {
            "conflict": "oracle_confidence: legado usa 0.65, v3 requiere 0.70",
            "resolution": "v3 gana por defecto. Legado puede ganar si ΔCausal(0.65) > ΔCausal(0.70) en OOS"
        },
        {
            "conflict": "Feature branch: legado hace push a main, v3 prohíbe",
            "resolution": "v3 gana siempre — es un invariante de seguridad, no un parámetro"
        }
    ]
)
```

### 7.5 El Ciclo Cosecha → Validación → ADN Permanente → Purga

El Mosaic Bridge no es solo el proceso de adaptación. Es el ciclo completo que va desde el legado bruto hasta la eliminación del origen:

```
legacy_vault/component.py   (Capa 1 — UNVALIDATED)
         │
         │ cgalpha vault index
         ▼
legacy_vault/component.py   (Capa 1 — IN_REVIEW)
         │
         │ cgalpha vault harvest --component X --target Y_v3
         │ [5 pasos del Bucle de Reciclaje]
         ▼
feature/mosaic_Y_v3         (Branch — ADAPTED, tests pasando)
         │
         │ OOS Validation ≥ 2 semanas
         │ Hit-Rate OOS improvement > 0
         │ ΔCausal > 0 confirmado
         ▼
NexusGate Evaluation        (PROMOTE_TO_LAYER_2 o REJECT)
         │                           │
         │ [PROMOTED]                │ [REJECTED]
         ▼                           ▼
component_library/Y_v3      legacy_vault/component.py
(Capa 2 — ACTIVE)           (Capa 1 — IN_REVIEW, retry)
         │
         │ cgalpha vault purge-origin --component X
         │ Human confirmation required
         ▼
legacy_vault/component.py   (Capa 1 — PURGEABLE)
         │
         │ cgalpha vault purge --confirmed
         ▼
legacy_vault/component.py   ❌ ELIMINADO
         │
         │ [Cuando todos los componentes de Capa 1 están ELIMINADOS]
         ▼
legacy_vault/               ❌ DIRECTORIO COMPLETO ELIMINADO
                            ✅ Solo existe la Capa 2 — ADN Permanente puro
```

### 7.6 El Protocolo de Incorporación Atómica

La "Incorporación Atómica al ADN Permanente" (mencionada en el Dashboard de Evolución) es una operación que debe ser:

1. **Atómica:** O sucede todo o no sucede nada. No hay estados intermedios.
2. **Trazable:** Cada paso tiene log en `evolution_log/improvements.jsonl`.
3. **Reversible:** El rollback está disponible mientras exista la versión anterior en `evolved/`.
4. **Aprobada:** La aprobación humana es el último paso, nunca el primero.

```bash
# Comando de incorporación atómica (ejecutado por el operador tras revisión)
cgalpha vault promote \
    --component ZonePhysicsMonitor_v3 \
    --from-branch feature/mosaic_zone_physics_v3 \
    --causal-score 0.81 \
    --oos-period "2026-02-01/2026-02-14" \
    --hit-rate-improvement 3.2 \
    --confirm-purge-origin \
    --human-id "vaclav"

# Output esperado:
# ✅ ZonePhysicsMonitor_v3 promovido a Capa 2 (ACTIVE)
# ✅ Embedding vectorial generado y registrado
# ✅ Correlaciones actualizadas en correlation_map.json
# ✅ Origen legacy_vault/v1/cgalpha/labs/zone_physics_lab.py marcado PURGEABLE
# ✅ evolution_log/improvements.jsonl actualizado
# ✅ Nexus notificado del nuevo componente activo
# → Ejecuta `cgalpha vault purge --confirmed` para eliminar origen cuando estés listo.
```

---

## SECCIÓN 8: MÉTRICAS DE EVOLUCIÓN CAUSAL

### 8.1 El Delta de Eficiencia Causal (ΔCausal) — Métrica Reina

```
ΔCausal(θ) = CATE(θ) = E[Y | T=θ_new, X] − E[Y | T=θ_old, X]
```

Donde:
- `Y` = Resultado observado (en unidades ATR del `outcome_ordinal`)
- `T` = Tratamiento (el cambio o componente bajo evaluación)
- `X` = Vector de confounders (régimen, volatilidad, sesión, Trinity state)
- El contrafactual `E[Y | T=θ_old, X]` se estima mediante gemelos estadísticos en el bridge.jsonl

### 8.2 Jerarquía Completa de Métricas v3.0

| Nivel | Métrica | Umbral v3.0 |
|---|---|---|
| **L0 — Supervivencia** | Uptime sistema | ≥ 99.5% |
| **L1 — Datos** | `blind_test_ratio` | ≤ 0.25 |
| **L1 — Datos** | Microstructure lag promedio | ≤ 150ms |
| **L1 — Oracle** | Accuracy OOS | ≥ 75% |
| **L1 — Oracle** | Oracle confidence operativa | > 0.70 |
| **L1 — Oracle** | Train-Test Delta | ≤ 10% |
| **L2 — Causal** | **ΔCausal** | > 0 en 3 ciclos OOS consecutivos |
| **L2 — Causal** | `min_causal_accuracy` | ≥ 0.55 |
| **L2 — Causal** | `min_efficiency` | ≥ 0.40 |
| **L2 — Estrategia** | Hit-Rate OOS Simple Foundation Strategy | Mejora neta > 0 por iteración |
| **L3 — Evolución** | Drift de features Trinity | < 20% mensual |
| **L3 — Evolución** | Proposal Quality | ≥ 60% con ΔCausal > 0 en OOS |
| **L4 — Sistema** | Test Coverage (Capa 2) | ≥ 80% |
| **L4 — Sistema** | Rollback Rate | < 5% de cambios |
| **L5 — Bóveda** | Capa 1 componentes restantes | Decreciente hacia 0 |
| **L5 — Bóveda** | Capa 2 componentes activos | Creciente |
| **L5 — Bóveda** | Component Reuse Rate | > 60% |
| **L5 — Bóveda** | `vault_origin_purged_rate` | Creciente hacia 100% |

---

## EPÍLOGO: LOS CINCO PRINCIPIOS INVARIANTES DE LILA v3

**Principio I — Causalidad sobre Correlación:**  
Todo resultado debe pasar por el filtro del ΔCausal. Un trade ganador en mercado alcista no es evidencia de buena decisión. `blind_test_ratio > 0.25` significa suspender inferencias causales hasta mejorar la cobertura de microestructura. Nunca operar en modo `BLIND_TEST` con confianza alta.

**Principio II — Construcción sobre Exploración:**  
La misión primaria es producir la Simple Foundation Strategy, no explorar la Bóveda indefinidamente. El análisis al servicio de la construcción. La exploración justificada por la necesidad técnica concreta. Sin producto concreto, no hay validación real.

**Principio III — Propuesta sobre Imposición:**  
Lila no actúa sin aprobación humana en cambios de producción. Builder propone; Observer analiza; operador decide; CodeCraft implementa. La incorporación atómica al ADN Permanente requiere siempre la firma del operador.

**Principio IV — Integridad sobre Velocidad:**  
La Triple Barrera de CodeCraft no es opcional. La reescritura total sin gates repetidos es un antipatrón. `Fail Closed` es la postura correcta ante la ambigüedad. La Política de Precedencia (v3 gana por defecto) no tiene excepciones de seguridad.

**Principio V — Purificación como Destino:**  
Cada componente que Lila construye o recicla debe terminar en la Capa 2 o eliminar su origen en Capa 1 al no superar el Gate. La Bóveda Provisional tiene fecha de muerte. La acumulación de legado no validado es deuda técnica disfrazada de precaución. El ADN Permanente solo acepta lo que lo merece.

---

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║  "El norte no es un lugar al que se llega.                      ║
║   Es la dirección en la que uno se mantiene mientras construye." ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  FIN DEL BLUEPRINT CAUSAL v3.0.0                                ║
║  LILA v3 — EL NORTE MAESTRO DE LA RECONSTRUCCIÓN               ║
║                                                                  ║
║  Versión: 3.0.0 — Abril 2026                                    ║
║  Sustituye: v1.0.0, v2.0.0                                      ║
║  Estado: CANON ACTIVO                                            ║
║                                                                  ║
║  Fuentes canonizadas: 8 documentos de corpus completo           ║
║  Secciones: 8 + Epílogo                                         ║
║  Principios invariantes: 5                                       ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## REGISTRO OPERATIVO: SESIÓN 2026-04-12 — OPERATIVIDAD TOTAL (v3.1)

En esta sesión se ha alcanzado la **Operatividad Total del Pipeline Causal**. El sistema ha dejado de ser un conjunto de experimentos para convertirse en un organismo vivo de trading.

### Hitos de Ingeniería Consolidados:
1. **Firma Causal Inmutable**: Implementación de la persistencia de firma en el Oracle. El NexusGate ahora valida contra datos reales, no baselines.
2. **Sistema Nervioso (EvolutionOrchestrator)**: Activación del bucle de auto-monitoreo. El sistema detecta su propia deriva y está listo para evolucionar.
3. **Brazo Ejecutor (OrderManager v3.1)**:
   - **Dry Run de Alta Fidelidad**: Simulación de latencia y slippage basada en OBI.
   - **Gestión Multi-Activo**: Soporte concurrente para BTC y ETH con límites de exposición (%) por símbolo.
   - **Blindaje Psicológico**: Alertas sonoras (Beeps sintéticos), Panic Button (Liquidación masiva) y Daily Profit Target (+2%).
4. **Interfaz de Mando (Control Room)**: Dashboard actualizado con gráficos de PnL dinámicos y desglose de exposición sectorial.

### ESTADO DEL SISTEMA:
- **Pipeline Live**: 🟢 OPERACIONAL
- **Auto-Gobernanza**: 🟢 ACTIVA
- **Riesgo**: 🛡️ BLINDADO (MODO DRY RUN)

**PRÓXIMO PASO CANÓNICO**: Fase 4.4 — Live Order Entry (Conexión Real Binance).
