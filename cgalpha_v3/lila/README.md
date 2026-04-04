# Lila — Biblioteca Central (cgalpha_v3)

## Propósito
Lila es el bibliotecario central de CGAlpha v3. Gestiona el conocimiento con
gobernanza explícita de calidad de fuentes (Sección C del Prompt Maestro).

## Inputs / Outputs

- **Inputs:** documentos (papers, blogs, libros), solicitudes de validación de claims
- **Outputs:** fuentes clasificadas, ratio primarias/totales, validación de claims,
  detección runtime de `primary_source_gap`, backlog adaptativo priorizado

## Reglas de calidad (no negociables)

1. Ningún claim operativo se apoya solo en fuentes **terciarias**.
2. Mínimo **1 fuente primaria** peer-reviewed por claim técnico relevante.
3. Sin `source_id`: la recomendación es rechazada → `insufficient_academic_basis`.
4. Duplicados detectados automáticamente por hash de contenido.
5. Contradicciones registradas explícitamente con nota.

## Clasificación de fuentes

| Tipo | Descripción |
|------|-------------|
| `primary` | Peer-reviewed (ACL, NeurIPS, ICML, JoF, RFS…) |
| `secondary` | Blogs técnicos, libros de texto, notas |
| `tertiary` | Sin autor/fecha verificables, documentación sin cita |

## Contratos

- `LibraryManager.ingest(source)` → `(LibrarySource, is_new: bool)`
- `LibraryManager.validate_claim(source_ids, claim)` → `(bool, mensaje)`
- `LibraryManager.detect_primary_source_gap(source_ids, claim)` → `dict` runtime + auto backlog
- `LibraryManager.search(query, source_type, tags)` → `list[LibrarySource]`
- `LibraryManager.primary_ratio` → `float` (visible en GUI)
- `LibraryManager.add_backlog_item(...)` → `AdaptiveBacklogItem`
- `LibraryManager.list_backlog(status, limit)` → `list[AdaptiveBacklogItem]`
- `LibraryManager.theory_live_snapshot(...)` → snapshot consolidado Theory Live

## Dependencias

Solo librería estándar Python.

## Estado actual

🚧 FASE 1 — `LibraryManager` + detección runtime de gaps + backlog adaptativo implementados.
GUI Theory Live ya conectada al snapshot real de Lila.

## Próximo incremento

- Ingesta inicial de fuentes teóricas de `bible/`
- Detector semántico de contradicciones
- Priorización dinámica de teoría por régimen/impacto operativo
