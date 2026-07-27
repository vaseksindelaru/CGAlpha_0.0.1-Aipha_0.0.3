—
type: learning-note
project: CGAlpha
tags: [proyecto/cgalpha, learning, graphify, tutor-activo, fase-6]
created: 2026-07-27
part: 6-of-6
prev: 05-synthesis-los-cinco-hilos
next: null
grafo_generado: 2026-07-27
---

# Clase Magistral 6: Graphify como Tutor Activo

> **Nivel**: S1 (Learning) — Herramienta de aprendizaje  
> **Fase**: Fase 6 — Integración graphify + Obsidian como sistema tutor  
> **Duración estimada**: 2 sesiones (1 para configuración + flujo, 1 para aplicación sobre la comunidad que elijas)  
> **Prerrequisito**: Clases 1-5 completadas; graphify funcionando sobre CGAlpha (`graphify explain "OracleTrainer_v3"` devuelve resultado)

## ⚠️ Cómo usar esta clase

Esta clase **no se lee de principio a fin**. Se ejecuta en orden:

1. Cada paso tiene una **acción concreta** (un comando graphify que corrés) y una **pregunta** que respondés en la nota
2. Antes de pasar al siguiente paso, **no seguís** — primero ejecutás la acción y escribís tu respuesta
3. La última sección ("Cierre") es donde se compara lo que predijiste con lo que el grafo muestra

---

## Paso 1 — Orientación espacial (antes de abrir un solo archivo)

**Acción**: Corré esto sobre el grafo de CGAlpha:

```bash
cd ~/CGAlpha_0.0.1-Aipha_0.0.3
PYTHONPATH=/home/vaclav/.local/share/uv/tools/graphifyy/lib/python3.13/site-packages \
/home/vaclav/.local/share/uv/tools/graphifyy/bin/graphify explain "OracleTrainer_v3" --graph graphify-out/graph.json
```

**Lo que vas a ver**: 47 conexiones para OracleTrainer_v3 — imports, métodos, test que lo usan, referencias desde MemoryPolicyEngine y EvolutionOrchestrator.

**Pregunta**: ¿Qué nodos tienen más aristas entrantes? ¿Y los que tienen más salientes? Los que tienen muchas entrantes probablemente son puntos de alta responsabilidad (otros dependen mucho de ellos). Los que tienen muchas salientes son puntos de integración (tocan muchos lugares). ¿Son los mismos nodos o distintos?

**Escribí en esta nota** (o en una nota aparte que linkees):

- Los 3 nodos que más aristas entrantes tienen → por qué creés que otros dependen tanto de ellos
- Los 3 nodos que más aristas salientes tienen → qué conectan y por qué

---

## Paso 2 — Hipótesis escrita, antes de leer

Con solo el grafo a la vista, **sin abrir ningún archivo todavía**:

**Acción**: Elegí un nodo de alta centralidad (alto grado) que no conozcas bien y escribí en la nota qué creés que hace. Solo por el nombre y por la cantidad de conexiones que tiene.

Ejemplo (no copiar — hacé el tuyo propio):
> *OracleTrainer_v3 tiene 47 conexiones y conecta con MemoryPolicyEngine y EvolutionOrchestratorV4. Antes de leer el código, creo que OracleTrainer_v3 es el coordinador que decide cuándo el sistema debe reentrenar el modelo y cuándo parar — conecta con memoria (para recordar qué propuestas ya probó) y con orchestrator (para decidir el siguiente paso del ciclo).*

**Pregunta del tutor**: ¿Estás prediciendo basándote en patrones del grafo (nombre + conexiones) o estás adivinando? La diferencia importa: predecir activa una forma de memoria que adivinar no activa.

---

## Paso 3 — Lectura dirigida por el grafo, no lineal

**Acción**: Ahora sí, abrí el archivo fuente (`cgalpha_v3/`) que corresponde al nodo elegido. Pero NO lo leés de arriba a abajo. Seguís este orden:

1. Buscá los nodos con los que OracleTrainer_v3 conecta (según el output de `graphify explain`)
2. Leé primero los métodos que implementan esas conexiones
3. Después leé el `__init__` y las estructuras de datos internas
4. Al final, el resto del archivo

