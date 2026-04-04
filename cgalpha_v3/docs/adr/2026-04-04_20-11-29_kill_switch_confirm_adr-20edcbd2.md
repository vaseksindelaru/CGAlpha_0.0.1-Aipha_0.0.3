# ADR adr-20edcbd2

- Fecha: 2026-04-04T20:11:29.681241+00:00
- Trigger: `kill_switch_confirm`
- Iteración: `2026-04-04_20-11_01`
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
