# Proposal Inbox — CGAlpha
# ========================
# Inbox unificado de propuestas de mejora.
# Ubicacion: documentation/proposals/proposal_inbox.json
#
# NO es un sistema de ejecucion. Es un buffer de ideas con trazabilidad.
# Cuando una propuesta madura, se convierte en EVO-TICKET para pasar por
# el Orchestrator (Cat.1/2/3) y eventualmente CodeCraftSage.

## Flujo de vida de una propuesta

```
Input (tu idea, documento, senal bloqueada, video, etc.)
  │
  ▼
Hermes extrae TechnicalSpec + source metadata
  │
  ▼
Agregado a proposal_inbox.json con status="pending_review"
  │
  ▼
Tu revisas y decides: ¿tiene evidencia suficiente?
  │
  ├─ SÍ → Se convierte en EVO-TICKET en documentation/EVO_TICKET_LOG.md
  │        → Pasa por Orchestrator (Cat.1/2/3)
  │        → CodeCraftSage aplica el cambio
  │
  ├─ NO → status="needs_evidence" + especificar qué falta
  │        → Se queda aquí hasta que haya evidencia
  │
  └─ RECHAZADA → status="rejected" + razón
```

## Cómo crear propuestas nuevas

### 1. Idea propia
Dime: "Creo que X podría mejorar si hacemos Y"
→ Yo evalúo, creo el TechnicalSpec, lo agrego con source_type="idea"

### 2. Documento viejo (Google Doc, PDF, nota)
Dime: "Revisa este documento [URL/nombre]"
→ Yo extraigo señales/parametros, comparo con código actual, genero propuestas
→ source_type: "google_doc" | "pdf" | "note"

### 3. Video/Artículo
Dime: "Mira este video [URL] / este artículo [URL]"
→ Extraigo conceptos clave, los traduzco a TechnicalSpec
→ source_type: "video" | "article" | "blog"

### 4. Señal histórica bloqueada
El sistema detecta que una señal válida fue rechazada
→ Comparo parametros con umbrales actuales
→ Genero propuestas de ajuste

## Cómo revisar el catálogo

| Tú dices | Yo hago |
|----------|---------|
| "Revisa el catálogo" | Muestro todas las propuestas pendientes ordenadas por prioridad |
| "Profundiza en X" | Analizo a fondo: código, tests, riesgos |
| "Aplica propuesta X" | La convierto en EVO-TICKET para el Orchestrator |
| "Descarta propuesta X" | Cambio status a "rejected" con razón |
| "Compara [documento] con código" | Busco diferencias, genero propuestas |

## Estados de una propuesta

| Estado | Significado |
|--------|-------------|
| `pending` | Lista para revisión, evidencia mínima |
| `pending_review` | En cola para que el humano decida |
| `needs_evidence` | Falta datos para justificar el cambio |
| `ready_for_evo` | Aprobada, lista para convertirse en EVO-TICKET |
| `rejected` | Descartada con razón |

## Prioridades

| Prioridad | Criterio |
|-----------|----------|
| `high` | Impacto alto, esfuerzo bajo (quick win) |
| `medium` | Impacto alto, esfuerzo medio |
| `low` | Impacto medio/alto, esfuerzo alto |

## Estructura de cada entrada

```json
{
  "id": "identificador-unico",
  "source": "Descripción corta del origen",
  "source_doc": "Nombre del documento (si aplica)",
  "source_type": "google_doc | pdf | note | video | article | idea | signal",
  "signal_ref": { ... } o null,
  "analysis": "Análisis narrativo de la propuesta",
  "specs": [
    {
      "change_type": "parameter | feature | optimization | bugfix",
      "target_file": "ruta/al/archivo.py",
      "target_attribute": "metodo o variable",
      "old_value": "valor actual",
      "new_value": "valor propuesto",
      "reason": "por qué este cambio mejora el sistema",
      "causal_score_est": 0.0-1.0,
      "confidence": 0.0-1.0,
      "categoria_sugerida": 1|2|3
    }
  ],
  "status": "pending|pending_review|needs_evidence|ready_for_evo|rejected",
  "priority": "high|medium|low",
  "created_at": "ISO timestamp",
  "tags": ["tag1", "tag2"],
  "governance": {
    "evidence_level": "idea|partial|strong",
    "requires_evo_ticket": true,
    "target_evo_ticket": null
  }
}
```
