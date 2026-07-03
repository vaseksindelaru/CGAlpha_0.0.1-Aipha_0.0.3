# AUDITORÍA: Plan de Reconstrucción GUI Training Review
# cgAlpha_0.0.1-Aipha_0.0.3 — Auditoría basada en código real

---

## 1. VERIFICACIÓN CONTRA CÓDIGO REAL

### 1.1 Estado actual de la GUI (verificado en código)

**Sección `#training` en index.html (línea ~1600 del archivo de 2830 líneas):**

| Elemento | ID real | Estado |
|----------|---------|--------|
| Tab de navegación | `<button onclick="showSection('training')">` | ✅ Existe |
| Título sección | `<h2>🕯️ Training Review [LEGACY - FASE 0]</h2>` | ⚠️ Marcado como LEGACY |
| Panel de resumen | `<div class="grid-4">` (4 paneles) | ✅ Existe |
| Gráfico velas | `<div id="training-candlestick-chart" style="height:520px">` | ✅ Existe (SVG) |
| Navegación zona | `<div id="zone-nav-bar">` con ←, →, "Mostrar todas", "Contexto ±20" | ✅ Existe |
| Tabla retests | `<table id="training-retest-table">` con `#training-retest-tbody` | ✅ Existe (9 columnas) |
| Labels granulares | ❌ **NO EXISTE** — la tabla tiene approve/reject pero NO hay Validar/Descartar-ruido/Edge-case |
| OBI/CumDelta | ✅ Datos en tabla (`rt.obi_10_at_retest`, `rt.cumulative_delta_at_retest`) pero NO se visualizan en el chart |
| Active learning | ❌ **NO EXISTE** — sin campo oracle_confidence ni oracle_predicted_outcome |
| Ghost candles | ✅ Funcionalidad "Contexto ±20" implementada en `trainingViewMode = "context"` |
| Atajos teclado | ❌ **NO EXISTE** |
| Contador progreso | ❌ **NO EXISTE** |
| Undo Ctrl+Z | ❌ **NO EXISTE** |

**Funciones JavaScript (app.js, 3892 líneas):**

| Función | Línea | Estado |
|---------|-------|--------|
| `fetchTrainingReviewData()` | 3390 | ✅ Existe — llama a `apiFetch("/api/training/review-data")` |
| `renderTrainingChart()` | 3591 | ✅ Existe — dibuja SVG con velas, zonas, retests, key candles |
| `renderTrainingRetestTable()` | ~3540 | ✅ Existe — genera tabla HTML con 9 columnas |
| `navigateZone(direction)` | 3433 | ✅ Existe — 1 definición, cicla zones_summary |
| `focusTrainingZone(zoneId, retestIndex)` | 3482 | ✅ Existe — 1 definición (el bug de duplicación está RESUELTO) |
| `updateZoneNavLabel()` | 3493 | ✅ Existe — actualiza `#zone-nav-label` |
| `setTrainingFilter(filter)` | ~3460 | ✅ Existe — filtra BOUNCE/BREAKOUT |
| `setTrainingRegime(regime)` | ~3470 | ✅ Existe — filtra LATERAL/TREND |
| `getFilteredRetests()` | ~3520 | ✅ Existe |
| `approveRetest(id, row)` | ❌ **NO EXISTE** — la función propuesta NO está implementada |
| `rejectRetest(id, row)` | ❌ **NO EXISTE** — la función propuesta NO está implementada |
| `trainingSelectedZone` | 3385 | ✅ Variable global existe |
| `trainingViewMode` | 3387 | ✅ Variable global existe (`"all"`, `"zone"`, `"context"`) |

**Endpoints server.py (verificados en código real):**

| Endpoint | Método | Estado |
|----------|--------|--------|
| `/api/training/review-data` | GET | ✅ Funciona — carga OHLCV + retests + training samples |
| `/api/training/retest/<retest_id>/approve` | POST | ⚠️ Funciona pero es STUB — escribe en `retest_curation.jsonl`, NO actualiza el dataset |
| `/api/training/retest/<retest_id>/reject` | POST | ⚠️ Funciona pero es STUB — escribe en `retest_curation.jsonl`, NO actualiza el dataset |

**Schema de datos (verificado en archivos reales):**

