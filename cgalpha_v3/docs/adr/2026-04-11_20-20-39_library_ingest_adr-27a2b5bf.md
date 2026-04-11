# ADR adr-27a2b5bf

- Fecha: 2026-04-11T20:20:39.237585+00:00
- Trigger: `library_ingest`
- Iteración: `2026-04-11_20-20`
- Nivel evento: `info`

## Contexto
LILA: ingesta nueva [tertiary] src-5babae85

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "source_id": "src-5babae85",
  "source_type": "tertiary",
  "is_new": true,
  "title": "Blog only signal claim"
}
```
