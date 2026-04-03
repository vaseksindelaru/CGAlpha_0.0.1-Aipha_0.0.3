# QUICK START: Implementación de Order Book en CGAlpha

**Duración estimada para leer:** 10 minutos  
**Para:** Equipo técnico listo para implementar  
**Estado:** Pre-implementación - lista de preparación

---

## 🎯 OBJETIVO EN 30 SEGUNDOS

Integrar análisis de Order Book (microestructura) en CGAlpha para escalping 5min/1min sin romper v1.

**Cómo:** Modularidad + Feature Flags + Threading aislado  
**Tiempo:** 16 semanas (4 meses) con 2-3 personas  
**Riesgo:** BAJO (mitigable con arquitectura propuesta)

---

## ✅ CHECKLIST PRE-IMPLEMENTACIÓN

### Decisiones Arquitectónicas (Debe completar ANTES de código)

- [ ] **Decidir:** ¿Aprobamos arquitectura modular propuesta?
  - Opción A: SÍ → Proceder con Fase 0
  - Opción B: NO → Justificar cambios

- [ ] **Decidir:** ¿Requerimos DataSourceProvider abstracción?
  - Opción A: SÍ → 2 semanas previas
  - Opción B: NO → Requiere re-diseño (riesgo ALTO)

- [ ] **Decidir:** ¿Threading separado o async conversion?
  - Opción A: Thread + Queue (recomendado, bajo riesgo)
  - Opción B: Convertir todo a async (recomendado NO, riesgo ALTO)

- [ ] **Decidir:** ¿Cuál es prioridad: v1 estabilidad o velocidad v2?
  - Opción A: v1 estabilidad primero (recomendado)
  - Opción B: Velocidad (requiere más riesgo)

### Preparación Técnica

- [ ] **Equipo:** ¿Tienes 2-3 personas disponibles 16 semanas?
  - SÍ → Óptimo (parallelizar Fase 0-1)
  - NO → Mínimo 1 persona, timeline crece a 24 semanas

- [ ] **Testing:** ¿Infraestructura de testing robusta?
  - Revisar: ¿Tests corren < 10 segundos?
  - Revisar: ¿Coverage actual > 75%?

- [ ] **CI/CD:** ¿Tienes pipeline de deployment?
  - Requerido: Pre-deployment testing
  - Requerido: Canary deployment support

- [ ] **Monitoring:** ¿Sistema de alertas/logging en lugar?
  - Necesario para: WebSocket health
  - Necesario para: Signal latency tracking

### Documentación & Conocimiento

- [ ] **Docs:** ¿Equipo ha leído CGALPHA_OBSERVATIONS_SUMMARY.md?
- [ ] **Docs:** ¿Equipo ha revisado puntos críticos (3)?
- [ ] **Docs:** ¿Equipo entiende feature flags strategy?
- [ ] **Code:** ¿Alguien ha mapeado acoplamiento DuckDB?
- [ ] **Code:** ¿Alguien ha identificado threading points?

---

## 📋 FASE 0: PREPARACIÓN (2 Semanas)

### Week 1: DataSourceProvider Abstracción

#### Tareas:
1. **Crear interfaz**
   ```
   File: core/interfaces/data_source.py
   - DataSourceProvider (ABC)
   - Methods: load_data(), get_metadata(), disconnect()
   - Tests: MockDataSource
   ```

2. **Refactor trading_engine.py**
   ```
   Change: trading_engine.load_data()
   From: duckdb.query(...).to_df()
   To: self.data_source.load_data()
   
   Requirement: 100% backward compatible
   Tests: MUST pass identical
   ```

3. **Create implementations**
   ```
   File: core/data_sources/duckdb_source.py
   File: core/data_sources/mock_source.py
   
   Both: Implement DataSourceProvider
   ```

4. **Update tests**
   ```
   - Mock out DataSourceProvider
   - Run 100 existing tests
   - Verify: 100% pass, same behavior
   ```

#### Verification:
```
✓ All tests passing
✓ Zero latency regression
✓ load_data() behavior unchanged
✓ DuckDB abstracted (no direct calls)
```