`retests_dataset.json` (7 samples):
```jsonc
{
  "zone_id": "318_bearish",
  "retest_index": 318,
  "retest_price": 53740.63,
  "retest_timestamp": 1705208400000,
  "vwap_at_retest": 60634.81,
  "obi_10_at_retest": 0.0071,
  "cumulative_delta_at_retest": -272.56,
  "delta_divergence": "BEARISH_EXHAUSTION",
  "atr_14": 862.44,
  "regime": "LATERAL",
  "outcome": "BOUNCE"
  // ← BUG: falta el campo direction en todos los samples
}
```

**CONFIRMADO:** `direction` está ausente en TODOS los 7 samples. En `app.js`, `(rt.direction || "").toLowerCase()` cae al default no-bullish, por lo que la tabla y el chart pintan flecha bajista `▼` aunque el dato no exista.

### 1.2 Verificación de afirmaciones del plan vs código real

**Layout side-by-side (chart 65%/tabla 35%):**
- ❌ **NO IMPLEMENTADO** — El layout actual es vertical: chart arriba (height: 520px fijo), tabla debajo. No hay CSS Grid de 2 columnas.
- Veredicto: **Requiere implementación de CSS Grid**

**Glassmorphism oscuro:**
- ❌ **NO IMPLEMENTADO** — No hay `backdrop-filter: blur` ni fondos RGBA con blur en el CSS actual.
- Veredicto: **Requiere implementación de CSS**

**Sync chart-tabla (click en fila resalta chart, navegación de flechas hace scroll):**
- ⚠️ **Parcialmente implementado** — `focusTrainingZone()` existe y recibe `(zoneId, retestIndex)`. Se llama desde `onclick` en cada fila de la tabla (app.js ~3576). Sin embargo, el resaltado en el chart se hace vía `trainingSelectedZone` que se usa en `renderTrainingChart()`, pero NO hay highlight visual en la fila de la tabla ni scrollSync en ambas direcciones.
- Veredicto: **Requiere completar la sincronización bidireccional**

**Labels granulares (Validar/Descartar-ruido/Edge-case):**
- ❌ **NO EXISTE** — No hay campos de status en `retests_dataset.json` ni en el HTML ni en los endpoints.
- Veredicto: **Requiere nuevo campo en schema JSON + nuevo endpoint o extensión del approve**

**Visualización OBI/CumDelta:**
- ✅ **Datos disponibles** en `rt.obi_10_at_retest` y `rt.cumulative_delta_at_retest` (tabla). NO se muestran en el chart SVG.
- Veredicto: **Viable sin cambios de backend** (añadir mini-panel o SVG overlay)

**Active learning (Oracle prediction vs realidad):**
- ❌ **NO EXISTE** — `training_dataset.json` tiene campo `outcome` (BOUNCE/BREAKOUT) pero NO tiene `oracle_confidence` ni `oracle_predicted_outcome`.
- Veredicto: **Requiere nuevo campo en training_dataset.json**

**Ghost candles multi-temporal:**
- ✅ **Implementado** — Funcionalidad "Contexto ±20" existe (`trainingViewMode = "context"`, `trainingContextPadding = 20`). Dibuja `displayOhlcv = ohlcv.slice(startIdx, endIdx+1)`.
- Veredicto: **Ya implementado** (pero es 5m fijo, no multi-temporal)

**Auto-avance:**
- ❌ **NO EXISTE** — No hay lógica de auto-avance en el código.
- Veredicto: **Requiere implementación completa**

**UI Optimista:**
- ❌ **NO EXISTE** — `approve_retest()` y `reject_retest()` son stubs que escriben a `retest_curation.jsonl` pero no actualizan el dataset ni devuelven estado.
- Veredicto: **Requiere refactor completo de endpoints**

**Undo (Ctrl+Z):**
- ❌ **NO EXISTE** — No hay historial de decisiones ni mecanismo de undo.
- Veredicto: **Requiere implementación nueva**

### 1.3 Bugs documentados — Estado actual

| Bug | Estado | Evidencia |
|-----|--------|-----------|
| `rt.direction` indefinido | ❌ **SIGUE PRESENTE** | 7/7 samples no tienen campo `direction` en `retests_dataset.json`. La tabla y el chart caen al default bajista `▼`. |
| `focusTrainingZone()` duplicada | ✅ **RESUELTO** | Solo 1 definición encontrada (línea 3482). El bug ya fue corregido en una sesión anterior. |
| Endpoints approve/reject son stubs | ❌ **SIGUE PRESENTE** | Escriben a `retest_curation.jsonl` pero NO actualizan dataset ni pipeline. Solo loguean evento. |

