# Risk Management Layer — cgalpha_v3

## Propósito
Capa formal de gestión de riesgo que protege el capital en todo momento (Sección M).
Ninguna señal llega al mercado sin pasar por este módulo.

## Inputs / Outputs

- **Inputs:** señales del sistema, drawdown actual, latencia API, estado de Data Quality
- **Outputs:** `(ok: bool, motivo: str)` por señal; estado del kill-switch; incidentes P0-P3

## Contratos

- `RiskManager.validate_signal(signal, data_quality_ok)` → `(bool, str)`
- `RiskManager.update_drawdown(pct)` → activa circuit breaker si supera límite
- `KillSwitchState.arm_request()` → paso 1
- `KillSwitchState.confirm()` → paso 2 (activa suspensión total)
- `KillSwitchState.reset()` → re-arma desde GUI

## Parámetros por defecto

| Parámetro | Valor por defecto |
|-----------|-------------------|
| `max_drawdown_session_pct` | 5.0% |
| `max_position_size_pct` | 2.0% |
| `max_signals_per_hour` | 10 |
| `min_signal_quality_score` | 0.65 |

## Dependencias

- `cgalpha_v3.domain.models.signal` (Signal)
- Librería estándar Python

## Estado actual

🚧 FASE 0/2 — `RiskManager`, `KillSwitchState`, `CircuitBreaker` implementados.
GUI integrada parcialmente (endpoint `/api/risk/params`).

## Próximo incremento

- Conectar `update_drawdown` con datos reales de posiciones
- Persistir incidentes en `memory/incidents/`
- Test de activación de circuit breaker end-to-end
