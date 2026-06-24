# ADR-ORACLE-FASE-B-1 — Schema de Features Dinámicas del Oracle v6 Fase B

## Estatus
ACEPTADO e IMPLEMENTADO (2026-06-24).

Aprobado por el operador. 12 features dinámicas del `l2_temporal_profile` seleccionadas para integración en el Oracle v6 Fase B. Implementación en `OracleTrainer_v3` y `OracleRegressor_MAE`.

## Contexto

El Oracle v6 Fase A (EVO-TICKET-0001, IMPLEMENTED) usa features estáticas:
- `vwap_at_retest`, `obi_10_at_retest`, `cumulative_delta_at_retest`, `atr_14`
- One-hot de `regime`, `direction`, `delta_divergence` (D-012 ENCODING_MAPS)

El `l2_temporal_profile` (23 campos del Ring Buffer, P3) ya está disponible en el dataset `training_dataset_v2.jsonl` pero el Oracle no lo consume. La Fase B del Oracle (EVO-TICKET-0002) consiste en integrar estas features dinámicas.

### Evidencia material verificada

**Oracle v6 skeleton (`cgalpha_v4/oracle_v6_skeleton.py`):**
- `OracleTrainerV6.feature_cols` = `["vwap", "obi_10", "cum_delta", "atr", "enc_regime", "enc_direction", "enc_delta_divergence"]` (L173-181)
- `predict()` construye el feature vector desde `features.get(k, 0.0)` para `["vwap", "obi_10", "cum_delta", "atr"]` + encoding (L214-216)
- No referencia `l2_temporal_profile` en ningún lugar.

**OracleTrainer_v3 (`cgalpha_v3/lila/llm/oracle.py`):**
- `_feature_cols` = `["vwap_at_retest", "obi_10_at_retest", "cumulative_delta_at_retest", "atr_14", ...]` (L75-79)
- `_normalize_sample()` hace flatten del snapshot pero no extrae campos de `l2_temporal_profile`.
- `train_model()` construye `X = df[self._feature_cols]` — solo features estáticas.

**Dataset `training_dataset_v2.jsonl`:**
Cada sample tiene:
```json
{
  "l2_snapshot_at_touch": {"retest_price", "obi_1", "obi_5", "obi_10", "obi_20", "cumulative_delta", ...},
  "l2_temporal_profile": {
    "window_seconds": 30,
    "n_snapshots": int,
    "l2_data_quality": "FULL"|"PARTIAL"|"EMPTY"|"CAUSAL_REJECTED",
    "obi_10_gradient_5s", "obi_10_gradient_15s", "obi_10_gradient_30s",
    "obi_10_min_30s", "obi_10_max_30s", "obi_10_std_30s",
    "obi_10_at_minus_5s", "obi_10_at_minus_15s", "obi_10_at_minus_30s",
    "delta_rate_5s", "delta_rate_15s", "delta_rate_30s",
    "delta_acceleration_5s", "delta_acceleration_15s",
    "depth_ratio_1_10", "depth_ratio_1_10_gradient_5s",
    "trade_intensity_5s", "trade_intensity_15s",
    "aggressive_buy_pct_5s", "aggressive_buy_pct_15s"
  }
}
```

### El problema de fondo

El Oracle entrena con features estáticas (snapshot en el momento del retest). No ve la **dinámica** del libro de órdenes en los 30 segundos previos al retest. Esto significa que no puede distinguir:
- Un retest donde el OBI sube gradualmente (acumulación pasiva) vs uno donde el OBI cae (descoordinación).
- Un retest con alta intensidad de trades agresivos vs uno silencioso.
- Un retest donde el delta acelera vs uno donde se estanca.

Estas son señales de microestructura que el Ring Buffer captura pero el Oracle ignora.

## Decisión propuesta

**Extender `OracleTrainerV6.feature_cols` y `OracleTrainer_v3._feature_cols` para incluir 12 features dinámicas del `l2_temporal_profile`, seleccionadas por su valor predictivo teórico y su baja correlación con las features estáticas existentes.**

### Features dinámicas seleccionadas (12 de 23)

