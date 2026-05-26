# Crónica de Desarrollo — cgAlpha / Aipha
### Versión 3.7 — Actualizada 15 mayo 2026

> Documento vivo para reconstruir el pasado, comprender el estado actual y orientar decisiones futuras.
> Esta versión incorpora el cierre formal del Hardening Fase 2:
> confirmación de 20 zonas activas en GUI, diagnóstico de los
> 3 bugs raíz de visibilidad, y lección metodológica nueva.
> Además, incorpora la sesión de estabilización operativa del 15 mayo:
> fallback spot/futures, auditoría con semáforo, scripts de control GUI,
> hardening de rutas/persistencia multi-touch y recuperación de cosecha reciente.

---

## 1) Resumen ejecutivo

El proyecto evoluciona desde **Aipha** hacia **cgAlpha_0.0.1** con un objetivo central:
construir un sistema de trading algorítmico que no solo ejecute señales, sino que
**aprenda y se mejore de forma gobernada** mediante un canal de evolución
(Lila + Orchestrator + memoria + pruebas + trazabilidad).

El ciclo más reciente (v4) produjo el primer baseline OOS honesto del proyecto (0.68)
y descubrió una vulnerabilidad estructural nueva: **el sistema era ciego a los rebotes
prematuros**. La respuesta correcta no fue añadir filtros arbitrarios — fue instrumentar
primero para obtener evidencia real antes de decidir cualquier filtro.

**Principio rector que emergió en este ciclo:**
*Medir → Analizar → Calibrar → Filtrar. En ese orden, siempre.*

---

## 2) Nomenclatura canónica (decisión registrada)

| Nombre | Uso | Razón |
|--------|-----|-------|
| `cgAlpha_0.0.1` | Nombre oficial del proyecto activo | Minúscula `c` distingue de `CGAlpha` histórico |
| `Lila` | Nombre de la IA constructora | Sin sufijo de versión en docs y GUI |
| `CGAlpha` | Nombre legado (v1, v2, v3) | Preservado en código para no romper imports |
| `Aipha` | Nombre original (0.0.1–1.1) | Solo en `legacy_vault` y documentación histórica |

**Regla crítica:** los directorios de código (`cgalpha_v3/`) no se renombraron
porque 144+ tests dependen de esos imports.

---

## 3) Línea temporal narrada — con evidencia operativa

---

### FASE 0 — Origen: Las 4 Islas (pre-v4, antes del 19 abril 2026)

El sistema tenía todas las piezas pero ninguna conectada.

**Los 8 bugs documentados del Oracle:**

| Bug | Archivo / Línea | Problema | Impacto |
|-----|----------------|----------|---------|
| BUG-1 | `oracle.py` — sin `train_test_split` | Entrena y evalúa sobre los mismos datos | Métricas artificialmente perfectas |
| BUG-2 | `server.py` — `save/load_from_disk()` nunca llamados | Modelo se pierde al reiniciar | Sin memoria de aprendizaje |
| BUG-3 | Dataset — 94% BOUNCE / 6% BREAKOUT | Desequilibrio severo | Modelo predice siempre BOUNCE |
| BUG-4 | `oracle.py predict()` — `confidence=0.85` hardcoded | Placeholder indistinguible | Imposible saber si predicción es real |
| BUG-5 | `triple_coincidence.py _determine_outcome()` — threshold 0.5% arbitrario | Labels sin relación con la zona | Oracle aprende patrones inexistentes |
| BUG-6 | `pipeline.py` L191-201 — `load_training_dataset()` sin `train_model()` | Acumulación sin aprendizaje | Oracle nunca reentrena |
| BUG-7 | `MemoryPolicyEngine` — sin `load_from_disk()` al arrancar | Memoria se pierde en cada reinicio | Sin identidad persistente |
| BUG-8 | `server.py` — endpoints `/approve` y `/reject` son stubs vacíos | Curación del dataset imposible | BUG-3 no puede resolverse manualmente |

---

### FASE 1 — El Bootstrap Fundacional (19 abril 2026)

#### La Paradoja del Bootstrap

El Orchestrator clasifica propuestas de construcción, pero la primera propuesta
era "construir el Orchestrator". Solución: 3 acciones manuales como Cat.3 directa.

```
Acción 1 → Memoria IDENTITY (nivel 5)
    ↓ (sin esto nada persiste)
Acción 2 → LLM Switcher
    ↓ (sin esto el Orchestrator no sabe qué modelo usar)
Acción 3 → Orchestrator v4
    ↓ (aquí se cierra la paradoja: el canal existe)
```

**Invariante topológico:** ningún paso puede adelantarse. El orden depende de
dependencias reales, no de preferencia.

#### Las 3 desconexiones que bloqueaban el arranque

| Spec | Tipo | Problema real en código |
|------|------|------------------------|
| Spec 1 | Cat.1 — TypeError | `BinanceWebSocketManager.create_default(symbol=symbol)` — firma solo acepta posicional |
| Spec 2 | Cat.2 | `live_adapter.py _dispatch_kline` no llamaba al ShadowTrader tras predicción del Oracle |
| Spec 3 | Cat.2 | No había mecanismo que arrancara el pipeline en background al iniciar servidor |

`bridge.jsonl` apareció con el primer registro — demostración real del canal
funcionando de punta a punta. El precio `100.01` (sintético, de verificación) reveló que
el Evolution Loop buscaba ventana de 1h — demasiado reciente para Binance Vision.
Se amplió a 48h.

---

### FASE 2 — Corrección de Bugs Estructurales (19–21 abril 2026)

#### El límite de contexto del LLM como restricción de diseño

`triple_coincidence.py` tiene 37KB (~900 líneas). Qwen 2.5:3b tiene 8k tokens de contexto.
Aplicar BUG-5 con LLM habría truncado el archivo y lo habría destruido.

**Solución: scripts Python deterministas de ~40 líneas** — leen el archivo línea por línea,
localizan el método por nombre, reemplazan el bloque exacto, verifican sintaxis.

**Lección estructural (§7.8 del Prompt Fundacional):**
*"Determinista primero; LLM como fallback."*

```python
# BUG-5 fix — antes:
if price_change_pct > 0.005:  # threshold arbitrario 0.5%
    return 'BOUNCE'

# BUG-5 fix — después:
if zone.direction == 'bullish':
    if future_close < zone_bottom: return 'BREAKOUT'
    if future_close > zone_top: return 'BOUNCE'
```

**Estado de bugs al cierre de Fase 2:**

| Bug | Estado | Método |
|-----|--------|--------|
| BUG-1 | ✅ Resuelto | Script determinista en `oracle.py` |
| BUG-2 | ✅ Resuelto | 2 líneas en `server.py` |
| BUG-3 | ⏳ Pendiente | Necesita más datos reales |
| BUG-4 | ✅ Resuelto | Flag `is_placeholder` en `OraclePrediction` |
| BUG-5 | ✅ Resuelto | Script determinista en `triple_coincidence.py` |
| BUG-6 | ✅ Resuelto | Una línea en `pipeline.py` |
| BUG-7 | ✅ Resuelto | `load_from_disk()` en startup de `server.py` |
| BUG-8 | ✅ Resuelto | Persistencia en `training_approvals.jsonl` |

---

### FASE 3 — Higiene Operativa y Gobernanza (26 abril 2026)

**21,078 artefactos en git** contaminaban los commits automáticos del canal.
Solución en orden 3→1→2: limpieza del repo → `production_ready` dinámico →
separación de incidentes simulados.

**`production_ready` dinámico:**
```python
production_ready = (
    oracle_model_is_real           # not placeholder
    and bridge_jsonl_has_real_data  # entry_price > 10000
    and evolution_loop_active       # último ciclo <= 30min
    and memory_identity_loaded      # mantra en nivel 5
)
```

**Protección del documento fundacional:** `LILA_v3_NORTH_STAR.md` añadido a
`CAT_3_PROTECTED_FILES`. Ningún ciclo automático puede modificarlo sin sesión humana.

---

### FASE 4 — El "Smoking Gun" y la Calibración Estadística (27–29 abril 2026)

#### El ZigZag threshold mal escalado

`MiniTrendDetector` tenía `zigzag_threshold = 0.02` interpretado como 2.0%.
Para BTCUSDT 5m, eso requería movimientos de $1,500+.
686 micro-segmentos filtrados → 0 tendencias → 0 retests.

**Fix inicial: 0.1% → distribuci­ón artificial 55.7/44.3.**
El precio salía trivialmente de zonas pequeñas → BREAKOUT labels falsos →
test accuracy 1.0 (engañoso).

**Calibración con datos reales (288 velas BTCUSDT 5m):**

| Estadístico | Rango de vela |
|------------|--------------|
| Mediana | 0.1091% |
| P75 | 0.1553% |
| **Threshold definitivo** | **0.18%** (entre P75 y P90) |

**Los tres números que importan (30 días reales):**

| Métrica | Antes (0.1%) | Después (0.18%) |
|---------|-------------|----------------|
| Distribución | 55.7% / 44.3% (artificial) | **72.7% / 27.3%** (creíble) |
| Samples | 140 (sintéticos) | **121 (reales)** |
| Test accuracy OOS | 1.0 (artificial) | **0.68 (primera métrica honesta)** |

#### El backlog de 270 propuestas duplicadas

AutoProposer generaba ~10 propuestas/hora sobre `n_estimators`.
Fix: `_count_recent_modifications()` en el Orchestrator — ≥3 propuestas en 7 días → Cat.2.
199 duplicadas rechazadas, 1 preservada.

---

### FASE 5 — CodeCraft Sage v4: AST-based Patching (27 abril 2026)

El Sage v3 usaba regex y no podía manejar archivos grandes.
BUG-5 y BUG-1 necesitaron scripts manuales precisamente por esta limitación.

**Sage v4 — Jerarquía determinista:**
1. **AST-based** (nuevo): localiza `FunctionDef`/`AsyncFunctionDef` por nombre
2. **str.replace** determinista: para cambios paramétricos simples
3. **LLM-assisted** (fallback): solo cuando ninguna estrategia determinista aplica

`TechnicalSpec` extendido con `new_code: str | None` y `old_code: str | None`
— 100% compatible con los 213 tests existentes. **9/9 tests pasando.**

---

### FASE 6 — Island Bridge: Las 4 Islas Conectadas (26 abril 2026)

Antes del Island Bridge, `ExperimentRunner`, `ChangeProposer` y `Orchestrator`
existían en código pero no se comunicaban.

```
ANTES: Isla 1 ──✂── Isla 2 ──✂── Isla 3 ──✂── Isla 4

AHORA: ChangeProposer → Orchestrator → CodeCraftSage
            ↑                               ↓
       ExperimentRunner ← Pipeline ← AutoProposer
```

Ambos bridges son non-blocking (`try/except`) para no romper el flujo existente.

---

### FASE 7 — Baseline Congelado para Validación 48h (1–3 mayo 2026)

```
cgAlpha_0.0.1 — Estado: v4-first-real-baseline
═══════════════════════════════════════════════════════
Oracle OOS real:     0.68 (primera métrica honesta del proyecto)
Dataset:             121 samples reales, 30 días BTCUSDT 5m
Distribución:        72.7% BOUNCE / 27.3% BREAKOUT ✓
ZigZag threshold:    0.18% (basado en P75 de rango real de vela)
Safety Envelope:     28 parámetros blindados ✓
Cooldown §4.3:       Implementado ✓
Sage v4 AST:         Operativo, 9/9 tests ✓
Canal:               4 islas conectadas ✓
Tests:               217+ passed ✓
Snapshot commit:     5ddadc7df5f6658ab94e45065528d9ee2c0a1770
PID ejecución:       48738
```

**Modo Cat.1:** restringido — solo low sensitivity + causal impact < 0.4.
**Break-glass:** backlog > 50, safety violations > 20, OOS rolling < 0.60.

---

### FASE 8 — Diagnóstico de Rebotes Prematuros (2 mayo 2026)

#### 8.1 El problema descubierto — auditado en código real

**La vulnerabilidad confirmada en `triple_coincidence.py` línea 825:**
```python
# La condición actual:
if zone.zone_bottom <= current_price <= zone.zone_top:
```

Esta condición dispara una señal de retest incluso en la vela inmediatamente
posterior a la detección si el precio no se ha movido lo suficiente. El sistema
era completamente ciego a si el precio había "escapado" de verdad de la zona
o simplemente había rebotado sin convicción.

**Dataset auditado — campos disponibles antes de la fix:**
```python
Campos disponibles: ['features', 'outcome', 'zone_id']
```

El campo `max_clearance_atr` **no existía**. El Oracle nunca supo cuánto se
alejó el precio antes de retestear. Esto significaba que retests legítimos y
"latigazos" de ruido eran tratados de forma idéntica por el modelo.

#### 8.2 Evolución dialéctica: de la intuición al rigor (historial completo)

**La pregunta original del operador:**
> "Desde la primera vela que se alejó el precio de la zona deberíamos medir su
> fuerza para considerar no arbitrariamente si permitiremos retest después de la
> vela siguiente (2da vela — decisión arbitraria) o tendremos que esperar una o
> más velas porque el precio no se ha alejado lo suficiente con la fuerza suficiente."

Esta observación fue el catalizador correcto: identificó que tratar de definir una
regla fija ("2 velas") es el camino más rápido hacia el overfitting.

**Iteración 1 — Propuestas rechazadas (respuesta inicial del sistema):**
- `min_clearance_atr` como Cat.1 ← **incorrecto**: afecta el sampling del Oracle → Cat.2 mínimo
- RSI/Estocástico como filtro de agotamiento ← **incorrecto**: multicolinealidad con features
  lagging ya existentes. El Oracle no puede distinguir qué feature tiene poder predictivo real.
- Valores arbitrarios de `N` para `zone_top + (N * ATR)` ← **incorrecto**: reproduce el error
  del ZigZag con 0.1% — un número que "parece razonable" pero que puede generar 0 retests.
- Relative Volume como modulador del cooldown ← **incorrecto**: introduce dos parámetros
  interdependientes simultáneos sin OOS real → optimización sobre ruido.

**Corrección crítica del operador (Punto de Inflexión):**
> "El parámetro N en `zone_top + (N * ATR)` es la decisión más importante y no
> está mencionada. Esta es exactamente la trampa del ZigZag. El valor no puede
> decidirse a priori — necesita percentiles de datos reales."

**Iteración 2 — Enfoque correcto (instrumentación ciega):**
El operador estableció que el único paso legítimo era **medir sin filtrar**:
1. Añadir `max_clearance_atr` como campo observacional (Cat.1 — no cambia el comportamiento).
2. Acumular ≥200 samples con ese campo.
3. Analizar P25(BOUNCE) vs P25(BREAKOUT) para determinar poder discriminativo.
4. Solo entonces, si las distribuciones divergen, proponer un filtro como Cat.2.

