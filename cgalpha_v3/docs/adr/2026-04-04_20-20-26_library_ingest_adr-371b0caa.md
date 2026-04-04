# ADR adr-371b0caa

- Fecha: 2026-04-04T20:20:26.854273+00:00
- Trigger: `library_ingest`
- Iteración: `2026-04-04_20-20_01`
- Nivel evento: `warning`

## Contexto
LILA: ingesta duplicada [secondary] src-396b4425

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "source_id": "src-396b4425",
  "source_type": "secondary",
  "is_new": false,
  "title": "Same Paper"
}
```
