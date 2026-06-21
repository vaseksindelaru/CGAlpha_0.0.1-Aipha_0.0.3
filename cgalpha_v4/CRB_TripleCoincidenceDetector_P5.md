# CRB — TripleCoincidenceDetector (P5)

## cgAlpha_0.0.1 — Component Reconstruction Brief

```
COMPONENTE    : P5 — TripleCoincidenceDetector
UBICACIÓN     : cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py
LÍNEAS        : 1807
ESTADO        : ✅ ESTABLE — PROTEGIDO (Cat.3 obligatorio para cambios)
CRB CREADO    : 2026-06-21
```

---

### §1 — Propósito y lugar en el sistema

Detecta zonas de soporte/resistencia usando tres confluencias (vela clave + zona de acumulación + mini-trend). Monitorea retests y captura features en el momento exacto del toque. Entrega zone_geometry y training_samples al Oracle vía `DeferredOutcomeMonitor`.

Fragmento del grafo de dependencias (Nexus §2):
```
[Binance WS] → [TripleCoincidence] → [DeferredOutcomeMonitor] → [Oracle]
                    ↓
              [BWS L2 Ring Buffer]
```

---

### §2 — Estado actual

- **Cobertura de tests:** [NO MEDIDA AÚN — error de entorno al ejecutar `pytest --cov` sobre `test_signal_detector_integration.py`: `ImportError: cannot load module more than once per process` en numpy. Requiere sesión de entorno separada.]
- **Tests pasando:** [NO VERIFICABLE — mismo error de entorno.]
- **Issues conocidos:**
  1. `zone_max_distance_atr=5.0` es PROVISIONAL (intuición, no percentiles) — EVO-TICKET-0005.
  2. `_cleanup_expired_zones` usaba `candle_index` inestable entre reinicios — corregido a tiempo+distancia ATR en EVO-TICKET-0005 / ADR-0005-1.
  3. `warm_start` no reproducía detección histórica — corregido en EVO-TICKET-0005.
  4. `feed_kline_for_zone_detection` recalculaba ZigZag por vela — corregido a precálculo en EVO-TICKET-0005.
  5. Fallbacks de timestamp `candle["index"] * 300000` y `idx * 300000` asumen 5m sin documentar — detectado en EVO-TICKET-0006.
  6. `zigzag_threshold=0.0018` hardcoded — calibrado para 5m, no adaptable sin recalibración.
  7. PC#7 (single clock source dependency) no añadido formalmente a `architectural_analysis.md` — identificado en EVO-TICKET-0003.
  8. No recibe Ring Buffer de 30s todavía — prerequisito P3.

---

### §3 — Schema de interfaces

#### Entrada pública — constructor
```python
TripleCoincidenceDetector(config: Dict = None)
```
Parámetros por defecto (del código, L741-768):
| Parámetro | Valor | Nota |
|---|---|---|
| `volume_percentile_threshold` | 70 | KeyCandleDetector |
| `body_percentage_threshold` | 40 | KeyCandleDetector |
| `lookback_candles` | 30 | unidades de velas de 5m (post-EVO-0006) |
| `atr_period` | 14 | |
| `atr_multiplier` | 1.5 | |
| `volume_threshold` | 1.2 | |
| `min_zone_bars` | 5 | |
| `quality_threshold` | 0.45 | AccumulationZoneDetector |
| `r2_min` | 0.45 | MiniTrendDetector |
| `min_trend_length` | 5 | MiniTrendDetector |
| `zigzag_threshold` | 0.0018 | D-001, P75 rango 5m BTCUSDT |
| `proximity_tolerance` | 8 | |
| `retest_timeout_bars` | 50 | unidades de velas de 5m |
| `outcome_lookahead_bars` | 10 | D-002 |
| `breakout_confirm_atr_buffer` | 0.03 | |
| `volume_z_threshold` | 0.5 | |
| `min_clearance_atr` | 1.0 | |
| `retest_proximity_pct` | 0.001 | 0.1% del precio |
| `zone_max_distance_atr` | 5.0 | PROVISIONAL, calibration_pending |
| `state_path` | `"aipha_memory/operational/detector_state.json"` | |
| `market` | `"futures"` | |

#### Entrada pública — métodos principales
```python
seed_history(df: pd.DataFrame) -> None
process_live_tick(new_kline: Dict, micro_data: Dict) -> List[RetestEvent]
feed_kline_for_zone_detection(kline: dict, micro_data: dict) -> None
check_intra_candle_retest(price: float, timestamp_ms: int, debounce_ms: int = 5000) -> list
save_state() -> None
load_state() -> None
```

#### Salidas
- `List[ActiveZone]` en `self.active_zones`
- `List[RetestEvent]` desde `process_live_tick()` y `check_intra_candle_retest()`
- `List[TrainingSample]` en `self.training_samples`
- JSON en `aipha_memory/operational/detector_state.json`

#### Tipos de datos relevantes
- `ActiveZone` (dataclass, L66-180): zona activa con lifecycle_state, touch_history, polarity flip.
- `RetestEvent` (dataclass, L182-200): evento de retest con features L2.
- `TrainingSample` (dataclass, L202-214): sample para Oracle.
- `TripleSignal` (dataclass, L717-730): señal interna de triple coincidencia.

---

### §4 — Módulos protegidos dentro de este componente

