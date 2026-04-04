# ADR adr-2bd8fe33

- Fecha: 2026-04-04T20:31:15.394323+00:00
- Trigger: `kill_switch_arm`
- Iteración: `2026-04-04_20-31`
- Nivel evento: `warning`

## Contexto
KILL-SWITCH: solicitud de activación (paso 1 de 2)

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "kill_switch_status": "arming"
}
```
