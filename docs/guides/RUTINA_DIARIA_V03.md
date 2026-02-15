# Rutina Diaria V03 (Deep Causal)

## 1. Por qué esta rutina es necesaria

CGAlpha está en transición `v0.2.2 -> v0.3 (Deep Causal)`.
La rutina diaria sirve para acumular evidencia de calidad antes de desbloquear Live/Hybrid.

Sin esta evidencia, el sistema queda en Paper-only por gates constitucionales.

Estado típico cuando no hay datos de microestructura:
- `data_quality_pass = false`
- `causal_quality_pass = false`
- `decision = HOLD_V03`

## 2. Qué está pasando en tu estado actual

### Tabla de diagnóstico

| Métrica | Valor actual (ejemplo) | Umbral requerido | Estado |
|---|---:|---:|---|
| `blind_test_ratio` | `1.00` | `<= 0.25` | FAIL |
| `order_book_coverage` | `0.00` | `> 0` (ideal `> 0.75`) | FAIL |
| `accuracy_causal` | `0.00` | `>= 0.55` | FAIL |
| `efficiency` | `0.00` | `>= 0.40` | FAIL |

### Interpretación práctica

- `blind_test_ratio = 1.00`:
  - 100% de trades están en modo ciego.
  - El sistema no puede distinguir bien entre `fakeout` y `structure break`.
- `order_book_coverage = 0.00`:
  - existe poco o ningún match entre trades y microestructura.
  - el archivo `order_book_features.jsonl` puede existir pero sin matches útiles.

## 3. Modos de alineación de microdatos (por trade)

| Modo | Qué significa |
|---|---|
| `ENRICHED_EXACT` | Match por `trade_id` |
| `ENRICHED_NEAREST` | Match por timestamp cercano (hasta `±250ms`) |
| `BLIND_TEST` | Sin match de microestructura |
| `LOCAL_ONLY` | Solo datos locales, sin enriquecimiento real |

Métricas derivadas:
- `blind_test_ratio = BLIND_TEST / total_trades`
- `order_book_coverage = trades_con_features / total_trades`

## 4. Gates de Readiness V03 (fuente de verdad en código)

Implementado en `cgalpha/ghost_architect/simple_causal_analyzer.py`:
- thresholds por entorno: `cgalpha/ghost_architect/simple_causal_analyzer.py:74`
- lógica de readiness: `cgalpha/ghost_architect/simple_causal_analyzer.py:1163`

Variables (defaults):
- `CGALPHA_MAX_BLIND_TEST_RATIO = 0.25`
- `CGALPHA_MAX_NEAREST_LAG_MS = 150`
- `CGALPHA_MIN_CAUSAL_ACCURACY = 0.55`
- `CGALPHA_MIN_CAUSAL_EFFICIENCY = 0.40`

Regla final:
- `proceed = has_data AND data_quality AND causal_quality`

## 5. Rutina diaria (10-15 minutos)

### Paso 1. Health + calidad base

```bash
cgalpha ask-health --smoke
python -m pytest -q tests/test_ghost_architect_phase7.py
```

### Paso 2. Ejecutar análisis V03

Comando oficial:

```bash
cgalpha auto-analyze --working-dir . --log-file aipha_memory/operational/action_history.jsonl --min-confidence 0.0
```

Si tienes script interno de chequeo en tu entorno, puedes usarlo.
En este repositorio base no existe `scripts/check_phase7.sh` por defecto.

### Paso 3. Registrar 4 campos clave

Archivo recomendado:
- `aipha_memory/evolutionary/v03_readiness_log.csv`

Header inicial:

```csv
date,blind_test_ratio,order_book_coverage,decision,notes
```

Ejemplo:

```csv
2026-02-15,1.00,0.00,HOLD_V03,Sin datos de order book asociados a trades
```

### Paso 4. Decisión diaria

- Si `data_quality_pass=false` o `causal_quality_pass=false` -> `HOLD`.
- Solo considerar avance cuando los gates pasen de forma repetida.

## 6. Acciones concretas para mejorar métricas

| Métrica objetivo | Acción práctica |
|---|---|
| Bajar `blind_test_ratio` | Poblar `order_book_features.jsonl` y asegurar match por `trade_id` |
| Subir `order_book_coverage` | Adjuntar snapshot microestructural a cada trade (bid/ask depth, spread, imbalance, etc.) |
| Subir `accuracy_causal` | Recolectar `>= 50` trades con microestructura válida para calibrar hipótesis |
| Subir `efficiency` | Convertir hipótesis válidas en acciones concretas y revisables |

## 7. Cuándo pasar de HOLD a PROCEED_V03

Condición mínima:
1. `blind_test_ratio <= 0.25`
2. `nearest_match_avg_lag_ms <= 150` (si aplica)
3. `accuracy_causal >= 0.55`
4. `efficiency >= 0.40`
5. resultado repetido en varios días (no un único pase aislado)

## 8. Checklist diario corto (operador)

1. Health ok (`ask-health`).
2. Tests críticos en verde.
3. `auto-analyze` ejecutado con log real.
4. Registrar métricas en `v03_readiness_log.csv`.
5. Decidir `HOLD` o `PROCEED_V03` con base en gates, no intuición.

## 9. Referencias recomendadas

- `00_QUICKSTART.md`
- `docs/reference/gates.md`
- `docs/reference/parameters.md`
- `docs/CGALPHA_MASTER_DOCUMENTATION.md`
- `UNIFIED_CONSTITUTION_v0.0.3.md`
