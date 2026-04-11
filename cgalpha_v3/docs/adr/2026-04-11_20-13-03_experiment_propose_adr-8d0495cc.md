# ADR adr-8d0495cc

- Fecha: 2026-04-11T20:13:03.385441+00:00
- Trigger: `experiment_propose`
- Iteración: `2026-04-11_20-13`
- Nivel evento: `info`

## Contexto
EXPERIMENT: propuesta generada prop-46900c14

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "proposal_id": "prop-46900c14",
  "frictions": {
    "fee_taker_pct": 0.05,
    "fee_maker_pct": 0.02,
    "slippage_bps": 2.0,
    "latency_ms": 100.0
  },
  "walk_forward_windows": 3
}
```
