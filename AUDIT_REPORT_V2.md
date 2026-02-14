# AUDIT_REPORT_V2

## VEREDICTO DE CALIDAD
**Necesita Refactorización**.

El núcleo de Redis fallback funciona, pero el pipeline de Code Craft Sage no está suficientemente robusto para Fase 7-9 sin endurecimiento arquitectónico y de seguridad.

Nota de auditoría: el archivo solicitado `bible/legacy_handover/session_001_context.md` no existe en este workspace. La revisión se hizo contra código real y documentación disponible en `bible/codecraft_sage/*` y `UNIFIED_CONSTITUTION_v0.0.3.md`.

Evaluación de checklist:
- Alineación constitucional (Parte 9 / Triple Barrera): **Parcial**.
- Separación de memoria `operational/` vs `evolutionary/`: **Mayormente correcta**.
- Resiliencia Redis (lock + fallback SQLite): **Parcialmente correcta**.
- Robustez de `ast_modifier.py` y `proposal_parser.py`: **Con riesgos críticos**.
- Preparación para Fase 7 (Ghost Architect) y Fase 8 (Execution Engine): **Insuficiente sin refactor**.

## HALLAZGOS DE SEGURIDAD
1. **Riesgo alto: escritura fuera de alcance por ruta de archivo no confinada al repo**.
   - `TechnicalSpec.is_valid()` permite rutas absolutas (`cgalpha/codecraft/technical_spec.py:140`), y `ASTModifier.modify_file()` escribe directamente `file_path` (`cgalpha/codecraft/ast_modifier.py:171`).
   - Resultado: una spec maliciosa o errónea puede apuntar a archivos fuera del proyecto.

2. **Riesgo alto: fallback textual inseguro en modificación de código**.
   - Fallback por texto reemplaza por coincidencia de substrings (`cgalpha/codecraft/ast_modifier.py:239`), sin validar contexto semántico (clase/atributo real).
   - Puede alterar comentarios, strings, atributos homónimos y producir cambios silenciosos no intencionados.

3. **Riesgo medio: generación de tests con campos no saneados**.
   - `module_path`, `class_name`, `attribute_name` se inyectan en template Jinja2 (`cgalpha/codecraft/templates/parameter_change_test.j2:11`, `:21`, `:22`) y luego se ejecutan via `pytest` (`cgalpha/codecraft/test_generator.py:253`).
   - Un parser/LLM comprometido podría introducir código inválido o peligroso en tests generados.

4. **Concurrencia: lock parcial en buffer SQLite**.
   - `threading.Lock` existe y protege `save_task()` (`cgalpha/nexus/task_buffer.py:23`, `:52`), mitigando la race principal de escritura concurrente.
   - `get_pending_tasks()`, `mark_as_recovered()` y `cleanup_old_tasks()` no usan lock; hay ventana de inconsistencias en escenarios de recuperación concurrente.

## ANÁLISIS DE ARQUITECTURA
Alineación constitucional (Parte 9):
- Implementa barreras de calidad de salida (`new_test_status`, `regression_status`, `coverage>=80`) en `_determine_overall_status()` (`cgalpha/codecraft/test_generator.py:425`).
- Gap importante: `Integration tests` no se modelan como fase explícita; se aproximan con “tests relacionados”.
- Gap importante: si no encuentra tests relacionados, regresión se marca como `passed` (`cgalpha/codecraft/test_generator.py:289`), debilitando la barrera.
- Gap importante: no hay validación de performance en Fase 3 pese a Constitución Parte 9 (`UNIFIED_CONSTITUTION_v0.0.3.md:3097`).

Separación de memoria:
- No hay imports cruzados a módulos `operational`/`evolutionary` en `cgalpha/codecraft` y `cgalpha/nexus`.
- En Fase 6, `ProposalGenerator` consume explícitamente ambos archivos (`cgalpha/codecraft/proposal_generator.py:75-76`), lo cual es coherente con su rol de puente analítico.

