# Codex Runbook

## A. Estructura Mínima
1. Implementar `codex_kernel.py` con validadores:
- `validate_schema(entry)`
- `validate_immutability(previous_entry, new_entry)`
- `validate_canonical_protection(entry, canonical_registry)`

2. Definir esquema v4 con campos obligatorios:
- `id`, `type`, `status`, `supersedes`, `harness_inject_when`, `evidence`

## B. Test First
1. Crear `tests/test_codex_integrity.py`
2. Casos mínimos:
- Rechazo de mutación ilegal de entrada firmada
- Rechazo de borrado de IDs canónicos
- Rechazo de entrada fuera de esquema
- Rechazo de `supersedes` inválido
- Rechazo de regla sin evidencia técnica

## C. Seeding por Sesiones
1. Session I: Decisiones (D-XXX) y Bugs (B-XXX)
2. Session II: Lecciones (L-XXX)
3. Session III: Features (F-XXX) y Reglas (R-XXX)
4. Seeding solo vía scripts (`seed_codex_foundations.py`), no edición manual directa

## D. Integración con Harness
1. Hook pre-tarea: resolver entradas relevantes por tipo de tarea
2. Construir `World Model Packet` con:
- Restricciones duras
- Lecciones aplicables
- Reglas operativas vigentes
3. Registrar audit log de inyección por ejecución

## E. Sincronización Regla-Código
Para cada `R-XXX` crítica:
1. Definir `evidence_query` (grep/test marker)
2. Falla de evidencia => falla integridad Codex

## F. Gobierno de Cambios
1. Toda actualización debe ser `supersede`, no overwrite
2. Estados permitidos: `PROPOSED`, `PARTIAL`, `ACTIVE`, `DEPRECATED`
3. Revisión obligatoria para cualquier cambio de IDs canónicos

## G. Gates en CI/CD
1. Ejecutar `pytest tests/test_codex_integrity.py`
2. Validación automática de esquema en entradas nuevas
3. Validación de evidencia para reglas críticas

## H. Operación Diaria
1. Antes de merge: referencia explícita de D/B/L/F/R en PR
2. Después de deploy: verificar logs de inyección Harness
3. Revisión semanal: drift entre Codex declarado y estado real en código
