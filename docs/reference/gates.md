# Gates de Readiness (Deep Causal / v0.3)

Este archivo define el criterio operativo para decidir `HOLD` vs `PROCEED_V03`.

## 1. Precondiciones obligatorias (Live/Hybrid)

1. Fuente de microestructura disponible:
   - `aipha_memory/operational/order_book_features.jsonl`
2. Reporte causal reciente con:
   - `data_alignment`
   - `causal_metrics`
   - `readiness_gates`

Si falta cualquiera: **bloquear Live/Hybrid** y operar solo en modo Paper.

## 2. Gates mínimos

- `readiness_gates.data_quality_pass = true`
- `readiness_gates.causal_quality_pass = true`
- `readiness_gates.proceed_v03 = true`

## 3. Thresholds recomendados

- `max_blind_test_ratio <= 0.25`
- `max_nearest_match_avg_lag_ms <= 150`
- `min_causal_accuracy >= 0.55`
- `min_efficiency >= 0.40`

## 4. Reglas de bloqueo

Bloquear promoción de fase si:
- `blind_test_ratio` supera el umbral,
- no hay cobertura suficiente de order book,
- la calidad causal pasa solo de forma aislada (no repetida).

## 5. Regla práctica

- Un pase aislado no es promoción.
- Requiere pases repetidos con datos estables.
