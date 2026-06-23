# ADR-RECONCILIATION-1 — Reconciliación del Nexus §4/§5.4/§5.7 con el código vivo

## Estatus
ACEPTADO e IMPLEMENTADO (2026-06-23).

Aprobado por el operador tras revisión exhaustiva del borrador. Los 4 cambios al Nexus fueron aplicados a `documentation/NEXUS_SUPERIOR.md` en una sola pasada. Evento registrado en `constitutional_events.jsonl` (D-009).

## Contexto

Durante la deliberación arquitectónica Ruta B (sesión 2026-06-23), se redactaron los CRB de P3 (`cgalpha_v4/CRB_BinanceWebSocketManager_P3.md`) y P4 (`cgalpha_v4/CRB_DeferredOutcomeMonitor_P4.md`) mediante inspección forense directa del código vivo, desconfiando de las descripciones del Nexus.

El forense reveló **Document Drift severo** en dos secciones del Nexus:

- **§5.7 (BinanceWebSocketManager)** reporta 4 issues como pendientes. Los 4 ya están resueltos en código.
- **§5.4 (DeferredOutcomeMonitor)** reporta 3 issues como pendientes. Los 3 ya están resueltos en código. Además, existe una funcionalidad completa (Shadow Harvesting con `touch_sequence`/`polarity_flipped`/`prior_touch_outcomes`) que el Nexus no menciona.
- **§4 (Orden de ataque)** P3 y P4 reportan estados y razones desfasados que inducen a planificar trabajo ya hecho.

### Evidencia material verificada

**P3 — `cgalpha_v3/infrastructure/binance_websocket_manager.py` + `l2_ring_buffer.py`:**

| Issue reportado en Nexus §5.7 | Estado real en código | Línea |
|---|---|---|
| #1 Sin L2RingBuffer | ✅ Integrado: `self.l2_buffers = {sym: L2RingBuffer() for sym in self.symbols}` | WS L57-59 |
| #2 CumDelta global, no rolling | ✅ Rolling: `get_rolling_delta(symbol, window_seconds=300)` | WS L264-280 |
| #3 Timestamps con `time.time()` | ✅ Mitigado: `binance_ts_ms = data.get("E", data.get("T", time.time()*1000))` + `local_offset_ms` | WS L145-148, L183 |
| #4 Reconexiones sin marcar PARTIAL | ✅ Implementado: `mark_reconnection(epoch)` + `l2_data_quality = "FULL" if len(epochs_in_w30) == 1 else "PARTIAL"` | WS L99-102, L17-18, L60-62 |

Además, `synthesize_at_retest()` (L2RingBuffer L38-126) está conectado al flujo de producción vía `LiveDataFeedAdapter._on_retest_detected` (`live_adapter.py` L631-635), que popula `snapshot["l2_temporal_profile"]` con los 23 features antes de pasar el snapshot a `DeferredOutcomeMonitor.register_retest()`.

**P4 — `cgalpha_v3/domain/deferred_outcome_monitor.py`:**

| Issue reportado en Nexus §5.4 | Estado real en código | Línea |
|---|---|---|
| #1 Sin buffer temporal L2 | ✅ Conectado vía `live_adapter.py` L631-635; `raw_buffer` persistido en `aipha_memory/raw_buffers/{sample_id}.json.gz` | DOM L196-200 |
| #2 lookahead fijo = 10 velas | ✅ Adaptativo: `adaptive_lookahead(zone_width_atr) = max(5, min(20, int(5 + zone_width_atr*3)))` | DOM L34-43 |
| #3 Etiquetado terciario sin calibrar | ✅ Implementado: `BOUNCE_STRONG`/`BOUNCE_WEAK`/`BREAKOUT`/`INCONCLUSIVE` con umbrales `0.5*atr` y `0.3*atr` | DOM L337-376 |

Además, existe **Shadow Harvesting** completo no documentado en el Nexus:
- `PendingLabel` con campos `touch_sequence`, `polarity_flipped`, `prior_touch_outcomes`, `zone_original_direction`, `hours_since_flip` (DOM L66-71)
- `register_retest` acepta estos campos (DOM L135-144)
- `_flush_resolved` inyecta `touch_context` con `effective_direction`, `is_secondary_retest`, `is_tertiary_retest` (DOM L406-419)
- Introducido por patches en `rebound/` (`patch_deferred_monitor_multitouch.py`, `patch_live_adapter_multitouch.py`, `patch_zone_lifecycle.py`) sin ADR previo.