### 1.4 Estado de las 5 sugerencias estratégicas del usuario

| Sugerencia | Estado en código | Necesita backend |
|------------|-----------------|-----------------|
| Layout side-by-side 65/35 | ❌ Vertical actual | CSS solo (Grid) |
| Labels granulares (Validar/Descartar/Edge) | ❌ No existe | Sí: campo nuevo en schema + endpoint |
| Active learning (Oracle pred vs real) | ❌ Sin campos oracle | Sí: nuevos campos en training_dataset.json |
| Ghost candles multi-temporal | ✅ Funcional (5m fijo ±20) | No (pero necesita datos de 4H) |
| OBI en chart | ❌ Solo en tabla | No (datos existen, solo dibujar en SVG) |

---

## 2. LISTA DE REQUISITOS CORREGIDA (P0/P1/P2)

### P0 — Bloqueante para v1 (debe existir antes de que el operador use la GUI)

| Req | Cambio vs plan original | Justificación |
|-----|------------------------|---------------|
| **FIX: `rt.direction` indefinido** | **AÑADIDO** (no estaba en el plan original) | 100% de samples no tienen `direction`. Sin esto, la flecha de dirección en tabla y chart está rota porque cae al default bajista. Debe fijarse en el backend del endpoint o en un fix de datos. |
| **FIX: Endpoints approve/reject con persistencia real** | **AÑADIDO** (no estaba en el plan original) | Escriben a un archivo de curation separado pero no devuelven el status al frontend ni actualizan el dataset. Sin esto, la UI optimista es inútil — no hay forma de saber si un retest fue aprobado. |
| **Layout CSS Grid 65/35** | **YA ESTABA en el plan original** | Chart a la izquierda (SVG con 520px fijo → cambiar a `flex:1` o `min-width:65%`), tabla a la derecha con scroll independiente (`overflow-y:auto`, `max-height:calc(100vh - Xpx)`). CSS puro, sin backend. |
| **Sync chart ↔ tabla (bidireccional)** | **PARCIALMENTE implementado** | `focusTrainingZone()` ya existe y cambia `trainingSelectedZone` + llama a `renderTrainingChart()`. Faltan: (a) resaltar fila seleccionada en tabla (`classList.add('row-selected')`) + scrollIntoView, (b) click en chart navegar en tabla. JS puro. |

### P1 — Siguiente iteración (mejora UX significativa)

| Req | Cambio vs plan original | Justificación |
|-----|------------------------|---------------|
| **Botones approve/reject con UI optimista** | **YA ESTABA en el plan original** | `approveRetest()` y `rejectRetest()` requieren POST a endpoints existentes. Los endpoints actuales son stubs (fix P0). La UI optimista es JS puro (pintar fila verde/roja antes de respuesta del servidor). |
| **Labels granulares (Validar/Descartar/Edge)** | **YA ESTABA en el plan original** | Requiere: (a) nuevo campo `label_status` en `retests_dataset.json` con valores `validated|discarded_noise|edge_case`, (b) nuevo endpoint PATCH `PUT /api/training/retest/<id>/label` o extensión del approve, (c) exportador de dataset "estricto" (solo validated). |
| **Atajos de teclado (A/R/←/→)** | **AÑADIDO** (recomendación del usuario) | `document.addEventListener('keydown')` — A=approve, R=reject, ←/→=navigateZone. No requiere backend. |
| **OBI/CumDelta como mini-panel lateral** | **YA ESTABA** (bajar prioridad del plan original) | Los datos existen (`obi_10_at_retest`, `cumulative_delta_at_retest`). Dibujar mini-panel SVG fijo junto al chart, NO sobre el candlestick. |

### P2 — Nice-to-have (segunda iteración)

