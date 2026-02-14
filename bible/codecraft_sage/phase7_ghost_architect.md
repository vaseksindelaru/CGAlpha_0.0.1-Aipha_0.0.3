# Fase 7 - Ghost Architect v0.2 (Inferencia Causal)

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

## Fuente de Datos
Fuente principal:
- `aipha_memory/cognitive_logs.jsonl`

Fallbacks de lectura:
- `aipha_memory/operational/action_history.jsonl`
- `aipha_memory/evolutionary/bridge.jsonl`
- `aipha/evolutionary/bridge.jsonl`

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
