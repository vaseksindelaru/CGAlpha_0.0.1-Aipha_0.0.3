# ADR-ACOPLAMIENTO-TEMPORAL-2-EVO-0007: Activación de D-014 en pipeline Live

## Contexto

El filtro causal D-014 (`t_feature ≤ t_candle_close_ms − 200ms`) fue implementado en `L2RingBuffer.synthesize_at_retest()` pero quedó inactivado en producción: `live_adapter.py` lo estaba llamando (en la línea 634) omitiendo pasar el parámetro `t_candle_close_ms`. En consecuencia, toda muestra recopilada operaba como `PRE_D014` sin garantías causales. Esto comprometía los 150 samples necesarios para el Set A, contaminando un eventual modelo predictivo con datos posiblemente obtenidos post-cierre de vela.

## Decisión

**Opción B (La Matemática)** es la ÚNICA OPCIÓN VIABLE que se adopta bajo este evento. El adapter (`live_adapter.py`) ya realiza internamente el cálculo del tiempo de cierre con alta confianza: `current_kline["close_time"] = open_time + interval_ms - 1`. Por tanto, delegamos este parámetro ya deducido para anclar la línea de tiempo límite de `D-014`.

### Alternativa descartada
**Opción A (La Nativa)** fue **DESCARTADA**. El WebSocket de trades (`@trade` y `aggTrade`) no divulga la llave estructural `k['T']` (close time de kline) ya que el stream no está suscrito a la estructura `@kline_5m`. Introducir esta suscripción representaría un cambio de arquitectura mayor ajeno al alcance mitigador de este ticket urgente.

## Consecuencias

*   **Efectividad Inmediata:** La modificación inyecta el `t_candle_close_ms` a `synthesize_at_retest()` y obliga al estricto límite inmutable de tolerancia `epsilon_ms=200ms`. El requisito `D-014` transita de estado "Implementado" a "Activo" en producción plena.
*   **Segmentación del Catálogo (`Set A`):** 
    *   `POST-commit`: Las futuras muestras están legitimadas causales y portarán la calidad `POST_D014`.
    *   `PRE-commit`: Los 47 samples del Set A existentes restan registrados como `PRE_D014`, los cuales deberán ser excluidos de cualquier benchmark comparativo A/B de validación por carecer de certificación temporal estricta.