#### Exit Criteria:
- [ ] PR created, reviewed, merged
- [ ] Tests: 100/100 passing
- [ ] Benchmark: latency unchanged
- [ ] Code review: approved by 2 people

---

### Week 2: Branch Creation & Feature Flags

#### Tareas:
1. **Create v2 branch**
   ```
   Branch: feature/orderbook-v2-integration
   Base: main
   ```

2. **Add feature flags to config**
   ```json
   {
     "features": {
       "use_orderbook": false,
       "use_threaded_worker": false,
       "v2_engine": false
     }
   }
   ```

3. **Create trading_engine_v2.py**
   ```python
   # Same as trading_engine.py, but:
   # - Accepts use_orderbook parameter
   # - Has placeholder for Order Book code
   # - 100% backward compatible when use_orderbook=False
   ```

4. **Update bootstrap.py**
   ```python
   # Add optional Order Book attributes
   # But don't initialize unless feature flag set
   ```

#### Verification:
```
✓ Feature flag functional
✓ use_orderbook=False → v1 behavior
✓ No code changes visible to users
✓ Ready for Fase 1
```

#### Exit Criteria:
- [ ] trading_engine_v2.py exists, passes tests
- [ ] Feature flags working
- [ ] Branch created and protected
- [ ] Ready for PR to start Fase 1

---

## 📋 FASE 1: ORDER BOOK FOUNDATION (4 Weeks)

### Week 3: Core Orderbook Module

#### Create Structure:
```
core/orderbook/
├─ __init__.py
├─ interfaces/
│  ├─ __init__.py
│  ├─ provider.py       # OrderBookProvider (ABC)
│  ├─ calculator.py     # MicrostructureCalculator (ABC)
│  └─ parser.py         # OrderBookL2Parser (ABC)
├─ models/
│  ├─ __init__.py
│  ├─ order_book.py     # OrderBook dataclass
│  ├─ level2.py         # Level2 dataclass
│  └─ metrics.py        # MicrostructureMetrics dataclass
├─ providers/
│  ├─ __init__.py
│  └─ mock_provider.py  # MockL2Provider
├─ parsers/
│  ├─ __init__.py
│  └─ generic_parser.py # Generic Level2 parser
├─ calculators/
│  ├─ __init__.py
│  ├─ obi_calculator.py
│  ├─ delta_calculator.py
│  └─ vwap_calculator.py
└─ tests/
   └─ test_mock_provider.py
```

#### Deliverables:
- [ ] Interfaces defined (50 tests)
- [ ] MockL2Provider working (50 tests)
- [ ] All tests green
- [ ] Documentation for each module

### Week 4: Calculators & Signal Generation

#### Create:
```
core/orderbook/calculators/ COMPLETE
├─ obi_calculator.py      # Order Book Imbalance
├─ delta_calculator.py    # Cumulative Delta
├─ spread_analyzer.py     # Spread analysis
├─ volume_analyzer.py     # Volume concentration
└─ vwap_calculator.py     # VWAP

core/orderbook/signals/
└─ microstructure_signals.py
```

#### Tests:
- [ ] 60 tests for calculators
- [ ] Edge cases covered
- [ ] Performance validated
- [ ] Integration tests with MockL2Provider

#### Integration:
- [ ] Calculators integrate with trading_engine_v2
- [ ] Signals generated from mock data
- [ ] Latency < 50ms per calculation

### Week 5: Threading & Queue Architecture

#### Create:
```
core/orderbook/worker.py
├─ OrderBookWorkerThread (class)
├─ Queue communication
├─ Signal aggregation
└─ Error handling

core/trading_engine_v2.py
├─ start_orderbook_worker()
├─ read_from_signal_queue()
├─ combine_signals()
└─ execute_trade()
```

#### Tasks:
- [ ] Worker thread implementation
- [ ] Queue-based communication
- [ ] Signal merging logic
- [ ] Error handling & reconnection

#### Testing:
- [ ] 40+ threading tests
- [ ] Stress tests (1000+ signals)
- [ ] Deadlock validation
- [ ] Performance benchmarking

### Week 6: Validation & Staging Deployment

