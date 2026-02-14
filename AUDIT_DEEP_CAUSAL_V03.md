# AUDIT_DEEP_CAUSAL_V03

## 1) Veredicto Ejecutivo
**Estado:** `APROBADO CON RESERVAS` para transicionar de v0.2.2 a v0.3.

**Conclusión corta:**
- La base actual **sí soporta** inyección de microestructura (`order_book_features.jsonl`) sin romper CLI.
- `simple_causal_analyzer.py` ya incorpora lógica Deep Causal parcial (join por `trade_id` y por `timestamp` cercano, métricas de alineación, modo `BLIND_TEST`, prompt microestructural).
- Aún faltan componentes de v0.3 para causalidad profunda operacional: **capa de ingesta nativa**, **validación de calidad de features en tiempo real**, y **métrica causal out-of-sample** más estricta.

---

## 2) Evidencia Técnica (Código + Runtime)

### 2.1 Evidencia de soporte Deep Causal en código
- Carga de features externos: `cgalpha/ghost_architect/simple_causal_analyzer.py:303` (`_load_order_book_feature_index`).
- Join por `trade_id` y fallback por timestamp nearest con tolerancia ±250ms: `cgalpha/ghost_architect/simple_causal_analyzer.py:340` (`_match_order_book_feature`).
- Extracción explícita de microestructura (`cancel_ratio`, `replenishment_rate`, `micro_reversal_ticks`, `spread_bps`, `bid_size_1_5`, etc.): `cgalpha/ghost_architect/simple_causal_analyzer.py:425` (`_extract_trade_snapshot`).
- Marcado de calidad del dato: `ENRICHED_EXACT`, `ENRICHED_NEAREST`, `BLIND_TEST`, `LOCAL_ONLY`: `cgalpha/ghost_architect/simple_causal_analyzer.py:493`.
- Prompt causal orientado a microestructura y JSON estricto: `cgalpha/ghost_architect/simple_causal_analyzer.py:889` + `cgalpha/ghost_architect/templates/deep_causal_prompt.j2`.
- Métricas de alineación y cobertura de profundidad: `cgalpha/ghost_architect/simple_causal_analyzer.py:1102`.
- Integración pipeline sin cambios disruptivos en comando principal: `cgalpha/orchestrator.py:26` (`auto_analyze`).

### 2.2 Evidencia de ejecución
- Tests relevantes ejecutados: `10 passed`.
  - `tests/test_ghost_architect_phase7.py`
  - `tests/test_librarian_cli.py`
- Dataset de profundidad presente:
  - `aipha_memory/operational/order_book_features.jsonl` (con campos microestructura).

---

## 3) Auditoría Crítica v0.2.2

### 3.1 Fortalezas (cumple)
1. **Inyección externa no invasiva:** la arquitectura actual permite agregar profundidad sin refactor masivo.
2. **Fallback bien definido:** si no hay match de microdatos, la muestra se marca `BLIND_TEST` en lugar de inventar evidencia.
3. **Prompt disciplinado:** instruye al LLM a no inventar datos y a emitir JSON estructurado.
4. **Compatibilidad operativa:** `cgalpha auto-analyze` sigue siendo el entrypoint estable.

### 3.2 Reservas (riesgo real)
1. **Calidad causal aún proxy:** `accuracy_causal` y `efficiency` son útiles, pero todavía cercanas a métricas internas/in-sample; falta validación out-of-sample robusta.
2. **Ingesta de book no nativa end-to-end:** existe lectura de JSONL, pero no se ve una capa formal de captura/normalización continua de order book en vivo.
3. **Riesgo de deriva de esquema:** no hay validación estricta de contrato por fila (tipos obligatorios, rangos, nulos críticos).
4. **Cobertura dependiente de joins:** exceso de `BLIND_TEST` degrada inferencia causal; requiere gate operacional.

---

## 4) Brecha v0.2.2 -> v0.3 (Deep Causal)

Para llamar al sistema v0.3 real, deben cumplirse 3 condiciones:

1. **Data Layer formal de microestructura**
   - Pipeline dedicado para recolectar y normalizar book depth/ticks.
   - Escritura controlada de `order_book_features.jsonl` con esquema versionado.

2. **Quality Gates de datos causales**
   - Límite de `blind_test_ratio` (ej. <= 0.25).
   - Límite de `nearest_match_avg_lag_ms` (ej. <= 150ms).
   - Rechazo de filas inválidas por contrato.

3. **Validación causal out-of-sample**
   - Holdout temporal + ventana walk-forward.
   - Métricas por etiqueta causal (`fakeout`, `structure_break`, `risk_logic_failure`).

