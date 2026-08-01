# Metodología del Tutor con graphify — Clase Magistral + Obsidian

> Para Hermes (tutor AI) y Vaclav (estudiante). Respuesta a las 6 preguntas sobre cómo convertir graphify en hilo conductor, no en demo puntual.

## Nota de alcance — qué sé y qué no

Dos honestidades antes de entrar: no tengo acceso a graphify en sí, así que donde propongo algo que asume una capacidad suya (por ejemplo, comparar dos grafos automáticamente), lo marco como *"a verificar si graphify ya lo hace, o si hay que scriptearlo aparte"* — no lo doy por hecho. Tampoco vi la estructura real de backlinks del vault de notas de Vaclav, solo la descripción de las 5 clases — así que en la sección de detección de lagunas describo *patrones a buscar*, no un diagnóstico ya hecho sobre el vault actual.

---

## 1. El flujo de 3-5 pasos — graphify como hilo conductor, no demo de apertura

La diferencia entre "mostrar el grafo al inicio de la clase" y "usar el grafo como hilo conductor" es que en el segundo caso el estudiante vuelve al grafo en cada fase del aprendizaje, no una sola vez. Cinco pasos, cada uno con una acción concreta:

**Paso 1 — Orientación espacial (antes de abrir un solo archivo).**
`graphify explain "OracleTrainer_v3"` (o el nodo que corresponda). Antes de leer código, ver el tamaño de la comunidad y el grado de cada nodo. Pregunta guía: ¿qué nodos tienen más aristas entrantes o salientes? Esos son probablemente los puntos de mayor responsabilidad — vale la pena leerlos primero, no en el orden en que aparecen en el archivo. graphify ya tiene un comando dedicado para esto — `graphify god-nodes` — no hace falta escanear la leyenda a ojo buscando los conteos más altos.

**Paso 2 — Hipótesis escrita, antes de leer.**
Con solo el grafo a la vista (sin código todavía), el estudiante escribe en la nota de Obsidian qué cree que hace cada nodo, basándose en el nombre y la posición. Este paso es el que casi siempre se salta, y es el que más aprendizaje genera — escribir una predicción y después compararla contra la realidad activa la memoria de una forma que leer pasivamente no logra.

**Paso 3 — Lectura dirigida por el grafo, no lineal.**
Leer el código en el orden de centralidad que sugiere graphify (los hubs primero, las hojas periféricas después), no de arriba a abajo del archivo. Esto refleja cómo se entiende realmente un sistema: núcleo antes que detalle.

**Paso 4 — Verificación de camino.**
Ya con el código leído, usar `graphify path "A" "B"` para confirmar o corregir la intuición formada en el Paso 2. Si el camino real no coincide con la hipótesis, ahí está exactamente la laguna — y ahora es visible, no una sospecha vaga. Cuando la pregunta no es "¿A se conecta con B?" sino "¿qué depende de X?" — por ejemplo, antes de tocar un parámetro sensible — `graphify affected "X"` hace ese traversal inverso sin necesitar ya saber el destino.

**Paso 5 — Transferencia: una pregunta que el tutor no hizo.**
El estudiante elige dos nodos que la clase *no* mostró explícitamente y predice si hay conexión antes de correr `graphify path`. La señal de que el aprendizaje prendió no es que el estudiante repita las preguntas de la clase — es que empiece a hacerle al grafo preguntas que el tutor no anticipó.

---

## 2. Preguntas del tutor — 3 comunidades reales de CGAlpha

No genéricas: ancladas a comunidades que existen de verdad en tu grafo, con contexto real del proyecto.