### Tests existentes (no reportados en el Nexus)

P4 tiene tests reales que el Nexus no menciona:
- `tests/test_dataset_deduplication.py` — 1 test sobre la Triple Barrera de dedup.
- `tests/test_spatial_multitouch.py` — 3 tests sobre B-008 v2 (huella causal sin `zone_direction`).

Estos tests cubren `register_retest` (dedup) pero **no cubren** `_evaluate`, `tick`, ni `_flush_resolved`. La Puerta de Cobertura Base está parcialmente abierta.

P3 tiene **0 tests** sobre `BinanceWebSocketManager` y `L2RingBuffer` (verificado por `find_path`).

## Decisión

Reconciliar el Nexus §4 (P3 y P4), §5.4 y §5.7 para reflejar la verdad inmutable del código vivo. Los cambios son de documentación, no de código. Se aplican los diffs exactos de la sección siguiente.

### Principios de la reconciliación

1. **No se elimina información histórica.** Los issues resueltos se marcan como `✅ RESUELTO` con referencia al código, no se borran. Esto preserva la trazabilidad para modelos futuros (D-010 Cognitive Portability).
2. **Se añade la funcionalidad no documentada** (Shadow Harvesting, conexión vía `live_adapter.py`) como nueva información.
3. **Se actualiza el estado de cobertura** con lo verificado: P3 = 0 tests, P4 = tests parciales sobre dedup.
4. **Se actualizan los bloqueos reales** en §4: P3 y P4 no requieren "implementar" sino "auditar, testear, caracterizar drift, y decidir fricción económica".
5. **No se decide la fricción económica ni el acoplamiento temporal en este ADR.** Esos son ADRs de diseño separados (pendientes). Este ADR solo reconcilia documentación.

## Cambios exactos al Nexus

### Cambio 1 — §4 P3 (líneas 257-262)

**Texto actual:**
```
P3          L2 Ring Buffer                🟡 PARCIAL          [CRB PENDIENTE]
            (BinanceWebSocketManager)
            Razón: prerrequisito directo para Oracle Fase B.
                   Sin Ring Buffer de 30s, las features dinámicas
                   del Oracle son imposibles.
```

**Texto propuesto:**
```
P3          L2 Ring Buffer                🟡 OPERATIVO —      ✅ CRB creado
            (BinanceWebSocketManager)       AUDIT PENDIENTE    (CRB_BinanceWebSocketManager_P3.md)
            Razón: Ring Buffer IMPLEMENTADO en código (push, synthesize,
                   clock drift mitigation, CumDelta rolling, epoch tracking).
                   Conectado al flujo vía live_adapter._on_retest_detected.
                   Bloqueo real: 0 tests + time drift sin caracterizar.
                   Ver ADR-RECONCILIATION-1 y CRB_BinanceWebSocketManager_P3.md.
```

### Cambio 2 — §4 P4 (líneas 263-267)

**Texto actual:**
```
P4          DeferredOutcomeMonitor        🟡 OPERATIVO        [CRB PENDIENTE]
            Fase Bridge (etiquetado enriquecido)
            Razón: prerrequisito para Oracle Fase B.
                   Etiquetado terciario + lookahead adaptativo
                   son mejoras de calidad de datos.
```

**Texto propuesto:**
```
P4          DeferredOutcomeMonitor        🟡 OPERATIVO —      ✅ CRB creado
            Fase Bridge IMPLEMENTADA         AUDIT PENDIENTE    (CRB_DeferredOutcomeMonitor_P4.md)
            Razón: Etiquetado terciario + lookahead adaptativo + Shadow
                   Harvesting IMPLEMENTADOS en código. Bloqueo real:
                   fricción económica sin decidir (ADR pendiente) +
                   cobertura incompleta (_evaluate/tick/_flush_resolved
                   sin tests) + acoplamiento temporal con P3.
                   Ver ADR-RECONCILIATION-1 y CRB_DeferredOutcomeMonitor_P4.md.
```

### Cambio 3 — §5.4 (líneas 417-445)

**Texto actual:**
```
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
```

