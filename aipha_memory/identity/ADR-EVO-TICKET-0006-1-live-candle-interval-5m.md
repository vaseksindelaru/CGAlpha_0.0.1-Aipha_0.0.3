# ADR-EVO-TICKET-0006-1 — Live Candle Interval: 5m Alignment with Detector Calibration

## Estatus
ACEPTADO e IMPLEMENTADO (2026-06-20)

## Contexto
El pipeline live de CGAlpha v3 opera a través de `LiveDataFeedAdapter`, que agrega ticks de WebSocket en velas cerradas y las alimenta al `TripleCoincidenceDetector` para detección de zonas.

Investigación de arqueología de git (EVO-TICKET-0006) reveló que el intervalo de vela live fue fijado en 1 minuto por razones de demo, no de calibración:

- Commit `aa0190df` (2026-04-12): introdujo `self.interval_s = 60` con el comentario original `# Default 1m para el MVP live demo`.
- Commit `807b772` (2026-05-04): refactorizó el adaptador a la "Two-Speed Architecture" (Speed 1 = zone detection @ 1min, Speed 2 = retest @ tick), eliminando el comentario demo y convirtiendo 1m en un hecho no cuestionado.
- Calibración del ZigZag: `zigzag_threshold = 0.0018` está documentado como "P75 rango real vela 5m BTCUSDT" en `triple_coincidence.py` (líneas 536 y 753).

Esto creó un desajuste no resuelto: el detector fue calibrado con velas de 5m, pero el pipeline live operaba en 1m. Durante el diagnóstico de EVO-TICKET-0005 se observó que el detector no detectaba zonas en 1m durante régimen actual de BTC, aunque sí lo hacía en 5m sobre períodos más largos.

Tests de control adicionales descartaron que el problema fuera puramente de timeframe:
- 200 velas de 1m → 0 zonas.
- Las mismas 200 velas agrupadas sintéticamente a 5m → 0 zonas.
- 1000 velas de 1m → 0 zonas.
- Las mismas 1000 velas agrupadas sintéticamente a 5m → 0 zonas.

Conclusión: el régimen de las últimas ~16h fue atípicamente quieto (rango ~$600), lo que suprime la detección independientemente del timeframe. Sin embargo, el desajuste 1m-vs-5m sigue siendo una deuda arquitectónica real que debe resolverse deliberadamente.

## Decisión
Alinear el intervalo de operación live con el intervalo de calibración del detector:

1. Cambiar `LiveDataFeedAdapter.interval_s` de `60` a `300` (5 minutos).
2. Cambiar la URL de `warm_start()` para solicitar velas de 5m a Binance REST (`interval=5m`) en lugar de 1m.
3. Mantener `lookback_candles=30` y `retest_timeout_bars=50` en `TripleCoincidenceDetector` sin cambios, asumiendo que fueron diseñados como contadores de velas de 5m.
4. Mantener `warm_start(lookback_bars=200)` en `server.py`; ahora representa 200 velas de 5m (~16.6h de historia), suficiente para el detector ZigZag.

## Consecuencias
- **Positivas**:
  - El pipeline live usa el mismo timeframe para el que fueron calibrados los thresholds (especialmente `zigzag_threshold`).
  - Reduce ruido de velas de 1m y potencialmente mejora calidad de zonas detectadas.
  - Elimina una inconsistencia arquitectónica heredada de un MVP demo.
- **Neutrales**:
  - Latencia de detección de zonas pasa de ~1 min a ~5 min. No impacta el modo actual de cosecha de datos de entrenamiento.
  - El warm_start descarga menos granularidad pero más historia real en minutos.
- **Riesgos**:
  - Si algún componente downstream asumía implícitamente 1m (por ejemplo, SLOs de freshness), debe revisarse.
  - Los fallback `candle["index"] * 300000` en `triple_coincidence.py` ahora son consistentes con el intervalo real.

## Alternativas consideradas
- **Opción B — Recalibrar thresholds para 1m**: Descartada porque requiere un estudio de percentiles completo en 1m sin evidencia previa de que 1m sea superior. La calibración existente es de 5m.
- **Opción C — Hacer el timeframe configurable**: Descartada como EXPANSION_DEBT prematura. El objetivo actual es estabilizar el pipeline, no generalizarlo.
- **Mantener 1m**: Descartada porque perpetúa un desajuste entre operación y calibración sin justificación técnica.

---
*Referencia: EVO-TICKET-0006, EVO-TICKET-0005, `documentation/Optimizing ZigZag Threshold Calibration.md`.*