| Req | Cambio vs plan original | Justificación |
|-----|------------------------|---------------|
| **Contador de progreso de sesión** | **AÑADIDO** (recomendación del usuario) | `47/261 revisados, 12 min, ritmo 4/min`. Solo JS con contadores locales. Sin backend. |
| **Undo Ctrl+Z** | **AÑADIDO** (recomendación del usuario) | Mantener stack de últimas 10 decisiones. Al Ctrl+Z, revertir última decisión del stack. UI optimista revertida + POST de undo al backend. |
| **Active learning (Oracle pred vs realidad)** | **YA ESTABA en el plan original** | Requiere nuevos campos `oracle_confidence` (0-1) y `oracle_predicted_outcome` ("BOUNCE"/"BREAKOUT") en `training_dataset.json`. Cálculo de discrepancia necesita backend o precomputación. |
| **Ghost candles multi-temporal** | **YA ESTABA** (bajar prioridad) | Ya implementado en modo 5m. Multi-temporal (4H, 1H) requiere datos adicionales que probablemente no están cacheados. Postergar. |
| **Glassmorphism** | **YA ESTABA en el plan original** | `backdrop-filter: blur`, `rgba` oscuro. Estético, no funcional. P2. |

---

## 3. AUDITORÍA DE LOS 4 PROMPTS

### Prompt A (DeepSeek V4 Flash — Auditoría de viabilidad)

**Problemas detectados:**
1. ❌ **No menciona que la sección está marcada `[LEGACY - FASE 0]`** — Esto es importante: el plan trata de reconstruir una sección que el equipo ya marcó como legacy. El auditor debería advertir sobre esto.
2. ❌ **No pregunta sobre el estado real de los datos** — El prompt asume que hay datos de retests para auditar, pero el endpoint actual carga datos sintéticos de `phase0_results/` (7 samples), no datos live. El auditor debería evaluar si estos datos son suficientes.
3. ⚠️ **No verifica si los layouts existentes son compatibles** — El plan propone "cambiar de vertical a side-by-side", pero no menciona que el CSS actual usa `style="height:520px"` fijo, no CSS Grid. Esto afecta la estimación de esfuerzo.
4. ✅ **Bueno:** Pide identificar riesgos de UX (auto-avance, UI optimista). Esto es relevante.
5. ❌ **No incluye el contexto de los bugs existentes** — El prompt no menciona `rt.direction` indefinido ni endpoints stub, que son prerequisitos antes de cualquier nueva funcionalidad.

**Prompt A corregido:**
> [Agrega al final del Prompt A:]
> "Adicionalmente, antes de evaluar viabilidad, verifica los siguientes factores contextuales que ya conoces del código:
> 1. La sección Training Review está marcada como `[LEGACY - FASE 0]` — esto indica que el equipo planea reemplazarla eventualmente. Evalúa si el esfuerzo vale la pena.
> 2. El dataset actual de retests tiene solo 7 samples sintéticos (phase0_results/retests_dataset.json). Evalúa si la UI debe ser diseñada para escala (1000+ samples) o para dataset pequeño actual.
> 3. Hay 3 bugs documentados que deben resolverse antes de añadir features: (a) `rt.direction` indefinido en todos los samples, (b) endpoints approve/reject son stubs sin persistencia real, (c) focusTrainingZone duplicada (RESUELTO). Incluye estos fixes como prerequisitos en la evaluación."

### Prompt B (Qwen3.6 Coder — Generación de código)

**Problemas detectados:**
1. ✅ **Nombres de funciones correctos** — `renderTrainingChart()`, `renderTrainingRetestTable()`, `navigateZone()`, `focusTrainingZone()` están todos en el código real.
2. ✅ **IDs de elementos DOM correctos** — `training-candlestick-chart`, `training-retest-tbody` existen en el HTML real.
3. ✅ **Rutas de API correctas** — `/api/training/retest/{id}/approve` y `/api/training/retest/{id}/reject` existen en server.py.
4. ❌ **No menciona que el CSS actual tiene `height: 520px` fijo** — El prompt pide CSS Grid con altura viewport-based, pero el código actual usa `style="height: 520px"`. El prompt debe especificar que se debe reemplazar este style inline por CSS variables o clases.
5. ❌ **No incluye el contexto de las variables de estado globales** — El prompt no menciona que existen `trainingSelectedZone`, `trainingCurrentFilter`, `trainingCurrentRegime`, `trainingViewMode`, `trainingContextPadding` como variables globales. Si Qwen sobrescribe estas funciones, debe mantener las variables globales existentes.
6. ❌ **No menciona el endpoint `/api/training/review-data`** — `fetchTrainingReviewData()` lo llama, pero el prompt B no incluye este contexto. Si Qwen necesita extender los datos de retests, debe saber la ruta.
7. ❌ **No menciona que la tabla tiene 9 columnas fijas** — El prompt asume que Qwen reescribe la tabla, pero no especifica las columnas existentes: `#`, `Zone`, `Price`, `Regime`, `Δ Divergence`, `VWAP`, `OBI`, `Outcome`, `Dir`. Qwen debe saber qué columnas mantener y cuáles son los IDs de los `<th>`/`<td>`.

