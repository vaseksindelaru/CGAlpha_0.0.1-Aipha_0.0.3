# ADR adr-0a150c3d

- Fecha: 2026-04-04T20:32:42.529057+00:00
- Trigger: `experiment_propose`
- Iteración: `2026-04-04_20-32`
- Nivel evento: `info`

## Contexto
EXPERIMENT: propuesta generada prop-906c927d

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "proposal_id": "prop-906c927d",
  "frictions": {
    "fee_taker_pct": 0.05,
    "fee_maker_pct": 0.02,
    "slippage_bps": 2.0,
    "latency_ms": 100.0
  },
  "walk_forward_windows": 3
}
```
