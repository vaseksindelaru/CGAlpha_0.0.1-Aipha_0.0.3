# ADR adr-ffab70f8

- Fecha: 2026-04-04T20:14:54.164582+00:00
- Trigger: `experiment_run`
- Iteración: `2026-04-04_20-14_01`
- Nivel evento: `critical`

## Contexto
EXPERIMENT: temporal leakage detectado ([DQ] TemporalLeakageError: 1 feature(s) con timestamp >= OOS start (1775294094.148931). Violación del protocolo OOS (Sección E).)

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "error": "[DQ] TemporalLeakageError: 1 feature(s) con timestamp >= OOS start (1775294094.148931). Violación del protocolo OOS (Sección E)."
}
```
