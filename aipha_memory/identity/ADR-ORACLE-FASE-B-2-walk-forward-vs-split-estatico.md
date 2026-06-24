# ADR-ORACLE-FASE-B-2 — Walk-Forward Validation vs Split Estático

## Estatus
ACEPTADO e IMPLEMENTADO (2026-06-24).

Aprobado por el operador. Walk-Forward Validation con 4 folds temporales. Implementación en `OracleTrainer_v3._walk_forward_cv()`.

## Contexto

El Oracle v6 usa actualmente un **split estático aleatorio** para separar train/test:
```python
# oracle.py L220-224
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
```

Este split tiene dos problemas para un sistema de trading temporal:

### Problema 1: Data leakage temporal
`train_test_split` mezcla samples del pasado y del futuro en ambos conjuntos. El modelo puede aprender patrones que solo existen porque tiene información de samples temporalmente posteriores en el set de entrenamiento. En producción, el modelo predice sobre samples que ocurren **después** del entrenamiento — el split aleatorio no simula esto.

### Problema 2: No refleja la operación real
En producción, el Oracle se entrena con datos históricos y predice sobre samples nuevas. Un split aleatorio mide la capacidad del modelo para interpolar dentro de la distribución del dataset, no para extrapolar hacia el futuro.

### Evidencia material verificada

**Dataset `training_dataset_v2.jsonl`:**
- 239 samples totales
- 238 con `capture_ts_unix_ms` (1 sample sin timestamp)
- **NO ordenados** por timestamp — necesitan sort antes de walk-forward
- Span: 1225 horas (~51 días, 2026-05-04 a 2026-06-24)
- D-003: OOS mínimo = 30 samples para A/B

**Split actual:**
- `test_size=0.2` → ~48 samples de test (suficiente para D-003)
- `random_state=42` → split determinista pero aleatorio temporalmente
- `stratify=y` → mantiene proporción de clases

**Pipeline A/B (`train_oracle_ab.py`):**
- Set A = samples con `l2_data_quality == "FULL"`
- Set B = samples legacy + FULL (hybrid bridge)
- Cada set se entrena independientemente con el split aleatorio
- Promoción: `a_brier <= b_brier and a_test >= 0.52 and a_gap <= 0.20`

### El problema de fondo

Con 12 features dinámicas nuevas (ADR-ORACLE-FASE-B-1), el modelo pasa de 14 a 26 features. El riesgo de overfitting aumenta. Un split aleatorio puede ocultar overfitting temporal: el modelo puede memorizar patrones de un régimen de mercado específico y generalizar mal cuando el régimen cambia.

El walk-forward validation resuelve esto simulando la operación real: entrena en una ventana temporal, prueba en la siguiente, deslaza la ventana, repite. Cada fold de test es temporalmente posterior al fold de train.

## Decisión propuesta

**Recomendación: Walk-Forward Validation con ventanas móviles, manteniendo el split estático como baseline de comparación.**

### Análisis comparativo

#### Opción A — Split Estático Aleatorio (actual)

**Diseño:** `train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)`

**Ventajas:**
- Simple, ya implementado.
- Stratify mantiene proporción de clases.
- Determinista (`random_state=42`).

**Desventajas:**
- **Data leakage temporal.** Samples del futuro en train, samples del pasado en test.
- No refleja la operación real.
- Con 26 features y 239 samples, el split aleatorio puede ocultar overfitting temporal.

#### Opción B — Walk-Forward Validation (propuesta)

**Diseño:** Ordenar samples por `capture_ts_unix_ms`. Dividir en K folds temporales secuenciales. Para cada fold i:
- Train: folds 0..i-1
- Test: fold i
- Métricas: accuracy, brier, gap por fold
- Métrica agregada: media ± std de accuracy/brier across folds

