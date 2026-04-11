# ADR adr-50da3fd7

- Fecha: 2026-04-11T19:27:08.157971+00:00
- Trigger: `experiment_run`
- Iteración: `2026-04-11_19-27_02`
- Nivel evento: `critical`

## Contexto
EXPERIMENT: temporal leakage detectado (Simulated leakage)

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "error": "Simulated leakage"
}
```
