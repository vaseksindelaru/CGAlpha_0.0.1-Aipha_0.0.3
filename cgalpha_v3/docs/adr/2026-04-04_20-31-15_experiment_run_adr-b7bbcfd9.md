# ADR adr-b7bbcfd9

- Fecha: 2026-04-04T20:31:15.312510+00:00
- Trigger: `experiment_run`
- Iteración: `2026-04-04_20-31_01`
- Nivel evento: `critical`

## Contexto
EXPERIMENT: temporal leakage detectado ([DQ] TemporalLeakageError: 1 feature(s) con timestamp >= OOS start (1775295075.305247). Violación del protocolo OOS (Sección E).)

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "error": "[DQ] TemporalLeakageError: 1 feature(s) con timestamp >= OOS start (1775295075.305247). Violación del protocolo OOS (Sección E)."
}
```
