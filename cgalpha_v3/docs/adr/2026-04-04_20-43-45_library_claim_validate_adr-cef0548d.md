# ADR adr-cef0548d

- Fecha: 2026-04-04T20:43:45.575344+00:00
- Trigger: `library_claim_validate`
- Iteración: `2026-04-04_20-43_01`
- Nivel evento: `warning`

## Contexto
LILA: primary_source_gap detectado

## Decisión
- Registrar decisión runtime para trazabilidad.

## Consecuencias
- Revisión futura en auditoría de iteraciones.

## Evidencia
```json
{
  "claim": "Momentum intradia robusto",
  "source_ids": [
    "src-29536413"
  ],
  "primary_source_gap": true,
  "claim_ok": false,
  "validation_message": "claim 'Momentum intradia robusto' apoyado solo en fuentes ['tertiary'] — se requiere ≥1 primaria",
  "sources_total": 1,
  "primary_count": 0,
  "missing_source_ids": [],
  "backlog_item_id": "bl-fc66a56d"
}
```
