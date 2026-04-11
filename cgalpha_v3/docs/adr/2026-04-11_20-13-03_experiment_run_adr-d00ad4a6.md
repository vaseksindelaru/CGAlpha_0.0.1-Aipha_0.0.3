# ADR adr-d00ad4a6

- Fecha: 2026-04-11T20:13:03.409856+00:00
- Trigger: `experiment_run`
- Iteración: `2026-04-11_20-13_01`
- Nivel evento: `critical`

## Contexto
EXPERIMENT: temporal leakage detectado ([DQ] TemporalLeakageError: 1 feature(s) con timestamp >= OOS start (1775898783.405498). Violación del protocolo OOS (Sección E).)

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "error": "[DQ] TemporalLeakageError: 1 feature(s) con timestamp >= OOS start (1775898783.405498). Violación del protocolo OOS (Sección E)."
}
```
