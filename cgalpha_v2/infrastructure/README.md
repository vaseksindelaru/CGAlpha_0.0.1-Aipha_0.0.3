# cgalpha_v2/infrastructure/

## Propósito
Capa de infraestructura: implementaciones concretas de los puertos definidos en `domain/ports/`.
Contiene adapters para fuentes externas (Binance, Redis, LLM providers), persistencia, data quality gates y risk management layer.

## Inputs / Outputs y contratos
- **Inputs:** datos crudos de fuentes externas (klines, order book, streams)
- **Outputs:** objetos de dominio tipados que implementan los Protocols de `domain/ports/`
- **Contrato:** todo adapter implementa al menos un Protocol de `domain/ports/`. La infraestructura NO importa desde `application/` ni `interfaces/`.

## Dependencias
- `cgalpha_v2/domain/ports/` — Protocols que cada adapter debe implementar
- `cgalpha_v2/shared/` — tipos, excepciones

## Módulos activos (Fase 0)
| Módulo | Estado |
|--------|--------|
| `data_quality/` | ✅ Fase 0 — Data Quality Gates |
| `risk/` | ✅ Fase 0 — Risk Management Layer |
| `persistence/` | 🔲 Pendiente — migración de cgalpha/nexus/ (Redis) |
| `llm/` | 🔲 Pendiente — migración de core/llm_providers/ |
| `market/` | 🔲 Pendiente — BinanceAdapter |

## Estado actual
`EN CONSTRUCCIÓN` — módulos data_quality y risk implementados en Fase 0.

## Próximo incremento planificado
- `infrastructure/market/binance_adapter.py`
- `infrastructure/persistence/redis_adapter.py`
- `infrastructure/llm/openai_adapter.py`
