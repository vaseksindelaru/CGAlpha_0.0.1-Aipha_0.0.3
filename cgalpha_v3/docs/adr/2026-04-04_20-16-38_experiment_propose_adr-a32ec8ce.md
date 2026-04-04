# ADR adr-a32ec8ce

- Fecha: 2026-04-04T20:16:38.546345+00:00
- Trigger: `experiment_propose`
- Iteración: `2026-04-04_20-16`
- Nivel evento: `info`

## Contexto
EXPERIMENT: propuesta generada prop-3f379f44

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "proposal_id": "prop-3f379f44",
  "frictions": {
    "fee_taker_pct": 0.05,
    "fee_maker_pct": 0.02,
    "slippage_bps": 2.0,
    "latency_ms": 100.0
  },
  "walk_forward_windows": 3
}
```
