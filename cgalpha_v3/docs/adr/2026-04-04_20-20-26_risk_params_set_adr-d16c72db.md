# ADR adr-d16c72db

- Fecha: 2026-04-04T20:20:26.709050+00:00
- Trigger: `risk_params_set`
- Iteración: `2026-04-04_20-20`
- Nivel evento: `info`

## Contexto
Parámetros de riesgo actualizados: ['max_drawdown_session_pct', 'max_position_size_pct', 'max_signals_per_hour', 'min_signal_quality_score']

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "updated": [
    "max_drawdown_session_pct",
    "max_position_size_pct",
    "max_signals_per_hour",
    "min_signal_quality_score"
  ],
  "risk_parameters": {
    "max_drawdown_session_pct": 4.5,
    "max_position_size_pct": 1.5,
    "max_signals_per_hour": 8,
    "min_signal_quality_score": 0.72
  }
}
```
