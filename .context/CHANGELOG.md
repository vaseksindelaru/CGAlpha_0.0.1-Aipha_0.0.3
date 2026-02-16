# CGAlpha v2 Reconstruction Changelog

All notable changes to the v2 reconstruction are documented here.

## [2026-02-16] Phase 2.1 - Foundation

### Added

#### Domain Models (`cgalpha_v2/domain/models/`)
- `signal.py` - Signal value object for trading signals
  - Immutable dataclass with validation
  - Fields: symbol, direction, confidence, timestamp, detectors
  - Tests: tests_v2/unit/domain/test_signal.py (pending)
  
- `trade.py` - TradeRecord entity and TradeOutcome value object
  - TradeRecord: Complete trade data with MFE/MAE trajectories
  - TradeOutcome: Result classification (TP/SL/Timeout)
  - Tests: tests_v2/unit/domain/test_trade.py (pending)

- `prediction.py` - Prediction value object for Oracle ML
  - Fields: probability, direction, features, model_version
  - Tests: tests_v2/unit/domain/test_prediction.py (pending)

- `analysis.py` - Pattern, Hypothesis, Recommendation models
  - Pattern: Detected pattern across trade snapshots
  - Hypothesis: Causal explanation for pattern
  - Recommendation: Actionable insight from hypothesis
  - Tests: tests_v2/unit/domain/test_analysis.py (pending)

- `proposal.py` - Proposal entity for code evolution
  - Fields: proposal_id, spec, status, score
  - Tests: tests_v2/unit/domain/test_proposal.py (pending)

- `health.py` - HealthEvent value object
  - Fields: level, component, message, timestamp
  - Tests: tests_v2/unit/domain/test_health.py (pending)

- `config.py` - SystemConfig immutable configuration
  - Replaces legacy dict-based config
  - Full backward compatibility (to_dict/from_dict)
  - Tests: tests_v2/unit/domain/test_config.py (pending)

#### Domain Ports (`cgalpha_v2/domain/ports/`)
- `data_port.py` - MarketDataReader, BridgeWriter protocols
- `prediction_port.py` - Predictor, FeatureExtractor protocols
- `memory_port.py` - ActionLogger, StateStore protocols
- `llm_port.py` - LLMProvider protocol
- `config_port.py` - ConfigReader, ConfigWriter protocols

#### Configuration (`cgalpha_v2/config/`)
- `paths.py` - ProjectPaths value object (ADR-005)
  - Centralized path management
  - Eliminates hardcoded paths
  
- `settings.py` - Settings Pydantic model
  - Environment-based configuration
  - Type-safe settings

#### Shared (`cgalpha_v2/shared/`)
- `exceptions.py` - Domain exception hierarchy
  - CGAlphaError (base)
  - DomainError, InfrastructureError
  - ConfigurationError, ValidationError
  
- `types.py` - Type aliases
  - SignalId, TradeId, ProposalId
  - Symbol, Timeframe

#### Bootstrap
- `cgalpha_v2/bootstrap.py` - Composition root
  - Wires dependencies together
  - Currently thin, will expand

### Architecture Decisions
- ADR-006: Separate v2 codebase in parallel directory
- ADR-007: Use frozen dataclasses for all value objects

### Migration Status
- [x] Phase 2.1: Foundation
- [ ] Phase 2.2: Signal Detection
- [ ] Phase 2.3: Prediction (Oracle)
- [ ] Phase 2.4: Causal Analysis
- [ ] Phase 2.5: Code Evolution
- [ ] Phase 2.6: System Operations
- [ ] Phase 2.7: Interfaces

### Verification
- Mypy: Success (strict mode)
- Tests: 256 passed (legacy tests)
- Imports: Zero circular dependencies

---

## Legend

- `Added` - New features/classes
- `Changed` - Changes to existing features
- `Deprecated` - Features to be removed
- `Removed` - Features removed
- `Fixed` - Bug fixes
- `Security` - Security improvements