---

## 5) Diseño de Arquitectura v0.3 (Incremental, sin romper núcleo)

```text
[Market Feed / Logs]
        |
        v
[OrderBook Feature Builder]
  - normaliza ticks/depth
  - calcula features micro
  - valida contrato
        |
        v
[aipha_memory/operational/order_book_features.jsonl]
        |
        v
[SimpleCausalAnalyzer._extract_trade_snapshot]
  - join trade_id
  - fallback nearest timestamp (<= 250ms)
  - marca ENRICHED_EXACT / ENRICHED_NEAREST / BLIND_TEST
        |
        v
[_build_causal_prompt + LLM]
        |
        v
[Hypotheses + confidence + causal_metrics + data_alignment]
        |
        v
[cgalpha auto-analyze -> proposals]
```

### Punto de inserción principal
- Mantener `_extract_trade_snapshot` como punto único de enriquecimiento.
- No mover orquestación principal; solo fortalecer ingesta y gates de calidad.

---

## 6) Contrato de Datos recomendado (`order_book_features.jsonl`)

Campos mínimos por fila (v0.3):
- `timestamp` (ISO8601 UTC, obligatorio)
- `trade_id` (string, recomendado; si falta, usa join temporal)
- `symbol` (string)
- `bid_size_1_5` (float >= 0)
- `ask_size_1_5` (float >= 0)
- `spread_bps` (float >= 0)
- `replenishment_rate` (float >= 0)
- `cancel_ratio` (float >= 0)
- `micro_reversal_ticks` (int >= 0)
- `sweep_events` (int >= 0)
- `aggressive_buy_sell_delta` (float en [-1, 1], si aplica)

Reglas de calidad:
- Si `trade_id` no existe y nearest lag > 250ms -> `BLIND_TEST`.
- Registrar `order_book_match_type` y `order_book_lag_ms` para trazabilidad.

---

## 7) Distinción Causal Requerida: Fakeout vs Ruptura

### Fakeout (ruido microestructural)
Indicadores típicos:
- `micro_reversal_ticks` muy bajos (reversión rápida)
- `spread_bps` estresado
- `cancel_ratio` alto + `replenishment_rate` alto
- barridas (`sweep_events`) con retorno rápido

### Structural Break (cambio estructural)
Indicadores típicos:
- desbalance persistente + baja reposición
- continuidad direccional sin reversión rápida
- confirmación en régimen de vela/tendencia

Requisito v0.3:
- Clasificación causal debe reportar **evidencia explícita** por campo (`evidence_fields`).

---

## 8) Plan de Validación v0.3

1. **Unit tests (parser/enrichment):**
   - Join exacto por `trade_id`.
   - Join nearest por timestamp dentro y fuera de ventana.
   - Marcado correcto de `BLIND_TEST`.

2. **Integration tests (`auto-analyze`):**
   - Con dataset enriquecido.
   - Con dataset sin features (debe degradar de forma segura, no romper).

3. **Out-of-sample causal tests:**
   - Walk-forward por ventanas temporales.
   - Métricas:
     - `causal_accuracy_oos`
     - `precision_fakeout`
     - `precision_structure_break`
     - `blind_test_ratio`
     - `noise_rejection_rate`

4. **Acceptance gates para producción:**
   - `blind_test_ratio <= 0.25`
   - `nearest_match_avg_lag_ms <= 150`
   - `precision_fakeout >= 0.60`
   - `precision_structure_break >= 0.60`

---

## 9) Constitución (Part 10 + Part 11) - Propuesta de actualización

### Part 10 (Data Causality Governance)
- Definir `order_book_features.jsonl` como fuente oficial de microestructura.
- Exigir contrato de datos versionado y validación por fila.
- Prohibir inferencias causales de alta confianza con `blind_test_ratio` alto.

### Part 11 (Causal Evaluation Protocol)
- Exigir evaluación out-of-sample para aprobar cambios causales.
- Separar métricas in-sample vs out-of-sample en cada reporte.
- Requerir trazabilidad: hipótesis -> evidencia -> acción -> resultado.

---

## 10) Decisión Final
**PROCEDER a v0.3 incremental** con enfoque Data Layer + Quality Gates + OOS Validation.

**No recomendado:** refactor total del núcleo en esta fase.

**Riesgo controlable:** medio, siempre que se mantenga `NO-ROLLBACK` solo a nivel de estrategia y no se comprometa la ruta de ejecución estable (`cgalpha auto-analyze`).