| Feature | Origen | Justificación |
|---|---|---|
| `obi_10_gradient_5s` | l2_temporal_profile | Tendencia OBI en ventana corta. Positivo = acumulación bid. |
| `obi_10_gradient_15s` | l2_temporal_profile | Tendencia OBI en ventana media. Más estable que 5s. |
| `obi_10_gradient_30s` | l2_temporal_profile | Tendencia OBI en ventana completa. Contexto de régimen. |
| `obi_10_std_30s` | l2_temporal_profile | Volatilidad del OBI. Alta = libro inestable. |
| `delta_rate_5s` | l2_temporal_profile | Velocidad del delta en ventana corta. Compra/venta agresiva reciente. |
| `delta_rate_15s` | l2_temporal_profile | Velocidad del delta en ventana media. |
| `delta_acceleration_5s` | l2_temporal_profile | Aceleración del delta. Positivo = momentum creciente. |
| `depth_ratio_1_10` | l2_temporal_profile | Ratio depth nivel 1 vs nivel 10. Alta = walls protectoras. |
| `depth_ratio_1_10_gradient_5s` | l2_temporal_profile | Cambio del ratio. Positivo = walls apareciendo. |
| `trade_intensity_5s` | l2_temporal_profile | Número de trades en 5s. Alta = actividad. |
| `aggressive_buy_pct_5s` | l2_temporal_profile | % de volumen agresivo de compra. >0.5 = presión compradora. |
| `aggressive_buy_pct_15s` | l2_temporal_profile | % de volumen agresivo de compra en ventana media. |

### Features NO seleccionadas (11 de 23) — justificación

| Feature | Razón de exclusión |
|---|---|
| `window_seconds` | Constante (30). Sin valor predictivo. |
| `n_snapshots` | Correlacionada con `l2_data_quality`. Redundante. |
| `l2_data_quality` | Es un flag de calidad, no una feature. Se usa como filtro (solo FULL). |
| `obi_10_min_30s` | Correlacionada con `obi_10_at_retest` (snapshot estático). |
| `obi_10_max_30s` | Correlacionada con `obi_10_at_retest`. |
| `obi_10_at_minus_5s` | Correlacionada con `obi_10_gradient_5s` (redundante). |
| `obi_10_at_minus_15s` | Correlacionada con `obi_10_gradient_15s`. |
| `obi_10_at_minus_30s` | Correlacionada con `obi_10_gradient_30s`. |
| `delta_rate_30s` | Correlacionada con `delta_rate_15s` y `delta_acceleration_5s`. |
| `delta_acceleration_15s` | Correlacionada con `delta_acceleration_5s`. |
| `trade_intensity_15s` | Correlacionada con `trade_intensity_5s`. |

### Implementación técnica

**No se implementa en este ADR.** Este ADR establece el schema. La implementación se detalla en los pasos siguientes. El esquema es:

1. **En `OracleTrainer_v3._feature_cols`:** añadir las 12 features dinámicas con prefijo `l2tp_` para evitar colisiones:
   ```python
   DYNAMIC_FEATURES = [
       "l2tp_obi_10_gradient_5s", "l2tp_obi_10_gradient_15s", "l2tp_obi_10_gradient_30s",
       "l2tp_obi_10_std_30s",
       "l2tp_delta_rate_5s", "l2tp_delta_rate_15s", "l2tp_delta_acceleration_5s",
       "l2tp_depth_ratio_1_10", "l2tp_depth_ratio_1_10_gradient_5s",
       "l2tp_trade_intensity_5s",
       "l2tp_aggressive_buy_pct_5s", "l2tp_aggressive_buy_pct_15s",
   ]
   ```

2. **En `_normalize_sample()`:** extraer las 12 features de `l2_temporal_profile` con prefijo `l2tp_`:
   ```python
   profile = sample.get("l2_temporal_profile", {})
   for feat in DYNAMIC_FEATURES:
       # Quitar prefijo l2tp_ para lookup en el profile
       original_key = feat.replace("l2tp_", "")
       normalized[feat] = profile.get(original_key, 0.0)
   ```