**Prompt B corregido:**
> [Agrega al final del Prompt B:]
> "Contexto adicional crítico del código existente:
> 1. Variables globales que DEBES MANTENER existentes (no las redefinas): `trainingData`, `trainingCurrentFilter`, `trainingCurrentRegime`, `trainingSelectedZone` (null o zone_id string), `trainingViewMode` (valores: 'all', 'zone', 'context'), `trainingContextPadding` (número de velas para modo context, default 20).
> 2. El CSS inline `style="height:520px"` en `#training-candlestick-chart` debe ser reemplazado por CSS con flexbox o grid (no dejar estilos inline).
> 3. La tabla tiene 9 columnas con IDs de `<th>`: `#`, `Zone`, `Price`, `Regime`, `Δ Divergence`, `VWAP`, `OBI`, `Outcome`, `Dir`. Los `<td>` usan índices 0-8.
> 4. `focusTrainingZone(zoneId, retestIndex)` actualiza `trainingSelectedZone` y llama `renderTrainingChart()`. Tu código NO debe romper esta función existente.
> 5. `renderTrainingRetestTable()` genera `<tr>` con `onclick="focusTrainingZone('${rt.zone_id}', ${rt.retest_index})"` en cada fila. Mantén este onclick."

### Prompt C (DeepSeek V4 Pro — Decisiones UX y features analíticas)

