# ADR adr-14a59ecf

- Fecha: 2026-04-04T20:31:25.202359+00:00
- Trigger: `library_ingest`
- Iteración: `2026-04-04_20-31_01`
- Nivel evento: `info`

## Contexto
LILA: ingesta nueva [secondary] src-2f615c0c

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "source_id": "src-2f615c0c",
  "source_type": "secondary",
  "is_new": true,
  "title": "Secondary note"
}
```