**Mecánica:**
```python
# Pseudocódigo conceptual
samples_sorted = sorted(samples, key=lambda s: s["_meta"]["capture_ts_unix_ms"])
n = len(samples_sorted)
n_folds = 5  # 5 folds temporales
fold_size = n // n_folds  # ~47 samples por fold

results = []
for i in range(1, n_folds):
    train = samples_sorted[:i * fold_size]
    test = samples_sorted[i * fold_size:(i + 1) * fold_size]
    # Entrenar en train, evaluar en test
    model.fit(train)
    metrics = evaluate(model, test)
    results.append(metrics)

# Métricas agregadas
mean_accuracy = mean(r["accuracy"] for r in results)
std_accuracy = std(r["accuracy"] for r in results)
mean_brier = mean(r["brier"] for r in results)
```

**Ventajas:**
- **Sin data leakage temporal.** Cada fold de test es posterior al fold de train.
- Refleja la operación real: entrenar en el pasado, predecir en el futuro.
- Detecta overfitting temporal: si la accuracy cae en folds recientes, el modelo no generaliza.
- Con 239 samples y 5 folds: fold 0 = 47, fold 1 = 47, etc. Train crece: 47, 94, 141, 188. Test: 47 cada uno. Suficiente para D-003 (≥30).

**Desventajas:**
- Más complejo de implementar.
- Menos samples de train por fold (47 en el primer fold vs 191 en el split estático).
- No hay stratify por clase — un fold puede tener desbalance.
- El primer fold tiene pocos samples de train (47) — riesgo de underfitting.

#### Opción C — Split Estático Temporal (compromiso)

**Diseño:** Ordenar samples por timestamp. Los primeros 80% = train, los últimos 20% = test.

```python
samples_sorted = sorted(samples, key=lambda s: s["_meta"]["capture_ts_unix_ms"])
split_idx = int(len(samples_sorted) * 0.8)
train = samples_sorted[:split_idx]
test = samples_sorted[split_idx:]
```

**Ventajas:**
- Sin data leakage temporal.
- Simple de implementar.
- Más samples de train (191) que walk-forward.

**Desventajas:**
- Una sola evaluación — no mide estabilidad temporal.
- El test set es un solo período — puede ser atípico.

### Por qué se recomienda la Opción B (Walk-Forward)

1. **Detecta overfitting temporal.** Con 12 features dinámicas nuevas, el riesgo de overfitting es real. Walk-forward mide si el modelo generaliza a través de regímenes de mercado cambiantes.
2. **Mide estabilidad.** La std de accuracy across folds indica si el modelo es estable o volátil.
3. **Suficiente volumen.** 239 samples / 5 folds = ~47 por fold. Train mínimo = 47 (fold 1), suficiente para RandomForest.
4. **D-003 compatible.** 47 samples de test > 30 mínimo.
5. **Refleja la operación real.** En producción, el modelo se re-entrena periódicamente con datos nuevos. Walk-forward simula esto.

### Mitigación de desventajas

| Desventaja | Mitigación |
|---|---|
| Pocos samples en primer fold (47) | Usar 4 folds en lugar de 5: fold 0 = 60, train mínimo = 60 |
| Sin stratify por clase | Verificar balance por fold; si un fold está extremadamente desbalanceado, reportarlo |
| Complejidad | Implementar como método `_walk_forward_cv()` en `OracleTrainer_v3` |
| Primer fold puede underfitting | Reportar métricas por fold; si fold 1 es atípicamente bajo, excluirlo del agregado |

### Parámetros propuestos

- **n_folds = 4** (no 5): fold 0 = 60, fold 1 = 60, fold 2 = 60, fold 3 = 59. Train: 60, 120, 180. Test: 60, 60, 60, 59.
- **Métricas por fold:** accuracy, brier_score, train_oos_gap, n_train, n_test
- **Métricas agregadas:** mean_accuracy, std_accuracy, mean_brier, std_brier, worst_fold_accuracy
- **Criterio de promoción (extiende `_promotion_decision`):**
  - `mean_accuracy >= 0.52` (mismo que actual)
  - `mean_brier <= set_b_brier` (mismo que actual)
  - `worst_fold_accuracy >= 0.45` (nuevo: ningún fold debe ser catastórfico)
  - `std_accuracy <= 0.15` (nuevo: estabilidad temporal)

