# ADR-ACOPLAMIENTO-TEMPORAL-1 — Restricción de Acoplamiento Temporal: t_feature ≤ t_candle_close − ε

## Estatus
ACEPTADO e IMPLEMENTADO (2026-06-23).

Aprobado por el operador y Tech Lead tras evaluación de diseño, con modificación conservadora: ε = 200ms (en lugar de 100ms propuesto) para mitigar riesgo de network jitter y micro-stutters de Binance. Establece D-014 en el Registro de verdades inmutables del Nexus §3. Cuando el estudio forense de drift consolidado valide que p95 ≤ 100ms, se considerará bajar ε a 100ms.

## Contexto

La alerta #3 de la deliberación Ruta B identificó el riesgo de lookahead bias al acoplar el feed hiper-rápido de P3 (L2 Ring Buffer, 100ms) con la maquinaria de 5m estabilizada de P5 (TripleCoincidenceDetector, `interval_s=300`, D-011). Si los relojes no se cierran con precisión de milisegundos idéntica a la detección de la vela, el Oracle aprende con features del futuro (tiempo posterior al "toque").

El forense de código vivo reveló que `time.time()` (wall clock local) aparece en **7 paths críticos** entre P3, P4 y `live_adapter.py`, mezclado con `binance_ts_ms` (event time de Binance). Esta inconsistencia es la materialización concreta del riesgo de lookahead bias.

### Evidencia material verificada — mapeo completo de `time.time()`

**P3 — `cgalpha_v3/infrastructure/binance_websocket_manager.py`:**
- L147: `binance_ts_ms = data.get("E", data.get("T", time.time() * 1000))` — fallback a wall clock si no hay `E`/`T`.
- L179: `local_ts_ms = time.time() * 1000` — wall clock para calcular `local_offset_ms`.
- L269-273: `get_rolling_delta` usa `last_known_binance_ts_ms` con fallback a `time.time() * 1000`.

**P4 — `cgalpha_v3/domain/deferred_outcome_monitor.py`:**
- L161: `sample_id = meta.get("sample_id", f"re_{int(time.time())}")` — fallback a wall clock si no hay `sample_id`.
- L204: `hours_since = (time.time() - flip_ts) / 3600.0` — wall clock para `hours_since_flip`.
- L208: `capture_ts = meta.get("capture_ts_unix_ms", time.time() * 1000) / 1000.0` — fallback a wall clock si no hay `capture_ts_unix_ms`.
- L283: `label.resolution_ts = time.time()` — wall clock para el momento de resolución.

**`live_adapter.py` (punto de acoplamiento crítico):**
- L83-87: `self._last_aggtrade_ts_ms = int(time.time() * 1000)` — inicialización con wall clock.
- L258-260: `self._last_aggtrade_ts_ms = int(data.get("T", data.get("E", time.time() * 1000)))` — fallback a wall clock.
- L263-268: `depth_ts_ms = int(data.get("E", data.get("T", time.time() * 1000)))` — fallback a wall clock en heartbeat watchdog.
- **L271-275 (CRÍTICO):** `ts = int(trade.get("T", trade.get("E", time.time() * 1000)))` seguido de `kline_start = (ts // (self.interval_s * 1000)) * (self.interval_s * 1000)` — **este es el punto exacto donde el reloj del trade se acopla al reloj de la vela.** Si `ts` usa wall clock (fallback), `kline_start` se calcula con un reloj distinto al de Binance.
- L411-416: `micro_data["timestamp"] = kline.get("close_time", int(time.time() * 1000))` — fallback a wall clock para el timestamp del micro_data que recibe el detector.

### El problema de fondo

El sistema tiene **dos relojes**:
1. **`binance_ts_ms`** (event time de Binance, campos `E` y `T`): el reloj del mercado.
2. **`time.time()`** (wall clock local): el reloj de la máquina.

Estos relojes **no están sincronizados**. El drift típico entre un servidor local y Binance es de 1-500ms dependiendo de la latencia de red y la calidad del NTP. En condiciones adversas (NTP desync, carga de CPU, GC pause), puede llegar a segundos.

El lookahead bias ocurre cuando:
1. El detector identifica un retest en el tick `t_retest` (reloj de Binance).
2. El Ring Buffer sintetiza features L2 con snapshots cuyo `ts` (reloj de Binance) es posterior a `t_retest` pero anterior al cierre de la vela `t_candle_close`.
3. El Oracle entrena con features que incluyen información posterior al retest pero anterior al cierre de la vela.

Si el Oracle predice en producción usando features del mismo rango temporal, no hay lookahead. Pero si el entrenamiento incluye features posteriores al momento de predicción en producción, hay lookahead.

**El caso más peligroso:** `synthesize_at_retest()` se invoca en `_on_retest_detected` cuando un tick toca la zona. El buffer contiene snapshots de los últimos 30 segundos. Si el retest ocurre en `t_retest` y el buffer incluye snapshots hasta `t_retest + δ` (porque el callback se procesa asíncronamente después de que el buffer ya tiene snapshots más recientes), entonces las features incluyen información de `δ` milisegundos en el futuro relativo al retest.

