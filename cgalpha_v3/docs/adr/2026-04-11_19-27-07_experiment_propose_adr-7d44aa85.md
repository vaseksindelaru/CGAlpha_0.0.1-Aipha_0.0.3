# ADR adr-7d44aa85

- Fecha: 2026-04-11T19:27:07.893348+00:00
- Trigger: `experiment_propose`
- Iteración: `2026-04-11_19-27`
- Nivel evento: `info`

## Contexto
EXPERIMENT: propuesta generada prop-19d62044

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "proposal_id": "prop-19d62044",
  "frictions": {
    "fee_taker_pct": 0.05,
    "fee_maker_pct": 0.02,
    "slippage_bps": 2.0,
    "latency_ms": 100.0
  },
  "walk_forward_windows": 3
}
```
