# Análisis Comparativo: Mi Evaluación vs LLM Externo — Oracle CGAlpha

**Fecha:** 2026-07-31  
**Fuentes:**
- Mi evaluación v2 (datos frescos: 954/358 FULL)
- Respuesta LLM externo (análisis operativo con datos verificados hoy)

---

## 1. Resumen Ejecutivo

El LLM externo entrega un **análisis operativo superior**: datos verificados *hoy* (fees Binance, TabPFN-2.5/3), protocolos concretos de validación, y priorización clara. Mi evaluación v2 proporciona el **contexto estructural** (arquitectura, dataset, protocolo anti-desactualización) y el **protocolo anti-desactualización** obligatorio.

**Síntesis:** Combinar mi marco estructural + protocolo anti-desactualización + datos frescos (954/358) con la profundidad operacional, datos verificados hoy, y protocolos concretos del LLM externo.

---

## 2. Comparativa Detallada

| Aspecto | Mi Evaluación v2 | LLM Externo | Síntesis |
|---------|------------------|-------------|----------|
| **Datos frescos** | 954/358 FULL ✅ | Asume 358 FULL ✅ | Consenso |
| **MAE Regressor** | Gap crítico identificado | **#1 prioridad + 3 pruebas validación** | Prioridad 1 + protocolo 3 pruebas |
| **Walk-forward 358 FULL** | "Viable" ⚠️ | "Piloto, no validación" (7-8% std error) | **Piloto de instrumentación** |
| **Algorithm shootout** | Pregunta abierta | **RF/LGBM/TabPFN en mismos folds** | Prioridad 2 |
| **TabPFN** | Pregunta | **TabPFN-2.5/3 verificado hoy** | Incluir si licencia compatible |
| **Feature selection L2** | Pregunta genérica | **Protocolo: correlación → permutation CV → SHAP** | Adoptar protocolo |
| **Cost model** | Gap identificado | **Fees Binance hoy + book depth real** | Prioridad 3 |
| **MAE validation** | Gap | **3 pruebas: ablación, placebo, baseline** | Adoptar protocolo 3 pruebas |
| **Walk-forward expanding vs rolling** | Pregunta | **Expanding + sample_weight + reportar por fold** | Adoptar |
| **Métricas económicas** | Pregunta | **Expectancy + bootstrap CI, no solo Sharpe** | Adoptar |
| **Online learning** | No mencionado | Descartado (con matices) | Evaluar A/B vs retrain completo |
| **Datos verificados hoy** | No | **Fees Binance, TabPFN-2.5/3** | Datos frescos críticos |

---

## 2. Crítica Constructiva a la Respuesta del LLM Externo

### ✅ Fortalezas Principales
1. **Datos verificados *hoy***: Fees Binance (spot 0.10%, perp 0.02%/0.05%), TabPFN-2.5/3 capabilities
2. **Protocolo MAE: 3 pruebas** (ablación, placebo, baseline) — concreto, falsable
3. **Validación L2 metodológicamente correcta**: Comparar (static+L2 en 358) vs (static-only en **mismos 358**)
3. **Estadísticas honestas**: 358 FULL → ~7-8% std error → "piloto de instrumentación"
4. **Fees Binance verificados hoy**: Spot 0.10%, perp 0.02%/0.05%, descuentos BNB
5. **Slippage con book depth real**: Usar `bid_wall_depth_10_btc` / `ask_wall_depth_10_btc`
6. **TabPFN-2.5/3**: 100% win rate vs XGB small/medium, 87% large, regresión nativa
7. **Correlaciones OBI**: obi_1/5/10/20 >0.85 → colapsar
8. **Protocolo MAE**: 3 pruebas (ablación, placebo, baseline ATR)
7. **Walk-forward expanding + sample_weight**: Commitido sensato
8. **Métricas económicas**: Expectancy + bootstrap CI, MaxDD como lower bound
9. **Priorización clara**: (1) MAE+3 pruebas, (2) shootout, (3) cost model

### ⚠️ Debilidades / Puntos a Cuestionar
1. **TabPFN licencia/token**: ¿Llamada de red? ¿Compatible 100% local (Ollama)?
2. **TabPFN CPU inference time** en 954 samples — ¿viable sin GPU?
3. **LightGBM hiperparámetros concretos** para 358 FULL no dados
4. **SHAP tiempo CPU** en 358×50 features — ¿orden de magnitud?
5. **Logistic Regression sanity-check**: ¿Cómo calibrar? `CalibratedClassifierCV`?
5. **MaxDD bootstrap CI**: ¿Cuántas remuestras? ¿Percentiles?
8. **Online learning descartado**: ¿Seguro? `SGDClassifier(partial_fit)` podría valer A/B test
9. **Falta test `n_jobs=1` vs paralelo** para RF determinista
9. **Falta test regresión predicción exacta** (2x mismo seed → predicciones idénticas)

