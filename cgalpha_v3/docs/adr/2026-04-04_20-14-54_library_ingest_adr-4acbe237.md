# ADR adr-4acbe237

- Fecha: 2026-04-04T20:14:54.768179+00:00
- Trigger: `library_ingest`
- Iteración: `2026-04-04_20-14`
- Nivel evento: `info`

## Contexto
LILA: ingesta nueva [primary] src-999d0e51

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "source_id": "src-999d0e51",
  "source_type": "primary",
  "is_new": true,
  "title": "Primary paper"
}
```
