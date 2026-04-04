# Mapa de Memoria Inteligente — CGAlpha v3

Fecha: 2026-04-04
Objetivo: dejar claro dónde ver y cómo auditar memoria inteligente durante el desarrollo.

## Niveles objetivo (según prompt v3.1)

- 0a: captura cruda
- 0b: normalización
- 1: hechos verificados
- 2: relaciones/contexto
- 3: playbooks operativos
- 4: estrategia/política

## Dónde está hoy

- Política declarada en prompt: `cgalpha_v3/PROMPT_MAESTRO_v3.1-audit.md` (Sección D).
- Persistencia operativa base:
  - `cgalpha_v3/memory/snapshots/`
  - `cgalpha_v3/memory/iterations/`
  - `cgalpha_v3/memory/archive/`
- Lógica de biblioteca (Lila): `cgalpha_v3/lila/library_manager.py`.

## Qué está implementado vs pendiente

Implementado:
- Gestión de fuentes y validación de claims en Lila.
- Snapshot/restore técnico de rollback (base para memoria operativa).

Pendiente:
- Motor de promoción/degradación automática entre niveles 0a..4.
- TTL real por nivel y retención automática.
- Visualización dedicada en GUI/learning del estado de memoria por nivel.

## Cómo seguir el rastro de cada avance

1. Revisar `cgalpha_v3/CHECKLIST_IMPLEMENTACION.md`.
2. Revisar esta carpeta de estudio (`learning/estudios/2026-04-04_cgalpha_v3_seguimiento/`).
3. Revisar tests nuevos en `cgalpha_v3/tests/`.
4. Revisar cambios de API/GUI en `cgalpha_v3/gui/`.

