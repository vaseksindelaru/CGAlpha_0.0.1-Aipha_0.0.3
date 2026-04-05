# ADR adr-507852de

- Fecha: 2026-04-05T08:16:53.702718+00:00
- Trigger: `learning_memory_regime_check`
- Iteración: `2026-04-05_08-16_01`
- Nivel evento: `warning`

## Contexto
LEARNING: cambio de régimen detectado y degradación aplicada

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "regime_shift": true,
  "event": {
    "shift_id": "regime-0001",
    "created_at": "2026-04-05T08:16:53.696192+00:00",
    "mean_historic": 1.01,
    "std_historic": 0.12688577540449522,
    "mean_recent": 4.075,
    "threshold": 1.2637715508089904,
    "affected_entries": 0
  }
}
```
