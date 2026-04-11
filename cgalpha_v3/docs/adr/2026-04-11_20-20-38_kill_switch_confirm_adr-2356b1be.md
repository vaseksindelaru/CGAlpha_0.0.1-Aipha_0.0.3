# ADR adr-2356b1be

- Fecha: 2026-04-11T20:20:38.781905+00:00
- Trigger: `kill_switch_confirm`
- Iteración: `2026-04-11_20-20_01`
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
