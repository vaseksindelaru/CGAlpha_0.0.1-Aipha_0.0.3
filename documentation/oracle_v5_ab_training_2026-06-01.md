# Oracle v5 A/B Training - 2026-06-01

## Resumen

El 2026-06-01, hora local Europe/Madrid, se ejecuto un entrenamiento A/B del Oracle v5 despues de recuperar el dataset operativo y blindarlo contra futuros `git reset` o `git checkout`.

El entrenamiento guardo dos modelos separados y no sobrescribio `aipha_memory/data/models/oracle_v5.joblib`.

- Set A: Pure L2 `FULL`, entrenado como challenger.
- Set B: Hybrid bridge, entrenado como champion candidate.
- Decision: mantener Set B como champion. Set A queda como challenger shadow.

## Checkpoint previo

Antes de entrenar se publico el estado recuperado en `origin/main`.

Comandos ejecutados:

```bash
git status --short --branch
git check-ignore -v aipha_memory/operational/training_dataset_v2.jsonl aipha_memory/operational/pending_labels.json
git add -A
git commit -m "chore(repo): checkpoint recovered oracle state"
git push origin main
```

Resultado:

- Commit: `c244961 chore(repo): checkpoint recovered oracle state`
- Push: `main -> origin/main`
- `training_dataset_v2.jsonl` y `pending_labels.json` siguen en disco, pero ignorados por Git.

## Estado del dataset

Fuente:

```text
aipha_memory/operational/training_dataset_v2.jsonl
```

Resumen:

| Medida | Valor |
| --- | ---: |
| Filas totales | 217 |
| IDs unicos | 217 |
| Duplicados | 0 |
| Filas entrenables | 131 |
| BOUNCE_STRONG total | 50 |
| BREAKOUT total | 81 |
| BOUNCE_WEAK total | 18 |
| INCONCLUSIVE total | 68 |
| FULL total | 73 |
| FULL + BOUNCE_STRONG | 9 |
| FULL + BREAKOUT | 26 |
| FULL + INCONCLUSIVE | 38 |

Readiness Set A:

```text
FULL total: 73
FULL outcomes: {'INCONCLUSIVE': 38, 'BREAKOUT': 26, 'BOUNCE_STRONG': 9}
Set A criteria: BOUNCE_STRONG>=8, BREAKOUT>=16, FULL>=24
Set A ready: True
```

## Cambios tecnicos para entrenar

Se agrego `cgalpha_v3/scripts/train_oracle_ab.py`.

El runner:

- Construye Set A con todas las filas `l2_data_quality == FULL`.
- Construye Set B con filas validas legacy/synth neutralizadas y filas `FULL` validas.
- Entrena ambos perfiles con `OracleTrainer_v3`.
- Guarda modelos separados.
- Genera reporte JSON reproducible.
- Calcula una decision de promocion sin sobrescribir el modelo vivo.

Tambien se corrigio `OracleTrainer_v3` para schema v2: si `vwap_at_retest` no existe, usa `vwap_session` y luego `retest_price` como fallback. Sin este ajuste, el quality gate bloqueaba Set A por NaNs.

## Comandos de entrenamiento

```bash
python3 cgalpha_v3/scripts/monitor_set_a_readiness.py
python3 cgalpha_v3/scripts/train_oracle_ab.py
python3 -m pytest cgalpha_v3/tests/test_oracle_training.py
```

Artefactos generados:

```text
aipha_memory/operational/prepared_sets/set_a_full_l2_all_outcomes.jsonl
aipha_memory/operational/prepared_sets/set_b_hybrid_bridge_trainable.jsonl
aipha_memory/data/models/oracle_v5_set_a_challenger.joblib
aipha_memory/data/models/oracle_v5_set_b_champion_candidate.joblib
aipha_memory/reports/oracle_v5_ab_training_20260601.json
```

## Resultados

### Set A - Pure L2 challenger

| Medida | Valor |
| --- | ---: |
| Input rows | 73 |
| Trainable rows | 35 |
| Trainable BOUNCE_STRONG | 9 |
| Trainable BREAKOUT | 26 |
| Train samples | 28 |
| OOS samples | 7 |
| Train accuracy | 1.0000 |
| OOS accuracy | 0.7143 |
| CV mean | 0.8667 |
| CV std | 0.1247 |
| Brier Score | 0.184939 |
| Train/OOS gap | 0.2857 |

Top features:

| Feature | Importance |
| --- | ---: |
| `atr_14` | 0.3712 |
| `cumulative_delta_at_retest` | 0.2448 |
| `obi_10_at_retest` | 0.1986 |
| `vwap_at_retest` | 0.1430 |
| `is_bullish` | 0.0423 |

Interpretacion: Set A ya entrena y supera el minimo operativo de readiness, pero todavia presenta muestra valida pequena y gap train/OOS alto.

### Set B - Hybrid bridge champion candidate

| Medida | Valor |
| --- | ---: |
| Input rows | 110 |
| Trainable rows | 110 |
| Trainable BOUNCE_STRONG | 49 |
| Trainable BREAKOUT | 61 |
| Train samples | 88 |
| OOS samples | 22 |
| Train accuracy | 0.8977 |
| OOS accuracy | 0.7727 |
| CV mean | 0.5797 |
| CV std | 0.0214 |
| Brier Score | 0.174978 |
| Train/OOS gap | 0.1250 |

Top features:

| Feature | Importance |
| --- | ---: |
| `atr_14` | 0.3661 |
| `vwap_at_retest` | 0.2498 |
| `obi_10_at_retest` | 0.1492 |
| `cumulative_delta_at_retest` | 0.1457 |
| `is_lateral` | 0.0645 |

Interpretacion: Set B mantiene mejor Brier Score y menor gap train/OOS. Es el perfil mas defendible como champion por ahora.

## Decision

Decision del runner:

```json
{
  "decision": "keep_set_b_champion",
  "champion": "set_b_hybrid_bridge",
  "challenger": "set_a_full_l2",
  "criteria": {
    "set_a_brier_lte_set_b": false,
    "set_a_oos_accuracy_gte_52_pct": true,
    "set_a_train_oos_gap_lte_20_pct": false
  },
  "set_a_train_oos_gap": 0.2857,
  "note": "oracle_v5.joblib was not overwritten by this runner"
}
```

No se promociona Set A porque:

- Su Brier Score es peor que Set B: `0.184939` vs `0.174978`.
- Su gap train/OOS es alto: `0.2857`.
- Su OOS se calcula sobre solo 7 muestras, insuficiente para reemplazar el champion.

## Validacion

Prueba ejecutada:

```bash
python3 -m pytest cgalpha_v3/tests/test_oracle_training.py
```

Resultado:

```text
10 passed, 10 warnings in 74.87s
```

Warnings conocidos:

- `CalibratedClassifierCV(cv='prefit')` esta deprecado en sklearn 1.6 y sera removido en 1.8.

## Proximos pasos recomendados

1. Mantener Set B como champion operativo y Set A como challenger shadow.
2. Seguir cosechando FULL L2 hasta que Set A tenga al menos 50 filas entrenables validas, no solo 50 filas FULL totales.
3. Repetir A/B cuando Set A alcance al menos 15 `BOUNCE_STRONG` y 35 `BREAKOUT` validos.
4. Migrar `CalibratedClassifierCV(cv='prefit')` a `FrozenEstimator` antes de actualizar sklearn hacia 1.8.
5. Solo promover Set A si mejora o iguala el Brier Score de Set B y mantiene gap train/OOS <= 0.20.