**Pregunta del tutor**: ¿El orden de lectura que sugerí arriba tiene sentido dado el patrón de conexiones que viste? ¿Hay algún nodo conectado que no tiene método — lo encontraste como dataclass o como constante? Si sí, ¿cómo cambia la forma en que entendés su rol?

---

## Paso 4 — Verificación de camino

**Acción**: Elegí dos nodos que mencionaste en tu hipótesis del Paso 2 y verificá si realmente están conectados:

```bash
/home/vaclav/.local/share/uv/tools/graphifyy/bin/graphify path "OracleTrainer_v3" "MemoryPolicyEngine" --graph graphify-out/graph.json
```

**Lo que vas a ver**: el camino real (o la ausencia de camino) entre los dos nodos.

**Pregunta del tutor**: ¿El camino real coincide con tu intuición del Paso 2? Si el camino existe pero más corto o largo de lo que esperabas, ¿qué te dice eso sobre la relación real que tenés entre esos dos conceptos? ¿Y si el camino no existe y vos creías que sí?

**Escribí en la nota**:

- Mi hipótesis del Paso 2 sobre la relación entre [nodo A] y [nodo B]: ___
- El camino real que graphify encontró: ___
- Lo que esto me dice sobre mi comprensión (qué acerté, qué me equivoqué): ___

---

## Paso 5 — Transferencia: una pregunta que el tutor no hizo

**Acción**: Elegí dos nodos que **la clase no mostró explícitamente** y predecí si están conectados antes de corrid `graphify path`.

Ejemplo de la comunidad Testing (Clase 4):
- El tutor mostró `test_clearance_instrumentation_robust` y `test_oracle_encoding.py`
- Pero no mostró `test_memory_v4` → predecí que estaría conectado a `MemoryPolicyEngine` porque comparten el nombre "memory"
- Ejecuté `graphify path "test_memory_v4" "MemoryPolicyEngine"` → confirmado

**Pregunta del tutor**: Si graphify confirma tu predicción, ¿es porque tu intuición es buena o porque el nombre "memory" ya te daba la pista? ¿Cómo sabrías la diferencia?

---

## Aplicación práctica: las 3 comunidades reales de CGAlpha

Usá este flujo de 5 pasos sobre estas tres comunidades. Las preguntas específicas para cada una están en el documento de metodología (`development/04-metodologia-tutor-graphify.md`).

| Comunidad | Para este paso, elegí un nodo... | Pregunta clave |
|---|---|---|
| **Oracle / ML** (47-52 nodos) | `OracleTrainer_v3` | ¿Por qué esta comunidad tiene 47+ nodos si el problema conceptual es binario (BOUNCE o BREAKOUT)? |
| **Gobernanza** (Orchestrator → CodeCraftSage → Memory) | `EvolutionOrchestratorV4` | El grafo NO muestra arista directa a TripleCoincidenceDetector — ¿qué te dice la ausencia de una conexión? |
| **Testing / Triple Barrier** | `test_clearance_instrumentation_robust` | Si un test está poco conectado, ¿es porque el módulo está bien diseñado (bajo acoplamiento) o porque el test no cubre las rutas reales? |

> **Importante para Testing/Clase 4**: `test_clearance_instrumentation_robust` es exactamente el test que falla con max_price_since_detection=10200 (el bug de fixture que investigamos en `development/01-max-price-since-detection.md`). Usar esta comunidad como material de práctica conecta la Clase 6 con un hallazgo real de las clases anteriores.

---

## Plantilla de frontmatter para notas de obsidian

Copiá esta plantilla en cada nota que generes con este flujo:

```yaml
---
type: learning-note
project: CGAlpha
tags: [proyecto/cgalpha, learning, graphify, fase-6]
created: 2026-07-27
prev: 05-synthesis-los-cinco-hilos
next: null
comunidad: oracle-ml
nodos_clave: [OracleTrainer_v3, DeferredOutcomeMonitor, L2RingBuffer]
nivel: intermedio
grafo_generado: 2026-07-27
---
```