| Comunidad | Lo que muestra el grafo | Pregunta del tutor |
|---|---|---|
| **Oracle / ML** (**82 nodos según la leyenda real de graphify** — la cifra "47-52" que se usaba antes corresponde a la comunidad `TechnicalSpec`, no a Oracle; corregido tras inspeccionar el `graph.html` real) | Un nodo enorme para algo que conceptualmente suena simple: "predecir BOUNCE o BREAKOUT" | *"¿Por qué esta comunidad tiene 82 nodos si el problema conceptual es binario? ¿Qué te dice eso sobre la diferencia entre la complejidad del problema y la complejidad de ingeniería necesaria para resolverlo sin trampas (sin leakage temporal, con encoding determinista, con features reales de microestructura en vez de un snapshot estático)?"* — Este es un caso donde la respuesta correcta no es "está sobre-diseñado", sino entender qué problema real resuelve cada pieza de esa complejidad. (Nota: `TripleCoincidenceDetector`, con 108 nodos, es la comunidad más grande de todo el grafo — también sirve, y mejor, para esta misma pregunta.) |
| **Gobernanza** (EvolutionOrchestratorV4 ↔ CodeCraftSage ↔ MemoryPolicyEngine) | Hay arista de Orchestrator hacia CodeCraftSage y hacia MemoryPolicyEngine, pero **no** hacia TripleCoincidenceDetector directamente | *"El grafo NO muestra una arista directa entre el Orchestrator y el detector de señales de trading — ¿por qué? ¿Qué te dice la ausencia de una conexión, no solo la presencia de una, sobre cómo está diseñado el sistema?"* — La ausencia de arista es tan pedagógica como la presencia: el Orchestrator no debería tocar la lógica de trading en runtime, solo a través de un parche aplicado por CodeCraftSage. |
| **Testing / Triple Barrier** (Clase 4) | Algunos tests tienen pocas aristas de entrada comparados con otros | *"Si un test está poco conectado en el grafo, ¿es señal de que el módulo que testea está bien diseñado (bajo acoplamiento), o de que el test no cubre las rutas reales de uso?"* — Y este no es un ejemplo hipotético: `test_clearance_instrumentation_robust` es exactamente ese caso. Lo diagnosticamos hoy — el test fallaba no por un bug de producción, sino porque el fixture inyectaba una zona antes de que el loop llegara al índice donde esa zona "nacía". Es material de clase ya verificado, listo para usar. |

**Sobre los nombres de comunidad** (ej. "Oracle / ML", que en el grafo real aparece como `OracleTrainer_v3`): no es el nodo de mayor grado — es un LLM (`label <path>`, backend configurable) leyendo los labels de todos los nodos de la comunidad y sintetizando un nombre. Desglose empírico real de las 151 comunidades, **verificado directo contra `graph.json`**: 40% nombres tipo archivo (`live_adapter.py`), 34% nombres tipo clase (`OracleTrainer_v3`, `ShadowTrader`), 26% frases descriptivas genuinas (`adaptive_lookahead`, `check_oos_leakage`, `renderTrainingRetestTable`) — cero artefactos de texto crudo; lo que parecía un banner de comentario filtrado era solo un artefacto de renderizado del reporte markdown, no del dato real. `community_name` es confiable para mostrar a un estudiante tal cual.

---

## 3. Obsidian como capa pedagógica — qué debería aparecer automáticamente

**Antes de construir nada de lo que sigue:** graphify tiene comandos nativos `wiki` y `obsidian` para exportar directamente a formato de vault. Correrlos primero y ver si ya resuelven esto — lo de abajo es el plan B si el output nativo no alcanza, no un punto de partida.

La idea central: que el estudiante no tenga que *recordar* la estructura, sino que el vault la traiga siempre a la vista. Al abrir cualquier nota de clase, debería aparecer, sin que el estudiante lo pida:

- **El subgrafo relevante embebido** (graphify exportando a SVG/HTML e insertándolo en la nota, no solo un link externo al HTML completo de 2798 nodos — nadie navega eso desde una nota).
- **Backlinks automáticos vía Dataview** a otras notas que tocan la misma comunidad, usando un campo de frontmatter (`comunidad:: oracle-ml`) en vez de enlaces manuales que hay que mantener a mano.
- **Nota anterior / siguiente**, vía frontmatter (`prev::`, `next::`), para que la secuencia de 5 clases no dependa de que el estudiante recuerde el orden.
- **Un campo por completar antes de leer**: `## Mi hipótesis` (se llena en el Paso 2 de la sección anterior). Para el "después" (Paso 4, lo que el grafo confirmó o contradijo), no hace falta inventar un segundo campo manual — graphify ya tiene `save-result` (guarda el resultado de cada consulta en un loop de memoria) y `reflect` (agrega esos resultados en `LESSONS.md`, con decaimiento — half-life). Es, estructuralmente, el mismo mecanismo que las reflexiones críticas del propio Prompt Fundacional de CGAlpha (§6): acumular evidencia, degradar lo viejo, promover lo que persiste. Mejor enlazar `LESSONS.md` desde la nota que duplicar ese registro a mano en el frontmatter.

