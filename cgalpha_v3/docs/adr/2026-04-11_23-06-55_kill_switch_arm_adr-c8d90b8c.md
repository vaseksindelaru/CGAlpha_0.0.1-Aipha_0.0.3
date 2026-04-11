# ADR adr-c8d90b8c

- Fecha: 2026-04-11T23:06:55.298980+00:00
- Trigger: `kill_switch_arm`
- Iteración: `2026-04-11_23-06`
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
