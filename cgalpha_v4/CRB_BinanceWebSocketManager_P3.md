# CRB — BinanceWebSocketManager + L2RingBuffer (P3)

## cgAlpha_0.0.1 — Component Reconstruction Brief

```
COMPONENTE    : P3 — BinanceWebSocketManager + L2RingBuffer
UBICACIÓN     : cgalpha_v3/infrastructure/binance_websocket_manager.py
                cgalpha_v3/infrastructure/l2_ring_buffer.py
LÍNEAS        : 292 (WS Manager) + 145 (Ring Buffer)
ESTADO        : 🟡 OPERATIVO — RING BUFFER YA IMPLEMENTADO EN CÓDIGO
                (Nexus §5.7 desfasado: reporta "RING BUFFER PENDIENTE"
                 pero la integración existe desde commit pre-2026-06-21)
CRB CREADO    : 2026-06-23
AUTOR         : Modelo operador (Ruta B — deliberación arquitectónica)
```

---

### §1 — Propósito y lugar en el sistema

Ingesta de datos en vivo desde Binance Futures/Spot WebSocket. Mantiene el estado del order book, calcula OBI multi-nivel y CumDelta rolling, y empuja micro-snapshots L2 a un `L2RingBuffer` de 30s/300 slots por símbolo. El Ring Buffer condensa los snapshots en 25 features sintéticos cuando el detector dispara RETEST.

Fragmento del grafo de dependencias (Nexus §2):
```
[Binance WS] → [TripleCoincidence] → [DeferredOutcomeMonitor] → [Oracle]
       │
[BWS L2 Ring Buffer] ─┘
```

**Por qué es prerrequisito de Oracle Fase B:** Las features dinámicas del Oracle v6 requieren microestructura L2 condensada en el momento exacto del retest. Sin Ring Buffer estable y sincronizado temporalmente con la vela de detección (5m, D-011), el Oracle entrena con features estáticas o — peor — con features del futuro (lookahead bias).

---

### §2 — Estado actual

- **Cobertura de tests:** [NO MEDIDA AÚN — Puerta de Cobertura Base bloqueante. No existe ningún test de `BinanceWebSocketManager` ni de `L2RingBuffer` (verificado por `find_path` sobre `test_*websocket*`, `test_*l2*`, `test_*ring*` — 0 matches relevantes).]
- **Tests pasando:** [N/A — no existen tests.]
- **Issues conocidos:**
  1. **Nexus §5.7 desfasado vs. código vivo.** El Nexus reporta issues #1-#4 como pendientes, pero el código ya implementa: (a) `L2RingBuffer` integrado (WS L57-59, L20), (b) `push()` en cada depth update (WS L223-239), (c) `binance_ts_ms` con `local_offset_ms` para clock drift (WS L145-148, L183), (d) CumDelta rolling window (WS L264-280), (e) `mark_reconnection()` con epoch tracking (WS L99-102, L17-18), (f) `l2_data_quality = "FULL"|"PARTIAL"` (L60-62). El CRB debe reconciliar esta divergencia antes de cualquier cambio.
  2. **`synthesize_at_retest()` no está invocado directamente por `TripleCoincidenceDetector`.** La conexión existe, pero vía `LiveDataFeedAdapter._on_retest_detected` (`live_adapter.py` L631-635): el detector dispara un callback que el adaptador consume, y el adaptador invoca `ws.l2_buffers.get(sym).synthesize_at_retest()` para poblar `snapshot["l2_temporal_profile"]` antes de pasarlo a `DeferredOutcomeMonitor.register_retest()`. El flujo P3→P4→Oracle **está cableado en producción**. El issue real no es "no conectado" sino "sin tests que validen esta cadena" y "sin caracterización del drift temporal en el momento exacto del retest".
  3. **`get_rolling_delta()` usa `last_known_binance_ts_ms` con fallback a `time.time()`** (WS L269-273). El fallback puede introducir drift si el primer mensaje no trae `E`/`T`. Riesgo bajo pero no cubierto por tests.
  4. **`last_trades` es un `List` con `pop(0)`** (WS L173-174). O(n) por pop. A 10 tps y 10000 elementos, ~100k ops/s de shifting. No es cuello de botella hoy, pero es deuda técnica. Debería ser `deque`.
  5. **`_empty_profile()` devuelve 21 ceros sin `n_snapshots` ni `l2_data_quality`** (L131-145). Inconsistencia con `synthesize_at_retest()` que devuelve 23 campos. Si el detector recibe un perfil vacío, el schema no coincide.
  6. **No hay marcado de huecos tras reconexión más allá del epoch.** `mark_reconnection()` incrementa el epoch y `synthesize_at_retest()` marca `PARTIAL` si hay múltiples epochs en la ventana, pero no hay metric de cuántos slots faltan. Un epoch nuevo con buffer lleno de snapshots frescos se reporta como `PARTIAL` aunque los datos sean completos para ese epoch.
  7. **`@trade` en lugar de `@aggTrade`** (WS L92-93, comentario: "global silence/lag on some endpoints"). Decisión operacional no documentada en ADR. Deuda de documentación.
  8. **Spot format normalization hardcoded** (WS L132-143). Si Binance cambia el schema, el normalization falla silenciosamente. No hay test que valide este path.