### ❓ Preguntas Abiertas para LLM Externo
1. TabPFN licencia/token → ¿llamada de red? ¿Compatible 100% local?
2. LightGBM hiperparámetros concretos para 358 FULL
3. SHAP tiempo CPU en 358×50 features
4. Online learning: ¿A/B test con `SGDClassifier(partial_fit)` vs retrain completo?
4. MaxDD bootstrap CI: ¿remuestras? ¿percentiles?
5. Pipeline slippage con `bid_wall_depth_10_btc` — código skeleton?

---

## 3. Síntesis Enriquecida: Plan de Acción Consolidado

### Prioridades Consenso (Ambos Análisis)

| # | Acción | Esfuerzo | Impacto | Dependencia |
|---|--------|----------|---------|-------------|
| **1** | Cerrar MAE Regressor + 3 pruebas validación (ablación, placebo, baseline ATR) | Medio | **CRÍTICO** | Fase A completa |
| **2** | Shootout RF / LightGBM / TabPFN en folds existentes | Bajo | **ALTO** | Folds existentes |
| **3** | Cost model con book depth propio + fees Binance hoy | Medio | **ALTO** | Fees verificadas hoy |

### Pipeline Unificado Fase A → B → Económico

```
FASE A (Cimientos - BLOQUEANTE)
├── 1. Encoding determinista (D-012) ✅
├── 2. MAE Regressor + 3 pruebas (ablación, placebo, baseline ATR)
├── 3. Save/load + SHA-256
├── 4. Encoding order-independent
├── 5. Placeholder/non-placeholder logging
└── GATE: Tests Fase A pasan → FASE B

FASE B (Features Dinámicas + Walk-Forward)
├── 1. Ring Buffer L2 (P3) integración
├── 2. L2 Temporal Profile features (358 FULL)
├── 3. Walk-forward CV (3-5 folds expanding + sample_weight)
├── 4. MAE regressor en OOS (3 pruebas: ablación, placebo, baseline)
├── 5. Walk-forward PnL neto (358 FULL, bootstrap CI)
└── GATE: PnL neto piloto viable → TEST ECONÓMICO

TEST ECONÓMICO PILOTO
├── 1. Cost model realista (book depth + fees Binance hoy)
├── 2. Walk-forward PnL neto con costos reales
├── 3. Métricas: PnL neto + expectancy + bootstrap CI
├── 4. Sharpe/Calmar con bootstrap CI
├── 5. MaxDD como lower bound + bootstrap CI
└── DECISIÓN: Edge modesto/plausible → Acumular a 1000+ FULL
```

---

## 3. Preguntas Pendientes para LLM Externo (Próxima Interacción)

1. **TabPFN licencia/token**: ¿Llamada de red en inferencia? ¿Compatible 100% local (Ollama)?
2. **LightGBM hiperparámetros concretos** para 358 FULL: `max_depth`, `subsample`, `learning_rate`, `early_stopping_rounds`
3. **SHAP tiempo CPU** en 358 samples × 50 features — orden de magnitud
4. **Online learning**: ¿A/B test `SGDClassifier(partial_fit)` vs retrain completo cada 50 FULL?
4. **MaxDD bootstrap CI**: ¿Remuestras? ¿Percentiles?
5. **Pipeline slippage**: Código skeleton usando `bid_wall_depth_10_btc` / `ask_wall_depth_10_btc`

---

## 4. Archivos Relacionados en Vault

- `CGAlpha/tutor-methodology/evaluacion_oracle_estado_actual_v2.md` — Mi evaluación v2 (datos frescos)
- `CGAlpha/tutor-methodology/evaluacion_externa_prompt.md` — Prompt para evaluador externo
- `CGAlpha/tutor-methodology/graphify-tutor-methodology.md` — Metodología tutor
- `documentation/NEXUS_SUPERIOR.md` — Plan maestro P1-P9
- `aipha_memory/operational/training_dataset_v2.jsonl` — **Fuente real** (954/358 FULL)

---

## 5. Protocolo Anti-Desactualización (Recordatorio)

```python
# EJECUTAR SIEMPRE ANTES DE CUALQUIER EVALUACIÓN:
def refrescar_estado_oracle_antes_de_evaluar():
    import json
    with open('aipha_memory/operational/training_dataset_v2.jsonl') as f:
        lines = [json.loads(l) for l in f]
    total = len(lines)
    full = sum(1 for l in lines if l.get('l2_temporal_profile',{}).get('l2_data_quality')=='FULL')
    return {'total': total, 'full': full, 'partial': total-full, 'full_pct': full/total*100, 'fuente': 'training_dataset_v2.jsonl (GUI live)', 'timestamp': __import__('datetime').datetime.now().isoformat()}

# USO OBLIGATORIO:
estado = refrescar_estado_oracle_antes_de_evaluar()
print(f"DATASET ACTUAL: {estado['total']} total, {estado['full']} FULL ({estado['full_pct']:.1f}%)")
```