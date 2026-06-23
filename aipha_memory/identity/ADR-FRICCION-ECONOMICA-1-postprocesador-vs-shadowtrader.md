# ADR-FRICCION-ECONOMICA-1 — Fricción Económica: Post-procesador (Opción B) vs Integración en ShadowTrader (Opción C)

## Estatus
ACEPTADO e IMPLEMENTADO (2026-06-23).

Aprobado por el operador y Tech Lead tras evaluación de diseño. La Opción C (Integración en ShadowTrader P9 con EconomicGate) es la decisión oficial. El Oracle (P1) y P4 mantienen etiquetas teóricas puras. La fricción económica se evalúa en tiempo real en P9. Feedback loop vía `economic_gate_decision` en `bridge.jsonl` hacia Fase B del Oracle.

## Contexto

La alerta #4 de la deliberación Ruta B identificó que `DeferredOutcomeMonitor` (P4) produce labels teóricamente puros: `BOUNCE_STRONG` si `price > zone_top + 0.5*atr`, `BREAKOUT` si `price < zone_bottom`, sin considerar slippage, costo de transacción, latencia de ejecución, ni impacto del libro de órdenes. El Oracle (P1) puede aprender a predecir etiquetas estadísticamente perfectas que son inoperables en `ShadowTrader` (P9) cuando se enfrentan a fricción económica real.

El operador descartó la Opción A (asimilar primitivas económicas en el label modificando `_evaluate`) para preservar la semántica teórica pura de P4 y P1. Este ADR evalúa las dos opciones restantes: B (post-procesador) y C (integración en ShadowTrader).

### Evidencia material verificada

**P4 — `cgalpha_v3/domain/deferred_outcome_monitor.py` L337-376 (`_evaluate`):**
```python
if label.zone_direction == "bullish":
    if price < label.zone_bottom:
        return "BREAKOUT"
    if price > label.zone_top + 0.5 * atr:
        return "BOUNCE_STRONG"
    if label.bars_elapsed >= label.lookahead_bars:
        if label.mfe > 0.3 * atr:
            return "BOUNCE_WEAK"
        return "INCONCLUSIVE"
```
El umbral `0.5*atr` es teórico. No hay slippage, ni costo, ni latencia.

**P9 — `cgalpha_v3/trading/shadow_trader.py`:**
- `DryRunOrderManager` ya existe (L54) y maneja PnL, SL/TP, MFE/MAE con comisiones.
- `open_shadow_trade` (L58-119) delega en `DryRunOrderManager.execute_signal(signal)` que aplica risk limits.
- `_compute_outcome_ordinal` (L178-200) calcula outcome en unidades ATR con Triple Barrier: `0 = SL/loss, 1 = TP1 (2 ATR), 2 = TP2 (3 ATR), 3 = TP3+ (4 ATR)`.
- `bridge.jsonl` persiste `pnl_pct`, `mfe`, `mae`, `mfe_atr`, `mae_atr`, `exit_reason`, `config_snapshot`, `signal_data`, `oracle_confidence`.

**P9 ya tiene un esquema de outcome ordinal (0-3) distinto del esquema de labels de P4 (`BOUNCE_STRONG`/`BOUNCE_WEAK`/`BREAKOUT`/`INCONCLUSIVE`).** Esta es una observación crítica: P4 y P9 ya miden cosas diferentes. P4 mide si el precio escapó de la zona; P9 mide si el trade llegó a TP1/TP2/TP3 o tocó SL.

### El problema de fondo

El Oracle entrena con labels de P4 (`BOUNCE_STRONG` = el precio escapó 0.5 ATR de la zona). Pero la operabilidad real de una predicción `BOUNCE_STRONG` depende de:
1. **Slippage estimado** en el momento de entrada (función del spread y depth).
2. **Costo de transacción** (comisión de Binance Futures: ~0.04% maker, ~0.06% taker por lado).
3. **Latencia de ejecución** entre la señal y el fill (función del feed y la API).
4. **Impacto del libro** si el orden es grande relativo al depth.

Si `0.5*atr < slippage + costo + latencia_impacto`, entonces una predicción `BOUNCE_STRONG` es teóricamente correcta pero económicamente perdedora. El Oracle no ve esta fricción durante el entrenamiento.

## Decisión propuesta

**Recomendación aprobada: Opción C (Integración en ShadowTrader P9), con un componente ligero de EconomicGate.**

### Análisis comparativo

#### Opción B — Post-procesador entre P4 y Oracle

**Diseño:** Un nuevo componente `EconomicWeighter` entre `DeferredOutcomeMonitor` y el trainer del Oracle. Toma el dataset `training_dataset_v2.jsonl` con labels puros de P4, y ajusta los sample weights del Oracle según la fricción estimada de cada sample.

