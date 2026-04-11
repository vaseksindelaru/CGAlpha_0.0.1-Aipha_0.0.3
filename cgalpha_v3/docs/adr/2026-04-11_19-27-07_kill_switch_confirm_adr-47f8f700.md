# ADR adr-47f8f700

- Fecha: 2026-04-11T19:27:07.961315+00:00
- Trigger: `kill_switch_confirm`
- Iteración: `2026-04-11_19-27_01`
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
