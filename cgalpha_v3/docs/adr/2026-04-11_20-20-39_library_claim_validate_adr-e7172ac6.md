# ADR adr-e7172ac6

- Fecha: 2026-04-11T20:20:39.249773+00:00
- Trigger: `library_claim_validate`
- Iteración: `2026-04-11_20-20_01`
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
    "src-5babae85"
  ],
  "primary_source_gap": true,
  "claim_ok": false,
  "validation_message": "claim 'Momentum intradia robusto' apoyado solo en fuentes ['tertiary'] — se requiere ≥1 primaria",
  "sources_total": 1,
  "primary_count": 0,
  "missing_source_ids": [],
  "backlog_item_id": "bl-7109b90d"
}
```
