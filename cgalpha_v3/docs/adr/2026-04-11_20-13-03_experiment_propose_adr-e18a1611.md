# ADR adr-e18a1611

- Fecha: 2026-04-11T20:13:03.403261+00:00
- Trigger: `experiment_propose`
- Iteración: `2026-04-11_20-13`
- Nivel evento: `info`

## Contexto
EXPERIMENT: propuesta generada prop-dc4f44e5

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "proposal_id": "prop-dc4f44e5",
  "frictions": {
    "fee_taker_pct": 0.05,
    "fee_maker_pct": 0.02,
    "slippage_bps": 2.0,
    "latency_ms": 100.0
  },
  "walk_forward_windows": 3
}
```