Plantilla de frontmatter sugerida:

```yaml
---
comunidad: oracle-ml
nodos_clave: [OracleTrainer_v3, DeferredOutcomeMonitor, L2RingBuffer]
nivel: intermedio
prev: 02-arquitectura-y-oop
next: 04-testing-sistema-inmunologico
grafo_generado: 2026-06-24
---
```

El campo `grafo_generado` no es decorativo — vuelve más abajo en la crítica honesta (punto 7.1).

---

## 4. El procedimiento generalizable — 5 pasos para cualquier proyecto

Lo específico de CGAlpha (Oracle, Orchestrator, ShadowTrader) no es transferible. Esto sí:

1. **Generar el grafo** con cualquier herramienta de análisis estático que produzca nodos + aristas (graphify u otra).
2. **Identificar comunidades por tamaño y grado, no por nombre de archivo.** Las comunidades grandes son donde vive la complejidad real del dominio — no necesariamente donde vive la mayor cantidad de líneas de código.
3. **Formular una pregunta de "por qué existe esta forma" antes de leer código**, para cada comunidad. Esta es la parte central transferible: usar el grafo para *generar preguntas*, no solo para *navegar*.
4. **Leer siguiendo el orden de centralidad** (hubs primero), no el orden alfabético o el orden de los archivos en el directorio.
5. **Cerrar el ciclo con un `path` elegido por el estudiante**, entre dos nodos que el material de clase no mostró. La generalización se prueba haciendo preguntas nuevas, no repitiendo las de la clase.

---

## 5. Detección de lagunas — patrones en el grafo de notas

Esto es sobre el grafo de *notas* (el modo texto de graphify), no el de código. Tres patrones a buscar:

- **Nodos huérfanos**: una nota de clase sin ningún backlink desde otras notas. Sugiere que el estudiante nunca conectó ese tema con nada más — quedó aislado, no integrado.
- **Aristas unidireccionales sin retorno**: A enlaza a B, pero B nunca fue revisitado después de creada la nota. Sugiere comprensión de paso, no consolidada.
- **La técnica más potente: comparar el grafo de notas contra el grafo de código real.** Si el subgrafo de *notas* sobre "Oracle" nunca menciona `DeferredOutcomeMonitor`, pero el subgrafo de *código* real tiene una arista fuerte hacia ese nodo — ahí está la laguna, expuesta como una divergencia estructural entre el mapa mental (las notas) y el territorio real (el código). No sé si graphify hace este cruce de forma nativa hoy; si no, es probablemente la integración de mayor apalancamiento de todas las que menciono acá (ver 6.3).

---

## 6. Niveles de profundidad en la investigación de correlaciones

graphify tal como está descripto (`explain`, `path`) muestra conexiones *explícitas* — aristas reales del código. Pero "correlación" es un concepto más amplio: relaciones que existen sin que haya una arista directa. El eje de "profundidad" no es solo "cuánto esfuerzo" — es, más precisamente, cuánto se puede resolver sin LLM antes de necesitar uno. Esto es la misma disciplina de "determinista primero, LLM como fallback" (§7.8 del Prompt Fundacional de CGAlpha), aplicada acá a la búsqueda de correlaciones.

| Nivel | Qué busca | ¿LLM? | Costo | Ejemplo real |
|---|---|---|---|---|
| **0 — Arista directa** | ¿Existe conexión explícita entre A y B? | No | Instantáneo | Ya existe: `graphify path "A" "B"` |
| **1 — Vecindad compartida** | A y B no se conectan directo, pero comparten vecinos | No | Rápido, pero requiere una capa nueva (Jaccard entre conjuntos de vecinos) sobre el output crudo de graphify | `EvolutionOrchestratorV4` y `test_orchestrator_v4.py` comparten vecinos (`TechnicalSpec`, `EvolutionResult`) sin que uno importe al otro siempre |
| **2 — Semántica (LLM lee contenido)** | Sin arista ni vecinos compartidos, pero conceptualmente relacionados | Sí, un LLM call por par | Moderado | `test_clearance_instrumentation_robust` no tiene arista con `_cleanup_expired_zones()` — el test llama a `process_stream`, no a esa función puntual. Hizo falta leer el código real y razonar sobre el *orden de ejecución* dentro del mismo loop para encontrar la causa del fallo. |
| **3 — Cruce entre dominios** | Correlacionar código ↔ notas ↔ gobernanza (EVO-TICKETs, ADRs) | Sí, con más contexto e iteración | El más alto | Verificar si un EVO-TICKET de gobernanza coincide con lo que el código implementa de verdad — dos fuentes heterogéneas cruzadas. |