| Función/Método | Razón de protección |
|---|---|
| `_determine_outcome()` | Lógica de etiquetado con `zone_top`/`zone_bottom` corregida en BUG-5; cambios invalidan el dataset de entrenamiento. |
| `_check_retest()` | Captura features en el momento exacto del retest; cambios alteran la distribución de features del Oracle. |
| `compute_adaptive_zigzag_threshold()` | Pertenece conceptualmente a `MiniTrendDetector` (PROTECTED_FUNCTIONS en Nexus §3); no mover aquí. |
| `_encode_categoricals()` | No existe en este componente; no añadir — pertenece al Oracle v6 (D-012). |

---

### §5 — Deuda técnica conocida

| Ítem | Origen | Severidad | Nota |
|---|---|---|---|
| `zone_max_distance_atr=5.0` PROVISIONAL | EVO-TICKET-0005 | Media | calibration_pending. Requiere percentile analysis de distancias reales zona expirada vs activa sobre ≥200 ciclos de detección. |
| Fallbacks `* 300000` hardcoded | EVO-TICKET-0006 | Baja | Asumen 5m. Ahora consistente con D-011, pero no parametrizados. |
| `zigzag_threshold=0.0018` hardcoded | D-001 | Media | Calibrado para 5m. Hacerlo adaptativo requiere recalibración y nuevo ADR. |
| PC#7 no añadido a `architectural_analysis.md` | EVO-TICKET-0003 | Baja | Documentado en ADR-0003-1; falta migrar a architectural_analysis.md. |
| Cobertura de tests no medida | Este CRB | Media | Bloqueado por error de entorno numpy. Requiere sesión de entorno. |
| No recibe Ring Buffer de 30s | Nexus §5.3 | Media | Prerequisito P3. Hasta entonces, micro_data viene de live_adapter. |
| `process_live_tick()` vs `feed_kline_for_zone_detection()` duplican lógica de buffer | EVO-TICKET-0005 | Baja | `process_live_tick` mantiene buffer interno; `feed_kline_for_zone_detection` es el path usado por live_adapter post-refactor. |

---

### §6 — Fases de reconstrucción

#### Fase A — Cambios deterministas de bajo riesgo
1. Extraer constantes hardcoded (`300000`, `0.0018` si se decide) a parámetros nombrados con defaults.
2. Añadir logging estructurado de detecciones/retests (observabilidad).
3. Medir y reportar cobertura de tests una vez resuelto el entorno.
4. Añadir PC#7 formalmente a `architectural_analysis.md` (sesión separada, documentación base).

#### Fase B — Cambios que requieren nuevos datos o pruebas
1. Calibrar `zone_max_distance_atr` con percentiles reales (nuevo EVO-TICKET).
2. Evaluar `zigzag_threshold` adaptativo (depende de recalibración 5m).
3. Integrar Ring Buffer de 30s cuando P3 esté listo.

---

### §7 — Criterios de éxito

P5 se considera "listo" (no "perfecto") cuando:
- Cobertura de tests medible y >70% (umbral pragmático dado el acoplamiento con WS).
- 0 constantes hardcoded sin nombre en el código de producción.
- `zone_max_distance_atr` calibrado con datos reales o con plan explícito de calibración.
- PC#7 añadido a `architectural_analysis.md`.
- Interfaces documentadas en este CRB mantenidas al día tras cada cambio.

---

### §8 — Lo que NO se cambia en esta sesión

- No se modifica `cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py`.
- No se calibra `zone_max_distance_atr`.
- No se reescribe ninguna función del detector.
- No se crean tests nuevos.
- No se toca `live_adapter.py`, `server.py`, ni módulos protegidos.
- No se reabre la decisión de timeframe (ya cerrada en D-011 + ADR-0006-1).
- No se añade PC#7 a `architectural_analysis.md` en esta sesión (documentación base, sesión separada).

---

### §9 — Referencias cruzadas

- `documentation/NEXUS_SUPERIOR.md` §2, §3 (D-001, D-002, D-011), §5.3
- `documentation/architectural_analysis.md` PC#1-#6
- `aipha_memory/identity/ADR-EVO-TICKET-0005-1-cleanup-por-tiempo-distancia.md`
- `aipha_memory/identity/ADR-EVO-TICKET-0006-1-live-candle-interval-5m.md`
- `documentation/EVO_TICKET_LOG.md` — EVO-TICKET-0005, EVO-TICKET-0006

---

### §10 — Cognitive Portability Check (adaptación de D-010 para CRBs)

1. **¿Un modelo menos capaz puede continuar desde aquí sin reconstruir el contexto de esta sesión?**  
   SÍ — este CRB contiene el propósito, interfaces, deuda y límites de P5 en un solo lugar.

2. **¿El CRB es auto-explicativo sin el historial de EVO-TICKET-0005/0006?**  
   PARCIALMENTE — las referencias cruzadas apuntan a los tickets y ADRs donde está el diagnóstico completo. Un modelo futuro debe leer esos archivos para entender el porqué de cada ítem de deuda.

3. **¿Hay decisiones implícitas que deberían convertirse en ADR antes de la Fase A de reconstrucción?**  
   SÍ — la suposición de que `lookback_candles=30` y `retest_timeout_bars=50` están en unidades de 5m es implícita y debería validarse/confirmarse en un ADR si se convierte en verdad inmutable.
