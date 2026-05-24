---
marp: true
title: Codex — El ADN de CGAlpha
author: CGAlpha
paginate: true
theme: default
---

# Codex — El ADN de CGAlpha
## De Memoria Documental a Memoria Ejecutable

---

## Problema Real
- El riesgo principal no es lentitud, es amnesia operativa.
- Sin memoria ejecutable, los errores reaparecen como regresiones.
- Casos típicos: thresholds arbitrarios, bugs de persistencia, gates mal configurados.

**Tesis:** autonomía sin memoria verificable escala errores.

---

## Qué es Codex
- Codex = memoria constitucional del sistema.
- No es un repositorio pasivo; es una capa de gobierno técnico.
- Convierte decisiones, bugs y lecciones en restricciones persistentes.

**Resultado esperado:** continuidad técnica más allá de reinicios, modelos y operadores.

---

## Kernel: Leyes Antes que Datos
- Componente: `codex_kernel.py`.
- Función: validar entradas antes de persistencia.

Invariantes:
- Inmutabilidad histórica
- Blindaje canónico (IDs críticos)
- Esquema obligatorio v4 (`harness_inject_when`, evidencia, estado)

---

## Guardrails First
- Primero tests de integridad, luego seeding.
- Suite objetivo: `test_codex_integrity.py`.

Debe bloquear:
- Mutaciones ilegales de historia
- Borrado de IDs canónicos
- Entradas fuera de esquema
- Reglas sin evidencia técnica

---

## Seeding por Capas
1. Session I: Decisiones y Bugs (`D-XXX`, `B-XXX`)
2. Session II: Lecciones (`L-XXX`)
3. Session III: Features y Reglas (`F-XXX`, `R-XXX`)

Regla de honestidad:
- `ACTIVE`, `PARTIAL`, `PROPOSED` según evidencia real, no intención.

---

## Del Archivo al Comportamiento
- Integración vía Harness.
- El Harness construye un `World Model Packet` por tarea.

Semántica operativa:
- `Prohibido`: política niega acción.
- `Inalcanzable`: entorno elimina la opción.

**Objetivo:** que el camino correcto sea el de menor energía.

---

## Verdad Técnica (Regla-Código)
- Si el Codex afirma una regla crítica, debe existir evidencia en código.
- Mecanismo: `evidence_query` (grep/test marker).
- Sin evidencia => falla integridad.

**Principio:** el Codex no puede declarar capacidades fantasma.

---

## Criterios de Aceptación (Go/No-Go)
- 100% entradas nuevas validadas por Kernel + tests.
- 0 mutaciones históricas ilegales aceptadas.
- 100% reglas críticas con evidencia verificable.
- Log de inyección del Harness por ejecución.

---

## Estado Actual y Ventaja
- Pipeline de cosecha endurecido (bypass controlado + auto-disable).
- Dataset protegido contra duplicados (`sample_id` dedup).
- Reporte de cosecha y preparación de sets A/B disponibles.

Ventaja: base operativa estable para evolucionar Codex sin romper producción.

---

## Próximos Pasos
1. Consolidar `test_codex_integrity.py` en CI/CD.
2. Vincular reglas `R-XXX` a evidencia automática.
3. Activar inyección de `World Model Packet` por tipo de tarea.
4. Auditar semanalmente drift entre Codex y código real.

**Cierre:** pasar de “hacer cambios” a “acumular criterio verificable”.
