# Application — cgalpha_v3

## Propósito
Casos de uso y orquestación de CGAlpha v3. Coordina dominio, infraestructura
y la capa de riesgo sin mezclar responsabilidades.

## Inputs / Outputs

- **Inputs:** comandos del usuario (via GUI o CLI), eventos del sistema
- **Outputs:** resultados de propuestas, estados de rollback, cápsulas de aprendizaje

## Módulos

| Módulo | Responsabilidad |
|--------|----------------|
| `change_proposer.py` | Genera propuestas con plantilla JSON v3.0-audit |
| `experiment_runner.py` | Ejecuta backtests con fricciones y walk-forward |
| `rollback_manager.py` | Snapshots automáticos y restauración verificable |

## Contratos

- `RollbackManager.take_snapshot(proposal_id, config, ...)` → `Path`
- `RollbackManager.restore(snapshot_path)` → `dict` (verificado por hash)
- Todo cambio registrado en `memory/iterations/YYYY-MM-DD_HH-MM/`

## Dependencias

- `cgalpha_v3.domain.models`
- `cgalpha_v3.risk.risk_manager`
- Librería estándar Python

## Estado actual

🚧 FASE 1/3 — `RollbackManager`, `ChangeProposer` y `ExperimentRunner` implementados en versión operativa mínima.

## Próximo incremento

- Integrar dataset de mercado real en `ExperimentRunner`
- Persistir artefactos de experimentos en `knowledge_base/experiments/`
- Generar cápsula de aprendizaje en 5 campos por cada cambio aplicado
