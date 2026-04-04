# ADR adr-0a05dc1f

- Fecha: 2026-04-04T20:43:45.263680+00:00
- Trigger: `experiment_run`
- Iteración: `2026-04-04_20-43_01`
- Nivel evento: `critical`

## Contexto
EXPERIMENT: temporal leakage detectado ([DQ] TemporalLeakageError: 1 feature(s) con timestamp >= OOS start (1775295825.25649). Violación del protocolo OOS (Sección E).)

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "error": "[DQ] TemporalLeakageError: 1 feature(s) con timestamp >= OOS start (1775295825.25649). Violación del protocolo OOS (Sección E)."
}
```
