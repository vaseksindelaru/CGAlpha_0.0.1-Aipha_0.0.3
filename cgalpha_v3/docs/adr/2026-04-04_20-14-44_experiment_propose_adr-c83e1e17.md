# ADR adr-c83e1e17

- Fecha: 2026-04-04T20:14:44.799005+00:00
- Trigger: `experiment_propose`
- Iteración: `2026-04-04_20-14`
- Nivel evento: `info`

## Contexto
EXPERIMENT: propuesta generada prop-35c86484

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "proposal_id": "prop-35c86484",
  "frictions": {
    "fee_taker_pct": 0.05,
    "fee_maker_pct": 0.02,
    "slippage_bps": 2.0,
    "latency_ms": 100.0
  },
  "walk_forward_windows": 3
}
```
