# CRB — DeferredOutcomeMonitor (P4)

## cgAlpha_0.0.1 — Component Reconstruction Brief

```
COMPONENTE    : P4 — DeferredOutcomeMonitor
UBICACIÓN     : cgalpha_v3/domain/deferred_outcome_monitor.py
LÍNEAS        : 488
ESTADO        : 🟡 OPERATIVO — PROTEGIDO (Cat.3 obligatorio)
                Fase Bridge ya implementada en código
                (Nexus §5.4 desfasado: reporta "PENDIENTE FASE BRIDGE"
                 pero etiquetado terciario + lookahead adaptativo + Shadow
                 Harvesting ya existen)
CRB CREADO    : 2026-06-23
AUTOR         : Modelo operador (Ruta B — deliberación arquitectónica)
```

---

### §1 — Propósito y lugar en el sistema

Asigna labels diferidos a los retests capturados por `TripleCoincidenceDetector`. Espera `lookahead_bars` (adaptativo al ancho de la zona en ATRs) antes de clasificar. Produce `BOUNCE_STRONG` / `BOUNCE_WEAK` / `BREAKOUT` / `INCONCLUSIVE`. Persiste samples resueltos en `training_dataset_v2.jsonl` con el snapshot completo + `l2_temporal_profile` + `touch_context` (Shadow Harvesting).

Fragmento del grafo de dependencias (Nexus §2):
```
[TripleCoincidence] → [DeferredOutcomeMonitor] → [Oracle]
                         │
                   labels │
                          ▼
                        [Oracle] ←─ zone_geometry
```

**Por qué es prerrequisito de Oracle Fase B:** La calidad de los labels determina directamente la calidad del modelo. Si el etiquetado contamina el dataset (lookahead bias, fricción económica ignorada, deduplicación rota), el Oracle aprende con datos defectuosos y ninguna cantidad de features dinámicas lo rescata. P4 es el componente donde la alerta #4 (etiquetado teórico vs fricción real) y la alerta #3 (time-leakage) convergen.

---

### §2 — Estado actual

- **Cobertura de tests:** [PARCIAL — existen tests pero no se ha medido cobertura con `pytest --cov`.]
- **Tests existentes** (verificados por `find_path`):
  - `tests/test_dataset_deduplication.py` — 1 test (`test_deduplication_integrity`): valida la Triple Barrera (fingerprint causal, dataset persistido, cola pending).
  - `tests/test_spatial_multitouch.py` — 3 tests: `test_spatial_multitouch_blocks_duplicates`, `test_different_events_are_not_blocked`, `test_fingerprint_survives_restart`. Validan B-008 v2 (huella causal sin `zone_direction`).
  - `test_hits3.py` (en raíz, no en `tests/`) — script ad-hoc que ejerce `register_retest` con `touch_sequence`, `polarity_flipped`, `prior_touch_outcomes`. No es un test formal de pytest.
