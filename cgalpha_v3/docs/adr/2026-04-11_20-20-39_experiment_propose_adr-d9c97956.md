# ADR adr-d9c97956

- Fecha: 2026-04-11T20:20:39.607056+00:00
- Trigger: `experiment_propose`
- Iteración: `2026-04-11_20-20_01`
- Nivel evento: `info`

## Contexto
EXPERIMENT: propuesta generada prop-69da8ea2

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "proposal_id": "prop-69da8ea2",
  "frictions": {
    "fee_taker_pct": 0.05,
    "fee_maker_pct": 0.02,
    "slippage_bps": 2.0,
    "latency_ms": 100.0
  },
  "walk_forward_windows": 3
}
```