**Problemas detectados:**
1. ❌ **No referencia el schema REAL de retests_dataset.json** — El prompt pide definir un schema para labels granulares, pero no menciona que el schema actual tiene campos específicos: `zone_id`, `retest_index`, `retest_price`, `retest_timestamp`, `vwap_at_retest`, `obi_10_at_retest`, `cumulative_delta_at_retest`, `delta_divergence`, `atr_14`, `regime`, `outcome`. El nuevo campo `label_status` debe integrarse sin romper la estructura existente, y `direction` debe derivarse o añadirse explícitamente.
2. ⚠️ **No menciona que los datos son de phase0_results/** — El prompt asume que los datos están en un endpoint live, pero los datos reales vienen de archivos JSON estáticos en `cgalpha_v3/data/phase0_results/`. Esto afecta cómo se calculan y actualizan los campos de active learning.
3. ❌ **No considera que `cumulative_delta_at_retest` ya existe** — El prompt original proponía añadir CumDelta como nueva visualización, pero el campo ya existe en `retests_dataset.json` como `cumulative_delta_at_retest`. No hay que añadirlo, solo dibujarlo.
4. ✅ **Bueno:** Pide especificación técnica concreta con nombres de campos y pseudocódigo.

**Prompt C corregido:**
> "Contexto REAL del schema de datos (no inventar campos que ya existen):
> retests_dataset.json tiene estos campos EXACTOS:
> {
>   zone_id: string (formato: '{key_idx}_{direction}'),
>   retest_index: int,
>   retest_price: float,
>   retest_timestamp: int (ms),
>   vwap_at_retest: float,
>   obi_10_at_retest: float,
>   cumulative_delta_at_retest: float,  ← YA EXISTE, NO añadirlo de nuevo
>   delta_divergence: string (ej: 'BEARISH_EXHAUSTION'),
>   atr_14: float,
>   regime: string ('LATERAL' | 'TREND'),
>   outcome: string ('BOUNCE' | 'BREAKOUT')
>   // direction NO existe actualmente en retests_dataset.json; derivarlo de zone_id o añadirlo explícitamente
> }
>
> Para active learning, training_dataset.json tiene:
> { sample_id, _meta, zone_geometry, l2_snapshot_at_touch, outcome }
> NO tiene oracle_confidence ni oracle_predicted_outcome. Propón cómo añadir estos campos sin romper el pipeline existente."

### Prompt D (DeepSeek V4 Pro — Code review final)

**Problemas detectados:**
1. ✅ **Buen enfoque:** Pide revisar bugs de sincronización, accesibilidad, memory leaks, rendimiento.
2. ❌ **No menciona el problema específico de renderTrainingChart que redibuja SVG completo cada vez** — Cada vez que se navega de zona o se cambia el filtro, `renderTrainingChart()` reconstruye TODO el SVG desde cero (líneas 3591-3892). Para 1000+ samples esto puede ser lento. El code review debería detectar este bottleneck y proponer virtualización o SVG incremental.
3. ❌ **No menciona que `trainingData` es un objeto global mutable** — Si dos pestañas envían approve/reject simultáneamente, el objeto global `trainingData` puede desincronizarse. El code review debe revisar la consistencia del estado global.
4. ✅ **Bueno:** Pide veredicto final LISTO/NECESITA CAMBIOS.

---

## 4. ENTREGABLE FINAL

### 4.1 Lista de requisitos corregida

| Prioridad | Requisito | Estado en código | Acción requerida |
|-----------|-----------|-----------------|------------------|
| **P0** | Fix `rt.direction` indefinido | ❌ 100% missing | Añadir `direction` a `retests_dataset.json` o hacer fallback en render |
| **P0** | Endpoints approve/reject con persistencia real | ⚠️ Stubs | Conectar endpoints con actualización real de status + respuesta al frontend |
| **P0** | Layout CSS Grid 65/35 | ❌ Vertical fijo | CSS Grid: `display:grid; grid-template-columns:65% 35%` |
| **P0** | Sync chart↔tabla bidireccional | ⚠️ Unidireccional | Completar: click en fila → highlight chart; click en chart → highlight fila |
| **P1** | Botones approve/reject UI optimista | ❌ No existe | JS puro + POST a endpoints existentes |
| **P1** | Labels granulares | ❌ No existe | Nuevo campo `label_status` + endpoint PATCH + exportador |
| **P1** | Atajos teclado (A/R/←/→) | ❌ No existe | JS: `addEventListener('keydown')` |
| **P1** | OBI/CumDelta mini-panel | ⚠️ Solo en tabla | Dibujar mini-panel SVG fijo al lado del chart |
| **P2** | Contador progreso sesión | ❌ No existe | JS: contadores locales |
| **P2** | Undo Ctrl+Z | ❌ No existe | JS: stack de decisiones + revert |
| **P2** | Active learning | ❌ Sin campos | Nuevos campos en training_dataset.json |
| **P2** | Ghost candles multi-temporal | ⚠️ Solo 5m fijo | Requiere datos 4H/1H |
| **P2** | Glassmorphism | ❌ No existe | CSS: `backdrop-filter: blur` |

### 4.2 Prerequisitos de código (ANTES de ejecutar el Prompt A)

Estos 3 bugs deben resolverse ANTES de construir cualquier feature nueva:

| Bug | Archivo | Acción |
|-----|---------|--------|
| `rt.direction` indefinido en 100% samples | `cgalpha_v3/data/phase0_results/retests_dataset.json` | Extraer dirección del `zone_id` (ej: `"318_bearish"` → `"bearish"`) o añadir campo |
| Endpoints approve/reject son stubs | `cgalpha_v3/gui/server.py` (líneas `def approve_retest` y `def reject_retest`) | Conectar con actualización real del status y respuesta al frontend con `{status, decision, label_status}` |
| Sección marcada `[LEGACY - FASE 0]` | `cgalpha_v3/gui/static/index.html` | Decidir: ¿se mantiene como legado o se reemplaza completamente? |

### 4.3 Veredicto del Prompt

**PLAN NECESITA DECISIÓN HUMANA EN:**

1. **Legado vs reescritura:** La sección está marcada `[LEGACY - FASE 0]`. ¿Vale la pena invertir en reconstruir una sección legacy? ¿O se va a reemplazar por la sección L2 Forensics que ya tiene funcionalidad similar?
2. **Escala de datos:** El dataset actual tiene 7 samples sintéticos. Si se mantiene la UI para escala (1000+ samples), el renderizado SVG completo de cada zona se vuelve lento. ¿Hay datos reales de producción para validar el diseño?
3. **Pipeline de datos:** Los endpoints approve/reject escriben a `retest_curation.jsonl` pero no devuelven estado al frontend ni actualizan el dataset. ¿El sistema de curation existe para ser consumido por el pipeline de entrenamiento, o es un archivo morto?

**PLAN LISTO PARA EJECUCIÓN SI:**
- El operador confirma que la sección Training Review merece mantenimiento activo (no reemplazo por L2 Forensics)
- El operador acepta que los fixes P0 (direction + endpoints) se hagan antes de cualquier feature nueva
- El operador valida la escala de datos (actual: 7 samples, potencial: 1000+)