**Texto propuesto:**
```
### 5.4 DeferredOutcomeMonitor — `cgalpha_v3/domain/deferred_outcome_monitor.py`

```
PROPÓSITO   : Asigna labels diferidos a los retests capturados.
              Espera outcome_lookahead_bars (adaptativo) antes de clasificar.
              Produce BOUNCE_STRONG / BOUNCE_WEAK / BREAKOUT / INCONCLUSIVE.
              Elimina el fallback "return BOUNCE" por defecto (BUG-5 ✅).
              Persiste samples en training_dataset_v2.jsonl con snapshot
              completo + l2_temporal_profile + touch_context (Shadow Harvesting).

ESTADO      : 🟡 OPERATIVO — PROTEGIDO — FASE BRIDGE IMPLEMENTADA
              (AUDIT PENDIENTE: tests + fricción económica + acoplamiento temporal)
COBERTURA   : [PARCIAL — tests existen para dedup (register_retest),
               pero _evaluate/tick/_flush_resolved SIN tests directos.
               No se ha medido con pytest --cov.]

MÓDULO PROTEGIDO: cambios = Cat.3 obligatorio

FUNCIONES CRÍTICAS QUE VIVEN AQUÍ (NO mover al Oracle):
  adaptive_lookahead(zone_width_atr)  → lookahead adaptativo IMPLEMENTADO
  _causal_fingerprint()               → sin zone_direction (B-008 v2 ✅)
  register_retest()                   → registra para etiquetado diferido
  tick(price, bar_closed)             → evalúa resolución en cada tick
  _evaluate()                         → etiquetado terciario IMPLEMENTADO
  _flush_resolved()                   → inyecta outcome + touch_context

