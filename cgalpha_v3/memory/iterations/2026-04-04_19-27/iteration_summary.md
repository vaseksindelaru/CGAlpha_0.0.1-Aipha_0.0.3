# Iteración: 2026-04-04_19-27 — FASE 0 Arranque

## Objetivo
Creación inicial de `cgalpha_v3/` con estructura completa y módulos base de Fase 0.

## Cambios aplicados

| Módulo | Acción | Descripción |
|--------|--------|-------------|
| `cgalpha_v3/` | Creado | Estructura raíz con README, CHECKLIST, PROMPT_MAESTRO |
| `gui/server.py` | Creado | Servidor Flask: Mission Control, Risk Dashboard, Kill-Switch 2 pasos |
| `gui/static/` | Creado | Control Room HTML/CSS/JS dark premium con autenticación |
| `domain/models/signal.py` | Creado | Signal (ApproachType obligatorio), Proposal (RiskAssessment), MemoryEntry (niveles 0a-4) |
| `risk/risk_manager.py` | Creado | KillSwitch, CircuitBreaker, RiskManager completo |
| `data_quality/gates.py` | Creado | 5 DQ gates + TemporalLeakageError |
| `lila/library_manager.py` | Creado | LibraryManager: ingesta, duplicados, validación claims |
| `application/rollback_manager.py` | Creado | Snapshot + restauración verificable por hash (SLA <60s) |
| `tests/test_risk.py` | Creado | Tests KillSwitch, CircuitBreaker, RiskManager |
| `tests/test_data_quality.py` | Creado | Tests DQ gates + leakage |
| `tests/test_lila.py` | Creado | Tests ingesta, búsqueda, validación claims |

## Riesgos identificados

- GUI server usa Flask (no async): en Fase 3 evaluar migración a FastAPI para SSE nativo.
- `RollbackManager` aún no tiene acceso a `git SHA` real; usa `"unknown"` como placeholder.
- `MemoryEntry` y tabla de transiciones no conectados al sistema de escritura aún (Fase 2).

## Próximos pasos

1. Ejecutar `pytest cgalpha_v3/tests/` y verificar que todos los tests pasan.
2. Arrancar GUI con `python cgalpha_v3/gui/server.py` y verificar paneles.
3. Avanzar a Fase 1: conectar Data Quality Gates con adaptador Binance real.
4. Activar panel Theory Live una vez Lila tenga al menos 3 fuentes ingestadas.

## Aprendizaje por campo

### codigo
- Uso de `dataclass(frozen=True)` para modelos inmutables de dominio.
- `@classmethod new()` como factory limpio sin acoplamiento a UUID externo.
- Separación clara entre `KillSwitchState` (estado puro) y `RiskManager` (orquestador).

### math
- `CircuitBreaker.check_drawdown`: comparación simple >threshold, sin α de confusión.
- Outlier gate usa σ estimado por media aritmética (sin numpy); suficiente para FASE 0.
- En Fase 3: reemplazar por rolling z-score con ventana temporal.

### trading
- `ApproachType` enum fuerza la taxonomía correcta en cada label (Sección O).
- `min_signal_quality_score=0.65` es conservador; ajustar tras backtesting real.
- 3 rechazos consecutivos activa CB: puede ser agresivo en mercados volátiles → revisar.

### architect
- Bounded contexts respetados: `risk/` no importa de `lila/`, `lila/` no importa de `risk/`.
- `RollbackManager` vive en `application/` (caso de uso), no en `infrastructure/`.
- GUI server es `interfaces/` lógicamente; en Fase 1 mover si la estructura lo exige.

### memory_librarian
- `LibraryManager.primary_ratio` es la métrica de calidad de la biblioteca.
- Detección por hash SHA-256 de título+abstract: robusta ante cambios menores de metadata.
- Contradicciones bidireccionales registradas en ambos `source.contradicts`.

## Qué vigilar en el siguiente ciclo

- ¿Los tests de risk pasan en el entorno del usuario? (dependencias Python)
- ¿La GUI sirve correctamente desde `127.0.0.1:8080`?
- Implementar `tests/test_rollback.py` antes de usar RollbackManager en producción.