---

### §3 — Schema de interfaces

#### Entrada pública — constructor (`BinanceWebSocketManager`)
```python
BinanceWebSocketManager(manifest: ComponentManifest, symbols: List[str] = ["btcusdt"])
```
Parámetros efectivos (del código, L37-61):
| Parámetro | Valor | Nota |
|---|---|---|
| `symbols` | `["btcusdt"]` | lowercased en init |
| `market` | `os.environ["CGALPHA_BINANCE_MARKET"]` o `"futures"` | spot/futures |
| `base_url` | `wss://fstream.binance.com/ws` (futures) o `wss://stream.binance.com:9443/ws` (spot) | |
| `l2_buffers` | `Dict[str, L2RingBuffer]` | uno por símbolo, creado en init |
| `_connection_epoch` | `0` | incrementa en cada reconexión |

#### Entrada pública — métodos principales
```python
add_callback(callback: Callable[[Dict], None]) -> None
async start() -> None
async stop() -> None
get_current_obi(symbol: str, levels: int = 10) -> float
get_rolling_delta(symbol: str, window_seconds: float = 300) -> float
```

#### Streams suscritos (L89-93)
- `{symbol}@depth20@100ms`
- `{symbol}@trade`  (no `@aggTrade` — ver issue #7)

#### Salida — `L2RingBuffer.push()` (L20-36)
Campos empujados en cada depth update (~10hz):
```
binance_ts_ms, local_offset_ms, obi_1, obi_5, obi_10, obi_20,
cum_delta, best_bid_size, best_ask_size, bid_depth_10, ask_depth_10,
spread_bps, trade_count, aggressive_buy_vol, aggressive_sell_vol
```

#### Salida — `L2RingBuffer.synthesize_at_retest()` (L38-126)
Devuelve dict con 23 campos:
```
window_seconds, n_snapshots, l2_data_quality,
obi_10_gradient_5s/15s/30s, obi_10_min/max/std_30s,
obi_10_at_minus_5s/15s/30s,
delta_rate_5s/15s/30s, delta_acceleration_5s/15s,
depth_ratio_1_10, depth_ratio_1_10_gradient_5s,
trade_intensity_5s/15s, aggressive_buy_pct_5s/15s
```

#### Tipos de datos relevantes
- `L2RingBuffer` (clase, L5-145): buffer circular con `mark_reconnection`, `push`, `synthesize_at_retest`, `get_raw_buffer`, `_empty_profile`.
- `MicrostructureRecord` (importado de `binance_data`, L19): no usado directamente en WS Manager pero parte del contrato.
- `ComponentManifest` (de `base_component`, L18): manifest del BaseComponentV3.

---

### §4 — Módulos protegidos dentro de este componente

| Función/Método | Razón de protección |
|---|---|
| `L2RingBuffer.synthesize_at_retest()` | Schema de 23 features consumido por Oracle v6 Fase B. Cambios invalidan el dataset de entrenamiento. Modificación requiere nuevo D-ID + ADR + re-entrenamiento. |
| `L2RingBuffer.push()` | Contrato de ingesta. Cambios en los campos empujados rompen `synthesize_at_retest` y el detector aguas abajo. |
| `BinanceWebSocketManager._handle_message()` | Normalization spot/futures + extracción de `binance_ts_ms`. Cambios pueden introducir clock drift silente (Punto Ciego #1). |
| `get_rolling_delta()` | Reemplazó al delta global infinito (Punto Ciego #3). Rolling window es la primitiva causal. No volver a global. |

**Nota:** `binance_websocket_manager.py` NO está en `PROTECTED_MODULES` (Nexus §3, L212-221). Esto es una omisión: el componente es prerrequisito de Oracle Fase B y su modificación puede introducir lookahead bias. **Recomendación: añadir a `PROTECTED_MODULES` en la próxima actualización del Nexus.** No se hace en este CRB (es cambio de gobernanza, no de código).

---

### §5 — Deuda técnica conocida

| Ítem | Origen | Severidad | Nota |
|---|---|---|---|
| Nexus §5.7 desfasado vs. código | Este CRB | Alta | El Nexus reporta 4 issues como pendientes que ya están resueltos en código. Reconciliación requiere actualización del Nexus §5.7 + §4 P3. |
| `synthesize_at_retest()` no invocado directamente por el detector | Este CRB | Alta | La conexión existe vía `LiveDataFeedAdapter._on_retest_detected` (`live_adapter.py` L631-635), no vía `TripleCoincidenceDetector`. El flujo P3→P4→Oracle está cableado. El issue real es la ausencia de tests sobre esta cadena y la falta de caracterización del drift temporal en el retest. |
| 0 tests sobre WS Manager y Ring Buffer | Este CRB | Alta | Puerta de Cobertura Base bloqueante. Sin tests, cualquier cambio es ciego. |
| `last_trades` con `pop(0)` O(n) | Código L173 | Baja | Deuda de performance. Cambiar a `deque(maxlen=10000)`. |
| `_empty_profile()` schema inconsistente | Código L131-145 | Media | 21 ceros vs. 23 campos de `synthesize_at_retest`. Si el detector recibe perfil vacío, el schema no coincide. |
| `@trade` sin ADR | Código L92-93 | Baja | Decisión operacional no documentada. |
| Spot normalization sin test | Código L132-143 | Media | Path no cubierto. |
| `PROTECTED_MODULES` no incluye WS Manager | Nexus §3 | Media | Omisión de gobernanza. |

---

### §6 — Fases de reconstrucción

#### Fase A — Cambios deterministas de bajo riesgo (DESPUÉS de Puerta de Cobertura)

**Prerrequisito absoluto:** Escribir tests para `L2RingBuffer` y `BinanceWebSocketManager` antes de cualquier cambio. Sin esta puerta, la Fase A no inicia.

1. **Test suite para `L2RingBuffer`** (nuevo archivo `tests/test_l2_ring_buffer.py`):
   - `test_push_populates_buffer`
   - `test_max_slots_300`
   - `test_mark_reconnection_changes_epoch`
   - `test_synthesize_at_retest_full_quality`
   - `test_synthesize_at_retest_partial_quality_multi_epoch`
   - `test_synthesize_at_retest_empty_buffer_returns_empty_profile`
   - `test_synthesize_at_retest_min_10_snapshots`
   - `test_empty_profile_schema_matches_synthesize_schema` (valida issue #5)
2. **Test suite para `BinanceWebSocketManager`** (nuevo archivo `tests/test_binance_websocket_manager.py`):
   - `test_get_current_obi_no_state_returns_zero`
   - `test_get_current_obi_multi_level`
   - `test_get_rolling_delta_window_300s`
   - `test_get_rolling_delta_empty_trades_returns_zero`
   - `test_spot_format_normalization` (valida issue #8)
   - `test_binance_ts_ms_extraction_from_E_field`
   - `test_binance_ts_ms_fallback_to_time_time` (valida issue #3)
3. **Fix `_empty_profile()` schema** (issue #5): añadir `n_snapshots: 0` y `l2_data_quality: "EMPTY"` para coincidir con `synthesize_at_retest()`.
4. **Cambiar `last_trades` a `deque(maxlen=10000)`** (issue #4): eliminar `pop(0)`.
5. **Medir y reportar cobertura** una vez resuelto el entorno (o confirmar que no hay bloqueo de numpy en este componente).

#### Fase B — Cambios que requieren nuevos datos o pruebas

1. **Conectar `synthesize_at_retest()` al `TripleCoincidenceDetector`** (issue #2). La conexión ya existe vía `LiveDataFeedAdapter._on_retest_detected` (`live_adapter.py` L631-635). Lo que falta es test de integración que valide la cadena end-to-end. **No se hace en este CRB.** Se documenta como prerrequisito cruzado con P4 (CRB de P4 cubre los tests de `register_retest` que reciben el snapshot con `l2_temporal_profile`).
2. **Estudio forense de Time Drift** (alerta #3 de la deliberación):
   - Medir `local_offset_ms` en producción sobre ≥1000 mensajes.
   - Reportar distribución (min, p50, p95, max).
   - Definir umbral de rechazo: si `|local_offset_ms| > X`, marcar el snapshot como `PARTIAL`.
   - Restricción matemática de acoplamiento: definir la ventana causal permitida. Propuesta: `t_feature ≤ t_candle_close - ε` donde ε es conservador (probablemente 100ms, igual al sample rate). Esto evita que el Oracle entrene con features posteriores al cierre de vela.
3. **Metric de huecos por epoch** (issue #6): en `synthesize_at_retest()`, reportar `n_epochs_in_window` y `slots_missing` además de `l2_data_quality`.
4. **ADR para `@trade` vs `@aggTrade`** (issue #7): documentar la decisión operacional.
5. **Reconciliar Nexus §5.7 + §4 P3 con el código vivo** (issue #1): actualizar el Nexus para reflejar que el Ring Buffer está implementado. Esto es cambio de documentación, no de código.

---

### §7 — Criterios de éxito

P3 se considera "listo" (no "perfecto") cuando:
- Cobertura de tests sobre `L2RingBuffer` ≥ 80% (umbral alto: componente prerrequisito de Oracle Fase B).
- Cobertura de tests sobre `BinanceWebSocketManager` ≥ 50% (umbral pragmático: el componente depende de red y es difícil de mockear completamente).
- `_empty_profile()` schema coincide con `synthesize_at_retest()` schema.
- `last_trades` es `deque`, no `List` con `pop(0)`.
- Estudio forense de Time Drift completado y reportado en ADR.
- Nexus §5.7 + §4 P3 reconciliados con el código vivo.
- **No** se conecta `synthesize_at_retest()` al detector en este CRB (es P5, Cat.3).

---

### §8 — Lo que NO se cambia en esta sesión

- No se modifica `cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py` (es P5, Cat.3).
- No se conecta `synthesize_at_retest()` al detector (es Fase B de P5).
- No se modifica `L2RingBuffer.synthesize_at_retest()` ni `push()` (son protegidos, §4).
- No se toca `live_adapter.py`, `server.py`, ni módulos protegidos.
- No se reabre la decisión de timeframe (cerrada en D-011 + ADR-0006-1).
- No se añade `binance_websocket_manager.py` a `PROTECTED_MODULES` en esta sesión (es cambio de gobernanza, requiere su propia actualización del Nexus).
- No se redacta el ADR de `@trade` vs `@aggTrade` en esta sesión (se agenda para Fase B).
- No se ejecuta código. Este CRB es deliberación arquitectónica (Ruta B).

---

### §9 — Referencias cruzadas

- `documentation/NEXUS_SUPERIOR.md` §2, §3 (D-011), §4 P3, §5.7
- `cgalpha_v4/CRB_TripleCoincidenceDetector_P5.md` (issue #2 de este CRB se resuelve en P5)
- `aipha_memory/identity/ADR-EVO-TICKET-0006-1-live-candle-interval-5m.md` (D-011, timeframe)
- `documentation/EVO_TICKET_LOG.md` — EVO-TICKET-0006
- `cgalpha_v3/infrastructure/binance_websocket_manager.py` (código vivo)
- `cgalpha_v3/infrastructure/l2_ring_buffer.py` (código vivo)

---

### §10 — Cognitive Portability Check (adaptación de D-010 para CRBs)

1. **¿Un modelo menos capaz puede continuar desde aquí sin reconstruir el contexto de esta sesión?**
   SÍ — este CRB contiene el propósito, interfaces, deuda y límites de P3 en un solo lugar, anclado en código vivo (no en descripciones).

2. **¿El CRB es auto-explicativo sin el historial de la deliberación arquitectónica (Ruta B)?**
   PARCIALMENTE — las referencias cruzadas apuntan al Nexus y al ADR-0006 donde está el contexto del timeframe. Un modelo futuro debe leer esos archivos para entender el porqué de las restricciones temporales. La sección §6 Fase B punto 2 (estudio forense de Time Drift) requiere conocer la alerta #3 de la deliberación para entender el motivo del umbral de rechazo.

3. **¿Hay decisiones implícitas que deberían convertirse en ADR antes de la Fase A de reconstrucción?**
   SÍ — tres:
   - (a) La constatación de que el Ring Buffer ya está implementado y el Nexus está desfasado. Esto debería ser un ADR de reconciliación antes de tocar el Nexus.
   - (b) La restricción matemática de acoplamiento temporal (`t_feature ≤ t_candle_close - ε`) debería ser un nuevo D-ID (probablemente D-014) antes de la Fase B.
   - (c) La omisión de `binance_websocket_manager.py` en `PROTECTED_MODULES` debería resolverse en una actualización de gobernanza del Nexus.

---

### §11 — Hallazgo crítico para la deliberación arquitectónica

Este CRB revela que **el supuesto bloqueo de P3 ("Ring Buffer pendiente") es falso**. El código vivo ya implementa el buffer, el push, la mitigación de clock drift, el CumDelta rolling y el marcado de reconexión. El verdadero bloqueo de P3 es:

1. **Cobertura cero** (Puerta de Cobertura Base bloqueante — alerta #2 de la deliberación).
2. **Cadena P3→P4→Oracle sin tests** (`live_adapter._on_retest_detected` invoca `synthesize_at_retest()` y popula `l2_temporal_profile`, pero no hay tests que validen esta cadena end-to-end).
3. **Time drift no caracterizado** (alerta #3 de la deliberación — riesgo de lookahead bias).

La re-jerarquización propuesta en la deliberación debe revisarse a la luz de este hallazgo: P3 no requiere "implementar el Ring Buffer" sino "auditarlo, cubrirlo de tests, caracterizar su drift temporal, y documentar la cadena cableada en `live_adapter.py`". La conexión al detector ya existe; lo que falta es evidencia de que funciona correctamente.
