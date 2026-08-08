# Learning & Memoria — cgalpha_v3

## Propósito
Sistema de memoria estructurada y aprendizaje continuo (Sección D).
5 campos de aprendizaje sincronizados con cada iteración técnica.

## Campos de aprendizaje

| Campo | Descripción |
|-------|-------------|
| `codigo` | Cambios en código, patrones, bugs, refactorizaciones |
| `math` | Fórmulas, modelos, estadística aplicada |
| `trading` | Señales, estrategias, régimen de mercado |
| `architect` | Decisiones arquitectónicas (ADR), patrones, puertos |
| `memory_librarian` | Estado y evolución de la biblioteca Lila |

## Niveles de memoria

Ver tabla completa en `PROMPT_MAESTRO_v3.1-audit.md` Sección D.

| Nivel | Nombre | TTL | Aprobador |
|-------|--------|-----|-----------|
| 0a | Raw intake | 24h | Automático |
| 0b | Normalizado | 7d | Automático |
| 1 | Hechos | 30d | Lila |
| 2 | Relaciones | 90d | Lila |
| 3 | Playbooks | Por versión | Humano |
| 4 | Estrategia | Indefinido | Humano |

## Degradación automática

Si volatilidad >2σ histórico sostenida >20 sesiones: degradar niveles 3/4.

## Salida educativa obligatoria

Cada cambio técnico produce cápsula de aprendizaje en los 5 campos.

## Estado actual

✅ FASE 2 — Memoria inteligente operativa en runtime:

- Motor: `learning/memory_policy.py` (`ingest_raw`, `promote`, `degrade`, `apply_ttl_retention`, `detect_and_apply_regime_shift`).
- API GUI:
  - `GET /api/learning/memory/status`
  - `GET /api/learning/memory/entries`
  - `POST /api/learning/memory/ingest`
  - `POST /api/learning/memory/promote`
  - `POST /api/learning/memory/retention/run`
  - `POST /api/learning/memory/regime/check`
- Persistencia: `memory/memory_entries/*.json`.

## Próximo incremento

- Implementar `LearningCapsule` narrativa por iteración en los 5 campos.
- Conectar `ChangeProposer` para generar cápsula automática por propuesta aceptada.
- Ampliar GUI Learning con historial navegable de cápsulas y filtros por nivel/campo.