#### Backtesting:
```python
# Compare v1 vs v2 on historical data
v1_signals = run_v1(historical_data)
v2_signals = run_v2(historical_data, use_orderbook=False)  # Same as v1
v2_ob_signals = run_v2(historical_data, use_orderbook=True)

Assert: v1_signals == v2_signals  # MUST be identical
```

#### Staging Deployment:
- [ ] Deploy to staging with use_orderbook=False
- [ ] Run 24h with v1 behavior
- [ ] Verify: zero errors
- [ ] Verify: latency unchanged
- [ ] Verify: trades executed correctly

#### Exit Criteria (Fase 1):
- [ ] 150+ new tests passing
- [ ] Order Book module complete
- [ ] v1 untouched (use_orderbook=False)
- [ ] Staging deployment successful
- [ ] Ready for Fase 2

---

## 📋 FASE 2: REAL-TIME INTEGRATION (4 Weeks)

### Week 7-8: Real Exchange Integration

#### Create:
```
core/orderbook/providers/binance_provider.py
├─ BinanceL2Provider (async)
├─ WebSocket handling
├─ Level2 parsing
├─ Reconnection logic
└─ Authentication
```

#### Tasks:
- [ ] Implement BinanceL2Provider
- [ ] TLS/auth validated
- [ ] WebSocket stress test
- [ ] Reconnection tested (artificial failures)
- [ ] 40+ integration tests

#### Forward Test:
```
Run: 24 hours with real Order Book data (mock trading)
Monitor:
- [ ] Signal generation rate
- [ ] Latency percentiles
- [ ] WebSocket uptime
- [ ] Error rate < 0.1%
```

### Week 9-10: Integration & Canary Deployment

#### Integration:
- [ ] Integrate into cgalpha_v2/domain/
- [ ] Create ScalpingService domain object
- [ ] Update bootstrap.py with Order Book provider
- [ ] Use case: analyze_market_with_orderbook

#### Canary Deployment:
```
Stage 1 (Testnet, 10%):
  ├─ 1 symbol (EUR/USD)
  ├─ Mock balances
  ├─ Monitor 7 days
  └─ Success criteria: 0 errors, signal quality 70%+

Stage 2 (Testnet, 50%):
  ├─ 2-3 symbols
  ├─ Mock balances
  ├─ Monitor 7 days
  └─ Success criteria: consistent performance

Stage 3 (Real, 10%):
  ├─ Real account (small)
  ├─ 1 symbol, $100 risk
  ├─ Monitor 7 days
  └─ Success criteria: profitability validated
```

#### Exit Criteria (Fase 2):
- [ ] Real exchange integration complete
- [ ] Canary deployment active
- [ ] 70%+ signal accuracy validated
- [ ] < 100ms latency confirmed
- [ ] Ready for Fase 3

---

## 📋 FASE 3: SCALING (6 Weeks)

### Week 11-12: Multi-Exchange Support

#### Create:
```
core/orderbook/providers/coinbase_provider.py
core/orderbook/providers/ib_provider.py
core/orderbook/providers/generic_provider.py (abstraction)

Factory: OrderBookProviderFactory
  ├─ create(exchange_type, config)
  └─ Supports: Binance, Coinbase, IB, Mock
```

#### Tasks:
- [ ] Implement 2-3 additional exchanges
- [ ] Generic parser for all
- [ ] 30+ tests per exchange
- [ ] Load testing

### Week 13-14: Production Deployment (50%)

#### Preparation:
- [ ] Symbol router architecture
- [ ] Worker pool (N threads)
- [ ] Config for multi-symbol
- [ ] Monitoring dashboard

#### Deployment:
```
50% rollout:
├─ 3-5 symbols active
├─ 50% of capital deployed
├─ Monitor 7 days
└─ Decision: proceed to 100%?
```

### Week 15-16: Full Production (100%)

#### Full Deployment:
- [ ] All symbols active
- [ ] 100% capital deployed
- [ ] v1 enters deprecation
- [ ] Monitoring & alerting active

---

## 🔍 SUCCESS METRICS

### Must-Have (Exit Blockers)