**El diagnóstico completo hecho hoy sobre este mismo proyecto fue, en esencia, una investigación de correlación de Nivel 2-3 hecha a mano** — el bug de `max_price_since_detection`, la verificación de `QUARANTINE_GATE`. No es un diseño hipotético: es sistematizar algo que ya se ejecutó turno a turno entre un humano y un LLM.

**Quién decide la profundidad — dos modos, no excluyentes:**
- *Auto-escalado* (default recomendado): arranca en Nivel 0, sube solo si ese nivel no encuentra nada interesante — no gasta LLM si el grafo ya contesta.
- *Profundidad explícita*: pedir Nivel 2 o 3 directamente cuando ya se sospecha que la relación es sutil (ej. un test falla sin razón obvia en el grafo).

```
graphify correlate "A" "B" --depth=0    # arista directa — ya existe, vía path
graphify correlate "A" "B" --depth=1    # + vecinos compartidos — a construir
graphify correlate "A" "B" --depth=2    # + LLM lee contenido real — a construir
graphify correlate "A" "B" --depth=3    # + cruce entre grafos/dominios — a construir
graphify correlate "A" "B"              # sin --depth: auto-escalado desde 0
```

Actualización con datos confirmados (`GRAPH_REPORT.md`, `--help`, `skill.md` de graphify): los 3 valores de `confidence` son `EXTRACTED` (94%, determinista — AST/imports), `INFERRED` (6%, 341 aristas, confianza promedio 0.51 — semántico, generado por LLM en `--mode deep`) y `AMBIGUOUS` (0% en este grafo). El cruce código+notas del Nivel 3 también está confirmado, no es diseño propio: `detect()` clasifica archivos en `code`/`document`/`paper`/etc. en una sola corrida, con extracción AST y extracción semántica (subagentes LLM) corriendo en paralelo.

Con esto, el Nivel 1 (aristas `INFERRED`) y parte del Nivel 3 ya existen — pero no confundir esto con el Nivel 2 tal como lo propuse acá. Los `INFERRED` de graphify se generan **en tiempo de extracción**: un LLM pasa una vez por todo el corpus y hornea lo que encuentra, antes de que nadie pregunte nada puntual — mismo problema de "foto, no película" que la crítica 7.1 ya señala. El Nivel 2 que propongo es investigación **a demanda**: el estudiante pregunta por un par específico ahora mismo, y el LLM lee y razona sobre exactamente ese par, aunque la extracción original nunca lo haya considerado. Son complementarios — uno no reemplaza al otro. Además, una confianza promedio de 0.51 en los `INFERRED` es apenas más que una moneda al aire: tratarlos con escepticismo real al mostrárselos a un estudiante, no como hecho confirmado.

**Concentración medida — y una trampa de comparación detectada al normalizar.** De las 341 aristas `INFERRED`, 38.4% aterriza en los 10 targets más frecuentes, sobre 93 targets únicos. Comparado en crudo contra `EXTRACTED` (8.3% en top-10, sobre 1879 targets únicos), parece un artefacto de atracción por hub. Pero comparar porcentajes crudos entre muestras de tamaños tan distintos (341 vs 5330 aristas, 93 vs 1879 targets) no es válido — con una muestra 16 veces más chica, el top-10 siempre va a capturar un % mayor, aunque el proceso de fondo sea idéntico. Normalizando por la razón top-10/promedio-general (que sí es comparable entre escalas distintas): `EXTRACTED` da ≈15.6× (44.2 de promedio en el top-10 contra 2.84 de promedio general), `INFERRED` da ≈3.6× (13.1 contra 3.67). **Por esta medida, `EXTRACTED` está más concentrado en sus propios hubs que `INFERRED`, no menos** — lo opuesto a la lectura inicial. Lo más consistente con esto: el codebase ya tiene una distribución de grado muy sesgada por naturaleza, e `INFERRED`, con una muestra mucho más chica, no alcanza a desmentir esa misma estructura — no evidencia clara de que el LLM esté sesgado hacia hubs más allá de lo que el propio grafo determinista ya es. Test definitivo pendiente si se quiere certeza completa: bootstrap submuestreando 341 aristas de `EXTRACTED` muchas veces y viendo dónde cae el 38.4% real de `INFERRED` contra esa distribución. Mitigación práctica razonable de todos modos, se resuelva o no: filtrar por `degree(target) < umbral` o exigir `confidence > 0.7` antes de mostrar un `INFERRED` como hallazgo.