**Campos explicados**:
- `comunidad`: qué comunidad de graphify estás estudiando (`oracle-ml`, `gobernanza`, `testing`)
- `nodos_clave`: los nodos principales de esa comunidad (copiá del grafo)
- `grafo_generado`: fecha de la última generación del grafo — **no es decorativo**. Antes de estudiar, chequear esta fecha vs. la fecha del último commit a P1 (Oracle v6) en `NEXUS_SUPERIOR.md`. Si hay desfase, regenerar el grafo primero.
- `prev`/`next`: la secuencia de la clase no depende de que el estudiante recuerde el orden — Obsidian lo hace por él via Dataview

---

## Cierre

**La Prueba de Aprendizaje Real** (no repetir las preguntas de la clase, sino hacerle al grafo una pregunta que el tutor no anticipó):

Después de completar los 5 pasos sobre una comunidad, ejecutá esto:

```bash
graphify query "neighbors of [una comunidad que NO estudiaste]" --graph graphify-out/graph.json
```

Si el resultado genera una pregunta nueva que vos *no* pediste — el aprendizaje prendió. No cuando repetís lo que la clase enseñó, sino cuando empezás a hacerle preguntas al grafo que la clase no preparó.

**Esto es lo que diferencia a un estudiante que aprendió de uno que solo navegó**: el primero tiene predicción verificada + un camino nuevo que descubrió solo. El segundo tiene un tour guiado. La Clase Magistral 6 entrena al primero.

---

## Referencias

- Clase 5 previa (síntesis de los cinco hilos): `05-synthesis-los-cinco-hilos.md`
- Metodología de tutor con graphify (resultado de consulta a LLM externo): `../development/04-metodologia-tutor-graphify.md`
- Máster class content: `../development/03-llm-externo-audit.md` (clarifies reliability categories)
- max_price_since_detection investigation (test fixture bug to practice on): `../development/01-max-price-since-detection.md`
- NEXUS_SUPERIOR governance (for `grafo_generado` date comparison): `../development/02-gobernanza-nexus-superior.md`

## Advertencia de alcance

El documento de metodología (`04-metodologia-tutor-graphify.md`) fue generado por un LLM externo que no ejecutó graphify él mismo — sus sugerencias sobre export SVG embebido y cruce de grafos de notas vs código asumen capacidades que necesitan verificarse contra graphify mismo. No confundir sugerencias no verificadas con capacidades confirmadas de graphify.

---

## Diagrama del flujo (para referencia rápida)

```
┌─────────────────────────────────────────────────────┐
│ CLASE 6: Graphify como Tutor Activo                 │
│                                                     │
│  [Grafo de CGAlpha]                                 │
│        │                                            │
│        ▼                                            │
│  Paso 1: Orientación espacial                      │
│  → graphify explain "nodo"                          │
│  → identificar hubs y hojas                          │
│        │                                            │
│        ▼                                            │
│  Paso 2: Hipótesis escrita (antes de leer)         │
│  → elegir un nodo, predecir qué hace               │
│  → escribir predicción en la nota                   │
│        │                                            │
│        ▼                                            │
│  Paso 3: Lectura dirigida por el grafo             │
│  → leer hubs primero, hojas después                  │
│  → no orden alfabético, no orden de archivo        │
│        │                                            │
│        ▼                                            │
│  Paso 4: Verificación de camino                    │
│  → graphify path "A" "B"                            │
│  → comparar con hipótesis del Paso 2               │
│  → registrar aciertos y errores en la nota          │
│        │                                            │
│        ▼                                            │
│  Paso 5: Transferencia                              │
│  → elegir DOS nodos que la clase NO mostró          │
│  → predecir conexión → verificar con graphify       │
│  → si predices bien Y descubres algo nuevo →       │
│    aprendizaje real (no solo tour guiado)           │
│                                                     │
│  🔑 Señal de aprendizaje:                          │
│  hacerle al grafo una pregunta que el tutor NO      │
│  anticipó                                           │
└─────────────────────────────────────────────────────┘
```