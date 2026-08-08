# Data Quality Gates — cgalpha_v3

## Propósito
Valida todos los datos de mercado (klines Binance) antes de usarlos en señales
o en el pipeline de entrenamiento (Sección E, F, K P0.3).

## Inputs / Outputs

- **Inputs:** lista de klines dict, símbolo, intervalo, timestamp de última actualización
- **Outputs:** `DQReport` con `status: "valid"|"stale"|"corrupted"` y lista de errores/advertencias

## Gates activos

| Gate | Tipo | Severidad |
|------|------|-----------|
| DQ-1: Schema | Campos obligatorios presentes | error |
| DQ-2: Freshness | Dato no más viejo que threshold | warning |
| DQ-3: Temporal order | Sin inversiones de timestamp | error |
| DQ-4: Gaps | Sin huecos > N × intervalo esperado | warning |
| DQ-5: Outliers | Sin valores >5σ en precio close | warning |

## Anti-leakage

`check_oos_leakage()` lanza `TemporalLeakageError` si features OOS contaminan train.

## Dependencias

Solo librería estándar Python (sin `numpy` en esta versión base).

## Estado actual

🚧 FASE 1 — Gates implementados. Pendiente: integración con `data_processor/`.

## Próximo incremento

- Integrar con adaptador Binance real
- Emitir eventos a GUI cuando DQ falla
- Añadir tests de consistencia en `tests/test_data_quality.py`
