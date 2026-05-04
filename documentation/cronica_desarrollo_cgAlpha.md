# Crónica de Desarrollo — cgAlpha / Aipha
### Versión 3.2 — Actualizada 3 mayo 2026

> Documento vivo para reconstruir el pasado, comprender el estado actual y orientar decisiones futuras.
> Esta versión incorpora la **Evaluación Estructural del Oracle** (3 mayo 2026),
> que identificó 5 debilidades en la resolución de features y el etiquetado,
> insertó una Fase Puente en la hoja de ruta, y revisó las Fases 10-14
> para coordinar la superación sistemática de cada ineficiencia.

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

## 4) Estado actual (3 mayo 2026)

| Componente | Estado | Evidencia |
|-----------|--------|-----------|
| Canal de evolución | ✅ Operativo | 4 islas conectadas, Island Bridge |
| Oracle OOS | ✅ 0.68 honesto | 30 días BTCUSDT, 121 samples reales |
| ZigZag threshold | ✅ Calibrado | 0.18% — P75 de rango real de vela |
| Safety Envelope | ✅ 28 parámetros | Gatekeeper activo |
| Cooldown §4.3 | ✅ Implementado | `_count_recent_modifications()` |
| Sage v4 AST | ✅ Operativo | 9/9 tests pasando |
| Clearance instrumentation | ✅ **OPERATIVO** | 26 samples capturados en vivo (6h monitoring) |
| OBI / CumDelta reales | ✅ **CONECTADO** | WS @depth20@100ms activo, ingesta L2 validada |
| 60 días históricos | ✅ **COMPLETADO** | 261 samples limpios, CV OOS 0.688 |
| Filtro rebotes prematuros | ⏳ Pendiente evidencia | Divergencia P25 < 0.2 ATR (insuficiente aún) |
| Buffer temporal L2 | 🔴 **NO EXISTE** | Oracle solo ve snapshot estático — Debilidad #1 |
| Etiquetado terciario | 🔴 **NO EXISTE** | Fallback `return 'BOUNCE'` L965 contamina labels — Debilidad #2 |
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

---

## 6) Próximos pasos — Hoja de ruta priorizada

### COMPLETADOS (Fase 8 y 9)

**[A] Cosecha de evidencia:** Instrumentación ciega `max_clearance_atr` inyectada y auditada en Live.
**[B] Ampliar a 60 días históricos:** Ejecutado. Generó 261 muestras con el threshold real (0.18%).
**[C] Análisis de percentiles:** Ejecutado empíricamente. Las diferencias de clearance entre P25(BOUNCE) y P25(BREAKOUT) fueron de apenas ~0.15 ATR. **Conclusión científica: el clearance puro de escape carece de poder predictivo suficiente.**
**[D] Conexión de OBI y CumDelta (Cat.2):** Efectuado. Transición al stream `@depth20@100ms`, destruyendo la ceguera al flujo L2.

### DESCARTADOS (Basado en Evidencia)

**[E] Filtro de rebotes prematuros en `_check_retest` (Cat.2):** **RECHAZADO**. La matemática del Paso C dictaminó que un filtro espacial duro destruiría la robustez, filtrando retests legítimos de alta liquidez.

### INMEDIATO — Esta semana (En progreso)

**Cosecha Viva L2:** Dejar el ShadowTrader capturar retests con el stream `@depth20` recién instrumentado (>24h). El objetivo es acumular mínimo 50+ samples limpios con `obi_10` y `cumulative_delta` reales.

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
- Prerrequisito: ≥50 samples con `obi_10 ≠ 0` en `training_dataset.json`.
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

---

## 9) Principio rector del proyecto

El proyecto pasó de "cuatro componentes capaces operando como islas con métricas
artificialmente perfectas" a "canal de evolución gobernado con ingesta L2 en tiempo real,
baseline OOS honesto de 0.68, y hoja de ruta calibrada hasta la independencia progresiva."

**La independencia del sistema se gana por evidencia, no por voluntad.
Las métricas honestas valen más que las brillantes.
Y los filtros solo se añaden después de medir, nunca antes.**
