# Fase 7 - Ghost Architect v0.2.2 (Inferencia Causal Deep)

## Objetivo
Evolucionar de un analisis reactivo (sintomas) a un analisis causal (causas raiz) sin reescribir la arquitectura.

El comando operativo sigue siendo:

```bash
cgalpha auto-analyze
```

## Cambio Clave
`cgalpha/ghost_architect/simple_causal_analyzer.py` ahora usa:

1. Inferencia causal con LLM (motor principal).
2. Fallback heuristico (si LLM no disponible o falla).
3. Metricas de calidad causal:
   - `accuracy_causal`
   - `efficiency`
4. Enriquecimiento de microestructura:
   - `order_book_features.jsonl` (join por `trade_id` o timestamp nearest)
   - marcadores `ENRICHED_EXACT`, `ENRICHED_NEAREST`, `BLIND_TEST`, `LOCAL_ONLY`
5. Gates de readiness para v0.3:
   - `readiness_gates.proceed_v03`
   - `data_quality_pass` (blind ratio + lag)
   - `causal_quality_pass` (accuracy + efficiency)

## Fuente de Datos
Fuente principal:
- `aipha_memory/cognitive_logs.jsonl`

Fallbacks de lectura:
- `aipha_memory/operational/action_history.jsonl`
- `aipha_memory/evolutionary/bridge.jsonl`
- `aipha/evolutionary/bridge.jsonl`

Fuente de microestructura (si existe):
- `aipha_memory/operational/order_book_features.jsonl`

## De Correlacion a Causalidad
### Aipha v0.1.4 (correlacion)
- Veia "win rate bajo" y sugeria "subir threshold".
- Relacionaba metricas agregadas sin separar contexto de mercado.

### CGAlpha v0.0.1 (causalidad)
- Evalua contexto completo por trade:
  - Order Book / microestructura
  - News impact
  - MFE/MAE
  - Fakeouts
  - Candle regime / trend breaks
- Propone hipotesis de causa raiz:
  - "Fakeout en order book -> mantener corto solo con confirmacion de profundidad"
  - "Ruptura de tendencia -> subir stop loss y reducir TP"

## Flujo v0.2
1. Cargar logs historicos.
2. Detectar patrones base (heuristicos causales).
3. Ejecutar inferencia LLM para hipotesis de causa raiz.
4. Si LLM falla: usar hipotesis heuristicas.
5. Convertir hipotesis en comandos accionables `cgalpha codecraft apply --text ...`.
6. Medir `accuracy_causal` y `efficiency`.
7. Guardar reporte JSON en `aipha_memory/evolutionary/causal_reports/`.

## Flujo v0.2.2 (Deep Causal incremental)
1. Parsear logs principales (bridge/cognitive/action_history).
2. Enriquecer snapshot por trade con `order_book_features.jsonl`.
3. Si no hay match de microdatos dentro de ventana, marcar `BLIND_TEST` (no inventar evidencia).
4. Construir prompt Deep Causal con evidencia microestructural.
5. Ejecutar LLM o fallback heuristico.
6. Calcular `causal_metrics` + `data_alignment`.
7. Evaluar `readiness_gates` para decidir si se puede escalar a v0.3.

## Metricas
### `accuracy_causal`
Precision promedio de hipotesis sobre subconjuntos donde la senal causal aparece en logs reales.

### `efficiency`
Combinacion de:
- porcentaje de hipotesis accionables,
- cobertura efectiva de senales sobre el historico.

## Garantias de Integracion
- No cambia estructura de carpetas.
- `auto-analyze` sigue operativo.
- `analyze_logs()` mantiene compatibilidad y delega a `analyze_performance()`.
- El sistema no depende 100% del LLM gracias al fallback heuristico.
- No se requiere refactor total; evoluciona por capas incrementales.

## Siguiente Capitulo
- Continuidad oficial: `bible/codecraft_sage/phase8_deep_causal_v03.md`