| Metric | Target | Actual | Status |
|---|---|---|---|
| Breaking Changes | 0 | TBD | |
| Test Coverage | 80% | TBD | |
| Latency (p95) | <100ms | TBD | |
| Signal Accuracy | 70%+ | TBD | |
| Uptime | 99%+ | TBD | |
| WebSocket Stability | 99%+ | TBD | |

### Nice-to-Have

- Latency <50ms (ultra-low latency)
- Accuracy 85%+ (excellent)
- Multi-exchange 5+ (highly scalable)
- CPU usage <50% (efficient)

---

## 🚨 CRITICAL PATHS

### Must NOT skip:
1. **DataSourceProvider abstraction** (Fase 0)
   - If skipped: guaranteed rupture of v1
   - If delayed: blocks everything else

2. **Feature Flags** (Fase 0-1)
   - If skipped: rollback impossible
   - If delayed: testing complex

3. **Threading design** (Fase 1)
   - If wrong: deadlocks, crashes
   - If delayed: performance issues

4. **Canary deployment** (Fase 2-3)
   - If skipped: production risk HIGH
   - If delayed: deployment risky

### Safe to parallelize:
- Testing infrastructure (parallel to Fase 0)
- Documentation (ongoing)
- Monitoring setup (before Fase 2)

---

## 📚 DOCUMENTATION CHECKLIST

### Create:
- [ ] API documentation (interfaces)
- [ ] Architecture decision records (ADRs)
- [ ] Deployment guide
- [ ] Troubleshooting guide
- [ ] Trading bot operations guide

### Update:
- [ ] README.md (add Order Book section)
- [ ] ARCHITECTURE.md
- [ ] DEPLOYMENT.md
- [ ] Testing guide

---

## 🎓 KNOWLEDGE REQUIREMENTS

### Required Before Starting:

**Python:**
- [ ] Async/await fundamentals
- [ ] Threading concepts
- [ ] Queue (thread-safe communication)
- [ ] ABC (abstract base classes)

**Architecture:**
- [ ] Adapter pattern
- [ ] Dependency injection
- [ ] Feature flags pattern
- [ ] Producer-consumer pattern

**Finance:**
- [ ] Order Book microstructure basics
- [ ] OBI (Order Book Imbalance)
- [ ] Scalping timeframes
- [ ] Level 2 data

### Nice to Know:

- WebSocket protocol
- Exchange APIs (Binance, Coinbase)
- Deployment patterns
- Monitoring tools

---

## 🎯 DECISION TREE

```
START
│
├─ Approve architecture?
│  ├─ NO → Modify ADRs, re-propose
│  └─ YES → Continue
│
├─ Have 2-3 people for 16 weeks?
│  ├─ NO → Plan 24 weeks for 1 person
│  └─ YES → Proceed
│
├─ DataSourceProvider abstraction priority?
│  ├─ NO → High risk! Reconsider
│  └─ YES → Start Fase 0
│
├─ Threading or async conversion?
│  ├─ THREADING → Low risk, proceed
│  └─ ASYNC → High risk, reconsider
│
└─ Ready to START FASE 0?
   ├─ NO → Fix blockers
   └─ YES → Begin implementation
```

---

## ✅ FINAL CHECKLIST

Before coding starts:

- [ ] Architecture approved by tech lead
- [ ] Equipo entiende 3 puntos críticos
- [ ] Feature flags strategy agreed
- [ ] Timeline confirmed (16 weeks)
- [ ] Roles assigned (architect, devs, QA)
- [ ] Testing infrastructure ready
- [ ] Monitoring setup planned
- [ ] Documentation structure created
- [ ] Deployment plan reviewed
- [ ] Rollback strategy validated

---

## 🚀 START HERE

**If all checkboxes above are DONE:**

1. Create branch: `feature/orderbook-v2-integration`
2. Open Fase 0 week 1 task
3. Run: `pytest tests/ -v` (baseline)
4. Create: `core/interfaces/data_source.py`
5. Begin refactoring: `core/trading_engine.py`

**Expected output after Week 1:**
```
✓ DataSourceProvider created
✓ 100 existing tests still passing
✓ load_data() refactored
✓ PR ready for review
```

---

**Cuando estén listos: Adelante con Fase 0. Éxito.**
