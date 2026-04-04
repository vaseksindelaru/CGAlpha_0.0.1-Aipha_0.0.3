# ADR adr-c0c95186

- Fecha: 2026-04-04T20:38:44.247085+00:00
- Trigger: `experiment_propose`
- Iteración: `2026-04-04_20-38`
- Nivel evento: `info`

## Contexto
EXPERIMENT: propuesta generada prop-c5f09b1f

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "proposal_id": "prop-c5f09b1f",
  "frictions": {
    "fee_taker_pct": 0.05,
    "fee_maker_pct": 0.02,
    "slippage_bps": 2.0,
    "latency_ms": 100.0
  },
  "walk_forward_windows": 3
}
```
