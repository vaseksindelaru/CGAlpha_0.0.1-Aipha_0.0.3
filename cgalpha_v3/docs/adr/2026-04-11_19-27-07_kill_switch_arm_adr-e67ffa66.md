# ADR adr-e67ffa66

- Fecha: 2026-04-11T19:27:07.958219+00:00
- Trigger: `kill_switch_arm`
- Iteración: `2026-04-11_19-27`
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