ISSUES CONOCIDOS — POST-RECONCILIACIÓN (ADR-RECONCILIATION-1)
  #1 ✅ Buffer temporal L2 conectado vía     → RESUELTO (live_adapter.py L631-635)
     live_adapter._on_retest_detected;          raw_buffer persistido en
     aipha_memory/raw_buffers/{sample_id}.json.gz
  #2 ✅ Lookahead adaptativo IMPLEMENTADO      → RESUELTO (DOM L34-43)
     adaptive_lookahead(zone_width_atr) =
     max(5, min(20, int(5 + zone_width_atr*3)))
  #3 ✅ Etiquetado terciario IMPLEMENTADO      → RESUELTO (DOM L337-376)
     BOUNCE_STRONG (>0.5 ATR), BOUNCE_WEAK (>0.3 ATR MFE),
     BREAKOUT, INCONCLUSIVE
  #4 🆕 Fricción económica ausente             → ADR de diseño PENDIENTE
     (alerta #4 deliberación Ruta B). Labels teóricamente puros,
     sin slippage/costo/latencia. Opción A descartada por operador;
     se trabajará Opción B (post-procesador) o C (ShadowTrader P9).
  #5 🆕 Acoplamiento temporal con P3           → ADR de diseño PENDIENTE
     (alerta #3 deliberación Ruta B). capture_ts y hours_since_flip
     usan time.time() en algunos paths. Requiere t_feature ≤
     t_candle_close - ε como nuevo D-ID.
  #6 🆕 _evaluate/tick/_flush_resolved          → Puerta de Cobertura Base
     sin tests directos                          bloqueante (CRB P4 §6 Fase A)
  #7 🆕 Shadow Harvesting no documentado        → Introducido por patches
     (touch_sequence, polarity_flipped,           en rebound/ sin ADR previo.
     prior_touch_outcomes, hours_since_flip,     Deuda de gobernanza.
     effective_direction, is_secondary/tertiary_retest)
  #8 adaptive_lookahead docstring desfasado     → Mención a "1min live"
                                                 post-EVO-0006 (D-011).
  #9 _load_pending no valida schema             → PendingLabel(**item) puede
                                                 fallar con TypeError.
  #10 Asimetría serialización                   → prior_touch_outcomes:
      prior_touch_outcomes                       asdict condicional en persist,
                                                 no reconstruido en load.

TESTS EXISTENTES (no reportados previamente en el Nexus)
  tests/test_dataset_deduplication.py — 1 test (Triple Barrera dedup)
  tests/test_spatial_multitouch.py — 3 tests (B-008 v2 huella causal)
  test_hits3.py (raíz) — script ad-hoc, no test formal de pytest

BRIEF EXISTENTE : ✅ CRB_DeferredOutcomeMonitor_P4.md (creado 2026-06-23)
PRIORIDAD       : P4 (bloqueo real: fricción económica + cobertura + acoplamiento)
```
```

### Cambio 4 — §5.7 (líneas 517-547)

**Texto actual:**
```
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
```

**Texto propuesto:**
```
### 5.7 BinanceWebSocketManager — `cgalpha_v3/infrastructure/binance_websocket_manager.py`

```
PROPÓSITO   : Conexión a Binance. Ingesta de velas 5m + book depth
              @depth20@100ms + @trade. Calcula OBI y CumDelta en tiempo real.
              Empuja micro-snapshots L2 a L2RingBuffer (30s, 300 slots).

ESTADO      : 🟡 OPERATIVO — RING BUFFER IMPLEMENTADO (AUDIT PENDIENTE)
COBERTURA   : [NO MEDIDA AÚN — 0 tests sobre WS Manager y L2RingBuffer.
               Puerta de Cobertura Base bloqueante (CRB P3 §6 Fase A).]

IMPLEMENTADO
  ✅ Stream @depth20@100ms activo
  ✅ Stream @trade (no @aggTrade — decisión operacional, ADR pendiente)
  ✅ OBI multi-nivel (obi_1, obi_5, obi_10, obi_20)
  ✅ CumDelta rolling window (get_rolling_delta, window_seconds=300)
  ✅ L2RingBuffer integrado (self.l2_buffers, uno por símbolo)
  ✅ push() en cada depth update (~10hz, 15 campos)
  ✅ synthesize_at_retest() condensa 300 slots → 23 features
  ✅ Conectado al flujo vía live_adapter._on_retest_detected (L631-635)
  ✅ binance_ts_ms con local_offset_ms para clock drift
  ✅ mark_reconnection(epoch) + l2_data_quality FULL/PARTIAL

ISSUES CONOCIDOS — POST-RECONCILIACIÓN (ADR-RECONCILIATION-1)
  #1 ✅ L2RingBuffer IMPLEMENTADO              → RESUELTO (WS L57-59, L20)
     (30s, 300 slots, push cada 100ms)
  #2 ✅ CumDelta rolling IMPLEMENTADO           → RESUELTO (WS L264-280)
     (get_rolling_delta, window_seconds=300)
  #3 ⚠️ Timestamps: mitigación existe pero      → PARCIAL — drift no caracterizado
     sin caracterizar                            binance_ts_ms + local_offset_ms
     (binance_ts_ms = data.get("E", data.get("T", time.time()*1000)))  (WS L145-148, L183)
     Fallback a time.time() si no hay E/T.       ADR de acoplamiento temporal
     Requiere estudio forense de drift (≥1000    PENDIENTE (alerta #3 Ruta B).
     mensajes) y umbral de rechazo.
  #4 ✅ Reconexiones marcadas como PARTIAL      → RESUELTO (WS L99-102, L17-18,
     (mark_reconnection + epoch tracking)         L60-62)
  #5 🆕 synthesize_at_retest() no invocado     → Conexión existe vía
     directamente por TripleCoincidenceDetector  live_adapter._on_retest_detected
     (L631-635), no vía el detector. Falta test  (live_adapter.py L631-635).
     de integración end-to-end.                  CRB P3 §6 Fase B punto 1.
  #6 🆕 0 tests sobre WS Manager y L2RingBuffer → Puerta de Cobertura Base
                                                   bloqueante (CRB P3 §6 Fase A).
  #7 🆕 last_trades con pop(0) O(n)             → Deuda de performance.
                                                   Cambiar a deque(maxlen=10000).
  #8 🆕 _empty_profile() schema inconsistente   → 21 ceros vs 23 campos de
                                                   synthesize_at_retest.
  #9 🆕 @trade sin ADR                           → Decisión operacional no
                                                   documentada (WS L92-93).
  #10 🆕 Spot normalization sin test             → Path no cubierto (WS L132-143).
  #11 🆕 binance_websocket_manager.py NO está   → Omisión de gobernanza.
      en PROTECTED_MODULES                       Recomendación: añadir en
                                                   próxima actualización del Nexus.

RING BUFFER IMPLEMENTADO (P3) — ver L2RingBuffer en l2_ring_buffer.py
  L2RingBuffer: deque(maxlen=300), push cada 100ms (15 campos)
  synthesize_at_retest(): condensa 300 slots → 23 features
  Costo en memoria: ~19KB por símbolo. Despreciable.
  Schema de salida: ver CRB_BinanceWebSocketManager_P3.md §3.

BRIEF EXISTENTE : ✅ CRB_BinanceWebSocketManager_P3.md (creado 2026-06-23)
                   (architectural_analysis.md §1.4 es referencia histórica)
PRIORIDAD       : P3 (bloqueo real: 0 tests + drift sin caracterizar)
```
```

### Cambio 5 — §3 PROTECTED_MODULES (líneas 211-221)

**No se aplica en este ADR.** El CRB de P3 §4 recomienda añadir `binance_websocket_manager.py` a `PROTECTED_MODULES`, pero eso es cambio de gobernanza que requiere su propia deliberación. Se documenta como recomendación en el CRB de P3 y se deja para una actualización futura del Nexus.

## Consecuencias

- **Positivas:**
  - El Nexus refleja la verdad material del código. Modelos futuros no planificarán trabajo ya hecho.
  - Los bloqueos reales (tests, drift, fricción económica) quedan explícitos en §4.
  - La trazabilidad histórica se preserva (issues resueltos marcados con ✅, no borrados).
  - Shadow Harvesting queda documentado, cerrando la deuda de gobernanza de los patches en `rebound/`.
- **Neutrales:**
  - No se cambia código. No se invalida el dataset existente.
  - No se decide la fricción económica ni el acoplamiento temporal (ADRs de diseño separados).
- **Riesgos:**
  - Si el código cambia entre la aprobación de este ADR y su aplicación al Nexus, el diff puede quedar desfasado. Mitigación: aplicar inmediatamente tras aprobación.
  - La mención de "ADR pendiente" para fricción económica y acoplamiento temporal crea una expectativa. Si esos ADRs no se redactan, el Nexus queda con referencias a documentos inexistentes. Mitigación: redactar los ADRs de diseño inmediatamente después de aplicar este ADR.

## Alternativas consideradas

- **Opción B — Reescribir §5.4 y §5.7 desde cero.** Descartada porque pierde trazabilidad histórica de los issues resueltos. D-010 (Cognitive Portability) exige que un modelo futuro pueda entender el porqué de cada decisión; borrar los issues resueltos rompe esa cadena.
- **Opción C — Aplazar la reconciliación hasta tener los ADRs de diseño.** Descartada porque el Nexus desfasado induce a planificar trabajo ya hecho (como ocurrió en la deliberación Ruta B). Limpiar el mapa antes de modificar el territorio es imperativo.
- **Opción D — Aplicar los cambios directamente sin ADR.** Descartada porque la reconciliación afecta a 4 secciones del Nexus y a la planificación de P3/P4. Requiere registro formal para trazabilidad (D-009 Constitutional Event Ledger).

## Próximos pasos (post-aprobación)

1. Aplicar los 4 cambios al Nexus (`edit_file` sobre `documentation/NEXUS_SUPERIOR.md`).
2. Registrar el evento en `constitutional_events.jsonl` (D-009).
3. Redactar ADR de Fricción Económica (Opción B o C, según lineamiento del operador).
4. Redactar ADR de Acoplamiento Temporal (`t_feature ≤ t_candle_close - ε` como nuevo D-ID).
5. Reabrir EVO-TICKET-0002 conforme a su protocolo de resurrección.

---

*Referencias:*
- *`cgalpha_v4/CRB_BinanceWebSocketManager_P3.md` (forense P3)*
- *`cgalpha_v4/CRB_DeferredOutcomeMonitor_P4.md` (forense P4)*
- *`cgalpha_v3/infrastructure/binance_websocket_manager.py` (código vivo P3)*
- *`cgalpha_v3/infrastructure/l2_ring_buffer.py` (código vivo P3)*
- *`cgalpha_v3/domain/deferred_outcome_monitor.py` (código vivo P4)*
- *`cgalpha_v3/application/live_adapter.py` L613-744 (conexión P3→P4)*
- *`cgalpha_v3/tests/test_dataset_deduplication.py`, `tests/test_spatial_multitouch.py` (tests P4)*
- *`rebound/patch_deferred_monitor_multitouch.py`, `patch_live_adapter_multitouch.py`, `patch_zone_lifecycle.py` (patches Shadow Harvesting)*
- *Deliberación arquitectónica Ruta B, sesión 2026-06-23 (alertas #2, #3, #4)*
