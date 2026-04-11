# ADR adr-c84e1cf1

- Fecha: 2026-04-11T20:20:38.483225+00:00
- Trigger: `experiment_propose`
- Iteración: `2026-04-11_20-20`
- Nivel evento: `info`

## Contexto
EXPERIMENT: propuesta generada prop-2f1f5199

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "proposal_id": "prop-2f1f5199",
  "frictions": {
    "fee_taker_pct": 0.05,
    "fee_maker_pct": 0.02,
    "slippage_bps": 2.0,
    "latency_ms": 100.0
  },
  "walk_forward_windows": 3
}
```
