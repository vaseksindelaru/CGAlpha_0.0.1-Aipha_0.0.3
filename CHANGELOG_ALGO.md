# CHANGELOG ALGORÍTMICO — cgAlpha Triple Coincidence Detector

Registro cronológico de cambios en la lógica algorítmica del detector
y del pipeline de datos. Cada entrada documenta qué cambió, por qué,
y cuál es el impacto esperado.

---

## v1.7.0 — 2026-05-10
### Cambio
**Z-Score Calibration Instrumentation** (Cat.1, observacional):
Método `_log_zscore_calibration()` registra para cada vela procesada:
`vol_z_score`, `body_pct`, `passed_filter`, `zone_detected`.
Archivo: `aipha_memory/operational/zscore_calibration_log.jsonl`.

**Archivo**: `cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py`
(feed_kline_for_zone_detection, _log_zscore_calibration)

### Motivación
El umbral `volume_z_threshold=0.5` fue seleccionado por intuición basada
en una sola vela. Principio del proyecto: "Medir → Analizar → Calibrar →
Filtrar". Este log permite analizar la distribución de Z-Scores en la
población real y recalibrar cuando haya ≥500 registros.

### Impacto esperado
Sin impacto en comportamiento. Genera ~29 KB/día de datos de calibración.
Permite calcular: zonas perdidas con threshold 0.3 vs 0.5 vs 0.7; distribución
de Z-Scores en zonas que produjeron BOUNCE_STRONG.

### Trazabilidad
Branch: main (Hardening Fase 2)

---

## v1.6.0 — 2026-05-10
### Cambio
**Multi-Touch Clearance Logic** (Cat.2):
Implementación de clearance validation en `check_intra_candle_retest`.
Para el 2do+ toque de una zona, el precio debe haberse alejado ≥
`min_clearance_atr * ATR` antes de que un nuevo contacto cuente como
retest independiente. Campos añadidos a `ActiveZone`:
`max_price_since_last_touch`, `min_price_since_last_touch` (reset en
`register_touch`). Parámetro `min_clearance_atr=1.0` en config defaults.

**Archivo**: `cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py`
(ActiveZone L70-71, register_touch L119-121, config L691, check_intra_candle_retest L1298-1312)

### Motivación
Sin clearance, el movimiento lateral dentro de una zona generaba múltiples
señales del mismo evento. El segundo toque tiende a ser más débil en defensa
institucional; el tercero frecuentemente precede una ruptura. Cada toque
adicional tiene valor predictivo diferente que el Oracle necesita aprender.

### Impacto esperado
Eliminación de retests duplicados por oscilación lateral. Retests genuinos
(post-clearance) enriquecidos con `touch_count` y `prior_touch_outcomes`
para que el Oracle diferencie primer toque vs subsiguientes.

### Trazabilidad
Branch: main (Hardening Fase 2)

---

## v1.5.0 — 2026-05-10
### Cambio
**GUI Zone Visibility Fix**: Separación de archivos de estado del detector
(`detector_state.json`) y vista GUI (`active_zones.json`). Rutas absolutas
basadas en `__file__` en `save_state()`, `load_state()` y
`_persist_active_zones()`. Eliminación de 5 procesos zombie que
competían por el mismo archivo.

**Archivo**: `cgalpha_v3/application/live_adapter.py` (L207-237),
`cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py` (L690, L721-754, L756-788)

### Motivación
El adaptador escribía `active_zones.json` con ruta relativa al CWD del proceso.
El servidor GUI lo leía con ruta absoluta (`project_root / ...`). Resultado:
la GUI mostraba datos obsoletos (zona TEST_DEBUG_123) durante 12+ horas
mientras el detector tenía zonas reales en memoria.

### Impacto esperado
Zonas visibles en la GUI inmediatamente tras el bootstrap (<30s vs >12h anterior).

### Trazabilidad
Branch: main (post-commit `2268d2f`)

---

## v1.4.0 — 2026-05-10
### Cambio
**Bootstrap Zone Survival**: Implementación del flag `is_bootstrapping` en
`process_stream()` que suspende `_cleanup_expired_zones()` durante el
warm-up histórico. Sin este flag, las zonas detectadas en índices tempranos
(ej: índice 100 de 499) eran eliminadas por timeout (50 bars) antes de
que el loop terminara.

