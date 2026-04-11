# ADR adr-9be6ee32

- Fecha: 2026-04-11T23:06:55.225833+00:00
- Trigger: `experiment_propose`
- Iteración: `2026-04-11_23-06`
- Nivel evento: `info`

## Contexto
EXPERIMENT: propuesta generada prop-b94f398e

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "proposal_id": "prop-b94f398e",
  "frictions": {
    "fee_taker_pct": 0.05,
    "fee_maker_pct": 0.02,
    "slippage_bps": 2.0,
    "latency_ms": 100.0
  },
  "walk_forward_windows": 3
}
```