**Mecánica:**
```python
# Pseudocódigo conceptual
for sample in dataset:
    label = sample["outcome"]["label"]  # BOUNCE_STRONG, etc.
    atr = sample["clearance"]["atr_at_detection"]
    spread_bps = sample["l2_snapshot_at_touch"]["spread_bps"]
    depth = sample["l2_snapshot_at_touch"]["bid_wall_depth_10_btc"]
    
    # Estimar fricción
    slippage_est = estimate_slippage(spread_bps, depth, order_size)
    cost_est = 2 * 0.0006  # 2 lados * 0.06% taker
    friction_atr = (slippage_est + cost_est) / atr
    
    # Penalizar samples donde la fricción excede el umbral del label
    if label == "BOUNCE_STRONG" and friction_atr > 0.5:
        sample_weight = 0.3  # Reducir peso, no eliminar
    elif label == "BOUNCE_WEAK" and friction_atr > 0.3:
        sample_weight = 0.1
    else:
        sample_weight = 1.0
```

**Ventajas:**
- Preserva el dataset puro de P4 (no lo modifica).
- El Oracle entrena con labels teóricos pero aprende a desvalorizar samples inoperables.
- Reversible: si la fricción estimada es incorrecta, se re-calculan los weights sin re-entrenar desde cero.

**Desventajas:**
- **Introduce un nuevo componente** en el grafo de dependencias. El Nexus §2 no lo tiene. Requiere actualización del grafo.
- **El Oracle sigue viendo labels teóricos.** Aprende a predecir `BOUNCE_STRONG` incluso en samples con peso bajo. La predicción es teóricamente correcta pero el modelo no "sabe" que es inoperable.
- **Duplica la noción de operabilidad.** P9 ya tiene `DryRunOrderManager` con comisiones y SL/TP. `EconomicWeighter` reimplementaría la estimación de fricción en paralelo.
- **La fricción estimada es estática** (calculada al momento del sample). La fricción real en ejecución depende del régimen de mercado en el momento del trade, no del momento del retest histórico.

#### Opción C — Integración en ShadowTrader P9 con EconomicGate

**Diseño:** No se añade un componente entre P4 y Oracle. El Oracle entrena con labels puros de P4. La fricción económica se evalúa en tiempo de ejecución en `ShadowTrader`, que ya tiene `DryRunOrderManager` con comisiones. Se añade un `EconomicGate` ligero dentro de `ShadowTrader.open_shadow_trade` que decide si una predicción del Oracle es operable antes de abrir el paper trade.

**Mecánica:**
```python
# Pseudocódigo conceptual — extensión de ShadowTrader.open_shadow_trade
def open_shadow_trade(self, entry_price, direction, atr, signal_data, ...):
    oracle_confidence = (signal_data or {}).get("oracle_confidence", 0.0)
    predicted_label = (signal_data or {}).get("prediction", "UNKNOWN")
    
    # EconomicGate: estimar fricción en tiempo real
    spread_bps = (signal_data or {}).get("spread_bps", 0)
    depth = (signal_data or {}).get("bid_wall_depth_10_btc", 0)
    
    slippage_est = estimate_slippage(spread_bps, depth, order_size=0.1)
    cost_est = 2 * 0.0006  # taker ambos lados
    friction_atr = (slippage_est + cost_est) / atr
    
    # Umbral de operabilidad por label
    required_edge = {
        "BOUNCE_STRONG": 0.5,  # P4 usa 0.5*atr
        "BOUNCE_WEAK": 0.3,    # P4 usa 0.3*atr
    }.get(predicted_label, 1.0)
    
    if friction_atr >= required_edge:
        logger.info(
            f"🚫 EconomicGate: {predicted_label} rechazado "
            f"(friction={friction_atr:.3f} ATR >= edge={required_edge} ATR)"
        )
        return ""  # No abrir trade
    
    # Si pasa el gate, abrir trade normalmente
    # DryRunOrderManager ya aplica comisiones reales
    ...
```

**Ventajas:**
- **No introduce un nuevo componente en el grafo.** `EconomicGate` es una extensión de `ShadowTrader` (P9), que ya existe.
- **Reutiliza `DryRunOrderManager`** que ya tiene comisiones, SL/TP, y risk limits. No duplica la estimación de fricción.
- **La fricción se evalúa en tiempo real** con el estado actual del libro de órdenes, no con un snapshot histórico. Esto es más preciso que la Opción B.
- **El Oracle permanece puro.** Aprende a predecir labels teóricos. La decisión de operabilidad es una capa de ejecución, no una capa de entrenamiento. Esto respeta la separación de concerns: P4 mide el mercado, P9 decide si es operable.
- **`bridge.jsonl` ya persiste `oracle_confidence` y `signal_data`.** Se puede añadir `economic_gate_decision` y `friction_atr_est` al schema sin romper nada.
- **Permite feedback loop.** Si `EconomicGate` rechaza muchas predicciones `BOUNCE_STRONG`, ese patrón es evidencia de que el régimen actual hace inoperable el label. Se puede alimentar de vuelta al Oracle como feature de régimen en Fase B.