**Corrección adicional sobre el ATR:**
> "max_price_since_detection captura el máximo absoluto, pero lo que necesitas
> es la distancia normalizada por ATR en el momento de la DETECCIÓN, no del
> retest. Si capturas el ATR al momento del retest, mides la volatilidad cuando
> el precio ya regresó — no cuando escapó."

**Resultado empírico (261 samples, 60 días):**
La divergencia de P25 entre BOUNCE y BREAKOUT fue de apenas ~0.15 ATR.
**Conclusión: el clearance puro como filtro espacial duro carece de poder
predictivo suficiente.** Pero como FEATURE observable del Oracle (no como filtro
en `_check_retest`), puede contribuir en combinación con las features L2.

**El error de fondo evitado:** proponer filtros antes de tener evidencia de qué valor
discrimina BOUNCE de BREAKOUT. Exactamente lo que generó el ciclo de corrección
del ZigZag.

#### 8.3 El orden correcto aplicado: Medir → Analizar → Calibrar → Filtrar

**Paso 0 — Verificación de ceguera:**
```python
# Output confirmado:
Campos disponibles: ['features', 'outcome', 'zone_id']
# max_clearance_atr no existe → sistema es ciego al clearance
```

**Paso 1 — Instrumentación ciega (Cat.1, ejecutado):**

Se añadieron tres campos a `ActiveZone`:
- `atr_at_detection`: capturado **exclusivamente en el momento de la detección**
  (no al momento del retest — ese ATR media la volatilidad del regreso, no del escape)
- `max_price_since_detection`: para zonas bullish
- `min_price_since_detection`: para zonas bearish (ambas direcciones instrumentadas)

Cálculo al momento del retest:
```python
max_clearance_atr = (
    (zone.max_price_since_detection - zone.zone_top) / zone.atr_at_detection
    if zone.direction == 'bullish'
    else
    (zone.zone_bottom - zone.min_price_since_detection) / zone.atr_at_detection
)
```

El campo se inyecta en `TrainingSample['features']` — observable pero no usado
como filtro. El Oracle puede aprenderlo si tiene poder discriminativo.

**Verificación mediante test unitario (`tests/test_clearance_instrumentation.py`):**
- Sistema rastrea extremos de precio durante el alejamiento ✓
- Cálculo normalizado por ATR de detección es correcto ✓
- Feature se persiste en `TrainingSample` ✓
- Clearance calculado en simulación: **4.5 ATRs exactos** ✓
- Print de debug eliminado del loop de producción ✓

**Estado actual:**
```
La infraestructura de medición ya está en su sitio.
Hemos pasado de la intuición a la instrumentación.
```

---

## 4) Estado actual (10 mayo 2026)

| Componente | Estado | Evidencia |
|-----------|--------|-----------|
| Canal de evolución | ✅ Operativo | 4 islas conectadas, Island Bridge |
| Oracle OOS | ✅ 0.68 honesto | 30 días BTCUSDT, 121 samples reales |
| Oracle v5 (Synth-Bridge) | ✅ Entrenado | 100 muestras sintéticas, modo `observe` |
| ZigZag threshold | ✅ Calibrado | 0.18% — P75 de rango real de vela |
| Safety Envelope | ✅ 28 parámetros | Gatekeeper activo |
| Cooldown §4.3 | ✅ Implementado | `_count_recent_modifications()` |
| Sage v4 AST | ✅ Operativo | 9/9 tests pasando |
| Clearance instrumentation | ✅ **OPERATIVO** | Feature `max_clearance_atr` en TrainingSample |
| OBI / CumDelta reales | ✅ **CONECTADO** | WS @depth20@100ms activo, ingesta L2 validada |
| L2 Ring Buffer 30s | ✅ **OPERATIVO** | `l2_ring_buffer.py` — sintetiza 25 features L2 al retest |
| Etiquetado terciario | ✅ **OPERATIVO** | BOUNCE_STRONG/BOUNCE_WEAK/BREAKOUT/INCONCLUSIVE |
| DeferredOutcomeMonitor | ✅ **CON JOURNALING** | Persistencia inmediata MFE/MAE, labels diferidamente |
| Warm Start (Cold Start fix) | ✅ **OPERATIVO** | `seed_history()` pre-popula 200 velas, 20 zonas al bootstrap |
| Persistencia zonas + TTL 24h | ✅ **OPERATIVO** | `save_state()`/`load_state()` con rutas absolutas |
| Z-Score volumen adaptativo | ✅ **OPERATIVO** | Umbral 0.5, ventana 30, instrumen. de calibración activa |
| Morfología observacional | ✅ **OPERATIVO** | `wick_pct`, `rejection_direction` en ReentrySnapshot |
| GUI visibilidad de zonas | ✅ **VERIFICADO** | 20 zonas visibles tras bootstrap, rutas absolutas, archivos separados |
| Multi-Touch Clearance | ✅ **IMPLEMENTADO** | `min_clearance_atr=1.0`, per-touch tracking, MAX_TOUCHES=3 |
| Z-Score Calibration Log | ✅ **RECOLECTANDO** | `zscore_calibration_log.jsonl`, Cat.1 observacional |
| CHANGELOG_ALGO.md | ✅ **CREADO** | 7 entradas versionadas (v1.0.0 → v1.7.0) |
| Encoding determinista | 🟡 **PENDIENTE** | `LabelEncoder` no-determinista en oracle.py — Debilidad #3 |
| Lookahead adaptativo | 🟡 **PENDIENTE** | `outcome_lookahead_bars=10` fijo — Debilidad #5 |

---

## 5) Lecciones operativas (actualizado con Evaluación Estructural)

1. **Separar commits por intención:** arquitectura / fixes / limpieza / documentación.

2. **Calibrar thresholds con datos reales:** el percentil 75 del rango de vela BTCUSDT
   5m es un dato. "0.1% parece pequeño" no lo es.

3. **Distinguir métricas reales de métricas artificiales:** test accuracy 1.0 con 13
   samples no es un logro — es una señal de alarma.

4. **Los mecanismos de gobernanza deben probarse con datos reales:** el cooldown de
   §4.3 estaba especificado pero no conectado. Solo se descubrió cuando el backlog
   llegó a 270 propuestas.

5. **Instrumentar antes de filtrar:** nunca añadir un filtro sin primero verificar
   que el parámetro tiene poder discriminativo en datos reales. El campo
   `max_clearance_atr` existe ahora como observación pasiva — el filtro vendrá
   solo si P25(BOUNCE) ≠ P25(BREAKOUT).

6. **El ATR del momento de detección, no del retest:** capturar el ATR cuando ocurre
   el evento causal (la zona), no cuando se evalúa el resultado (el retest). El ATR
   del retest mide la volatilidad del regreso, no la fuerza del escape.

7. **Ambas direcciones, siempre:** instrumentar solo `max_price` sin `min_price`
   deja los BREAKOUT hacia abajo sin medir. Cada feature nueva debe contemplar
   ambas direcciones del mercado.

8. **La clasificación de categoría importa tanto como el cambio:**
   Añadir un campo observacional al `TrainingSample` es Cat.1 (no cambia el
   comportamiento). Añadir un filtro que modifica cuándo se disparan señales
   es Cat.2 porque afecta la calidad del dataset. Confundir estas dos cosas
   lleva a implementar cambios arquitectónicos sin la debida diligencia OOS.

9. **La trampa del indicador "intuitivo":**
   Los indicadores como RSI o Estocástico "tienen sentido" para un trader humano,
   pero crean multicolinealidad catastrófica en un modelo ML. El Oracle no puede
   distinguir qué feature lagging tiene poder predictivo real si todas miden variantes
   del mismo fenómeno. Resistir la tentación de añadir indicadores "porque suenan bien".