## Decisión propuesta

**Establecer la restricción matemática de acoplamiento temporal como un nuevo D-ID (D-014) en el Registro de verdades inmutables del Nexus §3:**

> **D-014 — Acoplamiento Temporal Causal:** Toda feature L2 consumida por el Oracle debe satisfacer `t_feature ≤ t_candle_close − ε`, donde `t_feature` es el timestamp del snapshot L2 más reciente en el perfil sintetizado, `t_candle_close` es el timestamp de cierre de la vela de detección (Binance event time), y `ε` es un margen de seguridad conservador. El valor canónico de `ε` es **200ms** (2× el sample rate del Ring Buffer de 100ms). Esta restricción previene lookahead bias al garantizar que ninguna feature incluye información posterior al cierre de la vela de detección. El valor de ε = 200ms fue elegido por el operador y Tech Lead como mitigación conservadora frente a network jitter y micro-stutters de Binance (sacrificio asimétrico de 0.6% de la ventana L2 de 30s = 100% de tolerancia frente al lag típico antes de descartar un snapshot con CAUSAL_REJECTED). Cuando el estudio forense de drift consolide que p95 ≤ 100ms, se considerará bajar ε a 100ms.

### Argumentación del valor de ε

El valor de ε debe satisfacer tres constraints:

**1. ε ≥ sample_rate del Ring Buffer (100ms).**
El Ring Buffer empuja snapshots cada 100ms. Si ε < 100ms, un snapshot en el límite podría tener `t_feature` dentro del rango `[t_candle_close − 100ms, t_candle_close]`, introduciendo información del último 100ms antes del cierre. ε = 200ms (2× sample rate) garantiza margen adicional más allá del push rate.

**2. ε ≥ drift máximo esperado entre wall clock y Binance event time.**
El drift típico es 1-500ms. Con NTP bien configurado, <50ms. Sin NTP, hasta segundos. ε = 200ms cubre el caso típico con NTP + margen para network jitter y micro-stutters de Binance. Si el drift excede 200ms, el sistema debe rechazar el snapshot (marcarlo como `PARTIAL` o `CAUSAL_REJECTED`), no reducir ε.

**3. ε ≤ granularidad temporal del evento de etiquetado.**
El evento de etiquetado (retest) ocurre en un tick específico. La vela de detección cierra en `t_candle_close`. El Oracle predice en el momento del retest, que es anterior a `t_candle_close`. Si ε es muy grande, se descartan features legítimamente disponibles en el momento del retest. ε = 200ms es pequeño relativo a la ventana de 30s del Ring Buffer (0.6% de la ventana), por lo que el costo en información es despreciable.

**Decisión del operador y Tech Lead:** ε = 200ms (modificación conservadora sobre los 100ms propuestos originalmente). El sacrificio asimétrico de 0.6% de la ventana L2 otorga 100% de tolerancia frente al lag típico antes de verse forzados a descartar un snapshot con CAUSAL_REJECTED. Cuando el estudio forense de drift consolidado valide que p95 ≤ 100ms, se considerará bajar ε a 100ms.

### Implementación técnica propuesta

**No se implementa en este ADR.** Este ADR establece la restricción matemática. La implementación se detalla en los CRBs de P3 y P4 (Fase B). El esquema es:

1. **En `L2RingBuffer.synthesize_at_retest()`:** añadir parámetro `t_candle_close_ms`. Antes de sintetizar, filtrar snapshots con `ts > t_candle_close_ms − ε`. Si el filtrado reduce el buffer a <10 snapshots, retornar `_empty_profile()` con `l2_data_quality = "CAUSAL_REJECTED"`.

2. **En `live_adapter._on_retest_detected`:** pasar `t_candle_close_ms` al invocar `synthesize_at_retest(t_candle_close_ms=...)`. El valor se obtiene del `kline_start + interval_s * 1000` de la vela actual.

3. **En `DeferredOutcomeMonitor`:** reemplazar los 4 usos de `time.time()` (L161, L204, L208, L283) por `binance_ts_ms` del snapshot. Si el snapshot no trae `capture_ts_unix_ms`, rechazar el sample (no usar fallback a wall clock).

4. **En `BinanceWebSocketManager`:** el fallback a `time.time()` en L147 y L269-273 se mantiene solo para el primer mensaje antes de recibir `E`/`T`. Una vez recibido el primer `binance_ts_ms`, el fallback se deshabilita y se usa el último `binance_ts_ms` conocido.

5. **Estudio forense de drift (CRB P3 §6 Fase B punto 2):** medir `local_offset_ms` en producción sobre ≥1000 mensajes. Reportar distribución (min, p50, p95, max). Si p95 > 100ms, aumentar ε o mejorar NTP.

### Relación con D-011

D-011 fija `interval_s = 300` (5m) como verdad inmutable. D-014 es complementario: fija el acoplamiento temporal entre el Ring Buffer (100ms) y la vela de detección (5m). Ambos son verdades inmutables. Cambiar D-014 requiere ADR + re-entrenamiento (igual que D-011).

