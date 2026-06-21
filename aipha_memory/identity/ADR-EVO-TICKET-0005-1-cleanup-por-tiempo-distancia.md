# ADR-EVO-TICKET-0005-1 — Zone Cleanup: Tiempo+Distancia ATR vs Índice de Buffer

## Estado
**ACEPTADO e IMPLEMENTADO** — 2026-06-19 (commit e984c61)

## Contexto
`TripleCoincidenceDetector._cleanup_expired_zones()` usaba `candle_index` del buffer circular para determinar si una zona había expirado. Este índice **no es estable entre reinicios**: cada vez que el proceso arranca, el buffer empieza desde 0. Una zona creada en el ciclo anterior con `created_at_index=400` nunca expirará si el buffer actual solo tiene 50 velas — el índice actual nunca alcanzará 400 en ese ciclo de vida.

Consecuencia observada (EVO-TICKET-0005): zonas de soporte/resistencia de la semana pasada (66.5k-66.0k) aparecían en el GUI con precio actual en 63.9k, distorsionando la vista operacional y potencialmente afectando el etiquetado de retests.

Este patrón es idéntico al **Punto Ciego #4** documentado en `architectural_analysis.md`: estado persistido que no es estable ante restart.

**Alternativa evaluada:** persistir el índice absoluto de vela (counter global que sobrevive entre reinicios).
- Ventaja: semánticamente limpio, el índice sigue siendo el criterio.
- Desventaja: introduce una segunda fuente de estado a sincronizar — si el counter global y el buffer se desincronizан (crash, corrupción del archivo de estado), las zonas nunca expiran o expiran prematuramente. Cambia el criterio de expiración de "cuántas velas han pasado" (relativo, robusto) a "qué número de vela global es este" (absoluto, frágil).

## Decisión
Reemplazar el criterio de expiración basado en `candle_index` por **dos criterios independientes basados en timestamp y distancia ATR**:

1. **Tiempo transcurrido:** si el timestamp actual supera `zone.created_at_ts + max_age_seconds`, la zona expira.
2. **Distancia de precio:** si la distancia entre el precio actual y el centro de la zona supera `zone_max_distance_atr * atr_at_creation`, la zona expira.

Ambos criterios son absolutos y **sobreviven a reinicios sin sincronización adicional** — solo requieren el timestamp de creación y el ATR en el momento de formación, ambos ya persistidos en el estado de zona.

`zone_max_distance_atr=5.0` es PROVISIONAL (basado en intuición, no en percentiles reales). Está marcado con comentario en el código. La calibración real requiere ≥200 ciclos de detección con el timeframe correcto (5m, tras EVO-TICKET-0006).

## Consecuencias

**Positivas:**
- Cleanup funciona correctamente después de reinicios sin estado adicional.
- Zonas obsoletas desaparecen del GUI en el próximo ciclo de detección.
- El criterio de distancia ATR es más semánticamente coherente que el de índice: una zona "expira" cuando el precio ya no la está respetando, no solo porque hayan pasado N velas.

**Negativas / Trade-offs:**
- `zone_max_distance_atr=5.0` es provisional — demasiado permisivo o demasiado estricto si el ATR real difiere significativamente del supuesto. Requiere calibración con datos reales.
- El criterio de tiempo introduce una dependencia de `time.time()` del sistema, que puede tener drift menor respecto a los timestamps de Binance. Riesgo documentado en EVO-TICKET-0003 como Punto Ciego #1 — aceptado porque el drift esperado (~segundos) es irrelevante para expiración de zonas (escala de horas/días).

**Deuda residual:**
- `calibration_pending: true` para `zone_max_distance_atr` — no cambiar a una constante no marcada hasta completar el percentile analysis.
- Este ticket es la primera evidencia concreta de por qué P5 (TripleCoincidenceDetector) necesita su propio CRB. Componente protegido con 3 bugs documentados en un solo ticket sin CRB es un riesgo.

## Referencia
- EVO-TICKET-0005, commits e984c61 y 2155bdd
- Punto Ciego #4 en `architectural_analysis.md` (estado no estable ante restart)
- ADR-EVO-TICKET-0006-1 (decisión de timeframe 5m que habilita la calibración de zone_max_distance_atr)
