# ADR adr-e32558da

- Fecha: 2026-04-11T19:27:07.874965+00:00
- Trigger: `experiment_propose`
- Iteración: `2026-04-11_19-27`
- Nivel evento: `info`

## Contexto
EXPERIMENT: propuesta generada prop-fd7faf21

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "proposal_id": "prop-fd7faf21",
  "frictions": {
    "fee_taker_pct": 0.05,
    "fee_maker_pct": 0.02,
    "slippage_bps": 2.0,
    "latency_ms": 100.0
  },
  "walk_forward_windows": 3
}
```
