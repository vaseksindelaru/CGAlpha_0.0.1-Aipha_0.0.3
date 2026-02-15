# Parámetros Críticos (Resumen Operativo)

Este archivo centraliza parámetros de alto impacto para operación y análisis.

## 1. Trading / Triple Coincidencia

| Parámetro | Uso | Rango operativo recomendado |
|---|---|---|
| `trend_lookback` | Ventana de tendencia | según estrategia |
| `min_r_squared` | Calidad mínima de tendencia | típicamente `>= 0.45` |
| `volume_percentile_threshold` | Filtro de volumen | 70-95 según régimen |
| `body_percentile_threshold` | Cuerpo de vela clave | 20-40 según sensibilidad |
| `tolerance_bars` | Ventana de coincidencia | 4-12 |

## 2. Triple Barrier / Riesgo

| Parámetro | Uso | Referencia |
|---|---|---|
| `tp_factor` | Distancia de take-profit (ATR) | evaluar por régimen |
| `sl_factor` | Distancia de stop-loss (ATR) | evaluar por régimen |
| `time_limit` | Horizonte máximo por señal | según timeframe |
| `drawdown_threshold` | Tolerancia de drawdown intra-trade | usar con control estricto |

## 3. Capa Causal (Ghost Architect)

| Parámetro / métrica | Uso |
|---|---|
| `blind_test_ratio` | Riesgo de inferencia sin micro-match |
| `nearest_match_avg_lag_ms` | Calidad de alineación temporal |
| `causal_accuracy` | Calidad de hipótesis vs resultado |
| `efficiency` | Señal útil vs ruido generado |

## 4. Política de cambios

- Cambiar un parámetro por vez cuando sea posible.
- Validar con tests + `auto-analyze`.
- Registrar justificación causal antes de promover a fase superior.
