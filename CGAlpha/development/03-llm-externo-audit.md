—
type: development-note
project: CGAlpha
tags: [proyecto/cgalpha, development, s2, llm-externo-audit, verificado-en-vivo]
created: 2026-07-27
source: chat-con-llm-externo
confidence: alta
---

# 📋 Análisis del LLM Externo — Diagnóstico del Proyecto CGAlpha

> **Origen**: Chat con un LLM externo que propuso 8 pasos de desarrollo y luego verificó sus propias afirmaciones contra el repositorio clonado.
> **Fecha de verificación**: 2026-07-27.
> **Propósito de guardar**: Esta información es candidata a referencia permanente en Obsidian. Se almacana como artefacto de análisis externo verificado, no como opinión del LLM.

## Crónica del análisis del LLM

El LLM propuso un plan de 8 pasos de desarrollo. Antes de aceptar cualquier cosa, verificó cada punto contra el repositorio clonado en vivo. La conclusión central:

### La evaluación externa está obsoleta — de forma significativa

No es "desactualizada por poco" — describe un estado que el proyecto superó hace más de tres meses de trabajo documentado, y la propia crónica de Hermes (hasta el 3 de mayo) también quedó corta.

### Por qué la evaluación externa falló

La evaluación externa citó `S3_ORDEN_DE_CONSTRUCCION.md` (especificación de intención de abril, describe lo que debía pasar) como su fuente — el mismo error que el propio proyecto se prohíbe en su Prompt Fundacional §7.8 ("LLM como fuente de verdad... los números de línea, valores de parámetros, y paths de ficheros deben venir de parsing estático, no de generación de texto").

### Qué hizo el LLM diferente (y por qué pesa más)

| Nivel de evidencia | Qué usó | Por qué pesa más |
|---|---|---|
| Ejecución real | pytest corriendo contra el código clonado — 401 tests, 395/6 | No se puede fingir |
| Grep contra código fuente | grep -n "IDENTITY", classify() completo, wiring | Verificable línea por línea |
| Artefactos derivados | 11 ADRs viviendo en aipha_memory/identity/ | Un sistema no genera 11 docs en un nivel que "aún no existe" |
| Documentos de estado propios | CRB, EVO-TICKET | Más fiable que README porque son fechados |
| README / badges | Descartado activamente | El propio README dice "144 passing" — ni siquiera coincide con los 113 citados externamente |

### Hallazgo más importante que nadie sabía

El proyecto desarrolló una **capa de gobernanza constitucional completa** que no existe en ningún documento almacenado:

- Ciclo de vida formal por artefacto (10 estados)
- Detección de "archivos fantasma" — verifica que los archivos citados como evidencia existan en Git antes de aceptar una afirmación
- 11 ADRs numerados (D-003, D-008... D-014)
- Datasets estructurados como "Set A" / "Set B hybrid" con criterios de promoción explícitos

### Lo que el propio LLM admite que no verificó con el mismo rigor

- `git clone --depth 1` (superficial) — no prueba inactividad real
- 100% de NEXUS_SUPERIOR.md + los 11 ADRs uno por uno
- Coverage % real de la suite completa — solo el 54.77% autoreportado por el CRB de Oracle
- Falsos positivos en tests que cargan modelos `.joblib` (InconsistentVersionWarning de sklearn)

## Los 8 pasos propuestos por el LLM (no aceptados — verificados y corregidos)

El LLM propuso 8 pasos. La verificación en vivo mostró que varios de esos pasos ya se completaron (o nunca pendieron). Los que SÍ están pendientes de forma genuina son:

1. **max_price_since_detection** — Único hallazgo genuinamente abierto de este diagnóstico. Bug de fixture del test, no regresión de producción. El guard `_cleanup_expired_zones()` llega tarde. Puede corregirse en el test ajustando la inyección de la zona.

2. **QUARANTINE_GATE automatización** — Actualmente 🟡 SIMULADO en NEXUS_SUPERIOR.md. Sin verificar qué tan automatizado está.

3. **Lila GUI reconexión (P6.5)** — El "Eco Eterno" del Harness está bloqueado por chat de Lila desconectado. Determinar si es prioridad real de desarrollo.

4. **Oracle v6 Fase A** — ya en progreso (externo), cobertura 54.77%, OOS 0.68.

5. **P0-Codex ingestión** — ya completado (7 entradas).

6. **P5 TripleCoincidenceDetector L2** — ya completado (CRB creado).

## Verdicto

La evaluación externa no solo está desactualizada — describe un estado que el proyecto superó. El propio LLM verificador confirmó esto con evidencia empírica (ejecución real de tests, no solo lectura de texto).

## Lo que me falta aún confirmar

Antes de que esto pueda ser referencia permanente, necesito verificar en vivo:
- [ ] La tabla P0-P9 completa (línea exacta en NEXUS_SUPERIOR.md)
- [ ] El contenido verbatim del fallo de `test_clearance_instrumentation.py`
- [ ] Que `oracle_v6_skeleton.py` existe en `cgalpha_v4/` (no en `cgalpha_v3/`)
- [ ] Que `cgalpha_v4/` es hermano de `cgalpha_v3/` a nivel raíz, no anidado
- [ ] Que el bug de fixture es determinista (10200.0 cada vez, no flake)
- [ ] Que retest_index=0 es el valor medido, no asumido
- [ ] La tabla COMPLETA de los 6 tests fallando con mensajes verbatim

**Estos puntos ya fueron verificados en el turno siguiente** por el propio usuario (vaclav) directamente contra el repo. Los datos de este documento son los datos verificados, no la versión preliminar del LLM.