---

## 7. Lo que falta — con honestidad, no cortesía

Cinco cosas, ordenadas por importancia. No es "está bien así, pero...": son brechas reales.

**7.1 — El grafo es una foto, el sistema es una película.**
2798 nodos y 5671 aristas son un snapshot del momento en que corriste graphify. CGAlpha evoluciona rápido — el Oracle solo pasó de 11-12 features a 23-24 en cuestión de semanas, y hay reconstrucciones activas documentadas en el propio proyecto (P1-P9). Si las Clases Magistrales no se regeneran contra el grafo actual, van a terminar enseñando una arquitectura que ya no existe — literalmente el mismo problema que ya vivimos hoy con una evaluación externa que describía un estado del proyecto superado hace meses. **Actualización:** graphify ya tiene `watch` (auto-rebuild al cambiar archivos), `hook install` (git hook post-commit) y `check-update` (staleness check pensado explícitamente para cron) — la mitigación no hay que construirla, ya existe en tres formas distintas. El gap real es si alguno está efectivamente activado, no si la capacidad existe. Mitigación concreta mientras tanto: el campo `grafo_generado` de la plantilla de arriba no es decorativo — antes de estudiar una clase, chequear esa fecha contra la última reconstrucción documentada (P1-P9 en `NEXUS_SUPERIOR.md`) y regenerar si hay desfase.

**7.2 — Se verifica que el estudiante *ejecutó* el comando, no que *entendió* el resultado.**
Correr `graphify explain` o `graphify path` da un output, pero nada en el flujo captura si esa salida se interpretó bien. La sección 1 ya integra esto (Paso 2: hipótesis antes de leer), pero vale la pena nombrarlo como brecha explícita — sin ese paso, graphify es una herramienta de navegación, no de tutoría.

**7.3 — Grafo de código y grafo de notas: la capacidad de cruzarlos ya existe, falta usarla para esto.**
Confirmado: `detect()` clasifica archivos en `code`/`document`/`paper`/etc. en una sola corrida, con extracción AST y extracción semántica corriendo en paralelo — no son dos herramientas separadas como asumí originalmente. El gap real no es técnico, es de uso: nadie corrió todavía graphify apuntando a la vez al código de CGAlpha y al vault de notas de Vaclav, con el propósito específico de comparar dónde el `file_type: note` del estudiante diverge del `file_type: code` real (sección 5). Sigue siendo la mejora de mayor apalancamiento de todas — solo que ahora es "correrlo y mirar", no "construirlo".

**7.4 — El orden de las 5 clases parece narrativo, no verificado contra el grafo.**
"Viaje de un Dato → Arquitectura/OOP → ML → Testing → Síntesis" es un orden razonable a primera vista, pero no hay evidencia de que se haya chequeado contra el grafo real de dependencias. Es fácil de verificar: si los nodos centrales de la Clase 1 tienen aristas fuertes hacia los nodos centrales de la Clase 2, el orden está bien fundado. Si no, el orden pedagógico ideal podría ser distinto al orden narrativo elegido. Vale la pena correrlo antes de asumir que el orden actual es el óptimo.

**7.5 — Riesgo de que el grafo se confunda con comprensión.**
El grafo muestra *estructura* (quién llama a quién), no *semántica* (por qué existe esa lógica, qué decisión de negocio representa). Si el flujo se queda demasiado tiempo en el nivel del grafo sin bajar a leer código con atención real, el estudiante puede desarrollar una falsa sensación de dominio — "sé cómo se conecta todo" no es lo mismo que "entiendo por qué está hecho así". El grafo también es un mapa, no el territorio — y puede volverse engañoso u obsoleto exactamente igual que cualquier documento, si no se re-valida contra el código que realmente corre.