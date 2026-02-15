# UNIFIED_CONSTITUTION_v0.0.3 (Compact Operational Edition)

Estado de este archivo:
- Esta es la edición compacta y operativa.
- El histórico completo (monolítico) se conserva en:
  - `docs/archive/constitution/UNIFIED_CONSTITUTION_v0.0.3_FULL_LEGACY.md`

Propósito:
- Definir reglas no negociables de operación y evolución.
- Reducir ambigüedad documental para humanos y LLM local.

## 1. Jerarquía de Fuentes

Precedencia documental (de mayor a menor para operación diaria):
1. `UNIFIED_CONSTITUTION_v0.0.3.md` (este archivo).
2. `docs/reference/constitution_core.md`
3. `docs/reference/gates.md`
4. `docs/reference/parameters.md`
5. `docs/CGALPHA_MASTER_DOCUMENTATION.md`
6. `README.md` y `00_QUICKSTART.md`

Regla:
- Si hay conflicto operativo, prevalece esta constitución compacta.

## 2. Identidad del Sistema

- **Aipha (Cuerpo):** ejecución robusta, determinista y segura.
- **CGAlpha (Cerebro):** análisis causal y estrategia evolutiva.

Principio rector:
- evolución incremental,
- nunca reescritura destructiva como atajo.

## 3. Separación de Responsabilidades

Separación obligatoria de memoria:
- `aipha_memory/operational/` -> operación, runtime, observabilidad.
- `aipha_memory/evolutionary/` -> aprendizaje, bridge causal, decisiones evolutivas.

Regla:
- no mezclar capas de memoria sin puente explícito y trazable.

## 4. Arquitectura Operativa (Resumen)

Cuerpo (ejecución):
1. Infraestructura y orquestación.
2. Data preprocessor.
3. Trading manager.
4. Oracle (filtro probabilístico).
5. Data postprocessor (cierre de ciclo y retroalimentación).

Cerebro (estrategia):
- Ghost Architect + análisis causal profundo.

## 5. Seguridad y Calidad de Cambios

Reglas mínimas:
- prohibido escribir fuera del scope del repositorio,
- validación previa/post de cambios de código,
- rollback obligatorio ante fallos de validación,
- sin bypass de barreras de tests/regresión.

Política de merge:
- no promover cambios con tests en rojo,
- no aceptar “refactor total” sin justificación formal y plan de riesgo.

## 6. Readiness Gates (Deep Causal / v0.3)

Precondiciones para Live/Hybrid:
1. existe `aipha_memory/operational/order_book_features.jsonl`,
2. existe reporte causal reciente con:
   - `data_alignment`
   - `causal_metrics`
   - `readiness_gates`

Gates mínimos obligatorios:
- `readiness_gates.data_quality_pass = true`
- `readiness_gates.causal_quality_pass = true`
- `readiness_gates.proceed_v03 = true`

Thresholds recomendados:
- `max_blind_test_ratio <= 0.25`
- `max_nearest_match_avg_lag_ms <= 150`
- `min_causal_accuracy >= 0.55`
- `min_efficiency >= 0.40`

Regla de bloqueo:
- si falla cualquier gate, bloquear Live/Hybrid y mantener Paper.

## 7. Política de Decisión Operativa

- Un pase aislado no habilita promoción de fase.
- Se requiere pase repetido con datos estables.
- En incertidumbre, priorizar `HOLD` sobre `PROCEED_V03`.

## 8. Política de Documentación

- Documentación activa: `docs/`.
- Documentación histórica: `docs/archive/`.
- Evitar duplicación masiva: una fuente operativa por tema.

Referencias rápidas:
- `docs/DOCS_INDEX.md`
- `docs/reference/README.md`
- `VERSION.md`

## 9. Política de Versionado

- Estado oficial de versiones en `VERSION.md`.
- No declarar versiones divergentes en múltiples archivos.
- Si cambia versión o estado operativo, actualizar `VERSION.md` primero.

## 10. Cumplimiento y Auditoría

Criterios mínimos de cumplimiento:
- tests completos en verde,
- gates de readiness en verde cuando aplica,
- trazabilidad de cambios (código + docs + decisión).

Auditoría documental:
- mantener `docs/DOCS_COVERAGE_MATRIX.md` y `docs/DOCS_RETENTION_TABLE.md` actualizados.

## 11. Anexo de Continuidad

El monolito original no se elimina por trazabilidad histórica.
Ruta del snapshot íntegro:
- `docs/archive/constitution/UNIFIED_CONSTITUTION_v0.0.3_FULL_LEGACY.md`

Uso recomendado:
- operación diaria -> esta edición compacta,
- investigación histórica/legal -> snapshot íntegro archivado.
