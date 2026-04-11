# ADR adr-b8532cbf

- Fecha: 2026-04-11T20:13:03.547832+00:00
- Trigger: `library_ingest`
- Iteración: `2026-04-11_20-13_01`
- Nivel evento: `warning`

## Contexto
LILA: ingesta duplicada [secondary] src-6115bbc5

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "source_id": "src-6115bbc5",
  "source_type": "secondary",
  "is_new": false,
  "title": "Same Paper"
}
```
