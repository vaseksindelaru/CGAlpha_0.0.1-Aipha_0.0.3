# ADR adr-4c3047aa

- Fecha: 2026-04-04T20:31:15.401421+00:00
- Trigger: `kill_switch_confirm`
- Iteración: `2026-04-04_20-31_01`
- Nivel evento: `critical`

## Contexto
KILL-SWITCH: ACTIVADO — señales suspendidas

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "kill_switch_status": "triggered",
  "system_status": "kill-switch-active"
}
```