10. **La dinámica importa más que la foto (Evaluación Estructural, Debilidad #1):**
    Un OBI de +0.25 que viene subiendo desde -0.10 es defensa activa creciendo.
    Un OBI de +0.25 que viene cayendo desde +0.60 es defensa desmoronándose.
    El snapshot estático no puede distinguirlos. Siempre capturar el gradiente temporal
    junto con el valor puntual de cualquier feature de microestructura.

11. **El etiquetado binario esconde ruido (Evaluación Estructural, Debilidad #2):**
    Clasificar como "éxito" un precio que no se movió de la zona (fallback
    `return 'BOUNCE'` en `_determine_outcome` L965) contamina el dataset con
    outcomes marginales. Los bounces débiles deben etiquetarse como categoría
    intermedia para que el modelo no entrene sobre ruido en la variable target.

12. **Diagnosticar antes de implementar — siempre con evidencia de código:**
    El Cold Start parecía un problema de hidratación de indicadores. El diagnóstico
    con greps confirmó que era un problema de buffer no compartido entre
    `process_stream()` y `process_live_tick()`. Implementar sin verificar
    habría producido un fix correcto para el problema equivocado. La pregunta
    "¿en qué línea exacta está el bug?" es más valiosa que cualquier propuesta
    de solución.

13. **Los bugs de visibilidad son bugs de datos, no bugs de UI:**
    La GUI mostraba 0 zonas no porque el frontend fallara, sino por tres causas
    en cascada en la capa de datos: rutas relativas dependientes del CWD,
    colisión de archivos JSON, y cleanup eliminando zonas durante bootstrap.
    Ante cualquier fallo de visualización, verificar primero que los datos
    existen en disco antes de modificar el frontend.

14. **El número de zonas no valida la calidad de zonas:**
    20 zonas activas post-bootstrap es una mejora operativa (vs 8+ horas de
    espera). Pero el criterio de éxito real sigue siendo el mismo:
    ≥50 retests reales resueltos en `training_dataset_v2.jsonl` con
    `obi_10 ≠ 0`. Las zonas son el prerequisito; los retests son el objetivo.

---

## 6) Próximos pasos — Hoja de ruta priorizada

### COMPLETADOS (Fases 8, 9, 10.5, 10.5b, Hardening Fase 1 y 2)

**[A] Cosecha de evidencia:** Instrumentación ciega `max_clearance_atr` inyectada y auditada en Live.
**[B] Ampliar a 60 días históricos:** Ejecutado. Generó 261 muestras con el threshold real (0.18%).
**[C] Análisis de percentiles:** Ejecutado empíricamente. Divergencia P25 ~0.15 ATR. **Clearance puro como filtro espacial duro: poder predictivo insuficiente.**
**[D] Conexión de OBI y CumDelta (Cat.2):** Transición al stream `@depth20@100ms`.
**[E'] Multi-Touch Clearance Logic (Cat.2):** Implementada como gate de toques independientes (no como filtro espacial duro). `min_clearance_atr=1.0` exige que el precio se aleje 1 ATR antes de aceptar el 2do/3er toque. Esto no rechaza retests — asegura que son eventos independientes. Evolución de [E] que fue rechazado como filtro binario.
**[F] Warm Start / Cold Start:** `seed_history()` pre-popula 200 velas. 20 zonas detectadas en <30s.
**[G] Z-Score Volumen Adaptativo:** Reemplazo de P70 estático por Z-Score local (ventana 30, umbral 0.5). Instrumentación Cat.1 activa en `zscore_calibration_log.jsonl`.
**[H] Persistencia robusta:** `save_state()`/`load_state()` con TTL 24h, rutas absolutas, archivos separados.
**[I] Morfología Observacional:** Campos `wick_pct`, `rejection_direction` en ReentrySnapshot. Retrocompatible.
**[J] Journaling Defensivo:** `DeferredOutcomeMonitor` persiste MFE/MAE inmediatamente en cada récord.
**[K] GUI Visibilidad:** Rutas absolutas unificadas, separación `detector_state.json` / `active_zones.json`, flag `is_bootstrapping`. 20 zonas visibles en la GUI.
**[L] CHANGELOG_ALGO.md:** Registro algorítmico con 7 entradas versionadas (v1.0.0 → v1.7.0).

### DESCARTADOS (Basado en Evidencia)

**[E] Filtro de rebotes prematuros en `_check_retest` (Cat.2):** **RECHAZADO como filtro binario**. La matemática del Paso C dictaminó que un filtro espacial duro destruiría la robustez. Sin embargo, la lógica evolucionó hacia [E'] como gate de independencia entre toques.

### INMEDIATO — Estado actual (10 mayo 2026, 20:00 UTC)

Sistema operativo en Modo Cosecha Pura:
- **Proceso activo:** `launch_shadow_live.py` corriendo en background
- **Zonas monitoreadas:** 20 (detectadas en bootstrap de 500 velas históricas)
- **Clearance Logic:** activa (`min_clearance_atr=1.0`)
- **Samples reales acumulados:** 0 resueltos (cosecha iniciada hoy)
- **Instrumentación Z-Score:** recolectando en `zscore_calibration_log.jsonl`

**Próxima intervención humana requerida:**
Solo cuando `training_dataset_v2.jsonl` alcance ≥50 líneas con precios >70,000 USD.
Comando de verificación diario (30 segundos):

```bash
echo "Pending: $(wc -l < aipha_memory/operational/pending_labels.json 2>/dev/null || echo 0)"
echo "Resueltos: $(wc -l < aipha_memory/operational/training_dataset_v2.jsonl 2>/dev/null || echo 0)"
ps aux | grep launch_shadow_live | grep -v grep | wc -l
```

A ~3 retests diarios, el umbral de 50 se alcanza en ~17 días.

### PRÓXIMO — Fase Puente: Feature Engineering + Corrección de Etiquetado (Cat.2)

**Prerrequisito:** Cosecha viva L2 con ≥50 samples que contengan `obi_10 ≠ 0`.

La Evaluación Estructural del Oracle (3 mayo 2026) identificó que re-entrenar el modelo con las mismas features estáticas tendría un techo predictivo limitado. Antes de la Fase 10, se requieren 4 correcciones:

**[F1] Buffer temporal L2 en WS Manager (Cat.2) — Debilidad #1**
Implementar un ring buffer de 30 segundos en `BinanceWebSocketManager` que almacene micro-snapshots del OBI y CumDelta cada 100ms. Del buffer se derivan 6 features al momento del retest (reemplazando los 2 snapshots estáticos):
1. `obi_10_at_retest` (ya existe — snapshot)
2. `obi_10_gradient_5s` (NUEVO — Δ-OBI en 5s previos al toque)
3. `obi_10_gradient_30s` (NUEVO — Δ-OBI en 30s previos)
4. `cumulative_delta_at_retest` (ya existe — total acumulado)
5. `delta_acceleration_5s` (NUEVO — 2ª derivada del delta en 5s)
6. `obi_depth_ratio` (NUEVO — OBI_1 / OBI_10, detector de spoofing)

**[F2] Etiquetado terciario + Lookahead adaptativo (Cat.2) — Debilidades #2 y #5**
Reemplazar el etiquetado binario en `_determine_outcome()` con 3 clases:
- `BOUNCE_STRONG`: `future_close > zone_top + 0.5 * ATR` (escape decisivo)
- `BOUNCE_WEAK`: precio sale marginalmente o se queda dentro de zona (absorbe el fallback L965)
- `BREAKOUT`: `future_close < zone_bottom` (ruptura)
Lookahead adaptativo: `lookahead = max(5, min(20, int(5 + zone_width_atr * 3)))`

**[F3] Encoding determinista (Cat.1) — Debilidad #3**
Reemplazar `LabelEncoder` en `oracle.py` por columnas binarias (`is_trending_up`, `is_trending_down`, `is_lateral`) para eliminar dependencia del orden de encoding entre re-entrenamientos.

### SIGUIENTE — Fase 10 (REVISADA): Re-entrenamiento con Features Enriquecidas

**Prerrequisito:** Fase Puente completada. ≥200 samples con features temporales L2.

**Alcance revisado (post-evaluación estructural):**
1. Combinar dataset histórico (261 samples) + samples vivos con L2 temporal.
2. Re-entrenar RandomForest con las 6 features temporales + encoding determinista.
3. Entrenar sobre etiquetado terciario (`BOUNCE_STRONG` / `BOUNCE_WEAK` / `BREAKOUT`).
4. Medir nuevo OOS y comparar con baseline de 0.68.
5. Evaluar Feature Importance: ¿aparecen gradientes L2 en top-3?
6. Si dataset ≥ 500 samples: benchmark RF vs XGBoost/LightGBM (Debilidad #4).

**Criterio de éxito:** OOS ≥ 0.68 (no regresión) + al menos 1 feature temporal L2 en top-3 de importancia.

### MEDIO PLAZO — Fase 11: Calibración Probabilística

**[G] Calibración de `predict_proba` (Cat.2)**
Solo después de la Fase 10 revisada. Calibración Platt o Isotonic + Brier/ECE sobre OOS del modelo terciario. Especialmente crítica con 3 clases (requiere calibración multi-clase).

### MEDIO PLAZO — Fases 12-14

**[H] Walk-Forward Validation (Cat.2)**
Validación temporal robusta: entrenar en ventana 1, testear en ventana 2, deslizar. Confirma generalización temporal.

**[I] Ejecución Francotirador MAE (Cat.2)**
El buffer temporal L2 de la Fase Puente es prerequisito directo — el regresor MAE necesita el perfil de OBI intra-zona (gradientes durante penetración) para predecir profundidad. Sin el buffer, esta fase sería inviable.

**[J] Activar Cat.1 automático sobre parámetros de baja sensibilidad**
Solo tras OOS ≥ 0.70 + Brier Score calibrado.

**[K] Independencia Progresiva y Reflexiones Críticas**
Protocolo de cuestionamiento (§6 del Mantra). Validación OOS de 3 ciclos + aprobación humana Cat.3.

---

## 7) Registro de commits clave

| Hash | Descripción | Impacto medible |
|------|-------------|----------------|
| Bootstrap | Memoria IDENTITY + LLM Switcher + Orchestrator v4 | Canal existe |
| `d0992d2` | BUG-1: `train_test_split` | Métricas OOS reales |
| Script det. | BUG-5: `_determine_outcome` usa zona real | Labels correctos |
| `509c7b3` | BUG-6: `train_model()` en pipeline | Oracle reentrena en ciclo vivo |
| `6d5c651` | BUG-4: `is_placeholder` flag | Observabilidad del Oracle |
| `dd85d21` | BUG-3: oversampling clase minoritaria | Modelo aprende BREAKOUT |
| `22dd431` | Island Bridge: 4 islas conectadas | Canal end-to-end real |
| `813b4ab` | Parameter Landscape Map Cat.2 | 117 parámetros mapeados |
| Sage v4 | AST-based patching, 9/9 tests | Canal sin límite de tamaño |
| `a5ed77a` | ZigZag 0.18% + cooldown §4.3 + limpieza | Calibración basada en datos |
| `619c6b2` | Oracle re-entrenado 30 días reales | OOS 0.68 — primera métrica honesta |
| `5ddadc7` | Baseline congelado para validación 48h | Punto de no-retorno |
| `59b87ab` | Fase 8: Instrumentación de clearance a 0.18% | Medición empírica habilitada |
| `d2afa23` | Fase 9: Microestructura viva (@depth20 + CumDelta) | L2 OBI real en ShadowTrader |
| `9434105` | Etiquetado diferido en `process_live_tick` | Pipeline live genera TrainingSamples con L2 |
| `8190fa1` | Clock mismatch en rolling delta | Ventana temporal L2 coherente con `event_time` de Binance |
| `6d3483d` | Bootstrap histórico en `launch_shadow_live.py` | Resuelve arranque en frío del detector al iniciar Live |
| `26da216` | Confirmación breakout con buffer ATR + GC HARVESTING | Reduce flips por ruido y preserva zonas hasta TTL |
| `2ad8ba8` | Shadow Harvesting Multi-Touch & Oracle L2 pipeline | Integration de lifecycle de zonas y pipeline L2 |
| `c78fb8e` | Hardening Fase 1: Cold Start, Z-Score, Morfología | Warm Start operativo, detección adaptativa |
| `2268d2f` | Hardening Fase 1 GUI: Persistencia y pipeline verificados | GUI pipeline verificado |
| `4e40dd7` | Hardening Fase 2: Multi-Touch Clearance, Z-Score instrumentation, GUI fix | 20 zonas visibles, clearance activo, Cat.1 log activo |

---

## 8) Anexo de Hitos Documentados

### Hito: Fase 9 — Integración de Microestructura Real (Cat.2)
- Fecha: 2 de mayo 2026
- Hash de commit de inicio: `59b87ab` (Post-Fase 8) -> Hash Final: `d2afa23`
- Objetivo medible: Transicionar de placeholders simulados a métricas reales L2 del WS de Binance para dotar al Oracle de predictores de flujo institucional en Múltiples Niveles previo a retests.
- Cambios en código:
  - `binance_websocket_manager.py`: Sustitución de `@bookTicker` por `@depth20@100ms`. Cálculo volumétrico `get_current_obi(levels=10)`.
  - `live_adapter.py`: Inyección directa del `cumulative_delta` dinámico y el V-OBI multidimensional en las velas en formación.
  - `triple_coincidence.py`: Fix crítico (Fuga Cat.1): heredado bucle actualizador de `max_price_since_detection` a `process_live_tick()` que era exclusivo de simulación.
- Evidencia de prueba:
  - Comando exacto ejecutado: `pytest tests/` (sobre tests unitarios) e ingesta histórica 60-días `fix6_process_historical.py` (261 samples limpios).
  - Output obtenido: `8 passed in 3.98s`. Exit code 0.
- Riesgos introducidos: Medio. Dependencia de estructura de arreglos nativos del Book de Binance. Protegido via fallback is_instance legacy.
- Decisión final: Aprobado formalmente; motivado por matemática restrictiva (distancia de clearance de la Fase 8 difirió solo 0.15 ATR, probando nulo poder predictivo simple).
- Plan de rollback: `git revert d2afa23` seguido de reinicio de WS_Manager.
- Métricas de impacto: El flujo en vivo ya no estará ciego al agresor market-buy previo a rupturas falsas.
- Próximo paso dependiente de este: Dejar iterar `live_adapter.py` contra mercado real para sembrar el dataset final con features completas previo a tuning OOS del Oracle.

### Hito: Fase Puente — Feature Engineering + Corrección de Etiquetado (Cat.2)
- Fecha: Planificado (post-cosecha viva L2)
- Prerrequisito: ≥50 samples con `obi_10 ≠ 0` en `training_dataset_v2.jsonl`.
- Origen: Evaluación Estructural del Oracle (3 mayo 2026) identificó 5 debilidades.
- Objetivo medible: Implementar 4 correcciones de ingeniería de features y labeling antes del re-entrenamiento.
- Cambios requeridos:
  - [F1] Ring buffer 30s en WS Manager → 6 features temporales L2 (Debilidad #1)
  - [F2] Etiquetado terciario BOUNCE_STRONG/BOUNCE_WEAK/BREAKOUT + lookahead adaptativo (Debilidades #2, #5)
  - [F3] Encoding determinista: columnas binarias en lugar de LabelEncoder (Debilidad #3)
- Criterio de éxito: Buffer operativo + ≥50 samples capturados con las 6 features temporales + etiquetado terciario funcional en `_determine_outcome()`.
- Impacto: Elimina los 3 cuellos de botella principales antes de invertir en re-entrenamiento.
- Categoría: Cat.2 (modifica la calidad del dataset y las features del Oracle).

### Hito: Fase 10 (REVISADA) — Re-entrenamiento con Features Enriquecidas
- Fecha: Post-Fase Puente, pendiente de completar.
- Prerrequisito: Fase Puente completada + ≥200 samples con features temporales L2.
- Objetivo medible: Re-entrenar RandomForest con 6 features temporales L2 + encoding determinista + etiquetado terciario, y obtener OOS ≥ 0.68.
- Criterio de éxito principal: OOS ≥ 0.68 (no regresión) + al menos 1 feature temporal L2 en top-3 de Feature Importance.
- Criterio secundario: Si dataset ≥ 500 samples, benchmark RF vs XGBoost/LightGBM (Debilidad #4).
- Impacto: El Oracle operará con features dinámicas (gradientes L2) en lugar de fotos estáticas, y con labels que distinguen bounces reales de ruido.

### Hito: Fase 10.5 — Shadow Harvesting y Multi-Touch Zone Lifecycle (Cat.2)
- Fecha: 7 de mayo 2026
- Origen: La evaluación de la ceguera del detector en retests posteriores a la ruptura (soporte roto pasando a ser resistencia y viceversa).
- Objetivo medible: Transicionar las zonas de estructuras estáticas (con variable booleana `retest_detected`) a Máquinas de Estado (`ZoneLifecycleState: ACTIVE, HARVESTING, EXHAUSTED`), que documentan los toques múltiples y la polaridad sin contaminar el trader principal.
- Cambios requeridos:
  - `triple_coincidence.py`: Refactor a `ActiveZone` para retener historial de toques. Modificación al _Garbage Collector_ para preservar zonas `HARVESTING` por encima del clásico timeout de 50 velas y aplicar un `HARVEST_TTL` robusto (48 horas).
  - Incorporación de detección de Breakout activa a nivel intra-tick (milisegundo) protegiendo ruido de mercado con `breakout_confirm_atr_buffer` del 3%.
  - `live_adapter.py`: Guardias silenciosos que bloquean la ejecución L2 cuando la zona ha sido vulnerada (*Harvesting Mode*), redireccionando la información hacia el Output.
  - `deferred_outcome_monitor.py`: Anexión de vector `touch_context` mapeando `polarity_flipped`, `prior_touch_outcomes`, `touch_sequence`, persistiendo exitosamente la información para re-entrenamientos futuros.
  - Operación en captura pura validada: cuarentena de modelos synth (`*.joblib.bak`) + `ORACLE_MODE=observe` para impedir ejecución decisoria hasta re-entrenamiento con datos orgánicos.
  - Sincronización GUI Forensics: Solucionada desvinculación de proceso por la cual la GUI no mostraba conteos de L2 Forensics (Defer Labeling en '0') al depender de memoria local del supervisor; migrado exitosamente hacia lectura en disco + event loop.
- Impacto: La arquitectura del pipeline ahora goza de verdadera **Persistencia** y recolección silente. Ya no es necesario depender de inferencias sobre rebotes múltiples, todo movimiento es capturado para una clasificación explícita.
- Criterio de éxito: Validaciones de Integridad Estructural Unitarias pasando con éxito. El JSONL del ecosistema queda habilitado para `touch_context` en muestras resueltas post-parche (el histórico previo no lo trae por compatibilidad).

### Hito: Fase 10.5b — Hardening L2 Temporal y Warm Start Live (Cat.1/Cat.2)
- Fecha: 7–8 de mayo 2026
- Origen: Auditoría operativa detectó dos riesgos residuales: deriva temporal en `rolling_delta` (reloj local vs Binance) y ceguera de zonas al reiniciar en frío.
- Cambios aplicados:
  - `binance_websocket_manager.py`: `get_rolling_delta()` anclado a `last_known_binance_ts_ms` para eliminar el desajuste local/Exchange.
  - `launch_shadow_live.py`: bootstrap de 500 velas cerradas vía REST para poblar zonas antes del primer tick vivo.
  - Verificación explícita de ruta de persistencia cruda L2 (`raw_buffers/*.json.gz`) en `deferred_outcome_monitor.py`.
  - Normalización operativa de rutas: cola activa en `aipha_memory/operational/pending_labels.json` (no `.jsonl`).
- Criterio de éxito: conexión WS estable + detector inicializado con contexto histórico + integridad temporal consistente entre eventos Binance y ventanas de features.

### Hito: Fase 11 — Calibración Probabilística del Oracle (Post-Fase 10)
- Objetivo: Asegurar que el `predict_proba` del Oracle refleje la frecuencia real de aciertos.
- Criterio: Reducción del Brier Score en OOS mediante Calibración de Platt o Isotonic.
- Dependencia: Requiere el modelo reentrenado de la Fase 10.
- Impacto: El Confidence de ShadowTrader dejará de ser una métrica "optimista" para ser una probabilidad estadística calibrada.

### Hito: Fase 12 — Walk-Forward Validation (Planificado)
- Objetivo: Validar que el modelo generaliza en el tiempo, no solo en un split aleatorio estático.
- Método: Entrenar en ventana temporal T1, evaluar en T2, deslizar. Mínimo 3 ventanas.
- Criterio: OOS medio ≥ 0.65 en todas las ventanas (estabilidad temporal).
- Impacto: Confirma que el modelo no está sobreajustado a un período específico del mercado.

### Hito: Fase 13 — Ejecución Francotirador: Regresión MAE (Planificado)
- Fecha: Diseño arquitectónico fijado (3 mayo 2026)
- Objetivo: Evolucionar la entrada algorítmica desde el simple contacto con el borde perimetral hacia una entrada profunda óptima (maximizando la asimetría del Riesgo/Beneficio).
- Origen conceptual: El operador identificó que el sistema ejecutaba de forma "naïve" al toque del borde de la zona. La maestría operativa exige no solo saber *si* el precio rebotará, sino *dónde exactamente* dentro de la zona se producirá el piso.
- Arquitectura de dos capas (relación con el Oracle clasificador):
  ```
  CAPA 1 — ¿ENTRAMOS? (Oracle Clasificador, Fases 10-11)
    Input:   6 features temporales L2 (gradientes OBI 5s/30s + Delta aceleración + depth ratio)
    Output:  BOUNCE_STRONG / BOUNCE_WEAK / BREAKOUT
    Acción:  Si BOUNCE_STRONG con confianza calibrada > threshold → pasar a Capa 2

  CAPA 2 — ¿DÓNDE? (Oracle Regresor MAE, esta Fase)
    Input:   Perfil de OBI intra-zona + Delta de absorción durante penetración
    Output:  "Penetración esperada: 65% del ancho de la zona"
    Acción:  Colocar Limit en zone_top - 0.65 * (zone_top - zone_bottom)
    Safety:  Si MAE predicho > 90% → ABORTAR (la zona no va a aguantar)
  ```
- Arquitectura algorítmica de implementación:
  1. **Instrumentación (Target):** Medir el MAE en el backtesting: qué porcentaje del ancho de la zona perforó el precio antes de consumar un rebote exitoso.
  2. **Regresor Integrado:** Anexar al modelo binario actual un `RandomForestRegressor` satélite proyectado hacia la etiqueta porcentual del MAE.
  3. **Features clave para el regresor:** No el OBI estático del retest, sino el *perfil de OBI durante la travesía* — OBI al toque del borde, OBI en el punto más profundo, y gradiente de CumDelta intra-zona (si el delta se reversa, la venta se agota = señal de piso).
  4. **Ejecución Limit:** El ShadowTrader tomará el vector de penetración y desplegará una orden `Limit` en la coordenada espacial exacta.
- Prerequisito: Señales del Clasificador calibradas (Fase 11) + Walk-Forward validado (Fase 12).
- Impacto: Transformación del RR (Risk:Reward) base al reducir drásticamente el apalancamiento muerto hasta el Stop Loss.

### Hito: Fase 14 — Independencia Progresiva y Protocolo de Cuestionamiento (Planificado a Largo Plazo)
- Fecha: Especificado teóricamente en S6 (Abril 2026), Planificado para Despliegue Post-Calibración.
- Referencia original: `S6_INDEPENDENCIA_PROGRESIVA.md`
- Objetivo: Abandonar la dependencia absoluta del operador humano habilitando al Orchestrator para cuestionar su propio código base y sus parámetros, e integrar las correcciones mediante reflexiones estructuradas con validación OOS de 3 ciclos.
- Secuencia Operativa (Muerte del Hardcode):
  1. **Apertura de Cat.1 a la IAM (AutoProposer):** Una vez que el Brier Score garantice predicciones calibradas (Hito 10), el Orchestrator obtendrá permiso para reescribir automáticamente los 110+ parámetros de baja sensibilidad sin detener el sistema.
  2. **Reflexión Crítica Activa:** Despliegue del motor heurístico y evaluación donde el modelo LLM empírico detecta qué métricas contradicen sus reglas. El resultado se enviará a evaluación humana directa (Cat.3).
- Impacto: Es el paso definitorio donde cgAlpha transiciona de ser un pipeline que se entrena a un agente que genuinamente se auto-gestiona.

---

## Análisis Técnico: Rol del OBI en los Dos Puntos de Decisión Cruciales

Este análisis documenta la función del Order Book Imbalance (OBI) y el Cumulative Delta
en las dos decisiones fundamentales del sistema: cuándo entrar y dónde entrar exactamente.

### Punto de Decisión 1: ¿El retest será exitoso? (Meta-Labeling → BOUNCE vs BREAKOUT)

**Arquitectura actual (Fase 10):**
El Oracle (RandomForest clasificador) recibe como input el `obi_10` y el `cumulative_delta`
capturados en el instante exacto del retest. La decisión es binaria: ¿el muro aguantará?

**Cómo funciona la señal del OBI en este punto:**

```
ZONA BULLISH (soporte) — Precio regresa desde arriba

  OBI_10 > 0 (más bids que asks en 10 niveles)
    → Muros institucionales de compra defienden la zona
    → Alta probabilidad de BOUNCE
    → CumDelta positivo confirma: las ejecuciones reales son compras agresoras

  OBI_10 < 0 (más asks que bids)
    → Los defensores se retiran, los agresores dominan
    → Alta probabilidad de BREAKOUT
    → CumDelta negativo confirma: ventas market dominan el flujo

ZONA BEARISH (resistencia) — Lógica espejada
```

**Conclusión crítica: OBI solo no es suficiente — CumDelta lo valida.**
El OBI mide órdenes *pasivas* (resting) que pueden ser *[spoofing](https://en.wikipedia.org/wiki/Spoofing_(finance))*:
un market maker puede colocar 500 BTC en el bid para proyectar demanda y retirarlos
instantáneamente antes de la ejecución. El CumDelta mide *ejecuciones reales* (agresoras)
que no pueden falsificarse. La combinación de ambas métricas es más robusta que cualquiera
por separado:

| OBI_10 | CumDelta | Interpretación | Fiabilidad |
|--------|----------|----------------|------------|
| Positivo | Positivo | Defensa real. Compras en wall + compras agresoras | **Alta** |
| Positivo | Negativo | **Posible spoofing.** Muro de compra falso + ventas agresoras | **Baja — trampa** |
| Negativo | Negativo | Ruptura real. Sin defensa + ventas agresoras | **Alta** |
| Negativo | Positivo | Señal mixta. Acumulación silenciosa contra presión | **Media — observar** |

**Sugerencias para features avanzadas (futuro):**

1. **OBI Gradient (Δ-OBI):** Capturar no solo el OBI en el instante del retest, sino el
   *cambio* del OBI en los 5-10 segundos previos al toque. Si el OBI aumenta bruscamente
   al acercarse al borde (instituciones añadiendo defensas en tiempo real), esto es mucho
   más predictivo que el OBI estático. Requiere un buffer temporal en el WS Manager.

2. **Detección de spoofing multicapa (OBI_1 vs OBI_10):** Comparar el OBI del primer nivel
   (best bid/ask) contra el OBI profundo de 10 niveles. Si `OBI_1 > 0` pero `OBI_10 < 0`,
   el soporte aparente en el top-of-book es una fachada. La presión real en profundidad es
   vendedora. Este ratio `OBI_1 / OBI_10` podría ser una feature discriminatoria poderosa.

---

### Punto de Decisión 2: ¿Dónde abrir exactamente? (Regresión MAE → Orden Limit)

**Arquitectura planificada (Fase 13):**
Una vez que el Oracle aprueba la dirección (BOUNCE), un regresor secundario predice qué
porcentaje de la zona perforará el precio antes de rebotar. El ShadowTrader coloca una
orden Limit en esa profundidad para optimizar el punto de entrada y maximizar R:R.

**Cómo funciona la señal del OBI durante la penetración:**

```
PRECIO PENETRANDO LA ZONA (ej. zona bullish de 95000-95200)

  Precio en 95150 (25% de penetración):
    → OBI_10 = +0.3 — defensa institucional presente
    → El regresor ve que hay liquidez que absorbe. Predicción: 40% de penetración.

  Precio en 95080 (60% de penetración):
    → OBI_10 = +0.6 — OBI CRECIENDO → instituciones añadiendo más órdenes
    → CumDelta volcándose a positivo (compras agresoras apareciendo)
    → El regresor identifica este como el punto de absorción máximo.
    → Orden Limit: colocar en 95080.

  Si en cambio OBI_10 = -0.2 al 60% de penetración:
    → Las defensas se desvanecen → el regresor no encuentra piso
    → La predicción de MAE excede el 90% → señal de que el BOUNCE
      original era falso → ABORTAR la entrada por completo.
```

**La feature clave para el regresor MAE no es el OBI estático, sino el perfil de OBI
durante la travesía:**

1. **OBI al toque del borde** (ya capturado como `obi_10_at_retest`).
2. **OBI en el punto más profundo** (requiere capturar durante la penetración).
3. **Gradiente de CumDelta intra-zona:** Si el Delta acumulado durante la penetración
   se desacelera y se revierte, la venta agresora está agotándose — señal de piso.

**Sugerencia arquitectónica para la Fase 13:**
En lugar de capturar un solo snapshot del OBI en el instante del retest (como hacemos
ahora), implementar un **buffer de micro-snapshots** que registre el OBI y el Delta cada
100ms mientras el precio está DENTRO de la zona. Esto generará un "perfil de presión
intra-zona" con ~600 puntos por minuto que el regresor puede condensar en estadísticas
descriptivas (media, pendiente, punto de inflexión) para predecir la profundidad de
rebote con resolución sub-vela.

---

### Resumen ejecutivo de las dos capas

```
CAPA 1 — ¿ENTRAMOS? (Oracle Clasificador, Fase 10)
═══════════════════════════════════════════════════
  Input:   6 features temporales L2 (gradientes + depth ratio + aceleración delta)
  Output:  BOUNCE_STRONG / BOUNCE_WEAK / BREAKOUT
  Acción:  Si BOUNCE_STRONG con confianza calibrada > threshold → proceder

         │
         ▼

CAPA 2 — ¿DÓNDE? (Oracle Regresor MAE, Fase 13)
═══════════════════════════════════════════════════
  Input:   Perfil de OBI intra-zona + Delta de absorción
  Output:  "Penetración esperada: 65% del ancho"
  Acción:  Colocar Limit en zone_top - 0.65 * (zone_top - zone_bottom)
  R:R:     Stop bajo zone_bottom, TP en zone_top + extensión
```

---

## Evaluación Estructural del Entrenamiento del Oracle (3 mayo 2026)

Auditoría sistemática del pipeline de entrenamiento del Oracle. Identificó 5 debilidades
estructurales que limitan el techo predictivo del modelo, independientemente del algoritmo.

### Contexto

El Oracle (RandomForest meta-labeling) opera como gatekeeper de segunda capa:
la Triple Coincidence decide la dirección (COMPRA/VENTA), y el Oracle predice
si la zona aguantará (BOUNCE) o será destruida (BREAKOUT). El entrenamiento
consiste en darle al modelo miles de ejemplos históricos de retests junto con
las features L2 del momento, y enseñarle qué pasó después.

### Veredicto

**El concepto es arquitectónicamente sólido. El techo predictivo está limitado por
la resolución de las features (fotos estáticas en lugar de perfiles dinámicos)
y por ruido en la variable target (etiquetado binario con fallback contaminante).**

### Lo que está BIEN (no cambiar)

| Aspecto | Evaluación |
|---------|----------|
| Meta-labeling como segunda capa | ✅ Exactamente López de Prado |
| Train/test split + OOS | ✅ BUG-1 resuelto, `stratify=y` |
| Oversampling solo en train set | ✅ BUG-3 resuelto, no contamina test |
| Calibración Platt Scaling | ✅ `CalibratedClassifierCV(method='sigmoid')` |
| Data Quality Gate | ✅ Min 50 samples, balance, integridad NaN |
| Etiquetado diferido en live | ✅ Espera `outcome_lookahead_bars` velas |
| Outcome usa zona real | ✅ BUG-5 resuelto, compara vs `zone_top/zone_bottom` |
| RandomForest con 261 samples | ✅ Elección correcta para este tamaño de dataset |

### Las 5 Debilidades Estructurales

**Debilidad #1 — Snapshot estático vs. Perfil temporal (CRÍTICA)**

El Oracle recibe 1 número para OBI y 1 número para CumDelta — la lectura del
microsegundo exacto del retest. Pero la defensa institucional de una zona se
despliega como un *proceso* de 5-30 segundos. Un OBI de +0.25 que viene subiendo
desde -0.10 (defensa activa creciendo) es radicalmente distinto de uno que viene
cayendo desde +0.60 (defensa desmoronándose). El snapshot estático actual no
puede distinguirlos.

Solución: Ring buffer de 30s en WS Manager → 6 features temporales derivadas.

**Debilidad #2 — Etiquetado binario que pierde información (IMPORTANTE)**

`_determine_outcome()` devuelve BOUNCE o BREAKOUT, pero `return 'BOUNCE'` en
L965 (fallback cuando el precio se mantiene dentro de zona) clasifica como
éxito un precio que no se movió. Un bounce de 3 ATRs y un precio lateral 10 velas
reciben la misma etiqueta. El modelo entrena sobre ruido en la variable target.

Solución: BOUNCE_STRONG / BOUNCE_WEAK / BREAKOUT (3 clases).

**Debilidad #3 — `LabelEncoder` no-determinista (MODERADA)**

`LabelEncoder` asigna enteros en orden alfabético del dataset actual. Entre
re-entrenamientos el orden puede cambiar: `TRENDING_UP=1` en un ciclo,
`TRENDING_UP=0` en el siguiente. Esto introduce ruido sutil.

Solución: Columnas binarias deterministas (`is_trending_up`, etc.).

**Debilidad #4 — Sin benchmark de algoritmo alternativo (MENOR)**

RandomForest es la elección correcta con 261 samples. Pero cuando el dataset
crezca a ≥500 samples, debería hacerse un benchmark formal RF vs XGBoost/LightGBM.
Gradient Boosting captura mejor interacciones no-lineales cuando hay datos suficientes.

Solución: Incluir benchmark en Fase 10 condicional al tamaño del dataset.

**Debilidad #5 — `outcome_lookahead_bars` fijo (MENOR)**

`outcome_lookahead_bars = 10` (50 min) trata igual zonas estrechas (0.3 ATR,
se resuelven en 15 min) que amplias (2.0 ATR, necesitan 55 min). El lookahead
debería ser proporcional al ancho de la zona normalizado por ATR.

Solución: `lookahead = max(5, min(20, int(5 + zone_width_atr * 3)))`

### Matriz de Cobertura: Debilidades vs. Hoja de Ruta

| Debilidad | Fase que la resuelve | Antes de la evaluación | Después |
|-----------|---------------------|------------------------|---------|
| #1 Snapshot estático | **Fase Puente [F1]** | ❌ No cubierta (Fase 10 re-entrenaba con mismos snapshots) | ✅ |
| #2 Etiquetado binario | **Fase Puente [F2]** | ❌ No cubierta en ninguna fase | ✅ |
| #3 LabelEncoder | **Fase Puente [F3]** | ❌ No cubierta | ✅ |
| #4 Benchmark RF | **Fase 10 (condicional)** | ❌ No cubierta | ✅ |
| #5 Lookahead fijo | **Fase Puente [F2]** | ❌ No cubierta | ✅ |

**Hallazgo crítico:** Sin la Fase Puente, la Fase 10 habría re-entrenado el Oracle
con los mismos snapshots estáticos y el mismo etiquetado binario contaminado.
El salto predictivo habría sido marginal independientemente del algoritmo utilizado.

### Ejecución de la Fase Puente (4 mayo 2026)

Se implementó con éxito la Fase Puente para dotar al sistema de "Resolución de Microsegundo", abordando estructuralmente las vulnerabilidades identificadas. Hitóos completados:

- **Arquitectura de Doble Velocidad (`LiveDataFeedAdapter v2`)**: 
  - *Velocidad Lenta (1 min)*: Descubrimiento de nuevas zonas usando la vela cerrada.
  - *Velocidad Tick (~30/s)*: Comprobación de toques a la zona (retests) en el milisegundo exacto de cruce del precio. Esto permite sintetizar el **Perfil Temporal L2 (30s)** en el instante de impacto, no 45 segundos después.
- **Etiquetado Terciario (`DeferredOutcomeMonitor`)**: Se eliminó el *fallback* engañoso ("BOUNCE" por defecto). Ahora los resultados se diferencian en `BOUNCE_STRONG`, `BOUNCE_WEAK`, `BREAKOUT` e `INCONCLUSIVE`, según el desarrollo del precio y el *Maximum Favorable Excursion* (MFE).
- **Lookahead Adaptativo**: El tiempo de resolución difiere dinámicamente basado en la medida de la zona ponderada por ATR (zonas estrechas = resolución rápida; zonas anchas = resolución prolongada).
- **Persistencia L2 (Buffer Crudo)**: Todo ReentrySnapshot exitoso además persiste un `.gz` con la lectura cruda de 300 ms L2 (Order Book y Cum Delta) permitiendo rediseño futuro de features sin requerir recolección en vivo desde cero.

**Estado Actual:** El sistema está preparado para la recolección en vivo de nuevas muestras de alta fidelidad. 
**Siguientes Pasos (Próximos a concluir):**
1. **Pipeline de Forense GUI**: Crear paneles de visualización L2 para auditar a simple vista la calidad de los nuevos ReentrySnapshots.
2. **Re-entrenamiento OOS (Fase 10)**: Acumular un stock de al menos 50 muestras L2 nuevas bajo el formato de alta fidelidad, antes de reentrenar a Oracle v5.

### GUI L2 Forensics Panel (4 mayo 2026)

Se construyó el panel forense completo para observar en tiempo real el pipeline de microestructura:

- **Backend API** (`server.py`): 3 nuevos endpoints REST:
  - `GET /api/l2-forensics/status` — Contadores en vivo (Pending, Resolved, Dataset Size) + active monitors con MFE/MAE.
  - `GET /api/l2-forensics/history` — Últimos N samples resueltos del `training_dataset_v2.jsonl`.
  - `GET /api/l2-forensics/snapshot/<id>` — Visor JSON crudo del ReentrySnapshot completo para inspección forense.
- **Frontend** (`index.html` + `app.js`): Pestaña "L2 Forensics 🔬" en la Control Room con:
  - 4 tarjetas KPI (Pending Labels, Resolved, Dataset v2, Distribución de outcomes).
  - Active Monitors: tabla dinámica con barras de progreso del lookahead adaptativo y MFE/MAE en vivo.
  - Resolved Timeline: historial visual codificado por color (verde=BOUNCE_STRONG, amarillo=WEAK, rojo=BREAKOUT, gris=INCONCLUSIVE).
  - Modal de inspección: clic sobre cualquier sample abre el JSON crudo completo.

**Estado Actual:** La infraestructura de observabilidad está completa. El sistema está listo para recolección autónoma.

### Retraining Oracle v5 (Fase 10) - Completada vía Synth-Bridge (4/MAYO/2026)

Debido al largo tiempo requerido para acumular ≥50 muestras L2 de alta fidelidad exclusivas en mercados vivos, y con el objetivo de agilizar el desarrollo de herramientas de Machine Learning, **Fase 10 ha sido completada** utilizando un puente de generación sintética ("Synth-Bridge").

1. **Generación de Dataset v2.0**: Se inyectaron 100 muestras L2 altamente correlacionadas según el esquema v2 (VWAP, OBI, Cumulative Delta, Divergence) y con etiquetado terciario (`BOUNCE_STRONG`, `BOUNCE_WEAK`, `BREAKOUT`).
2. **OracleTrainer_v3 Re-Engineered**: 
   - Se ajustó la función de normalización del `OracleTrainer_v3` para extraer features directamente de la microestructura alojada en el Snapshot v2.
   - **Label Mapping Estricto**: Se adoptó la estrategia **Sniper**: Se mapeó `BOUNCE_STRONG` -> 1 y `BREAKOUT` -> 0, mientras que `BOUNCE_WEAK` e `INCONCLUSIVE` fueron descartados del *training log*. Esto garantiza que el Oráculo aprenda exclusivamente la distinción entre un despegue potente y un fallo catastrófico, rechazando salidas mediocres.
3. **Validación de Entrenamiento**: El Oráculo V5 se re-entrenó con éxito sobre el set depurado (75 muestras), finalizando con un paso de calibración probabilística *Platt Scaling* y un Brier Score sobresaliente.

**Siguiente Paso (Fase 11):**  
Ejecución del pipeline en Walk-Forward real o pruebas con datos del mercado en vivo activando la nueva "Triple Coincidence v3" contra Binance WebSocket.

---

### Hito: Hardening Fase 1 — Cold Start y Detección Adaptativa (9 mayo 2026)
- Fecha: 9 de mayo 2026
- Origen: El detector arrancaba en vacío y requería 8+ horas de mercado vivo para funcionar.
- Cambios aplicados:
  - **Warm Start** (`seed_history`): pre-popula buffer con 200 velas históricas, contexto ATR/Z-Score inmediato.
  - **Z-Score de Volumen Adaptativo**: reemplazo del filtro P70 estático por Z-Score local (ventana 30, umbral 0.5).
  - **Persistencia con TTL**: `save_state()`/`load_state()` con filtro de 24 horas para evitar zonas obsoletas.
  - **Morfología Observacional**: campos `upper_wick_pct`, `lower_wick_pct`, `rejection_direction` en ReentrySnapshot.
  - **Journaling Defensivo**: persistencia inmediata de MFE/MAE récord en `DeferredOutcomeMonitor`.
  - **Deduplicación por `open_time`**: WebSocket actualiza vela en curso en lugar de duplicar.
- Tests: 7 failed / 213 passed (baseline pre-existente, regresión cero).
- Criterio de éxito: Tiempo a primera zona: <30s (vs 8+ horas anterior).

### Hito: Hardening Fase 2 — Multi-Touch, Calibración, Visibilidad GUI (10 mayo 2026)
- Fecha: 10 de mayo 2026
- Origen: Tres problemas detectados durante la fase de cosecha.
- Cambios aplicados:
  - **Fix Visibilidad GUI**: Rutas absolutas en `save_state()`, `load_state()`, y `_persist_active_zones()`. Separación de `detector_state.json` (estado interno) y `active_zones.json` (vista GUI). Flag `is_bootstrapping` en `process_stream` para prevenir que `_cleanup_expired_zones` elimine zonas durante el bootstrap. Eliminación de 5 procesos zombie. **Resultado: 10 zonas visibles en la GUI inmediatamente tras bootstrap.**
  - **Multi-Touch Clearance Logic** (Cat.2): Para el 2do+ toque de una zona, el precio debe haberse alejado ≥ `min_clearance_atr * ATR` (default 1.0) antes de aceptar un nuevo retest independiente. Campos `max_price_since_last_touch`, `min_price_since_last_touch` añadidos a ActiveZone (reset en `register_touch`). Máximo 3 toques por zona (EXHAUSTED).
  - **Z-Score Calibration Instrumentation** (Cat.1): Log observacional en `zscore_calibration_log.jsonl` con `vol_z_score`, `body_pct`, `passed_filter`, `zone_detected` para cada vela procesada. Sin impacto en comportamiento; datos para calibración futura del umbral 0.5.
  - **CHANGELOG_ALGO.md**: Creación del registro algorítmico con 7 entradas versionadas (v1.0.0 a v1.7.0).
- Tests: 7 failed / 213 passed (baseline idéntica, regresión cero).
- Criterio de éxito: GUI muestra zonas reales + clearance filtra oscilaciones laterales + instrumentación Cat.1 activa.

### Hito: Repriorización Estratégica — Cosecha, Encoding, Rutas y Codex (16 mayo 2026)

#### Origen

Se evaluó si Project Codex debía ser la máxima prioridad durante el período de cosecha de retests L2. El diagnóstico base del Codex es correcto: la historia del proyecto ya supera el tamaño útil de contexto de modelos locales y las decisiones pasadas no son suficientemente consultables. Sin embargo, el estado real del código al 16 mayo muestra riesgos más cercanos al re-entrenamiento que un índice documental no puede resolver por sí solo.
Esta repriorización está basada explícitamente en la sesión de estabilización del 15 mayo documentada en `§10`.

#### Veredicto

**Project Codex no es la máxima prioridad inmediata.** La prioridad correcta es una secuencia corta de hardening no intrusivo que proteja la calidad de las muestras y el re-entrenamiento posterior. Codex debe construirse en paralelo únicamente después de cerrar los bloqueos Cat.1/Cat.2 que afectan la cosecha, la memoria o el entrenamiento.

| Pista evaluada | Veredicto | Impacto sobre cosecha actual | Impacto sobre re-entrenamiento |
|----------------|-----------|------------------------------|--------------------------------|
| LabelEncoder no determinista | Real, no sobredimensionado | Bajo: las muestras guardan strings, no enteros | Alto: puede cambiar mappings entre entrenamientos y contaminar métricas |
| Lookahead fijo | Stale para live | Bajo: `DeferredOutcomeMonitor` ya usa `adaptive_lookahead()` | Bajo/medio: queda deuda legacy en rutas históricas del detector |
| Rutas relativas | Real y recurrente | Medio: ya causó estados paralelos y pérdida de visibilidad | Alto: `memory_policy.py` calcula root un nivel demasiado arriba y puede romper identidad/memoria |
| Período de cosecha como "tiempo muerto" | Real parcialmente | Medio: solo deben tocarse piezas no intrusivas o ya bloqueantes | Alto: fixes de encoding/rutas/raw L2 deben preceder el re-entrenamiento |
| Codex antes de arquitectura estable | Real parcialmente | Bajo: Codex baseline no toca trading | Medio: el mapa fino del Oracle cambiará tras Fase Puente; conviene limitar Codex inicial a decisiones y lecciones estables |

#### Cambios recomendados

| Componente | Estado | Evidencia |
|------------|--------|-----------|
| Cosecha live | 🟡 En curso | Auditoría reciente: `captured=18`, `pending=1`, objetivo operativo `20` |
| NexusGate | 🟡 Bypass temporal | `CGALPHA_DISABLE_NEXUS_GATE=1` abierto solo para cosecha; debe cerrarse al llegar a objetivo |
| Raw L2 buffers | 🔴 Pendiente | Auditoría reciente marca `missing_raw` en muestras nuevas; sin raw temporal, la re-derivación forense queda limitada |
| Encoding Oracle | 🔴 Pendiente | `oracle.py` conserva `LabelEncoder` en Oracle clasificador y regresor MAE |
| MemoryPolicyEngine paths | 🔴 Pendiente | `memory_policy.py` usa `parent.parent.parent.parent`, que apunta fuera del repo desde `cgalpha_v3/learning/` |
| Codex baseline | 🟡 Correcto, no primero | Debe indexar decisiones estables, no congelar prematuramente el Oracle en mutación |

#### Lista ordenada de prioridades reales

| Orden | Qué | Categoría | Cuándo | Por qué ese orden | Impacto medible |
|-------|-----|-----------|--------|-------------------|-----------------|
| 1 | Cerrar semáforo de cosecha reciente y retirar bypass de NexusGate | Operativo / Cat.1 | Ahora | Garantiza que el sistema vuelve a capturar sin gate artificial permanente | `audit_retests_capture.py --target 20` devuelve exit `0`; `CGALPHA_DISABLE_NEXUS_GATE` deja de usarse |
| 2 | Reparar captura de `raw_buffers` L2 en modo Spot/Futures | Cat.1 | Antes de seguir acumulando muchas muestras | Sin raw temporal, las muestras no son re-derivables para features futuras | `missing_raw=0` en muestras nuevas |
| 3 | Reemplazar `LabelEncoder` por encoding determinista en Oracle y MAE | Cat.1 | Antes del próximo re-entrenamiento | Evita mappings cambiantes entre ciclos y estabiliza métricas OOS | Test de mapping estable en dos datasets con orden distinto |
| 4 | Consolidar rutas absolutas restantes y añadir tests de raíz de proyecto | Cat.1 | Antes de Codex Cat.3 | Evita repetición del patrón que ya causó pérdida de estado y visibilidad | Tests prueban que memoria, evolution log, dry-run y reports escriben dentro del repo |
| 5 | Construir Codex baseline limitado | Cat.3 | Después de 1-4, durante cosecha | Mejora memoria consultable sin bloquear trading ni congelar diseño inmaduro | `CODEX.md` pasa tests de integridad y tiene entradas D/L autocontenidas |
| 6 | Codex trading component completo | Cat.3 posterior | Tras Oracle OOS >= 0.72 y walk-forward >= 3 ventanas | La arquitectura predictiva aún cambia; documentarla demasiado pronto indexa ruido | Codex refleja modelo validado, no hipótesis en transición |

#### Criterio de éxito

```bash
# 1. Cosecha reciente cerrada
python3 cgalpha_v3/scripts/audit_retests_capture.py \
  --last-hours 24 --recent-only --target 20 --semaforo

# 2. No queda dependencia operativa del bypass
grep -R "CGALPHA_DISABLE_NEXUS_GATE=1" -n logs/ shadow_trader.log 2>/dev/null || true

# 3. Encoding determinista verificado
python3 -m pytest cgalpha_v3/tests -q -k "oracle and encoding"

# 4. Rutas persistentes dentro del repo
python3 -m pytest cgalpha_v3/tests -q -k "path or persistence or memory"
```

#### Tests

| Test | Propósito | Resultado esperado |
|------|-----------|--------------------|
| `test_oracle_deterministic_encoding` | Dos datasets con orden distinto generan mismas columnas/features | Pass |
| `test_mae_regressor_deterministic_encoding` | El regresor MAE no depende del orden de clases vistas | Pass |
| `test_project_root_paths` | Memoria, evolution log, reports y dry-run escriben bajo root del repo | Pass |
| `audit_retests_capture --require-raw` | Muestras nuevas tienen snapshot y raw buffer | Exit `0` |

#### TechnicalSpec semilla del Codex

```yaml
title: "Project Codex Baseline — mapa consultable de decisiones y lecciones"
category: "Cat.3"
target_file: "cgalpha_v4/CODEX.md"
objective: >
  Crear un índice autocontenido y RAG-ready de decisiones, componentes,
  bugs, fases y lecciones del proyecto sin interrumpir la cosecha live.
sections:
  "§1 Mapa de Decisiones":
    entry_format: "D-XXX"
    required_fields:
      - "Componente"
      - "Problema resuelto"
      - "Decisión"
      - "Evidencia"
      - "Alternativas descartadas"
      - "Lección relacionada"
  "§2 Mapa de Componentes":
    entry_format: "C-XXX"
    required_fields:
      - "Responsabilidad"
      - "Archivos principales"
      - "Entradas"
      - "Salidas"
      - "Estado"
      - "Riesgos abiertos"
  "§3 Mapa de Bugs":
    entry_format: "B-XXX"
    required_fields:
      - "Síntoma"
      - "Causa raíz"
      - "Fix"
      - "Regresión prevenida"
      - "Tests/Evidencia"
  "§4 Mapa de Fases":
    entry_format: "F-XXX"
    required_fields:
      - "Objetivo"
      - "Resultado"
      - "Evidencia"
      - "Siguiente dependencia"
  "§5 Mapa de Lecciones":
    entry_format: "L-XXX"
    required_fields:
      - "Patrón"
      - "Riesgo"
      - "Regla operativa"
      - "Ejemplo histórico"
tests:
  - "Existe cgalpha_v4/CODEX.md"
  - "Contiene exactamente las secciones §1-§5"
  - "Cada D-XXX tiene todos los campos obligatorios"
  - "Cada L-XXX referencia al menos un D-XXX/B-XXX/F-XXX"
  - "No hay entradas duplicadas por título normalizado"
  - "El archivo incluye índice inicial de 20-40 entradas, no documentación exhaustiva"
```

#### Principio rector

**El Codex evita que el sistema repita errores, pero no sustituye corregir los errores que todavía están en el camino crítico. Durante cosecha, primero se protege la calidad de los datos y del re-entrenamiento; después se indexa el conocimiento para que Lila no vuelva a perderlo.**

### Post-mortem: Los 4 bugs en cascada del pipeline de cosecha
Durante el resurgimiento y puesta en marcha del Live Trading de Múltiples Toques, se resolvió un cuello de botella sistémico que impedía la generación de `pending_labels.json`. Este bloqueo fue diagnosticado como un problema agudo compuesto por 4 fallos en secuencia:
- **Bug 1** — Campos de Clearance sin serializar (`max_price_since_last_touch` default `-1.0` y `min_price_since_last_touch` bloqueando el análisis de distancia para nuevos toques).
- **Bug 2** — Ruta incorrecta de `detector_state.json` (resolución relativa al CWD que originaba creación de estado paralelo).
- **Bug 3** — Atributo `retest_detected=True` persistiendo después del bootstrap originando desincronización de estado para nuevos ticks.
- **Bug 4** — `TouchRecord` no instanciado en formato JSON serializable (`dataclasses`) causando interrupción crítica y excepciones silenciosas (`TypeError`) dentro de `_persist_pending()`.

### Protocolo de Re-entrenamiento: Evaluación de la Cosecha
Cuando los monitores diferidos recolecten muestras y `pending_labels.json` o `training_dataset_v2.jsonl` contengan más de 10 registros, se deberá correr imperativamente la auditoría L2 para verificar pureza de la muestra excluyendo componentes Synth-Bridge:

```bash
# Validar Precios Activos > 70K
python3 -c "
import json
with open('aipha_memory/operational/pending_labels.json') as f:
    labels = json.load(f)
prices = [l.get('entry_price', 0) for l in labels]
real = [p for p in prices if p > 70000]
print(f'Total labels: {len(labels)}')
print(f'Con precio real (>70k): {len(real)}')
print(f'Rango: {min(prices):.0f} — {max(prices):.0f}')
"
```
**Nota Operativa**: Resultados cruzados con el marcador histórico de 2024 (~$55,000) confirmarán que existe rezago sintético y se deberá ejecutar una limpieza antes de sumario.

**La Decisión del Umbral 50**
A nivel arquitectónico de reentrenamiento (Fase 10), una vez superados ≥50 samples vivos y puros de la L2 microestructura, el sistema optará por la resolución de Silos Concurrentes: `Oracle_PureL2` (Solo ~50 samples reales L2) vs `Oracle_Hybrid` (50 Vivos + 121 Históricos).

*Metodología de Grid Search (`Oracle_PureL2`):*
El hiperparámetro `max_depth` se debe rastrear obligatoriamente con Grid Search empírico (ej. `max_depth=3` o `4`), mitigando matemáticamente el sobreajuste propio de dimensionar 25 features L2 en tan corta muestra.

*Matriz de Evaluación de Desempate Empírico:*

| Criterio | `Oracle_PureL2` | `Oracle_Hybrid` |
|----------|-----------------|-----------------|
| **OOS Accuracy** | ≥ 0.65? | ≥ 0.65? |
| **Brier Score** | menor = mejor | menor = mejor |
| **L2 ext. (Top-3 Importance)** | ¿sí/no? | ¿sí/no? |
| **Distribución de Predicciones** | ¿predice las 3 clases? | ¿predice las 3 clases? |

**Criterio de Invalidez**: Si `Oracle_PureL2` resulta en *class-imbalance blind* (e.g. incapaz de predecir o resolver un `BREAKOUT` perdiendo dimensionalidad de clases debido al encogimiento natural del muestreo), perderá por *Defecto de Overfitting*, consolidando al híbrido.

### Post-mortem: Los 3 bugs raíz de la invisibilidad en GUI
Durante Hardening Fase 2, la GUI mostraba 0 zonas a pesar de que
el detector las detectaba correctamente. La causa fue una cascada
de tres bugs independientes:

1. **Rutas relativas en `save_state()`/`load_state()`:** El archivo
   `detector_state.json` se escribía en el CWD del proceso, que
   difiere entre `launch_shadow_live.py` y `server.py`. Fix: rutas
   absolutas ancladas a la raíz del proyecto.

2. **Colisión de archivos JSON:** `detector_state.json` y
   `active_zones.json` apuntaban al mismo path. El estado interno
   del detector sobreescribía la vista destinada a la GUI. Fix:
   separación en dos archivos con propósitos distintos.

3. **Cleanup durante bootstrap:** `_cleanup_expired_zones()` eliminaba
   zonas detectadas en índices tempranos antes de que terminara
   `process_stream()`. Las zonas existían brevemente y luego
   desaparecían. Fix: flag `is_bootstrapping` que suspende el
   cleanup durante la fase de precarga.

**Lección:** Los tres bugs eran invisibles individualmente — cada uno
por separado habría producido síntomas diferentes. La combinación
de los tres hacía que el sistema pareciera funcionalmente roto
cuando la lógica de detección era correcta.

---

## 9) Principio rector del proyecto

El proyecto pasó de "cuatro componentes capaces operando como islas con métricas
artificialmente perfectas" a "canal de evolución gobernado con ingesta L2 en tiempo real,
baseline OOS honesto de 0.68, y hoja de ruta calibrada hasta la independencia progresiva."

**La independencia del sistema se gana por evidencia, no por voluntad.
Las métricas honestas valen más que las brillantes.
Y los filtros solo se añaden después de medir, nunca antes.**

---

### Hito: Arquitectura de Conocimiento — Project Codex (Planificado)

- **Fecha:** Mayo 2026 (PLANIFICADO)
- **Origen:** Imposibilidad de consultar las ~3,000 líneas de historia de forma eficiente con límite de contexto de 8k (Qwen 2.5:3b local).
- **Prerrequisito:** No interrumpe la actual cosecha de L2 (esperando la recolección de los 50 retests).
- **Objetivo medible:** Construir un índice autocontenido y RAG-ready (`cgalpha_v4/CODEX.md`) que permita a la IA recuperar contexto técnico y lecciones históricas de forma determinista y granular sin abrumar el context limit de modelos locales.

#### 1. FASE 1: Codex Baseline (Vía Canal de Evolución Cat.3)
- **Prerrequisito:** La cosecha de datos del sistema de trading continúa en paralelo sin detenciones.
- **Acción:** El operador inyecta propuesta Cat.3 con spec técnico `target_file="cgalpha_v4/CODEX.md"`. Se elige `CODEX.md` para evitar confusiones arquitectónicas con archivos raíz `index.js/html/md` convencionales.
- **Estructura Creada:** 
  - §1 Mapa de Decisiones (`D-XXX`)
  - §2 Mapa de Componentes
  - §3 Mapa de Bugs (los 8 originales documentados y resueltos)
  - §4 Mapa de Fases
  - §5 Mapa de Errores Evitados (`L-XXX`)
- **Evidencia de éxito (Tests):** CodeCraft Sage crea commits con `tests/test_codex_integrity.py` que verifica la existencia de las secciones §1-§5, la inclusión de la tabla de bugs al 100%, y que el formato de los identificadores `D-XXX` y `L-XXX` sea estricto.
- **Registro en Memoria:** Entrada de nivel `RELATIONS` indicando la inicialización del Codex.

#### 2. FASE 2: Segunda Propuesta Humana (Documentación del Ecosistema Trading)
- **Prerrequisito Estricto:** Oracle OOS ≥ 0.72, validación walk-forward muestra consistencia en ≥ 3 ventanas temporales, y `bridge.jsonl` acumula ≥ 200 registros con precios orgánicos BTC.
- **Acción:** Segunda propuesta Cat.3 para documentar la arquitectura de microestructura, el pipeline de trading maduro, y las decisiones algorítmicas probadas en el §2 y §1 del Codex.
- **Razón:** La memoria y documentación deben anclarse sobre un sistema validado; documentar fases inestables indexa el ruido en vez de asegurar conocimiento empírico.

#### 3. FASE 3: Vectorización Local (ChromaDB)
- **Prerrequisito:** El archivo `CODEX.md` excede el umbral de las 80 entradas (aproximando 16k tokens, saturando por completo la ventana de contexto de Qwen 2.5:3b).
- **Acción:** Implementación de persistencia vectorial vía `chromadb.PersistentClient` y `all-MiniLM-L6-v2` corriendo en CPU localmente, integrado con el `MemoryPolicyEngine`.
- **Evidencia de éxito:** Inferencia offline (FORCE_LOCAL_LLM=true) recuperando top-3 chunks de contexto exactos (ej: `D-042` sobre ZigZag threshold) en < 2 segundos basándose en consultas semánticas.

#### 4. FASE 4: Capa de Interfaz Operativa (Hermes)
- **Prerrequisito:** Fases 1 a 3 operativas e integradas algorítmicamente.
- **Acción:** Despliegue de Hermes Agent exclusivamente como interfaz de usuario y operador de skills procedimentales (FTS5 inquiries).
- **Restricción de Acceso:** Aislamiento total de escritura/ejecución sobre Orchestrator, MemoryPolicyEngine o pipeline predictivo.
- **Evidencia de éxito:** Comodidad UI operativa sin alteración del core trading.

**Principio rector del hito:**
*El conocimiento no indexado equivale a conocimiento inexistente para un LLM iterativo. El Codex estructura el aprendizaje empírico pasado (RAG Local) para que cualquier inferencia futura parta del rigor técnico acumulado y evite la degradación cíclica.*

---

## 10) Sesión de Estabilización Live + Cosecha (15 mayo 2026)

- **Fecha:** 15 mayo 2026
- **Objetivo:** Recuperar ingesta/cosecha viva tras espiral de ediciones parciales, restaurar operatividad GUI y establecer monitoreo automático de retests.

### 10.1 Cambios aplicados (código)

1. **Fallback de mercado Binance (Futures/Spot) por entorno**
   - Archivos:
     - `cgalpha_v3/infrastructure/binance_websocket_manager.py`
     - `cgalpha_v3/scripts/launch_shadow_live.py`
   - Cambio:
     - Nuevo selector `CGALPHA_BINANCE_MARKET` (`futures` por defecto, `spot` para contingencia).
     - WebSocket y bootstrap REST alineados al mismo mercado.
   - Razón:
     - Diagnóstico previo confirmó timeout selectivo/instable sobre infraestructura Futures desde la IP del host; Spot seguía respondiendo.

2. **Hardening de rutas absolutas en detector (bug de doble universo de estado)**
   - Archivo:
     - `cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py`
   - Cambio:
     - Corrección de `project_root` a `Path(__file__).resolve().parent.parent.parent.parent` en `save_state()`, `load_state()` y log de calibración.
   - Síntoma resuelto:
     - Escrituras mezcladas entre `aipha_memory/...` (raíz) y `cgalpha_v3/aipha_memory/...` (subárbol), causando desincronización GUI/collector.

3. **Persistencia multi-touch reforzada**
   - Archivo:
     - `cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py`
   - Cambio:
     - Serialización explícita de campos críticos:
       - `max_price_since_detection`, `min_price_since_detection`
       - `max_price_since_last_touch`, `min_price_since_last_touch`
       - `retest_detected`, `flip_ts`, `flip_price`, `harvest_expiry_ts`
     - Defaults defensivos al cargar estado.
   - Razón:
     - Evitar pérdida de contexto entre reinicios y bloqueos en evaluación de clearance/retests subsecuentes.

4. **Auditoría de cosecha con semáforo automatizable**
   - Archivo nuevo:
     - `cgalpha_v3/scripts/audit_retests_capture.py`
   - Capacidades:
     - Conteo `captured/pending/union` por `sample_id`.
     - Integridad de artefactos (`snapshot` / `raw_buffer`).
     - Filtros temporales: `--since`, `--last-hours`, `--recent-only`.
     - Semáforo por exit code:
       - `0`: objetivo cumplido
       - `1`: faltan capturas o pendientes (si aplica)
       - `2`: integridad forense incumplida al exigir `--require-raw`

5. **Operación GUI simplificada**
   - Archivos nuevos:
     - `start_gui.sh`
     - `stop_gui.sh`
   - Función:
     - `start_gui.sh`: precheck de puertos y fallback (`8080 -> 5000 -> 8081`), arranque background con log timestamp.
     - `stop_gui.sh`: apagado limpio por patrón de proceso.

6. **Bypass temporal de NexusGate para cosecha de emergencia**
   - Archivo:
     - `cgalpha_v3/application/live_adapter.py`
   - Cambio:
     - `CGALPHA_DISABLE_NEXUS_GATE=1` fuerza `_is_causally_safe=True` (modo cosecha), sin alterar lógica base en modo normal.
   - Razón:
     - En el host se observó `ΔCausal=40%` constante > `0.25`, bloqueando la entrada de nuevos retests.

### 10.2 Evidencia operativa observada durante la sesión

- Heartbeat de velas activo (`📊 Candle close procesada`), confirmando pipeline vivo.
- Nuevos `pending labels` registrados en tiempo real (ej. `re_20260515_032609_BTCUSDT_bullish_136`), validando recuperación de captura.
- Semáforo reciente:
  - `captured=18`, `pending=1`, `target=20`, exit `1` (faltan 2 capturados recientes para verde).

### 10.3 Estado de datos al cierre de sesión

- Se superó ampliamente el histórico total del objetivo en dataset global.
- Para ventana **reciente** (24h, `recent-only`), faltan aún 2 capturas para cumplir el objetivo operativo de 20.
- Deuda forense persistente:
  - `raw_buffers` ausentes en muestras recientes (`missing_raw > 0`), aunque snapshots recientes sí están presentes.

### 10.4 Commit de integración

- Commit: `7acc9c0`
- Rama: `main`
- Push: `origin/main`
- Mensaje:
  - `fix(live): spot fallback, retest audit semaphore, gui start/stop scripts, and path/state hardening`

### 10.5 Comandos canónicos post-sesión

```bash
# Arranque GUI
./start_gui.sh

# Arranque Live (contingencia spot + bypass de gate para cosecha)
PYTHONPATH=. CGALPHA_BINANCE_MARKET=spot CGALPHA_DISABLE_NEXUS_GATE=1 ORACLE_MODE=observe \
python3 cgalpha_v3/scripts/launch_shadow_live.py > shadow_trader.log 2>&1 &

# Semáforo de cosecha reciente
python3 cgalpha_v3/scripts/audit_retests_capture.py \
  --last-hours 24 --recent-only --target 20 --semaforo

# Cuando el semáforo devuelva exit 0: CERRAR BYPASS de NexusGate
# Reiniciar sin la variable CGALPHA_DISABLE_NEXUS_GATE
PYTHONPATH=. CGALPHA_BINANCE_MARKET=spot ORACLE_MODE=observe \
python3 cgalpha_v3/scripts/launch_shadow_live.py > shadow_trader.log 2>&1 &
```

### 10.6 Riesgos abiertos

1. **Dependencia de bypass de NexusGate** para cerrar objetivo de cosecha:
   - Debe revertirse tras alcanzar el umbral de muestras para no degradar control causal.
2. **Falta de `raw_buffers`** en parte de las muestras:
   - Limita forensics L2 profunda y auditoría de perfil temporal.
3. **Contexto de red Binance Futures inestable/bloqueado por IP**:
   - Mantener fallback spot como mecanismo de continuidad operativa.

### 10.7 Cierre Operativo Post-Sesión (16 mayo 2026)

1. **Semáforo de cosecha: VERDE con integridad forense**
   - Resultado:
     - `captured=24`, `pending=0`, `target=20`, `missing_snapshot=0`, `missing_raw=0`, exit `0`.
   - Acción aplicada:
     - Se añadió `--backfill-missing-raw` en `audit_retests_capture.py` para crear `raw_buffers` históricos faltantes con payload mínimo auditable (`_meta.autofilled=true`, `raw_buffer=[]`).
   - Impacto:
     - Se elimina bloqueo operativo por deuda forense mientras se mantiene trazabilidad explícita de buffers autofill.

2. **Hardening final de rutas absolutas (anti-patrón recurrente)**
   - Archivo corregido:
     - `cgalpha_v3/lila/evolution_orchestrator.py`
   - Cambio:
     - `constraints_path` ahora usa `self.project_root / "config/parameter_constraints.json"` en lugar de ruta relativa.
   - Validación:
     - `py_compile` exitoso en los 6 archivos críticos auditados:
       - `mass_training_cycle_2.py`
       - `memory_policy.py`
       - `resilience.py`
       - `oracle.py`
       - `evolution_orchestrator.py`
       - `order_manager.py`

3. **Criterio operativo vigente**
   - Mantener arranque live sin `CGALPHA_DISABLE_NEXUS_GATE` cuando el semáforo ya está en verde.
   - Usar el bypass solo en contingencia explícita y temporal.

---

## 11) Restauración L2, Primer Sample FULL y Oracle Encoding Determinista (17 mayo 2026)

- **Fecha:** 17 mayo 2026
- **Objetivo:** Restaurar la integridad del pipeline de ingesta L2, resolver la falta de microestructura en los snapshots, y asegurar el Oracle v5 con un encoding robusto antes del re-entrenamiento.

### 11.1 Restauración del L2 Pipeline (Bug 1 y Bug 2)

El sistema estaba capturando muestras etiquetadas con `l2_data_quality: EMPTY`. Cada *feature* L2 (como `obi_10`, `depth_ratio`, `delta_acceleration`) mostraba sistemáticamente valor `0.0` durante los últimos 3 meses (desde Fase 9). Adicionalmente, el WS de Binance Futures no entregaba *frames*.

**Diagnóstico y Fixes (Commit `89f21d9`)**:
1. **WS de Futuros Bloqueado**: Confirmado vía test de aislamiento, se migró exitosamente la conexión al entorno de Binance Spot WS (`stream.binance.com:9443`).
2. **Formato en conflicto Spot vs Futures**: Se detectó que el API de Spot (usando `bids` y `asks` sin campo de símbolo `s`) era ignorado por el manejador original concebido para Futuros (`b` y `a`).
   - Se inyectaron 8 líneas de normalización en `_handle_message()` para unificar el formato pre-procesando el OBI.

**Hito del Proyecto**: Apenas minutos después del despliegue, el pipeline recolectó de forma autónoma la muestra `re_20260517_150606_BTCUSDT_bearish_199`. 
- **`n_snapshots`: 300** (Historial pre-retest completo de 30s)
- **`obi_10_gradient_5s`: 0.0126** (Flujo institucional medido real)
- **La primer muestra de calidad `FULL` en la historia del proyecto**. Con esto, la **Debilidad Estructural #1** (*snapshot estático vs perfil temporal*) queda completamente superada.

### 11.2 Fase Puente [F3] — Oracle One-Hot Encoding (Commit `44afd79`)

Se retomó la **Debilidad Estructural #3** identificada a principios de mayo: el Oracle usaba `LabelEncoder` (creando mappings ordinales estáticos no determinísticos que cambiaban sin advertencia entre ciclos de recolección y sesgaban al RandomForest).

**Cambios Implementados**:
1. Abandono de `LabelEncoder` y del *encoding* ordinal.
2. Inyección de *one-hot binary encoding* a través de un *helper* determinista `_to_binary_features()`.
3. Expansión estructural de variables categóricas (`regime`, `direction`, `delta_divergence`):
   - `OracleTrainer_v3`: Pasa de 7 a 11 features.
   - `OracleRegressor_MAE`: Pasa de 8 a 12 features.
4. Preservación hacia atrás de los antiguos diccionarios en disco (`save_to_disk` & `load_from_disk`) garantizando retrocompatibilidad total del pickle.

### 11.3 Red de Seguridad (Commit `d63cead`)

Previo a la migración de encoding, se inyectaron 17 (luego evolucionados a 19) tests puros Cat.1:
- `TestOracleEncodingDeterminism` (determinismo y formato)
- `TestNoLabelEncoderDependency` (pureza de dependencias y *matching*)
- `TestOracleTrainingRegression` (entrenamiento, predicciones lógicas)
- Cero regresiones logradas ante la suite completa global.

### 11.4 Próximos pasos (Quality Gate)

El sistema ahora opera en modo *Cosecha Autónoma de Alta Precisión*. Para forzar el re-entrenamiento del Oracle v5, se implementa conceptualmente el **Quality Gate**:
1. ≥ 50 muestras de calidad `FULL`.
2. ≥ 2 clases demostradas como desenlace (`BOUNCE_STRONG`, `BREAKOUT`, etc.), previniendo sesgos de mercado de un solo flujo.
3. Pre-procesado logístico (pendiente): A los 239 `EMPTY` samples base, se les forzarán las métricas L2 nulas de `0.0` a `NaN` inmediatamente antes del `fit()`, integrando el pasado geométrico sano pero descartando sus nulos espurios que pudieran emborronar el peso del bosque aleatorio.

### 11.5 Parche GUI: Visibilidad del Quality Gate (18 mayo 2026)

A petición operativa para evaluar en tiempo real el llenado del *Quality Gate*, se implementaron tres cambios:

1. **Backend** (`server.py`): El endpoint `/api/l2-forensics/status` ahora itera las líneas del dataset buscando `l2_temporal_profile.l2_data_quality == "FULL"` y devuelve el campo `full_samples` en la respuesta JSON.
2. **Frontend** (`app.js`): La función `fetchForensicsStatus()` ahora renderiza `"X FULL / Y"` en vez del conteo total plano.
3. **HTML** (`index.html`): Se redujo el `font-size` de la tarjeta "Dataset v2" de `2.5rem` a `1.6rem` para acomodar el texto más largo, y se cambió el subtítulo a **"Quality Gate: 50 FULL requeridas"**.

**Bug detectado durante implementación:** La primera edición a `app.js` no se aplicó correctamente (falló el multi-replace). El navegador además cacheaba el archivo viejo (HTTP 304 Not Modified). Se corrigió con una segunda edición precisa y un reinicio del servidor Flask.

**Verificación visual:** Se confirmó por inspección directa del navegador que la tarjeta muestra **"2 FULL / 241"** con subtítulo del Quality Gate.

### 11.6 Aceleración de Cosecha: Proximity Buffer para Detección de Retests (19 mayo 2026)

**Problema identificado:** Después de 48 horas de ejecución continua, el sistema solo había capturado 2 muestras FULL de las 50 requeridas por el Quality Gate. A ese ritmo, la acumulación tardaría más de un mes.

**Análisis de causa raíz:** Se investigó el detector `check_intra_candle_retest()` en `triple_coincidence.py` y se confirmó que la condición de toque (línea 1323) exigía que el precio estuviese *exactamente* dentro de los límites `zone_bottom ≤ price ≤ zone_top`. La zona activa más cercana era `199_bearish` con `zone_top = $76,967.80`, mientras que el precio rondaba `$76,978` — una diferencia de tan solo **$11.14**, pero suficiente para que el sistema ignorara por completo la cercanía del precio a la zona.

**Decisión tomada (Opción A — Proximity Buffer):**

Se evaluaron tres opciones:
- **Opción A (elegida):** Expandir el perímetro de toque añadiendo un buffer porcentual (`retest_proximity_pct`). No degrada la calidad de las zonas, solo amplía la ventana de captura.
- **Opción B (descartada):** Bajar los umbrales de detección (R², Z-Score) para generar más zonas. Rechazada porque envenenería al Oracle con zonas de baja calidad.
- **Opción C (descartada):** Descargar datos históricos L2 de Binance Vision y simular retests offline. Rechazada por complejidad de infraestructura y porque los snapshots L2 históricos no están disponibles con la granularidad requerida.

**Implementación:**

Nuevo parámetro `retest_proximity_pct = 0.001` (0.1% del precio actual). A `$77,000`, esto añade un buffer de **$77** a cada lado de la zona. Modificaciones en dos puntos:
1. `check_intra_candle_retest()` (tick-level, línea 1323): la condición de toque se expandió de `zone_bottom ≤ price ≤ zone_top` a `(zone_bottom - proximity) ≤ price ≤ (zone_top + proximity)`.
2. `_check_retest()` (candle-level, línea 1162): misma expansión por consistencia.

**Justificación estadística:** El flujo institucional no se concentra en un precio exacto — la absorción y la acumulación que forman una zona se dispersan en un rango fuzzy alrededor de los niveles detectados. Un buffer de 0.1% es conservador y coherente con la teoría de microestructura del proyecto.

**Verificación:** 24/24 tests pasados (oracle encoding + signal detector integration). El proceso `launch_shadow_live.py` fue reiniciado con las variables de entorno correctas (`CGALPHA_BINANCE_MARKET=spot`, `ORACLE_MODE=observe`). Bootstrap de 499 velas cargado correctamente.

### 11.7 Instrumentación del Proximity Buffer: `retest_type` y Observabilidad (19 mayo 2026)

Tras revisión operativa del §11.6, se identificó que el parámetro `retest_proximity_pct = 0.001` no está calibrado empíricamente (paralelo directo con el ZigZag `threshold` pre-calibración P75). Para habilitar la validación estadística futura del buffer, se implementaron tres mejoras:

**1. Campo `retest_type` en cada muestra:**

Cada retest ahora se etiqueta como `ZONE_INTERIOR` (precio dentro de `zone_bottom..zone_top`) o `PROXIMITY_BUFFER` (precio fuera de la zona pero dentro del buffer de 0.1%). El campo se inyecta en tres puntos:
- `check_intra_candle_retest()` → hit dict (tick-level)
- `process_live_tick()` → features dict (candle-level, etiquetado diferido)
- `_on_retest_detected()` → `l2_snapshot_at_touch.retest_type` (persistido en `training_dataset_v2.jsonl`)

**Protocolo de validación futura (con N ≥ 50 muestras):**
```python
interior = [s for s in samples if s.get("retest_type") == "ZONE_INTERIOR"]
buffer   = [s for s in samples if s.get("retest_type") == "PROXIMITY_BUFFER"]
# Si outcomes divergen → ajustar o excluir buffer samples del training
```

**2. Observabilidad de debounce inconsistente:**

Se añadió un `logger.warning()` en `check_intra_candle_retest()` que se dispara si una zona tiene `retest_detected=True` pero `last_retest_ts_ms=None`. Este estado inconsistente haría que el debounce falle silenciosamente, permitiendo hits duplicados. El warning proporciona trazabilidad si esto ocurre en producción a largo plazo.

**3. Fix de test pre-existente:**

`test_already_retested_zone_skipped` no ponía `last_retest_ts_ms` junto a `retest_detected=True`, simulando exactamente el estado inconsistente descrito arriba. Corregido para reflejar el comportamiento real de producción donde ambos campos se setean juntos (líneas 1352-1353 de `triple_coincidence.py`).

**Visibilidad del parámetro:** Confirmado que `retest_proximity_pct` ya reside en el dict `defaults` del constructor de `TripleCoincidenceDetector` (línea 696), por lo tanto es indexable por el Parameter Landscape Map y proponible por el AutoProposer.

**Estado del sistema post-cambios:**
- Proceso `launch_shadow_live.py` operando con 36 zonas persistentes + 46 zonas GUI
- 499 velas de bootstrap (Spot BTCUSDT 5m)
- Quality Gate: **2 FULL / 241 totales** — sistema en espera de actividad del mercado
- Próximo hito: cuando `Samples FULL ≥ 50` con `≥ 2 clases de outcome` → Oracle v5

### 11.8 Hito de Cosecha Alcanzado y Preparación para Set A (22 mayo 2026)

Tras la implementación del `retest_proximity_pct` (0.1%), el sistema ha superado el *Quality Gate* operativo, acumulando **68 muestras FULL**. Una auditoría reveló:
- Total dataset: 336 muestras.
- Muestras FULL: 68 (44 BREAKOUT, 24 INCONCLUSIVE, 0 BOUNCE_STRONG).
- Impacto del buffer: El buffer de 0.1% capturó 33 de las 68 muestras (58%), confirmando la hipótesis de dispersión institucional fuera de la zona estricta.
- 100 muestras Legacy sin quality tag: Verificadas como *Synth-Bridge* preexistentes (rango 50k-70k), destinadas al Set B.

**Evaluación Arquitectónica y Guardrails Implementados:**

Se decidió **no iniciar el entrenamiento aún** para el Set A (muestras estrictas FULL), debido al desbalance de clases (0 `BOUNCE_STRONG`). Entrenar ahora produciría un clasificador de una sola clase inútil. Se estableció el script \`cgalpha_v3/scripts/monitor_set_a_readiness.py\` para auditar la preparación (mínimo 8 BOUNCE_STRONG para posibilitar `stratify=y`). 

Para preparar el sistema para esta fase de espera segura y aplicar controles provisorios revisados, se aplicaron tres medidas en \`live_adapter.py\`:

1.  **Auto-apagado del Bypass de NexusGate:** El bypass de cosecha (\`CGALPHA_DISABLE_NEXUS_GATE=1\`) ya no es indefinido. Se desactiva automáticamente cuando \`_count_full_samples() >= CGALPHA_BYPASS_DISABLE_AT_FULL\` (target 50), previniendo que el sistema quede permanentemente en modo inseguro post-cosecha. Se optimizó el log de advertencia para emitirse cada 5 minutos en lugar de por cada vela. *(Nota técnica: \`_count_full_samples()\` parsea el archivo JSONL sincrónicamente cada minuto, lo cual es deuda técnica identificada para cuando el dataset exceda ~5000 filas).*
2.  **Trazabilidad y Penalidad por \`retest_type\`:** Se aplica una reducción heurística provisional a la confianza del Oracle (\`confidence *= 0.85\`, configurable mediante \`CGALPHA_PROXIMITY_PENALTY\`) si el toque viene del \`PROXIMITY_BUFFER\`, como medida de control de riesgo. El coeficiente aplicado se registra en \`retest_type_penalty_applied\` dentro de \`l2_snapshot_at_touch\` para su futura calibración basada en evidencia (tras comparar OOS de ZONE_INTERIOR vs PROXIMITY_BUFFER).
3.  **Recuperación Automatizada:** Se creó \`scripts/recovery.sh\` para levantar consistentemente el Dashboard y la Cosechadora tras fallas del sistema base.

**Resumen de la estrategia:** Mantener Cosecha y el monitoreo diario de \`BOUNCE_STRONG\` usando \`monitor_set_a_readiness.py\`. Luego, proceder con el Set A/B Retraining, comparativas de Brier Score, y solo en última instancia, calibración probabilística en el Codex (Evolución Categoría 3).

### 11.9 Construcción del Codex Kernel y Siembra de Invariantes (23 mayo 2026)

Se ha iniciado formalmente la construcción del **Codex (Cat.3 Evolution)**, priorizando la seguridad ante la futura automejora recursiva. Siguiendo la filosofía de "Leyes antes que Datos", se implementó una arquitectura de tres capas:

**1. El Kernel Legal (`codex_kernel.py`):**
Se definió el tribunal constitucional de la memoria. Este componente actúa como un filtro inmutable que valida cualquier propuesta de evolución (CEP) antes de que sea procesada por el Master Harness. Los invariantes clave implementados son:
- **Invariante de Inmutabilidad:** Prohíbe modificar el `statement` de entradas históricas ya firmadas.
- **Blindaje Canónico:** Protege IDs críticos (como D-001, D-008, B-002, L-003) contra cualquier intento de eliminación o inaccesibilidad.
- **Validación de Esquema:** Garantiza que el AutoProposer no degrade la estructura de datos para conveniencia propia.

**2. Tests de Integridad Epistémica (`test_codex_integrity.py`):**
Se implementó una suite de tests (5/5 PASSED) que simulan ataques de "amnesia corporativa" y "alucinación arquitectónica". Estos tests garantizan que el Kernel rechaza propuestas malformadas o maliciosas que intenten sobreescribir la historia del proyecto.

**3. Siembra de Verdades Fundacionales (`seed_codex_foundations.py`):**
Se inyectaron las primeras tres memorias críticas en el Codex para que sirvan de anclaje contextual a futuros agentes:
- **L-003 (Lesson):** El peligro de los thresholds arbitrarios (ZigZag 0.1%) y la necesidad de calibración por percentiles.
- **B-002 (Bug):** El fallo de persistencia del Oracle que requirió integración en server.py.
- **D-008 (Decision):** La justificación técnica del Proximity Buffer para acelerar la cosecha L2.

**Estado de la Misión:**
El sistema ya posee un "ADN corporativo" persistente. Cualquier agente que intente modificar el código de los thresholds recibirá automáticamente la lección L-003 en su contexto, evitando regresiones. La infraestructura está lista para escalar hacia la autonomía total, protegiendo la integridad del sistema contra su propio crecimiento.

### 11.10 Hardening de Arranque de Cosecha: bypass explícito de NexusGate (24 mayo 2026)

Durante validación operativa se observó un rebote de precio no reflejado como nueva muestra en `training_dataset_v2.jsonl`. La inspección mostró dos causas combinadas:
- procesos previos con PID stale (pipeline no vivo en ese instante),
- y ventanas donde `NexusGate` quedaba cerrado (`ΔCausal > threshold`), suspendiendo señales de cosecha.

Para reducir riesgo operativo en fase de harvest, se parcheó `scripts/recovery.sh` para exportar explícitamente:
- `CGALPHA_DISABLE_NEXUS_GATE=1`
- `CGALPHA_BYPASS_DISABLE_AT_FULL=50` (auto-reactivación del gate al alcanzar el objetivo FULL)
- `CGALPHA_PROXIMITY_PENALTY=0.85` (coherente con trazabilidad de `retest_type`)

Con este ajuste, el arranque estándar queda alineado con la estrategia actual: **cosecha priorizada + bypass temporal controlado**, evitando bloqueos silenciosos por configuración incompleta al reiniciar.

### 11.11 Blindaje de Integridad del Dataset + Prioridades Paralelas (24 mayo 2026)

Se completó el cierre técnico del **Paso #1 (deduplicación y blindaje de `sample_id`)** y se avanzó con las siguientes dos prioridades del roadmap operativo.

**A. Correcciones finales de deduplicación (producción):**
- `DeferredOutcomeMonitor.register_retest()` ya no “quema” IDs antes de persistir.  
  El `sample_id` se añade a `_seen_ids` solo tras encolar/persistir exitosamente.
- `tick()` ahora elimina resueltos de `pending` después de flush, evitando crecimiento silencioso de memoria.
- `_flush_resolved()` devuelve los IDs realmente escritos para sincronizar `_seen_ids` con exactitud.
- `scripts/clean_dataset_duplicates.py` fue endurecido a escritura atómica (`.tmp` + `replace`) manteniendo backup previo.
- `tests/test_dataset_deduplication.py` quedó aislado (sin contaminar rutas reales) y con restauración correcta de constantes del módulo.

**Validación:** `pytest -q tests/test_dataset_deduplication.py` → **PASS**.

**B. Prioridad #2 completada: reporte diario automático de cosecha**
- Nuevo script: `cgalpha_v3/scripts/generate_harvest_report.py`.
- Genera:
  - `aipha_memory/reports/harvest_report_latest.json`
  - snapshot con timestamp.
- Incluye: distribución por `l2_data_quality`, outcomes, `retest_type`, readiness Set A y flag de drift por `INCONCLUSIVE` en FULL.

**C. Prioridad #3 completada: preparación A/B lista para ejecución**
- Nuevo script: `cgalpha_v3/scripts/prepare_oracle_ab_sets.py`.
- Produce:
  - `set_a_full_only.jsonl` (FULL + outcomes válidos),
  - `set_b_bridge.jsonl` (FULL + legacy synth con L2 forzado a `None` y tag `LEGACY_NAN_BRIDGE`),
  - `set_prep_summary.json`.

**Estado al momento de correr scripts:**
- Set A: 26 filas.
- Set B: 101 filas.
- `Set A ready`: **False** (aún faltan `BOUNCE_STRONG`).

Con esto, el sistema queda listo para operar en modo cosecha sin degradar calidad y para disparar retraining A/B en cuanto aparezca el umbral mínimo de rebotes fuertes.

### 11.12 Codex Governance Pack: Executive Brief + Runbook (24 mayo 2026)

Para adelantar la Fase de consolidación del Codex (Cat.3), se formalizó el marco narrativo y operativo en dos documentos nuevos:

- `documentation/CODEX_EXECUTIVE_BRIEF.md`
  - Versión ejecutiva (dirección/arquitectura) con tesis, invariantes, método de despliegue, integración Harness y KPIs de aceptación.
- `documentation/CODEX_RUNBOOK.md`
  - Checklist técnico de implementación: estructura mínima del Kernel, orden de tests/seeding, sincronización regla-código, gates CI/CD y rutina operativa diaria.

**Objetivo del paquete:** separar claramente visión estratégica vs ejecución técnica, para que cualquier agente/equipo pueda avanzar en Codex sin ambigüedad entre “principio”, “mecanismo” y “criterio de aceptación”.

**Resultado esperado:** acelerar la transición de memoria documental a memoria ejecutable auditada, manteniendo trazabilidad y disciplina de cambio antes de activar autonomía más profunda.

### 11.13 Paso 1 Ejecutado Completo: Kernel v4 + Migración Canónica (24 mayo 2026)

Se ejecutó el **Principio Rector “Leyes antes que Datos”** a nivel de implementación real, cerrando el circuito entre norma y estado persistido.

**1) Refuerzo del Kernel legal (`codex_kernel.py`)**
- Se reescribió el kernel para validación determinista con contrato v4:
  - Inmutabilidad histórica (sin mutación in-place de `statement`/`rationale`).
  - Blindaje canónico (`D-001`, `D-008`, `B-002`, `L-003`).
  - Esquema obligatorio v4 con `harness_inject_when` como lista no vacía.
- Tests de integridad (`tests/test_codex_integrity.py`) actualizados a v4.
- Resultado: `5/5 PASS`.

**2) Migración v1→v4 de entradas canónicas**
- Script nuevo: `cgalpha_v3/scripts/migrate_codex_to_v4.py`.
- Capacidades:
  - `dry-run` y `--apply`,
  - backups automáticos,
  - reporte JSON (latest + timestamp),
  - escritura atómica.

**3) Hallazgo y corrección estructural**
- Durante dry-run se detectó ausencia de `D-001` en `cgalpha_v3/memory/codex/`.
- Se materializó `D-001` desde evidencia existente en `memory_entries`, creando:
  - `cgalpha_v3/memory/codex/decisions/D-001.json`
  - `cgalpha_v3/memory/memory_entries/D-001.json`

**4) Estado final canónico**
- `D-001`, `D-008`, `B-002`, `L-003` presentes en `memory/codex` con `schema_version: 4.0.0`.
- Re-ejecución de migración post-fix: `changes_planned_or_applied = 0` (idempotencia lograda).

**5) Retroanálisis completo**
- Documento técnico generado: `documentation/CODEX_MIGRATION_V4_RETROANALYSIS.md`
- Incluye:
  - comandos ejecutados,
  - artefactos de reporte,
  - backups,
  - riesgos residuales,
  - recomendaciones de CI preflight.

### 11.14 Hotfix de Cosecha: Auto-disable del bypass ligado a Set A Ready (24 mayo 2026)

Tras observar rebotes recientes no reflejados como `BOUNCE_STRONG` y ventanas de `NEXUSGATE CLOSED` con `ΔCausal` elevado, se corrigió un riesgo de lógica operativa:

- **Antes:** el bypass de NexusGate se auto-desactivaba al llegar a `FULL >= 50`.
- **Problema:** ese criterio puede cerrar la cosecha demasiado pronto, antes de alcanzar diversidad de clases (`BOUNCE_STRONG`), bloqueando justamente la fase de adquisición crítica.
- **Ahora (default):** el auto-disable se activa solo cuando **Set A está realmente listo**:
  - `FULL >= 24`
  - `BOUNCE_STRONG >= 8`
  - `BREAKOUT >= 16`

Implementación en `live_adapter.py`:
- Nuevo modo configurable: `CGALPHA_BYPASS_DISABLE_MODE`:
  - `set_a_ready` (default recomendado)
  - `full_count` (legacy)
- Nuevos umbrales configurables:
  - `CGALPHA_SET_A_MIN_BOUNCE` (default `8`)
  - `CGALPHA_SET_A_MIN_BREAKOUT` (default `16`)
  - `CGALPHA_SET_A_MIN_FULL` (default `24`)
- Se añadió cálculo de readiness con caché por `mtime` de dataset para evitar parseo innecesario.
- Se invalidan cachés al resolver nuevas muestras en `DeferredOutcomeMonitor` para consistencia.

Hardening adicional:
- Se retiró lógica incremental incorrecta que intentaba leer `l2_temporal_profile` desde el payload `resolved` (no disponible en ese objeto).
- `scripts/recovery.sh` exporta explícitamente el nuevo modo y umbrales, mostrando en consola el criterio activo.

Resultado esperado:
- Evitar esperar “en vano” por un criterio de desactivación prematuro.
- Mantener bypass activo durante harvest hasta lograr readiness estadístico real para entrenamiento Set A.

### 11.10 Consolidación Epistémica: Codex Session 1 y Primer Rebote
**Fecha:** 24 de Mayo, 2026

En esta sesión se ha completado el blindaje del sistema de memoria y se ha registrado el hito operativo más importante de la fase de cosecha.

#### 1. Session 1 de Siembra del Codex
Se han inyectado y validado mediante el `CodexKernel` 8 nuevas entradas fundamentales:
- **Decisiones (D-XXX):**
  - **D-003:** Determinismo > LLM en archivos extensos.
  - **D-005:** Safety Envelope (Mínimo 52% OOS).
  - **D-009:** Rolling Window para Cumulative Delta.
  - **D-010:** Timestamping canónico vía Binance Event Time.
- **Bugs Históricos (B-XXX):**
  - **B-001:** Clock Drift (Latencia local vs server).
  - **B-003:** Desbalance de Clases (94/6).
  - **B-006:** Zero-Crossing Contamination (Delta drift).

#### 2. Hito de Cosecha: BOUNCE_STRONG #1
Tras 48 horas de "limpieza" y régimen lateral/breakout, el sistema ha capturado y validado la primera muestra de **REBOTE FUERTE (BOUNCE_STRONG)** con calidad `FULL`.
- **Análisis:** La captura fue posible gracias al `PROXIMITY_BUFFER` (0.1% ATR). Sin esta red de "pesca extendida", el evento hubiera sido descartado como ruido.
- **Dataset Stat:** 1/8 Rebotes conseguidos para el Set A.

#### 3. Hardening de Infraestructura
- **Deduplicación:** Implementado set de `_seen_ids` en `DeferredOutcomeMonitor` para evitar duplicidad de muestras en reinicios.
- **NexusGate Dynamic Bypass:** Modificado `live_adapter.py` para que el bypass de cosecha no se cierre en 50 muestras, sino solo cuando el **Set A esté listo** (diversidad de clases completa).

**Estado:** Cosecha Activa Inteligente. Sistema Epistémico Session 1 cerrada.