**Desventajas:**
- **El Oracle no aprende de la fricción durante el entrenamiento.** Aprende labels teóricos. Si la mayoría de `BOUNCE_STRONG` son inoperables en práctica, el Oracle seguirá prediciéndolos. Mitigación: el feedback loop anterior.
- **Requiere estimar slippage en tiempo real.** Función `estimate_slippage(spread_bps, depth, order_size)` no existe todavía. Requiere implementación y calibración.
- **`ShadowTrader` es P9 (prioridad baja).** Modificarlo requiere su propio CRB. Pero el cambio es aditivo (un gate antes de `open_shadow_trade`), no destructivo.

### Por qué se recomienda la Opción C

1. **Separación de concerns.** P4 mide el mercado (¿el precio escapó de la zona?). P9 decide la operabilidad (¿es rentable operar esta predicción?). Mezclar ambas (Opción B) viola esta separación.
2. **Reutilización de infraestructura.** `DryRunOrderManager` ya tiene comisiones. `EconomicGate` es una extensión natural, no un componente nuevo.
3. **Precisión.** La fricción real depende del régimen actual del libro. Evaluarla en tiempo real (Opción C) es más preciso que estimarla con un snapshot histórico (Opción B).
4. **Minimalidad.** No añade componentes al grafo de dependencias. No requiere actualizar el Nexus §2. El cambio se aísla en P9.
5. **Feedback loop.** El rechazo del gate es evidencia operacional que puede alimentar al Oracle como feature en Fase B, cerrando el ciclo sin contaminar el entrenamiento.

### Riesgos de la Opción C y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Oracle predice muchos `BOUNCE_STRONG` inoperables | Feedback loop: `economic_gate_decision` en `bridge.jsonl` → feature de régimen en Fase B |
| `estimate_slippage` mal calibrada | Calibrar con datos reales de `bridge.jsonl` (MFE/MAE vs spread/depth histórico) |
| `EconomicGate` rechaza demasiado → sin trades | Umbral ajustable + métrica de rejection rate en GUI |
| P9 es prioridad baja → retrasa la decisión | El gate es aditivo; se puede implementar independientemente de P1-P4 |

## Consecuencias

- **Positivas:**
  - El Oracle (P1) y P4 mantienen etiquetas teóricas puras. El dataset de entrenamiento no se modifica.
  - La fricción económica se evalúa en tiempo real con infraestructura existente (`DryRunOrderManager`).
  - No se añaden componentes al grafo de dependencias.
  - `bridge.jsonl` enriquece su schema con `economic_gate_decision` y `friction_atr_est`, habilitando feedback loop.
- **Neutrales:**
  - `ShadowTrader` (P9) requiere un CRB y una Fase A de reconstrucción para añadir `EconomicGate`. No bloquea P1-P4.
  - `estimate_slippage` requiere implementación y calibración. Es trabajo de Fase B de P9.
- **Riesgos:**
  - El Oracle no aprende fricción durante el entrenamiento. Si la mayoría de predicciones son inoperables, el modelo sigue prediciéndolas. Mitigación: feedback loop.
  - Si `estimate_slippage` es incorrecta, el gate rechaza predicciones válidas o acepta predicciones inválidas. Mitigación: calibración con datos reales.

## Alternativas consideradas

- **Opción A — Asimilar en el label (descartada por el operador).** Modificar `_evaluate` para penalizar con slippage + costo. Cambia la semántica del label, requiere nuevo D-ID + re-entrenamiento. Descartada porque el operador decidió preservar P4 y P1 puros.
- **Opción B — Post-procesador `EconomicWeighter`.** Descartada por las desventajas anteriores: nuevo componente en el grafo, duplica `DryRunOrderManager`, fricción estática, el Oracle sigue viendo labels teóricos.
- **Opción C — Integración en ShadowTrader P9 con EconomicGate.** Recomendada por las ventajas anteriores.
- **Opción D — No hacer nada.** Descartada porque perpetúa el riesgo de alerta #4: el Oracle aprende etiquetas inoperables.

## Próximos pasos (post-aprobación — aprobado 2026-06-23)

1. Redactar CRB de P9 (`ShadowTrader`) con `EconomicGate` como Fase A.
2. Implementar `estimate_slippage(spread_bps, depth, order_size)` con calibración inicial conservadora.
3. Añadir `economic_gate_decision` y `friction_atr_est` al schema de `bridge.jsonl`.
4. Métrica de rejection rate en GUI.
5. Feedback loop: en Fase B del Oracle, evaluar si `economic_gate_decision` histórica mejora la predicción como feature de régimen.

---

*Referencias:*
- *`cgalpha_v3/domain/deferred_outcome_monitor.py` L337-376 (`_evaluate`)*
- *`cgalpha_v3/trading/shadow_trader.py` (código vivo P9)*
- *`cgalpha_v3/risk/order_manager.py` (`DryRunOrderManager`)*
- *`cgalpha_v4/CRB_DeferredOutcomeMonitor_P4.md` §6 Fase B punto 1 (alerta #4)*
- *Deliberación arquitectónica Ruta B, sesión 2026-06-23 (alerta #4)*
