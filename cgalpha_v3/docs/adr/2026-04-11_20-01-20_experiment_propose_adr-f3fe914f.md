# ADR adr-f3fe914f

- Fecha: 2026-04-11T20:01:20.609232+00:00
- Trigger: `experiment_propose`
- Iteración: `2026-04-11_20-01`
- Nivel evento: `info`

## Contexto
EXPERIMENT: propuesta generada prop-a66b6ad5

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "proposal_id": "prop-a66b6ad5",
  "frictions": {
    "fee_taker_pct": 0.05,
    "fee_maker_pct": 0.02,
    "slippage_bps": 2.0,
    "latency_ms": 100.0
  },
  "walk_forward_windows": 3
}
```
