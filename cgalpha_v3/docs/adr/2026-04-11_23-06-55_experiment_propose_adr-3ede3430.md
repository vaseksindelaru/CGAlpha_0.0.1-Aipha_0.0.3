# ADR adr-3ede3430

- Fecha: 2026-04-11T23:06:55.204539+00:00
- Trigger: `experiment_propose`
- Iteración: `2026-04-11_23-06`
- Nivel evento: `info`

## Contexto
EXPERIMENT: propuesta generada prop-df658377

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "proposal_id": "prop-df658377",
  "frictions": {
    "fee_taker_pct": 0.05,
    "fee_maker_pct": 0.02,
    "slippage_bps": 2.0,
    "latency_ms": 100.0
  },
  "walk_forward_windows": 3
}
```