3. **En `predict()`:** aceptar las 12 features dinámicas en el dict de features del caller.

4. **En `live_adapter._on_retest_detected`:** el `l2_profile` ya está en el snapshot (L734). El Oracle lo recibirá automáticamente cuando se extraigan las features.

5. **Filtro de calidad:** solo samples con `l2_data_quality == "FULL"` se usan para entrenamiento. Samples con `PARTIAL`, `EMPTY`, o `CAUSAL_REJECTED` se excluyen (o se imputan a 0.0, según decida el ADR de walk-forward).

### Relación con D-014

D-014 garantiza que las features dinámicas no contienen información del futuro. El filtrado causal en `synthesize_at_retest()` ya está implementado (commit `f13b927`). Las features dinámicas que consume el Oracle son causalmente válidas por construcción.

### Relación con D-003

D-003 fija el OOS mínimo en 30 muestras para A/B. La adición de 12 features dinámicas aumenta el riesgo de overfitting. El ADR de walk-forward (O-B2) debe considerar:
- Regularización L1/L2 en el RandomForest.
- Feature importance analysis post-entrenamiento.
- Posible reducción de features si la importancia es baja.

## Consecuencias

- **Positivas:**
  - El Oracle ve la dinámica del libro de órdenes, no solo el snapshot estático.
  - 12 features con valor predictivo teórico y baja correlación con features existentes.
  - Las features ya están en el dataset — no requiere recaptura de datos.
  - D-014 garantiza causalidad.
- **Neutrales:**
  - El modelo pasa de 7 a 19 features. RandomForest maneja esto bien, pero el riesgo de overfitting aumenta.
  - Los samples antiguos (pre-Ring Buffer) no tienen `l2_temporal_profile` y se imputan a 0.0 o se excluyen.
- **Riesgos:**
  - Overfitting con 19 features y pocos samples. Mitigación: walk-forward + regularización.
  - Features dinámicas con baja importancia pueden añadir ruido. Mitigación: feature importance analysis.
  - Cambio de schema requiere re-entrenamiento completo. Mitigación: A/B testing (Set A con dinámicas vs Set B sin dinámicas).

## Alternativas consideradas

- **Incluir las 23 features.** Descartada por alta correlación entre muchas de ellas (min/max/at_minus son redundantes con gradients). 12 features capturan la señal sin redundancia.
- **No incluir features dinámicas (mantener Fase A).** Descartada porque perpetúa la limitación que motivó EVO-TICKET-0002: el Oracle aprende con features estáticas.
- **Incluir solo gradients (3 features).** Descartada porque pierde señales de trade intensity y aggressive buy pct, que son ortogonales al OBI.
- **Usar PCA sobre las 23 features.** Descartada porque pierde interpretabilidad y dificulta el feature importance analysis.

## Próximos pasos (post-aprobación)

1. Implementar la extracción de las 12 features en `_normalize_sample()`.
2. Añadir las 12 features a `_feature_cols`.
3. Actualizar `predict()` para aceptar las features dinámicas.
4. Re-entrenar Oracle v6 con features dinámicas (A/B testing).
5. ADR de walk-forward vs split estático (O-B2).

---

*Referencias:*
- *`cgalpha_v4/oracle_v6_skeleton.py` L173-181 (feature_cols actuales)*
- *`cgalpha_v3/lila/llm/oracle.py` L69-79 (OracleTrainer_v3 feature_cols)*
- *`cgalpha_v3/scripts/train_oracle_ab.py` (pipeline A/B)*
- *`cgalpha_v3/infrastructure/l2_ring_buffer.py` L38-126 (synthesize_at_retest, 23 features)*
- *`cgalpha_v3/application/live_adapter.py` L734 (l2_temporal_profile en snapshot)*
- *`aipha_memory/identity/ADR-ACOPLAMIENTO-TEMPORAL-1-t-feature-le-t-candle-close-minus-epsilon.md` (D-014)*
- *`documentation/EVO_TICKET_LOG.md` — EVO-TICKET-0002 (Fase B)*