### Relación con el Punto Ciego #1

El Punto Ciego #1 (Nexus §5.7 issue #3 original, ahora ⚠️ PARCIAL) documenta "Timestamps usan `time.time()` no Binance event time → clock drift posible". D-014 es la resolución formal de este Punto Ciego: establece la restricción matemática que lo cierra.

## Consecuencias

- **Positivas:**
  - Cierra formalmente el Punto Ciego #1 (clock drift).
  - Garantiza que el Oracle no entrene con features del futuro.
  - Establece un umbral cuantificable (ε = 100ms) que se puede medir y monitorear.
  - `l2_data_quality` gana un nuevo valor `CAUSAL_REJECTED` para snapshots que violan la restricción.
- **Neutrales:**
  - El Ring Buffer pierde los últimos 100ms de snapshots en cada síntesis. Despreciable (0.3% de la ventana de 30s).
  - Los 7 paths de `time.time()` deben migrarse a `binance_ts_ms`. Es trabajo de Fase A/B de P3 y P4.
- **Riesgos:**
  - Si el drift real excede 100ms (NTP mal configurado), el sistema rechaza snapshots legítimos. Mitigación: estudio forense de drift + alerta si p95 > 100ms.
  - Si `binance_ts_ms` no está disponible en algún path (mensaje sin `E`/`T`), el sistema debe rechazar el sample, no usar wall clock. Esto puede perder samples en condiciones adversas. Mitigación: Binance casi siempre envía `E`/`T`; el fallback a wall clock era una red de seguridad que ahora se elimina deliberadamente.

## Alternativas consideradas

- **ε = 0 (sin margen).** Descartada porque no cubre el drift entre wall clock y Binance event time. Un snapshot con `t_feature = t_candle_close` podría tener drift positivo y ser del futuro.
- **ε = 50ms.** Descartada porque no cubre el sample rate del Ring Buffer (100ms). Un snapshot en el límite podría estar dentro del rango prohibido.
- **ε = 100ms (propuesta original del modelo).** Cubre sample rate y drift típico con NTP, pero el operador y Tech Lead la consideraron insuficiente frente a network jitter y micro-stutters de Binance. Solo 100ms de tolerancia sobre el push rate de 100ms no deja margen. Se mantiene como objetivo futuro si el estudio forense de drift valida p95 ≤ 100ms.
- **ε = 500ms.** Descartada porque es demasiado conservadora. Descarta 1.6% de la ventana de 30s sin justificación si el NTP está bien configurado.
- **ε = 200ms (recomendada y aprobada por operador y Tech Lead).** 2× el sample rate, cubre drift típico con NTP + jitter, despreciable relativo a la ventana (0.6%). Sacrificio asimétrico que otorga 100% de tolerancia frente al lag típico antes de descartar un snapshot.
- **No establecer ε, confiar en NTP.** Descartada porque NTP no es garantía. El drift puede ocurrir por GC pause, carga de CPU, o desync temporal. La restricción matemática es independiente de la calidad del NTP.

## Próximos pasos (post-aprobación — aprobado 2026-06-23 con ε=200ms)

1. ✅ Añadir D-014 al Registro de verdades inmutables del Nexus §3.
2. ✅ Actualizar Nexus §5.7 issue #3 de `⚠️ PARCIAL` a `✅ RESUELTO via D-014 (pendiente implementación)`.
3. ✅ Actualizar Nexus §5.4 issue #5 de `🆕 ADR de diseño PENDIENTE` a `✅ D-014 establecido (pendiente implementación)`.
4. Implementar D-014 en Fase B de P3 (CRB P3 §6 Fase B punto 2) y Fase A de P4 (CRB P4 §6 Fase A punto 6).
5. Estudio forense de drift (`local_offset_ms` sobre ≥1000 mensajes) para validar si p95 ≤ 100ms y considerar bajar ε a 100ms.

---

*Referencias:*
- *`cgalpha_v3/infrastructure/binance_websocket_manager.py` L145-148, L179, L269-273 (P3 time.time)*
- *`cgalpha_v3/domain/deferred_outcome_monitor.py` L161, L204, L208, L283 (P4 time.time)*
- *`cgalpha_v3/application/live_adapter.py` L83-87, L258-260, L263-268, L271-275, L411-416 (acoplamiento crítico)*
- *`cgalpha_v3/infrastructure/l2_ring_buffer.py` L38-126 (synthesize_at_retest)*
- *`cgalpha_v4/CRB_BinanceWebSocketManager_P3.md` §6 Fase B punto 2 (estudio forense de drift)*
- *`cgalpha_v4/CRB_DeferredOutcomeMonitor_P4.md` §6 Fase B punto 2 (acoplamiento temporal)*
- *`aipha_memory/identity/ADR-EVO-TICKET-0006-1-live-candle-interval-5m.md` (D-011, timeframe)*
- *Deliberación arquitectónica Ruta B, sesión 2026-06-23 (alerta #3)*
