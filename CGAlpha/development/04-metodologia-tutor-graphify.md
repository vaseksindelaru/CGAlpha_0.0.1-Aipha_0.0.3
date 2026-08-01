—
type: development-note
project: CGAlpha
tags: [proyecto/cgalpha, development, graphify-tutoring-methodology, verificado]
created: 2026-07-27
source: chat-con-llm-externo-sobre-clase-magistral-6
confidence: alta
---

# 📐 Metodología del Tutor con graphify — Respuesta LLM Externo

> Resultado de enviarle al LLM externo la visión de la Clase Magistral y pedirle sugerencias para uso educativo de graphify, tanto para Vaclav como para Hermes.
> Guardado como referencia permanente para diseñar la Clase 6 y futuras sesiones de tutoring.

## Resumen de las 6 respuestas

1. **Flujo de 5 pasos** — orientación espacial → hipótesis escrita → lectura dirigida → verificación de camino → transferencia (pregunta que el tutor no hizo)
2. **Preguntas de tutor ancladas** a 3 comunidades reales de CGAlpha (Oracle/ML, Gobernanza, Testing)
3. **Obsidian como capa pedagógica** — subgrafo embebido, Dataview con campo `comunidad::`, frontmatter con `prev::`/`next::`, campos de predicción verificada
4. **Procedilaje generalizable de 5 pasos** para cualquier proyecto (no solo CGAlpha)
5. **Detección de lagunas** — 3 patrones en el grafo de notas (huérfanos, unidireccionales sin retorno, divergencia grafo-notas vs grafo-código)
6. **Honestidad** — 5 brechas nombradas, ordenadas por importancia

## Las 5 brechas nombradas (6.1–6.5)

| Brecha | Importancia | Acción requerida |
|---|---|---|
| 6.1 — El grafo es una foto, el sistema es una película | Alta | Campo `grafo_generado` + re-generar contra evolución P1-P9 |
| 6.2 — Verificar que ejecutó, no que entendió | Alta | Paso 2 (hipótesis escrita) ya lo cubre, pero falta captura |
| 6.3 — Grafo de código y grafo de notas no se cruzan | Alta | Cruzar ambos grafos = mayor apalancamiento |
| 6.4 — Orden de 5 clases no verificado contra grafo | Media | Chequear si el orden narrativo = orden de centralidad |
| 6.5 — Riesgo de confundir grafo con comprensión | Media | Bajar del grafo a código con intención |

## Diseños derivados de esta respuesta

- **Clase Magistral 6**: será la Clase 6 de la serie, enfocada en graphify como tutor activo (no análisis puntual)
- **Plantilla de frontmatter** para notas de learning con `comunidad::`, `nodos_clave::`, `nivel::`, `prev::`, `next::`, `grafo_generado::`
- **Integración Obsidian + graphify**: Dataview queries por comunidad, embeddings automáticos de subgrafos

## Honestidad propia

El LLM externo no ejecutó graphify — sugiere capacidades que asume (export SVG, cruce de grafos de notas vs código) que necesitan verificación contra las capacidades reales de graphify. Está marcado en las secciones 3 y 5 del documento. No confundir sugerencias no verificadas con capacidades confirmadas de graphify.