**Archivo**: `cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py`
(L1020-1022, L1074-1076, L1228-1229)

### Motivación
El bootstrap reportaba "4 zonas creadas" pero al finalizar el loop
quedaban 0 zonas activas. El timeout de 50 bars limpiaba cada zona
~250 iteraciones después de detectarla.

### Impacto esperado
100% de zonas bootstrap sobreviven al warm-up (10 zonas confirmadas post-fix).

### Trazabilidad
Branch: main (post-commit `2268d2f`)

---

## v1.3.0 — 2026-05-09
### Cambio
**Journaling Defensivo**: `DeferredOutcomeMonitor.tick()` ahora llama
`_persist_pending()` cada vez que se detecta un nuevo récord de MFE o MAE.

**Archivo**: `cgalpha_v3/domain/deferred_outcome_monitor.py` (L196-198)

### Motivación
Si el proceso caía entre un récord de MFE y el cierre de la vela, el
progreso de rentabilidad se perdía. Con journaling inmediato, cualquier
reinicio preserva el último MFE/MAE registrado.

### Impacto esperado
Pérdida cero de datos de labeling en caso de crash mid-retest.

### Trazabilidad
Commit: `2268d2f`

---

## v1.2.0 — 2026-05-09
### Cambio
**Morfología Observacional**: Campos `key_candle_upper_wick_pct`,
`key_candle_lower_wick_pct`, `key_candle_rejection` añadidos al
`ReentrySnapshot` en `live_adapter.py`. Retrocompatible via `.get(..., 0)`.

**Archivo**: `cgalpha_v3/application/live_adapter.py` (L308-313)

### Motivación
El Oracle no tenía acceso a la forma de la vela que generó la zona.
Las mechas largas (>40%) indican rechazo institucional — feature
predictiva para distinguir BOUNCE vs BREAKOUT.

### Impacto esperado
Feature importance del Oracle post-retraining: `rejection_direction`
debería aparecer en top-10 si las mechas son informativas.

### Trazabilidad
Commit: `c78fb8e`

---

## v1.1.0 — 2026-05-09
### Cambio
**Z-Score de Volumen Adaptativo**: Reemplazo del filtro P70 estático
por Z-Score local (ventana 30 velas, umbral 0.5). Parámetro
`volume_z_threshold` registrado en `parameter_landscape.py`
con sensitivity="high".

**Archivo**: `cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py`
(KeyCandleDetector.detect, L214-225)

### Motivación
El P70 global mezclaba sesiones asiática, europea y de fin de semana.
Una vela con volumen elevado para la sesión weekend era filtrada por
no superar el P70 de la sesión europea. El Z-Score local captura
outliers relativos al contexto inmediato.

### Impacto esperado
Detección de velas clave en sesiones de baja volatilidad (weekend, 
Asian session) sin incrementar falsos positivos en sesiones de alta
volatilidad.

### Trazabilidad
Commit: `c78fb8e`

---

## v1.0.0 — 2026-05-09
### Cambio
**Cold Start / Warm Start**: Implementación de `seed_history(df)` que
pre-popula `_kline_buffer` con 200 velas del bootstrap. Deduplicación
por `open_time` para evitar solapamiento bootstrap→WebSocket.
**Persistencia con TTL**: `save_state()` / `load_state()` con filtro
de 24 horas y serialización robusta de tipos numpy/Enum.

**Archivos**:
- `cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py` (seed_history, save_state, load_state)
- `cgalpha_v3/scripts/launch_shadow_live.py` (bootstrap_detector)

### Motivación
El detector arrancaba en vacío (`active_zones = 0`) y requería 8+ horas
de mercado vivo para detectar la primera zona. Con seed_history, el
detector tiene contexto estadístico (ATR, Z-Score) desde el primer tick.

### Impacto esperado
Tiempo a primera zona: <30s (vs 8+ horas anterior).

### Trazabilidad
Commit: `c78fb8e`
