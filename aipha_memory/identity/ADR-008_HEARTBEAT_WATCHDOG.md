# ADR-008 — Heartbeat Watchdog for Pipeline Clock Resilience

## Estatus
ACEPTADO e IMPLEMENTADO (2026-06-13)

## Contexto
El pipeline de CGAlpha depende de eventos de mercado para avanzar su reloj interno (formación de velas, detección de zonas, etiquetado de señales). Históricamente, esta responsabilidad recaía exclusivamente en el stream `aggTrade` de Binance. 

Se detectó una anomalía crítica (EVO-TICKET-0003) donde el stream `aggTrade` de Binance Futures queda silenciado (silent failure) mientras la conexión WebSocket permanece abierta y otros streams (como `depthUpdate`) siguen entregando datos. Debido a que el `live_adapter.py` ignoraba todo lo que no fuera `aggTrade`, el sistema quedaba congelado permanentemente, perdiendo días de recolección de datos.

## Decisión
Implementar un mecanismo de "Heartbeat" en el `live_adapter.py` que:
1. Monitorea el tiempo transcurrido desde el último evento `aggTrade`.
2. Utiliza los mensajes `depthUpdate` (que Binance envía cada 100ms independientemente de los trades) como fuente de reloj secundaria.
3. Si el silencio de `aggTrade` excede los 30 segundos (`_heartbeat_timeout_ms`), el sistema utiliza el timestamp del `depthUpdate` para evaluar si debe cerrar la vela actual.
4. En caso de cierre de vela por heartbeat, el precio de cierre se deriva del último trade conocido o, en su defecto, del mejor bid del libro de órdenes.

## Consecuencias
- **Positivas**: Resiliencia total ante fallos específicos de streams de trades. El pipeline avanzará incluso en mercados de bajísima liquidez o fallos de distribución de datos de Binance.
- **Neutrales**: El volumen de velas cerradas por heartbeat será 0.0, lo cual es factualmente correcto si no hay trades.
- **Riesgos**: Posible discrepancia menor de precio si el heartbeat usa el best bid y luego llega un trade con un precio muy distinto (poco probable dada la frecuencia de 100ms de `depthUpdate`).

## Alternativas consideradas
- **Reinicio automático**: Descartado por ser reactivo y no resolver el problema durante el tiempo de downtime entre fallos.
- **Ignorar trades y usar solo tiempo de sistema**: Descartado porque los trades proporcionan el timestamp oficial de Binance, evitando drift con el servidor.

---
*Referencia: EVO-TICKET-0003, Punto Ciego #7 (identificado tras el fallo).*
