# Fase 2 — Retroanálisis + Mejora Emergente

- Fecha: 2026-04-12 03:47:07 UTC
- Sharpe neto Fase 1: 1.1372

## Features más discriminantes (MI)
- cumulative_delta_at_retest: MI=0.051681, F=0.3220
- direction: MI=0.051642, F=4.6449
- atr_14: MI=0.042752, F=8.2210

## Features más débiles (MI)
- vwap_at_retest: MI=0.006740
- obi_10_at_retest: MI=0.000000
- regime: MI=0.000000

## Decisión
- promote_to_level4: False
- razón: Sharpe neto avg=1.1372 <= 1.5
- conclusión crítica: Fase 1 es positiva pero insuficiente para ADN nivel 4. Existe riesgo de sobreajuste por bajo recuento de eventos OOS en ventanas 1 y 3.
- siguiente paso emergente: Implementar CodeCraft Sage (parse->modify->tests->git), ampliar OOS a ventanas con mínimo 25 retests y activar Fase 3 live-data scaffolding.

## Propuesta clave
- Implementar `CodeCraft Sage` operativo para ejecutar `TechnicalSpec` aprobadas con barrera de tests y commit versionado.

## Readiness Fase 3
- WebSocket Binance detectado: False
- ShadowTrader presente: True
- NexusGate presente: True