- **Tests pasando:** [NO VERIFICADO en esta sesión — no se ejecutó pytest.]
- **Issues conocidos:**
  1. **Nexus §5.4 desfasado vs. código vivo.** El Nexus reporta issues #1-#3 como pendientes, pero el código ya implementa: (a) etiquetado terciario `BOUNCE_STRONG`/`BOUNCE_WEAK`/`BREAKOUT`/`INCONCLUSIVE` (L337-376), (b) `adaptive_lookahead` con `max(5, min(20, int(5 + zone_width_atr*3)))` (L34-43), (c) deduplicación por huella causal sin `zone_direction` (L92-101, B-008 v2 ✅), (d) Shadow Harvesting con `touch_sequence`/`polarity_flipped`/`prior_touch_outcomes`/`hours_since_flip` (L66-71, L206-222, L406-419). El CRB debe reconciliar esta divergencia.
  2. **Fricción económica ausente (alerta #4 de la deliberación).** El etiquetado es teóricamente puro: `BOUNCE_STRONG` si `price > zone_top + 0.5*atr`, `BREAKOUT` si `price < zone_bottom`, sin considerar slippage, costo de transacción, latencia de ejecución, o impacto del libro de órdenes. El Oracle puede aprender a predecir etiquetas perfectas que son inoperables en `ShadowTrader` (P9). **Este es el verdadero bloqueo de P4 para Oracle Fase B, no la implementación del etiquetado.**
  3. **`adaptive_lookahead` docstring desfasado.** L37 dice "Retorna número de barras de 5min (o 1min live)". Pero D-011 + ADR-0006-1 fijaron `interval_s=300` (5m) como verdad inmutable. La mención a "1min live" es deuda documental post-EVO-0006.
  4. **`_evaluate` no tiene test directo.** Los tests existentes cubren `register_retest` (dedup) pero no `_evaluate` (la lógica que asigna `BOUNCE_STRONG`/`BOUNCE_WEAK`/`BREAKOUT`/`INCONCLUSIVE`). La Puerta de Cobertura Base no está completa para la función más crítica del componente.
  5. **`tick` no tiene test directo.** La actualización de MFE/MAE, el incremento de `bars_elapsed` en `bar_closed`, y el flush de resueltos no están cubiertos.
  6. **`_flush_resolved` no tiene test directo.** La inyección de `outcome` + `touch_context` en el snapshot, y la escritura en `training_dataset_v2.jsonl` no están cubiertos. Si el schema de flush cambia, los scripts `prepare_oracle_ab_sets.py` y `train_oracle_ab.py` se rompen silenciosamente.
  7. **`_load_pending` no valida schema.** L476-483 hace `PendingLabel(**item)` con `setdefault` para campos nuevos, pero si el JSON en disco tiene un campo no esperado, `PendingLabel(**item)` falla con `TypeError`. El `except (json.JSONDecodeError, TypeError)` en L487 lo captura pero solo loggea un warning — los pending se pierden.
  8. **`_persist_pending` serializa `prior_touch_outcomes` con `dataclasses.asdict` condicional** (L453). Si un elemento no es dataclass, se serializa tal cual. Si es dataclass, se serializa como dict. En `_load_pending`, no se reconstruyen los dataclasses — quedan como dicts. Asimetría serialización/deserialización.
  9. **`capture_ts` se calcula de `meta.get("capture_ts_unix_ms", time.time()*1000) / 1000.0`** (L208). Si el snapshot no trae `capture_ts_unix_ms`, se usa `time.time()` (wall clock local). Esto es coherente con el issue #3 del CRB de P3 (clock drift). Si el snapshot viene de `live_adapter.py` L672 (`"capture_ts_unix_ms": timestamp_ms`), está bien. Pero si viene de otro path, hay drift.
  10. **`hours_since_flip` se calcula con `time.time() - flip_ts`** (L204). Usa wall clock local, no `binance_ts_ms`. Inconsistencia con la mitigación de drift del CRB de P3.
  11. **`rebound/` contiene patches aplicados** (`patch_deferred_monitor_multitouch.py`, `patch_live_adapter_multitouch.py`, `patch_zone_lifecycle.py`) que introdujeron Shadow Harvesting. No está documentado en ADR si estos patches se aplicaron manualmente o vía CodeCraftSage. Deuda de gobernanza.

---

### §3 — Schema de interfaces

#### Entrada pública — constructor
```python
DeferredOutcomeMonitor()
```
Sin parámetros. Las rutas de persistencia son constantes de módulo (L29-31):
| Constante | Valor | Nota |
|---|---|---|
| `PENDING_LABELS_PATH` | `aipha_memory/operational/pending_labels.json` | |
| `COMPLETED_SAMPLES_PATH` | `aipha_memory/operational/training_dataset_v2.jsonl` | Consumido por `prepare_oracle_ab_sets.py`, `train_oracle_ab.py`, `monitor_set_a_readiness.py`, `generate_harvest_report.py` |
| `RAW_BUFFERS_DIR` | `aipha_memory/raw_buffers` | Raw L2 buffer comprimido por retest |

#### Entrada pública — métodos principales
```python
register_retest(
    snapshot: dict,
    raw_buffer: Optional[list] = None,
    touch_sequence: int = 1,
    polarity_flipped: bool = False,
    prior_touch_outcomes: list = None,
    zone_original_direction: str = "",
    flip_ts: float = None,
) -> str
tick(current_price: float, bar_closed: bool = False) -> List[dict]
get_pending_count() -> int
get_resolved_count() -> int
get_pending_summary() -> List[dict]
```

#### Salida — `register_retest` devuelve `sample_id: str`
Efectos secundarios:
- Escribe snapshot completo en `aipha_memory/snapshots/{sample_id}.json`
- Escribe raw L2 buffer comprimido en `aipha_memory/raw_buffers/{sample_id}.json.gz` (si `raw_buffer` no es None)
- Añade `PendingLabel` a `self.pending`
- Persiste `pending_labels.json`

#### Salida — `tick` devuelve `List[dict]` con samples resueltos
Cada dict: `{sample_id, outcome, mfe, mae, bars_elapsed}`
Efectos secundarios:
- Actualiza MFE/MAE en cada tick
- Incrementa `bars_elapsed` si `bar_closed=True`
- Si resuelto: inyecta `outcome` + `touch_context` en el snapshot y lo appenda a `training_dataset_v2.jsonl`

#### Salida — schema del sample persistido en `training_dataset_v2.jsonl`
```
_meta: {schema_version, capture_ts_utc, capture_ts_unix_ms, symbol, sample_id, pipeline_version}
zone_geometry: {zone_id, direction, zone_top, zone_bottom, zone_width_abs, zone_width_atr, ...}
clearance: {atr_at_detection, max_clearance_price, max_clearance_atr, seconds_since_detection}
l2_snapshot_at_touch: {retest_price, obi_1, obi_5, obi_10, obi_20, cumulative_delta, ...}
l2_temporal_profile: {window_seconds, n_snapshots, l2_data_quality, obi_10_gradient_*, ...}  # 23 campos del Ring Buffer
market_context: {atr_14_current, regime, session, hour_utc}
outcome: {label, mfe, mae, mfe_atr, mae_atr, bars_to_resolution, resolution_ts, lookahead_bars_used}
touch_context: {touch_sequence, polarity_flipped, zone_original_direction, effective_direction, prior_touch_outcomes, hours_since_flip, is_secondary_retest, is_tertiary_retest}
```

#### Tipos de datos relevantes
- `PendingLabel` (dataclass, L47-71): sample pendiente con MFE/MAE, lookahead, y campos de Shadow Harvesting.
- `adaptive_lookahead` (función, L34-43): `max(5, min(20, int(5 + zone_width_atr*3)))`.

---

### §4 — Módulos protegidos dentro de este componente

| Función/Método | Razón de protección |
|---|---|
| `_evaluate()` | Lógica de etiquetado. Cambios invalidan el dataset de entrenamiento. Modificación requiere nuevo D-ID + ADR + re-entrenamiento. |
| `adaptive_lookahead()` | PROTECTED_FUNCTIONS en Nexus §3. Pertenece a este componente. Cambios alteran la ventana causal del label. |
| `_causal_fingerprint()` | B-008 v2 ✅. Sin `zone_direction`. Cambios rompen la deduplicación y permiten duplicados en el dataset. |
| `register_retest()` | Contrato de ingesta. Cambios en los campos persistidos rompen `prepare_oracle_ab_sets.py` y `train_oracle_ab.py`. |
| `_flush_resolved()` | Schema de `outcome` + `touch_context` consumido por Oracle v6. Cambios invalidan el dataset. |

**Nota:** `deferred_outcome_monitor.py` SÍ está en `PROTECTED_MODULES` (Nexus §3, L218). Confirmado.

---

### §5 — Deuda técnica conocida

| Ítem | Origen | Severidad | Nota |
|---|---|---|---|
| Nexus §5.4 desfasado vs. código | Este CRB | Alta | El Nexus reporta 3 issues como pendientes que ya están resueltos. Reconciliación requiere actualización del Nexus §5.4 + §4 P4. |
| Fricción económica ausente | Alerta #4 deliberación | Alta | El verdadero bloqueo de P4 para Oracle Fase B. El etiquetado es teóricamente puro. Resolución requiere decisión de diseño (¿asimilar primitivas económicas de P9 en el label, o en un post-procesador?). Probablemente nuevo D-ID. |
| `_evaluate` sin test directo | Este CRB | Alta | La función más crítica del componente no está cubierta por tests. Puerta de Cobertura Base incompleta. |
| `tick` sin test directo | Este CRB | Alta | MFE/MAE, bars_elapsed, flush no cubiertos. |
| `_flush_resolved` sin test directo | Este CRB | Alta | Schema de `outcome` + `touch_context` no cubierto. Si cambia, los scripts aguas abajo se rompen. |
| `adaptive_lookahead` docstring desfasado | Código L37 | Baja | Mención a "1min live" post-EVO-0006. |
| `_load_pending` no valida schema | Código L476-483 | Media | `PendingLabel(**item)` puede fallar con TypeError. Los pending se pierden silenciosamente. |
| Asimetría serialización `prior_touch_outcomes` | Código L453, L476-483 | Media | `asdict` condicional en persist, no reconstruido en load. |
| `hours_since_flip` con `time.time()` | Código L204 | Media | Inconsistencia con mitigación de drift del CRB de P3. |
| `rebound/` patches sin ADR | `rebound/` | Baja | Shadow Harvesting introducido por patches. Deuda de gobernanza. |
| `test_hits3.py` en raíz, no en `tests/` | `test_hits3.py` | Baja | Script ad-hoc, no test formal. Debería migrarse o eliminarse. |

---

### §6 — Fases de reconstrucción

#### Fase A — Cambios deterministas de bajo riesgo (DESPUÉS de Puerta de Cobertura)

**Prerrequisito absoluto:** Completar la Puerta de Cobertura Base midiendo cobertura con `pytest --cov` sobre los tests existentes, y añadir tests para `_evaluate`, `tick`, `_flush_resolved` antes de cualquier cambio de comportamiento.

1. **Medir cobertura actual** con `pytest --cov=cgalpha_v3.domain.deferred_outcome_monitor tests/test_dataset_deduplication.py tests/test_spatial_multitouch.py`. Reportar el número. Si hay bloqueo de entorno (numpy ImportError visto en CRB de P5), documentarlo y agendar sesión de entorno.
2. **Test suite para `_evaluate`** (nuevos tests en `tests/test_deferred_outcome_evaluate.py`):
   - `test_evaluate_bullish_breakout_price_below_zone_bottom`
   - `test_evaluate_bullish_bounce_strong_price_above_zone_top_plus_half_atr`
   - `test_evaluate_bullish_bounce_weak_lookahead_expired_mfe_above_threshold`
   - `test_evaluate_bullish_inconclusive_lookahead_expired_mfe_below_threshold`
   - `test_evaluate_bearish_breakout_price_above_zone_top`
   - `test_evaluate_bearish_bounce_strong_price_below_zone_bottom_minus_half_atr`
   - `test_evaluate_bearish_bounce_weak_lookahead_expired`
   - `test_evaluate_bearish_inconclusive_lookahead_expired`
   - `test_evaluate_returns_none_when_not_resolved`
   - `test_evaluate_atr_fallback_to_0.1_percent_of_price`
3. **Test suite para `tick`** (en `tests/test_deferred_outcome_tick.py`):
   - `test_tick_updates_mfe_bullish`
   - `test_tick_updates_mae_bullish`
   - `test_tick_updates_mfe_bearish`
   - `test_tick_updates_mae_bearish`
   - `test_tick_increments_bars_elapsed_on_bar_closed`
   - `test_tick_does_not_increment_bars_elapsed_without_bar_closed`
   - `test_tick_resolves_and_flushes`
   - `test_tick_removes_resolved_from_pending`
4. **Test suite para `_flush_resolved`** (en `tests/test_deferred_outcome_flush.py`):
   - `test_flush_writes_outcome_with_label_mfe_mae_mfe_atr_mae_atr`
   - `test_flush_writes_touch_context_with_all_fields`
   - `test_flush_appends_to_completed_samples_path`
   - `test_flush_skips_missing_snapshot_file`
5. **Fix docstring de `adaptive_lookahead`** (issue #3): eliminar mención a "1min live", citar D-011.
6. **Fix `hours_since_flip`** (issue #10): usar `binance_ts_ms` si está disponible en el snapshot, no `time.time()`. Requiere coordinación con CRB de P3 (issue #3).

#### Fase B — Cambios que requieren nuevos datos o pruebas

1. **Fricción económica (alerta #4 de la deliberación).** Esta es la decisión de diseño central de P4. Dos opciones:
   - **Opción A — Asimilar primitivas económicas en el label.** Modificar `_evaluate` para penalizar el umbral de acierto con slippage, costo, y latencia estimados. `BOUNCE_STRONG` requeriría `price > zone_top + 0.5*atr + slippage_est + cost`. Esto cambia la semántica del label y requiere nuevo D-ID (probablemente D-014) + ADR + re-entrenamiento.
   - **Opción B — Post-procesador económico.** Mantener el etiquetado teóricamente puro, pero añadir un componente entre `DeferredOutcomeMonitor` y `Oracle` que ajusta el peso de cada sample por su fricción estimada. El Oracle entrena con labels puros pero con sample weights económicos.
   - **Opción C — Integrar en ShadowTrader (P9).** Mantener el etiquetado puro, y dejar que ShadowTrader evalúe la operabilidad de cada predicción en tiempo real. El Oracle aprende etiquetas teóricas; ShadowTrader decide si son operables.
   - **Recomendación:** Discutir las tres opciones en un ADR antes de la Fase B. La decisión afecta a P4, P9, y al contrato del Oracle. No se decide en este CRB.
2. **Restricción matemática de acoplamiento temporal (alerta #3 de la deliberación, cruce con CRB de P3).** El `capture_ts` del snapshot (L208) y el `bars_elapsed` del `tick` (L276) deben usar el mismo reloj que el Ring Buffer. Si el Ring Buffer usa `binance_ts_ms` (CRB de P3 §6 Fase B punto 2), entonces `capture_ts` y `bars_elapsed` deben derivar de `binance_ts_ms`, no de `time.time()`. Esto evita lookahead bias. Requiere coordinación con CRB de P3.
3. **Validación de schema en `_load_pending`** (issue #7): filtrar campos no esperados antes de `PendingLabel(**item)`, o usar un constructor explícito.
4. **Simetría serialización `prior_touch_outcomes`** (issue #8): reconstruir dataclasses en `_load_pending` o serializar siempre como dicts.
5. **Reconciliar Nexus §5.4 + §4 P4 con el código vivo** (issue #1): actualizar el Nexus para reflejar que el etiquetado terciario, el lookahead adaptativo, y el Shadow Harvesting están implementados.
6. **ADR para `rebound/` patches** (issue #11): documentar la introducción de Shadow Harvesting.

---

### §7 — Criterios de éxito

P4 se considera "listo" (no "perfecto") cuando:
- Cobertura de tests sobre `_evaluate` ≥ 90% (umbral alto: es la lógica de etiquetado, el corazón del componente).
- Cobertura de tests sobre `tick` ≥ 80%.
- Cobertura de tests sobre `_flush_resolved` ≥ 80%.
- Cobertura total sobre `deferred_outcome_monitor.py` ≥ 70%.
- Docstring de `adaptive_lookahead` reconciliado con D-011.
- `hours_since_flip` usa `binance_ts_ms` si está disponible.
- ADR de fricción económica redactado (Opción A, B, o C) — no necesariamente implementado.
- ADR de acoplamiento temporal redactado (cruce con CRB de P3).
- Nexus §5.4 + §4 P4 reconciliados con el código vivo.

---

### §8 — Lo que NO se cambia en esta sesión

- No se modifica `_evaluate` (es protegido, §4). La fricción económica se decide en ADR, no se implementa.
- No se modifica `adaptive_lookahead` (es protegido, §4). Solo se fix el docstring.
- No se modifica `_causal_fingerprint` (B-008 v2 ✅).
- No se modifica `register_retest` (contrato de ingesta).
- No se modifica `_flush_resolved` (schema consumido por Oracle v6).
- No se decide la Opción A/B/C de fricción económica (requiere ADR).
- No se toca `live_adapter.py`, `server.py`, ni módulos protegidos.
- No se ejecuta código. Este CRB es deliberación arquitectónica (Ruta B).

---

### §9 — Referencias cruzadas

- `documentation/NEXUS_SUPERIOR.md` §2, §3 (D-002, D-005, D-011), §4 P4, §5.4
- `cgalpha_v4/CRB_BinanceWebSocketManager_P3.md` (issue #3 de este CRB se cruza con issue #3 del CRB de P3 — acoplamiento temporal)
- `cgalpha_v4/CRB_TripleCoincidenceDetector_P5.md` (P4 recibe samples del detector vía `live_adapter.py`)
- `aipha_memory/identity/ADR-EVO-TICKET-0006-1-live-candle-interval-5m.md` (D-011, timeframe)
- `documentation/EVO_TICKET_LOG.md` — EVO-TICKET-0002 (P4 es prerrequisito de Oracle Fase B)
- `cgalpha_v3/domain/deferred_outcome_monitor.py` (código vivo)
- `cgalpha_v3/tests/test_dataset_deduplication.py`, `cgalpha_v3/tests/test_spatial_multitouch.py` (tests existentes)
- `cgalpha_v3/scripts/prepare_oracle_ab_sets.py`, `train_oracle_ab.py`, `monitor_set_a_readiness.py`, `generate_harvest_report.py` (consumidores del dataset)
- `rebound/patch_deferred_monitor_multitouch.py`, `patch_live_adapter_multitouch.py`, `patch_zone_lifecycle.py` (patches de Shadow Harvesting)

---

### §10 — Cognitive Portability Check (adaptación de D-010 para CRBs)

1. **¿Un modelo menos capaz puede continuar desde aquí sin reconstruir el contexto de esta sesión?**
   SÍ — este CRB contiene el propósito, interfaces, deuda y límites de P4 en un solo lugar, anclado en código vivo y tests reales.

2. **¿El CRB es auto-explicativo sin el historial de la deliberación arquitectónica (Ruta B)?**
   PARCIALMENTE — las referencias cruzadas apuntan al Nexus, al ADR-0006, y al CRB de P3. Un modelo futuro debe leer esos archivos para entender el porqué de las restricciones temporales y la fricción económica. La sección §6 Fase B punto 1 (fricción económica) requiere conocer la alerta #4 de la deliberación para entender el motivo de las tres opciones.

3. **¿Hay decisiones implícitas que deberían convertirse en ADR antes de la Fase A de reconstrucción?**
   SÍ — cuatro:
   - (a) La constatación de que el etiquetado terciario, el lookahead adaptativo, y el Shadow Harvesting ya están implementados y el Nexus está desfasado. ADR de reconciliación.
   - (b) La decisión sobre fricción económica (Opción A/B/C). ADR nuevo, probablemente D-014.
   - (c) La restricción matemática de acoplamiento temporal (`t_feature ≤ t_candle_close - ε`). Nuevo D-ID, cruce con CRB de P3.
   - (d) La omisión de tests para `_evaluate`/`tick`/`_flush_resolved` debe resolverse antes de la Fase A (Puerta de Cobertura Base).

---

### §11 — Hallazgo crítico para la deliberación arquitectónica

Este CRB revela que **el supuesto bloqueo de P4 ("Fase Bridge pendiente") es falso**. El código vivo ya implementa el etiquetado terciario, el lookahead adaptativo, la deduplicación por huella causal (B-008 v2), y el Shadow Harvesting con `touch_sequence`/`polarity_flipped`. El verdadero bloqueo de P4 para Oracle Fase B es:

1. **Fricción económica ausente** (alerta #4 de la deliberación). El etiquetado es teóricamente puro. El Oracle puede aprender a predecir etiquetas perfectas que son inoperables en ShadowTrader. Esta es la decisión de diseño central de P4, no una implementación.
2. **Cobertura incompleta** (alerta #2 de la deliberación). Existen tests para dedup, pero no para `_evaluate`/`tick`/`_flush_resolved`. La Puerta de Cobertura Base está parcialmente abierta, pero no lo suficiente para aprobar un cambio de comportamiento.
3. **Acoplamiento temporal no resuelto** (alerta #3 de la deliberación, cruce con CRB de P3). `capture_ts` y `bars_elapsed` usan `time.time()` en algunos paths. Si el Ring Buffer se sincroniza con `binance_ts_ms` (CRB de P3), P4 debe hacer lo mismo.

La re-jerarquización propuesta en la deliberación debe revisarse a la luz de este hallazgo: P4 no requiere "implementar la Fase Bridge" sino "decidir la fricción económica (ADR), completar la cobertura de tests, y sincronizar el reloj con el CRB de P3".