### Implementación técnica

**No se implementa en este ADR.** Este ADR establece la decisión. La implementación es O-B3:

1. **En `OracleTrainer_v3`:** añadir método `_walk_forward_cv(X, y, n_folds=4)` que retorna métricas por fold y agregadas.
2. **En `train_model()`:** reemplazar `train_test_split` con `_walk_forward_cv` cuando el dataset tenga timestamps. Si no hay timestamps, fallback a split estático.
3. **En `train_oracle_ab.py`:** actualizar `_promotion_decision` para usar métricas walk-forward.
4. **En `_training_metrics`:** añadir `walk_forward_folds`, `mean_accuracy`, `std_accuracy`, `worst_fold_accuracy`.

### Relación con D-003

D-003 fija OOS mínimo en 30 samples. Con 4 folds de ~60 samples, cada fold de test tiene 60 > 30. Compatible.

### Relación con ADR-ORACLE-FASE-B-1

Las 12 features dinámicas aumentan el riesgo de overfitting. Walk-forward es la mitigación principal. Si la std_accuracy es alta (>0.15), considerar reducir el número de features dinámicas o añadir regularización.

## Consecuencias

- **Positivas:**
  - Sin data leakage temporal.
  - Detecta overfitting temporal con 26 features.
  - Mide estabilidad del modelo across regímenes.
  - Refleja la operación real.
- **Neutrales:**
  - El pipeline A/B necesita actualización para usar métricas walk-forward.
  - Los modelos entrenados con walk-forward no son directamente comparables con modelos entrenados con split estático (métricas diferentes).
- **Riesgos:**
  - Menos samples de train por fold (60 mínimo vs 191 del split estático). RandomForest puede underfitting en folds tempranos. Mitigación: reportar métricas por fold.
  - Sin stratify por clase. Un fold puede tener desbalance. Mitigación: reportar balance por fold.
  - El primer fold (train=60) puede ser atípico. Mitigación: excluir del agregado si es outlier.

## Alternativas consideradas

- **Opción A — Split estático aleatorio (actual).** Descartada por data leakage temporal y porque no refleja la operación real.
- **Opción B — Walk-Forward Validation.** Recomendada por las ventajas anteriores.
- **Opción C — Split estático temporal.** Descartada por ser una sola evaluación — no mide estabilidad temporal.
- **Opción D — Time Series Cross-Validation de sklearn.** Descartada porque `TimeSeriesSplit` de sklearn no respeta el orden temporal del dataset (requiere que el dataset ya esté ordenado). Walk-forward custom es más explícito y controlable.

## Próximos pasos (post-aprobación)

1. Implementar `_walk_forward_cv()` en `OracleTrainer_v3`.
2. Actualizar `train_model()` para usar walk-forward cuando haya timestamps.
3. Actualizar `train_oracle_ab.py` para usar métricas walk-forward en `_promotion_decision`.
4. Re-entrenar Oracle v6 con walk-forward + features dinámicas (O-B3).
5. Comparar métricas walk-forward vs split estático (A/B).

---

*Referencias:*
- *`cgalpha_v3/lila/llm/oracle.py` L220-224 (split actual)*
- *`cgalpha_v3/scripts/train_oracle_ab.py` L187-236 (_promotion_decision)*
- *`aipha_memory/operational/training_dataset_v2.jsonl` (239 samples, 51 días span)*
- *`aipha_memory/identity/ADR-ORACLE-FASE-B-1-schema-features-dinamicas.md` (12 features dinámicas)*
- *D-003 (OOS mínimo 30 samples)*
- *`documentation/EVO_TICKET_LOG.md` — EVO-TICKET-0002 (Fase B, O-B2)*
