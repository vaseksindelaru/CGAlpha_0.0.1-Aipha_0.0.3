# ADR adr-bcfd7bfc

- Fecha: 2026-04-11T23:06:55.216572+00:00
- Trigger: `experiment_run`
- Iteración: `2026-04-11_23-06_01`
- Nivel evento: `info`

## Contexto
EXPERIMENT: ejecución completada exp-af1207ae

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "experiment_id": "exp-af1207ae",
  "proposal_id": "prop-df658377",
  "metrics": {
    "gross_return_pct": -0.1318,
    "friction_cost_pct": 1.001,
    "net_return_pct": -1.1328,
    "sharpe_like": -8.0759,
    "max_drawdown_pct": 0.2414,
    "trades": 33.0,
    "walk_forward_windows": 3.0
  },
  "walk_forward_windows": 3,
  "no_leakage_checked": true
}
```
