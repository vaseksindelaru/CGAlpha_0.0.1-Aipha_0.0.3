# ADR adr-3b0295bd

- Fecha: 2026-04-11T20:12:52.329881+00:00
- Trigger: `experiment_propose`
- Iteración: `2026-04-11_20-12`
- Nivel evento: `info`

## Contexto
EXPERIMENT: propuesta generada prop-479e0a5c

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "proposal_id": "prop-479e0a5c",
  "frictions": {
    "fee_taker_pct": 0.05,
    "fee_maker_pct": 0.02,
    "slippage_bps": 2.0,
    "latency_ms": 100.0
  },
  "walk_forward_windows": 3
}
```
