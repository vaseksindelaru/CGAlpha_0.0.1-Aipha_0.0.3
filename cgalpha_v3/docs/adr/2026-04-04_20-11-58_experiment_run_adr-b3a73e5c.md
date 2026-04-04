# ADR adr-b3a73e5c

- Fecha: 2026-04-04T20:11:58.553399+00:00
- Trigger: `experiment_run`
- Iteración: `2026-04-04_20-11_01`
- Nivel evento: `critical`

## Contexto
EXPERIMENT: temporal leakage detectado ([DQ] TemporalLeakageError: 1 feature(s) con timestamp >= OOS start (1775293918.538423). Violación del protocolo OOS (Sección E).)

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "error": "[DQ] TemporalLeakageError: 1 feature(s) con timestamp >= OOS start (1775293918.538423). Violación del protocolo OOS (Sección E)."
}
```