Resiliencia Redis:
- Fallback a SQLite está cableado correctamente en `push_lab_task()` cuando Redis falla (`cgalpha/nexus/ops.py:160-170`).
- Recuperación automática de buffer existe (`cgalpha/nexus/ops.py:96-109`).
- Limitación: no hay semántica de ack/retry por mensaje del lado consumidor (colas por lista simple en `redis_client.py`), por lo que ante fallos de consumidor puede perderse trazabilidad.

Robustez de `proposal_parser.py` (cache):
- La key de cache es válida y determinista (`codecraft:parse:{md5}` en `cgalpha/codecraft/proposal_parser.py:47` y `:330-333`).
- El TTL está correctamente fijado a 24h (`CACHE_TTL = 86400` en `cgalpha/codecraft/proposal_parser.py:48` y uso en `:355`).
- Riesgo pendiente: no versiona por schema/modelo/código; puede devolver specs obsoletas tras cambios de arquitectura.

Escalabilidad hacia Fase 8 (Execution Engine):
- `CodeCraftOrchestrator.execute_pipeline()` concentra parsing, modificación, tests, git, rollback y armado de respuesta en un método largo y acoplado (`cgalpha/codecraft/orchestrator.py:76-331`).
- Actualmente está rígido a 4 fases hardcodeadas; introducir Ghost Architect o Execution Engine como etapas formales requerirá modificar lógica central, no extensión por contrato.
- Evidencia funcional: pruebas de integración de orquestación fallan ampliamente (7 fallos en `tests/test_codecraft_integration.py`) por fragilidad del parseo/ruteo de archivo.

## RECOMENDACIONES DE OPTIMIZACIÓN
1. **Confinar rutas + política de archivos permitidos**.
   - Forzar `file_path` relativo al `working_dir` del orchestrator.
   - Rechazar rutas absolutas y extensiones no permitidas.
   - Validar que target esté bajo un allowlist (`cgalpha/`, `core/`, etc.).

2. **Reemplazar fallback textual por modificación estructural segura**.
   - Mantener AST como primario y usar `libcst`/`parso` como fallback semántico.
   - Exigir `changes_made > 0`; si no, abortar con error explícito.
   - Integrar `SafetyValidator` dentro de `orchestrator` antes de persistir cambios.

3. **Refactor del orchestrator a pipeline extensible**.
   - Crear interfaz `PipelineStage` con contratos `run(ctx) -> ctx` y rollback por etapa.
   - Registrar fases por configuración para añadir Fase 7/8 sin editar el núcleo.
   - Emitir eventos/telemetría por etapa y razón de fallo.

## PLAN DE ACCIÓN PARA FASE 7
1. Definir contrato de mensajes para Ghost Architect con `proposal_id`, `request_id`, `payload`, `schema_version`, `created_at`, `timeout_s`.
2. Migrar de listas Redis a **Redis Streams + Consumer Groups** para request/response robusto (ack explícito, reintentos, pending entries).
3. Crear dos canales lógicos:
   - `cgalpha:stream:ghost_architect:requests`
   - `cgalpha:stream:ghost_architect:responses`
4. Implementar en `ProposalParser` modo async:
   - Publica request en Redis.
   - Espera respuesta correlacionada por `request_id`.
   - Si timeout/fallo, fallback controlado a heurísticas.
5. Implementar worker externo (CPU dedicada) para LLM local:
   - Consume requests.
   - Ejecuta inferencia local.
   - Publica respuesta estructurada + score de confianza.
6. Persistir y auditar todo el ciclo:
   - Guardar request/response en `aipha_memory/evolutionary/` para aprendizaje.
   - Guardar estado operativo en `aipha_memory/operational/`.
7. Añadir controles de resiliencia:
   - Dead-letter stream.
   - Retry con backoff y máximo intentos.
   - Idempotencia por `request_id`.
8. Añadir suite de pruebas de Fase 7:
   - Redis caído.
   - Worker lento.
   - Respuestas duplicadas.
   - Timeout + fallback heurístico.
