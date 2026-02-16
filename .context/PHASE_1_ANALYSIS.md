# CGAlpha Reconstruction — Phase 1: Analysis & Design

**Date:** 2026-02-16  
**Author:** Antigravity (with Vaclav)  
**Status:** DRAFT — for review before implementation begins  

---

## Table of Contents

1. [Component Map (Current State)](#1-component-map-current-state)
2. [Dependency Graph](#2-dependency-graph)
3. [Critical Pain Points](#3-critical-pain-points)
4. [Proposed Architecture](#4-proposed-architecture)
5. [Directory Structure Proposal](#5-directory-structure-proposal)
6. [Ubiquitous Language (Glossary)](#6-ubiquitous-language-glossary)
7. [Interface Contracts (Ports)](#7-interface-contracts-ports)
8. [Architecture Decision Records (ADRs)](#8-architecture-decision-records-adrs)
9. [Migration Strategy](#9-migration-strategy)

---

## 1. Component Map (Current State)

### 1.1 Physical Structure (As-Is)

```
CGAlpha_0.0.1-Aipha_0.0.3/
├── life_cycle.py                          # ENTRYPOINT: "Dual Heartbeat" main loop
├── aipha_config.json                      # Runtime configuration
├── pyproject.toml                         # Package definition (name="aipha", scripts: aipha/cgalpha → cli_v2)
│
├── core/                                  # LAYER: Orchestration + Infrastructure
│   ├── orchestrator_hardened.py            #   454 LOC - CentralOrchestratorHardened (signal handlers, cycle mgmt)
│   ├── trading_engine.py                  #   259 LOC - TradingEngine (signal pipeline + ATR sensor)
│   ├── config_manager.py                  #   134 LOC - ConfigManager (JSON-based config)
│   ├── context_sentinel.py                #   273 LOC - ContextSentinel (JSONL memory: actions, state, proposals)
│   ├── health_monitor.py                  #   344 LOC - HealthMonitor (event-based health tracking)
│   ├── change_evaluator.py                #   122 LOC - ProposalEvaluator (score proposals before applying)
│   ├── atomic_update_system.py            #   182 LOC - AtomicUpdateSystem (5-step: backup→diff→test→commit→rollback)
│   ├── execution_queue.py                 #   260 LOC - ExecutionQueue (thread-safe priority queue)
│   ├── quarantine_manager.py              #   331 LOC - QuarantineManager (blacklist failed parameters)
│   ├── performance_logger.py              #   294 LOC - PerformanceLogger (observability instrumentation)
│   ├── config_validators.py               #   ~300 LOC - Configuration validators
│   ├── exceptions.py                      #   ~300 LOC - Custom exception hierarchy
│   ├── memory_manager.py                  #   ~60 LOC  - Simple memory helper
│   ├── llm_assistant_v2.py                #   219 LOC - LLMAssistantV2 (modular LLM interface)
│   ├── llm_providers/                     #     Provider abstraction layer
│   │   ├── __init__.py                    #     Re-exports
│   │   ├── base.py                        #     LLMProvider ABC
│   │   ├── openai_provider.py             #     OpenAI implementation
│   │   └── rate_limiter.py                #     Rate limiting + retry
│   └── type_hints_generator.py            #   ~90 LOC  - Static analysis helper
│
├── trading_manager/                       # LAYER: Signal Detection ("Triple Coincidencia")
│   ├── building_blocks/
│   │   ├── detectors/
│   │   │   ├── accumulation_zone_detector.py  # AccumulationZoneDetector
│   │   │   ├── trend_detector.py              # TrendDetector (R²-quality)
│   │   │   └── key_candle_detector.py         # KeyCandleDetector (institutional absorption)
│   │   ├── labelers/
│   │   │   └── potential_capture_engine.py     # get_atr_labels (MFE/MAE trajectories)
│   │   └── signal_combiner.py                 # SignalCombiner (fuse detector outputs)
│   └── strategies/
│       └── (1 file)
│
├── oracle/                                # LAYER: ML Filtering
│   ├── building_blocks/
│   │   ├── features/
│   │   │   └── feature_engineer.py         # Feature extraction
│   │   └── oracles/
│   │       └── oracle_engine.py            # OracleEngine (RandomForest wrapper)
│   ├── strategies/
│   │   ├── train_oracle_multiyear.py       # Training script (multiyear, 83.33% acc)
│   │   ├── train_oracle_5m.py              # 5-min training
│   │   ├── validate_oracle_jan_2026.py     # Validation scripts
│   │   └── ... (9 files total)
│   └── models/                            # Serialized .joblib models
│
├── cgalpha/                               # LAYER: Intelligence (Causal Analysis + Auto-Modification)
│   ├── orchestrator.py                    #   54 LOC  - CGAlphaOrchestrator (thin bridge: Ghost→CodeCraft)
│   ├── ghost_architect/
│   │   ├── simple_causal_analyzer.py      # 1460 LOC - SimpleCausalAnalyzer ⚠️ GOD CLASS
│   │   └── templates/                     #   Jinja2 prompt templates
│   ├── codecraft/                         # "Code Craft Sage" auto-modification pipeline
│   │   ├── orchestrator.py                #   573 LOC - CodeCraftOrchestrator (4-phase pipeline)
│   │   ├── proposal_parser.py             #   398 LOC - ProposalParser (NL → TechnicalSpec)
│   │   ├── proposal_generator.py          #   367 LOC - ProposalGenerator (metrics → proposals)
│   │   ├── ast_modifier.py                #   497 LOC - ASTModifier (safe code modification)
│   │   ├── safety_validator.py            #   311 LOC - SafetyValidator (pre/post change validation)
│   │   ├── git_automator.py               #   521 LOC - GitAutomator (feature branches, conventional commits)
│   │   ├── test_generator.py              #   546 LOC - TestGenerator (generate + validate tests)
│   │   ├── technical_spec.py              #   ~200 LOC - TechnicalSpec dataclass
│   │   └── templates/                     #   Jinja2 test templates
│   ├── labs/
│   │   └── risk_barrier_lab.py            #   130 LOC - RiskBarrierLab (MFE/MAE analysis)
│   └── nexus/                             # "CGA_Nexus" - Resource & coordination layer
│       ├── ops.py                         #   245 LOC - CGAOps (resource semaphore + Redis queue)
│       ├── coordinator.py                 #   178 LOC - CGANexus (report aggregation + market regime)
│       ├── applicator.py                  #   102 LOC - ActionApplicator (apply config changes)
│       ├── redis_client.py                #   331 LOC - RedisClient (deterministic Redis wrapper)
│       └── task_buffer.py                 #   180 LOC - TaskBufferManager (SQLite fallback for Redis)
│
├── aiphalab/                              # LAYER: Interface (CLI)
│   ├── cli_v2.py                          #   342 LOC - Main CLI entrypoint (Click groups)
│   ├── dashboard.py                       #   ~250 LOC - Terminal dashboard
│   ├── formatters.py                      #   ~200 LOC - Output formatters
│   └── commands/                          # Modular CLI commands
│       ├── base.py, status.py, cycle.py,
│       ├── config.py, history.py, debug.py,
│       ├── codecraft.py, docs.py, librarian.py
│       └── __init__.py
│
├── data_processor/                        # LAYER: Data Ingestion
│   ├── acquire_data.py                    #   API data fetcher
│   └── data_system/                       #   Template-driven data system
│
├── data_postprocessor/                    # LAYER: Feedback Loop
│   ├── building_blocks/
│   │   └── (1 file)
│   └── strategies/
│       └── (1 file)
│
├── simulation/                            # Support: Synthetic data
│   └── market_generator.py
│
├── aipha_memory/                          # PERSISTENCE: 3-layer memory
│   ├── operational/                       #   Runtime state
│   ├── evolutionary/                      #   Bridge JSONL, causal reports
│   ├── config/                            #   Configuration snapshots
│   ├── testing/                           #   Test artifacts
│   └── temporary/                         #   Buffer DB, AST backups
│
├── tests/                                 # 18 test files + 3 subdirs
├── scripts/                               # 10 utility scripts
├── docs/                                  # 8 docs + archive + reference + guides
└── bible/                                 # 5 knowledge base files
```

### 1.2 Class/Responsibility Map

| Component | Class | Responsibility | LOC | Smell |
|---|---|---|---|---|
| `core/orchestrator_hardened` | `CentralOrchestratorHardened` | Signal handling, cycle management, metric collection, proposal verification | 454 | **Too many responsibilities** |
| `cgalpha/ghost_architect/simple_causal_analyzer` | `SimpleCausalAnalyzer` | Log reading, snapshot extraction, pattern detection, hypothesis building, LLM inference, prompt building, report generation, readiness gates | **1460** | **GOD CLASS — critical** |
| `cgalpha/codecraft/orchestrator` | `CodeCraftOrchestrator` | Pipeline orchestration for all 4 phases of code modification | 573 | Acceptable complexity for orchestrator |
| `core/trading_engine` | `TradingEngine` | Data loading, signal detection, ATR labeling, bridge writing | 259 | Mixes data access and domain logic |
| `core/health_monitor` | `HealthMonitor` | Event processing, broadcasting, persistence, statistics | 344 | Good — event-driven design |
| `cgalpha/codecraft/git_automator` | `GitAutomator` | Branch creation, commits, merge safety | 521 | Well-scoped |
| `cgalpha/codecraft/test_generator` | `TestGenerator` | Generate tests + run validation + coverage | 546 | Two responsibilities: generation + execution |

---

## 2. Dependency Graph

### 2.1 Import Flow (Top → Bottom)

```
                    life_cycle.py
                   /      |      \
                  v       v       v
    CentralOrchestratorH  TradingEngine  CGAOps
         |                    |              |
         v                    v              v
    ExecutionQueue       ConfigManager   RedisClient
    HealthMonitor        Detectors(3)    TaskBufferManager
    QuarantineManager    SignalCombiner  
    ContextSentinel      PCEngine       
    PerformanceLogger    OracleEngine   
    ChangeEvaluator      FeatureEngineer
    AtomicUpdateSystem
    LLMAssistantV2
         |
         v
    LLMProviders (base, openai, rate_limiter)
```

```
              CLI (cli_v2.py)
               /    |     \
              v     v      v
    CGAlphaOrchestrator   Command Groups (9 modules)
         /          \
        v            v
SimpleCausalAnalyzer  ProposalGenerator
                      CodeCraftOrchestrator
                       /   |    |     \
                      v    v    v      v
               Parser  AST  Tests  Git
                        |
                        v
                  TechnicalSpec (shared data model)
```

### 2.2 Critical Cross-Cutting Dependencies

| Dependency | Used By | Problem |
|---|---|---|
| `ConfigManager` | TradingEngine, Orchestrator, CLI | Singleton-like with hardcoded path |
| `ContextSentinel` | AtomicUpdateSystem, ChangeEvaluator, ExecutionQueue, CLI | Implicit coupling through duck-typing |
| `aipha_memory/` paths | 10+ modules | Hardcoded relative paths everywhere |
| `RedisClient` | CGAOps, CGANexus, ProposalParser | Optional dependency with `try/except ImportError` |
| `LLMAssistantV2` | SimpleCausalAnalyzer, ProposalParser | Global singleton pattern |

---

## 3. Critical Pain Points

### 3.1 🔴 P1: GOD CLASS — `SimpleCausalAnalyzer` (1460 LOC)

**Severity:** Critical  
**Impact:** Untestable, unmaintainable, impossible to evolve  

This single class handles **7 distinct responsibilities:**
1. **Log I/O** — reading JSONL files, resolving paths
2. **Order Book Feature Matching** — loading/matching microstructure data  
3. **Snapshot Extraction** — parsing raw logs into structured snapshots
4. **Pattern Detection** — 5 different pattern detectors (fakeout, news, microstructure, MFE/MAE, win_rate)
5. **Hypothesis Building** — causal inference logic (heuristic)
6. **LLM Integration** — prompt building, API calls, response parsing
7. **Report Generation** — saving analysis reports, readiness gates

**Recommendation:** Decompose into ≥5 focused classes behind a `CausalAnalysisPipeline` facade.

### 3.2 🔴 P2: Identity Crisis — `aipha` vs `cgalpha`

**Severity:** High  
**Impact:** Confusing onboarding, namespace pollution, naming collisions  

Evidence:
- `pyproject.toml` declares `name = "aipha"` but the system is conceptually "CGAlpha"
- CLI entry points: both `aipha` and `cgalpha` map to `aiphalab.cli_v2:cli`
- Module `aiphalab/` wrapping `cgalpha/` orchestrator
- Memory directory: `aipha_memory/` but managed by CGAlpha components
- Config file: `aipha_config.json` at root **and** `memory/aipha_config.json` via ConfigManager

**Recommendation:** Unify under a single namespace `cgalpha`. Keep `aipha` as a deprecated alias only.

### 3.3 🟠 P3: Hardcoded Paths Everywhere

**Severity:** High  
**Impact:** Broken portability, test setup friction  

Examples found:
- `ConfigManager(config_path=Path("memory/aipha_config.json"))` — default arg
- `TaskBufferManager(db_path="aipha_memory/temporary/task_buffer.db")` — default arg
- `FileSystemLoader("memory/aipha_lifecycle.log")` — in life_cycle.py
- `PerformanceLogger(memory_path="memory")` — default arg
- `HealthMonitor(memory_path="memory")` — default arg
- `SimpleCausalAnalyzer` hardcodes `aipha_memory/evolutionary/` paths

**Recommendation:** Inject a `ProjectPaths` value object from the composition root.

### 3.4 🟠 P4: No Interfaces (Ports)

**Severity:** High  
**Impact:** Cannot test layers in isolation, tight coupling  

Currently, all dependencies are concrete class references:
- `CentralOrchestratorHardened` directly imports `TradingEngine`, `ContextSentinel`, etc.
- `TradingEngine` directly imports detectors and `ConfigManager`
- `SimpleCausalAnalyzer` directly invokes `LLMAssistantV2`

**Recommendation:** Define `Protocol` interfaces (PEP 544) for every cross-layer boundary.

### 3.5 🟠 P5: Mixed Language in Code

**Severity:** Medium  
**Impact:** Cognitive load, grep confusion  

Examples:
- Spanish: `"Ejecutando tests"`, `"Backup creado"`, `"Esperando..."`, `class Evaluador`
- English: `class TradingEngine`, `def run_cycle`, `"Tests passed"`
- Docstrings: Mixed within the same file

**Recommendation:** Standardize to English for all code, logs, and docstrings. Spanish OK for user-facing CLI messages if desired.

### 3.6 🟡 P6: Duplicate/Redundant Names

| Concept | Current Names | Proposed Canonical Name |
|---|---|---|
| "The main orchestrator" | `CentralOrchestratorHardened`, `CGAlphaOrchestrator`, `CodeCraftOrchestrator` | `SystemOrchestrator`, `AnalysisOrchestrator`, `CodeModificationPipeline` |
| "The coordination layer" | `CGANexus`, `CGAOps`, `coordinator.py`, `nexus/` | `ResourceSupervisor`, `LabCoordinator` |
| "Apply a change" | `ActionApplicator`, `AtomicUpdateSystem`, `ASTModifier` | Clear distinct roles: `ConfigApplicator`, `AtomicUpdateProtocol`, `CodeModifier` |
| "Analyze performance" | `analyze_performance()` on 3 classes | Differentiate: `analyze_trade_logs()`, `analyze_metrics()`, `generate_improvement_proposals()` |

### 3.7 🟡 P7: Test Files at Root Level

**Severity:** Low  
**Impact:** Cluttered root directory  

Files at root that should be in `tests/`:
- `test_buffer_concurrency.py`
- `test_concurrency_fixed.py`
- `test_redis_recovery.py`
- `test_redis_resilience.py`
- `detectors_corrected.py`

### 3.8 🟡 P8: Global Singletons

**Severity:** Medium  
**Impact:** Hidden state, test contamination  

Found singleton patterns in:
- `get_health_monitor()` 
- `get_performance_logger()`
- `get_llm_assistant()`
- `_oracle_cache` in cli_v2.py

**Recommendation:** Replace with explicit dependency injection from the composition root.

---

## 4. Proposed Architecture

### 4.1 Bounded Contexts (DDD)

I identify **5 Bounded Contexts** in the domain:

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  1. SIGNAL DETECTION CONTEXT                                         │
│     "Detecting actionable trading signals from market data"          │
│     Entities: Signal, Candle, AccumulationZone, Trend                │
│     Services: TripleCoincidenceDetector, SignalCombiner              │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  2. PREDICTION CONTEXT (Oracle)                                      │
│     "Filtering signals through ML probability models"                │
│     Entities: Prediction, Feature, Model                            │
│     Services: OracleEngine, FeatureExtractor                        │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  3. CAUSAL ANALYSIS CONTEXT (Ghost Architect)                        │
│     "Understanding WHY trades succeed or fail"                       │
│     Entities: TradeSnapshot, Pattern, Hypothesis, Insight            │
│     Services: SnapshotExtractor, PatternDetector,                   │
│               HypothesisBuilder, CausalInferenceEngine               │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  4. CODE EVOLUTION CONTEXT (Code Craft Sage)                         │
│     "Automatically modifying system parameters and code"             │
│     Entities: Proposal, TechnicalSpec, ChangeResult                 │
│     Services: ProposalParser, CodeModifier, TestRunner,             │
│               GitAutomator, SafetyValidator                          │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  5. SYSTEM OPERATIONS CONTEXT                                        │
│     "Keeping the system running safely and observably"               │
│     Entities: HealthEvent, ResourceSnapshot, QuarantinedParam       │
│     Services: HealthMonitor, ResourceSupervisor, ConfigManager,     │
│               ExecutionQueue, AtomicUpdateProtocol                   │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 4.2 Layered Architecture (Clean Architecture)

```
┌─────────────────────────────────────────────────────────────────┐
│                         INTERFACE LAYER                          │
│   CLI Commands │ Dashboard │ REST API (future)                  │
│   ─ No business logic, only presentation and input parsing      │
│   ─ Pattern: Adapter (inbound)                                  │
├─────────────────────────────────────────────────────────────────┤
│                       APPLICATION LAYER                          │
│   SystemOrchestrator │ AnalysisOrchestrator │ EvolutionPipeline │
│   ─ Use Cases / Application Services                            │
│   ─ Coordinates domain objects, enforces workflow               │
│   ─ Pattern: Facade, Mediator                                   │
├─────────────────────────────────────────────────────────────────┤
│                         DOMAIN LAYER                             │
│   Entities │ Value Objects │ Domain Services │ Domain Events     │
│   ─ ZERO external dependencies                                  │
│   ─ Pure Python, fully testable                                 │
│   ─ Pattern: Entity, Value Object, Domain Service, Aggregate    │
├─────────────────────────────────────────────────────────────────┤
│                      INFRASTRUCTURE LAYER                        │
│   Redis │ SQLite │ JSONL │ DuckDB │ Git │ LLM Providers │ FS   │
│   ─ Implements Port interfaces defined in Domain                │
│   ─ Pattern: Adapter (outbound), Repository, Gateway            │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 Key Design Patterns Applied

| Pattern | Where | Why |
|---|---|---|
| **Repository** | Memory (JSONL, SQLite), Config | Abstract storage from domain |
| **Strategy** | Detectors, Oracle models, LLM providers | Swap implementations |
| **Pipeline** | CodeCraft (Parse→Modify→Test→Commit) | Sequential processing |
| **Observer** | HealthMonitor events | Decouple monitoring from components |
| **Facade** | `CausalAnalysisPipeline` (replaces God Class) | Simplify complex subsystem |
| **Factory** | ConfigManager, LLM providers | Controlled instantiation |
| **Value Object** | TechnicalSpec, ResourceSnapshot, Insight | Immutable domain data |
| **Ports & Adapters** | All external I/O | Testability, flexibility |

---

## 5. Directory Structure Proposal

```
cgalpha/                                    # Single unified package
├── __init__.py                             # Package metadata, version
├── __main__.py                             # python -m cgalpha
│
├── domain/                                 # 🧠 DOMAIN LAYER (zero dependencies)
│   ├── __init__.py
│   ├── models/                             # Entities and Value Objects
│   │   ├── __init__.py
│   │   ├── signal.py                       # Signal, Candle, AccumulationZone, Trend
│   │   ├── prediction.py                   # Prediction, Feature, ModelMetadata
│   │   ├── trade.py                        # TradeSnapshot, TradeOutcome
│   │   ├── analysis.py                     # Pattern, Hypothesis, Insight, CausalReport
│   │   ├── proposal.py                     # Proposal, TechnicalSpec, ChangeResult
│   │   ├── health.py                       # HealthEvent, HealthLevel, ResourceSnapshot
│   │   └── config.py                       # TradingConfig, OracleConfig (typed)
│   ├── ports/                              # Interfaces (Protocols / ABCs)
│   │   ├── __init__.py
│   │   ├── data_port.py                    # MarketDataReader, BridgeWriter
│   │   ├── memory_port.py                  # ActionLogger, StateStore, ProposalStore
│   │   ├── prediction_port.py              # Predictor, FeatureExtractor
│   │   ├── notification_port.py            # EventEmitter, EventSubscriber
│   │   ├── llm_port.py                     # LLMProvider
│   │   ├── vcs_port.py                     # VersionControlSystem
│   │   └── config_port.py                  # ConfigReader, ConfigWriter
│   ├── services/                           # Domain Services (pure logic)
│   │   ├── __init__.py
│   │   ├── signal_detection.py             # TripleCoincidenceDetector
│   │   ├── signal_combining.py             # SignalCombiner
│   │   ├── pattern_detection.py            # PatternDetector (5 strategies)
│   │   ├── hypothesis_builder.py           # HypothesisBuilder
│   │   ├── proposal_evaluator.py           # ProposalEvaluator (scoring logic)
│   │   ├── risk_analysis.py                # RiskBarrierAnalyzer
│   │   └── atr_labeler.py                  # ATRLabeler (MFE/MAE trajectory analysis)
│   └── exceptions.py                       # Domain exception hierarchy
│
├── application/                            # 🔧 APPLICATION LAYER (use cases)
│   ├── __init__.py
│   ├── trading_cycle.py                    # RunTradingCycleUseCase
│   ├── causal_analysis.py                  # RunCausalAnalysisUseCase
│   ├── code_evolution.py                   # ExecuteCodeEvolutionUseCase
│   ├── system_health.py                    # MonitorSystemHealthUseCase
│   └── orchestrator.py                     # SystemOrchestrator (dual heartbeat)
│
├── infrastructure/                         # 🔌 INFRASTRUCTURE LAYER (adapters)
│   ├── __init__.py
│   ├── persistence/                        # Storage adapters
│   │   ├── __init__.py
│   │   ├── jsonl_repository.py             # JSONL append-only log adapter
│   │   ├── json_state_store.py             # JSON mutable state adapter
│   │   ├── sqlite_buffer.py                # SQLite task buffer adapter
│   │   ├── duckdb_reader.py                # DuckDB market data reader
│   │   └── config_file_manager.py          # Config JSON reader/writer
│   ├── cache/                              # Caching adapters
│   │   ├── __init__.py
│   │   └── redis_adapter.py               # Redis cache/queue/pubsub adapter
│   ├── ml/                                 # ML model adapters
│   │   ├── __init__.py
│   │   ├── sklearn_oracle.py               # Scikit-learn RandomForest adapter
│   │   └── feature_pipeline.py             # Feature extraction adapter
│   ├── llm/                                # LLM provider adapters
│   │   ├── __init__.py
│   │   ├── openai_adapter.py               # OpenAI API adapter
│   │   ├── local_llm_adapter.py            # Local LLM adapter (Ollama etc)
│   │   └── rate_limiter.py                 # Rate limiting utility
│   ├── vcs/                                # Version control adapters
│   │   ├── __init__.py
│   │   └── git_adapter.py                  # GitPython adapter
│   ├── code_modification/                  # Code manipulation adapters
│   │   ├── __init__.py
│   │   ├── ast_modifier.py                 # AST-based code modification
│   │   ├── safety_validator.py             # Pre/post validation
│   │   └── test_runner.py                  # pytest execution adapter
│   └── system/                             # OS/system adapters
│       ├── __init__.py
│       └── resource_monitor.py             # psutil-based resource monitoring
│
├── interface/                              # 🖥️ INTERFACE LAYER (inbound adapters)
│   ├── __init__.py
│   ├── cli/                                # CLI commands
│   │   ├── __init__.py
│   │   ├── app.py                          # Click application root
│   │   ├── commands/                       # Command modules
│   │   │   ├── __init__.py
│   │   │   ├── status.py
│   │   │   ├── cycle.py
│   │   │   ├── config.py
│   │   │   ├── history.py
│   │   │   ├── debug.py
│   │   │   ├── codecraft.py
│   │   │   ├── oracle.py
│   │   │   └── analyze.py                  # Ghost Architect CLI
│   │   ├── formatters.py                   # Output formatting
│   │   └── dashboard.py                    # Terminal dashboard
│   └── api/                                # Future: REST API
│       └── __init__.py
│
├── config/                                 # ⚙️ CONFIGURATION
│   ├── __init__.py
│   ├── settings.py                         # Pydantic settings (env vars, defaults)
│   ├── paths.py                            # ProjectPaths value object
│   └── defaults.py                         # Default parameter values
│
└── bootstrap.py                            # 🚀 COMPOSITION ROOT
                                            #    Wires all dependencies together
```

### Supporting directories (outside `cgalpha/`):

```
tests/                                      # Mirror of source structure
├── unit/
│   ├── domain/
│   │   ├── test_signal_detection.py
│   │   ├── test_pattern_detection.py
│   │   └── ...
│   ├── application/
│   │   └── test_trading_cycle.py
│   └── infrastructure/
│       └── test_jsonl_repository.py
├── integration/
│   ├── test_full_cycle.py
│   ├── test_causal_analysis_pipeline.py
│   └── ...
├── conftest.py                             # Shared fixtures
└── factories.py                            # Test data factories

data/                                       # Runtime data (gitignored)
├── memory/
│   ├── operational/
│   ├── evolutionary/
│   └── temporary/
├── config/
├── models/
└── logs/

docs/
├── adr/                                    # Architecture Decision Records
│   ├── 001-unified-namespace.md
│   ├── 002-clean-architecture.md
│   └── ...
├── guides/
├── reference/
└── archive/

scripts/
├── train_oracle.py
├── validate_oracle.py
└── populate_memory.py
```

---

## 6. Ubiquitous Language (Glossary)

This glossary defines the **canonical terms** for the CGAlpha domain. All code, docs, and conversations should use these terms consistently.

### 6.1 Core Concepts

| Term | Definition | Current aliases (to unify) |
|---|---|---|
| **Signal** | A detected trading opportunity from market data | "señal", "alert" |
| **Triple Coincidence** | The requirement that 3 independent detectors agree | "triple coincidencia" |
| **Accumulation Zone** | A price range where institutional buyers accumulate | "rango lateral", "zone" |
| **Key Candle** | A candle showing institutional absorption characteristics | "vela clave", "candle absorción" |
| **Trend Quality** | A metric (R²) measuring how clean a price trend is | "calidad de tendencia" |
| **ATR Label** | Ordinal classification of trade outcome in ATR multiples | "label_ordinal", "R-multiple" |
| **MFE** | Maximum Favorable Excursion — best unrealized profit | — |
| **MAE** | Maximum Adverse Excursion — worst unrealized drawdown | — |
| **Trajectory** | The complete price path of a trade (MFE + MAE over time) | "trayectoria" |

### 6.2 Intelligence Layer

| Term | Definition | Current aliases |
|---|---|---|
| **Trade Snapshot** | A structured summary of one trade with all contextual data | "snapshot", "registro" |
| **Pattern** | A recurring characteristic detected across multiple trade snapshots | "patrón" |
| **Hypothesis** | A causal explanation for why a pattern exists | "hipótesis causal" |
| **Insight** | An actionable recommendation derived from hypotheses | "accionable", "propuesta" |
| **Causal Inference** | The process of determining cause-effect relationships | "inferencia causal" |
| **Readiness Gate** | A precondition that must pass before advancing to next phase | "gate" |

### 6.3 Evolution Layer

| Term | Definition | Current aliases |
|---|---|---|
| **Proposal** | A suggested change to system parameters or code | "propuesta", "changeset" |
| **Technical Spec** | The machine-parseable specification of a proposal | "TechnicalSpec", "spec" |
| **Change Pipeline** | The 4-phase process: Parse → Modify → Test → Commit | "pipeline", "CodeCraft" |
| **Atomic Update** | A change applied with rollback guarantee | "protocolo atómico" |
| **Quarantined Parameter** | A parameter value known to cause failures | "blacklisted", "en cuarentena" |

### 6.4 Operational Layer

| Term | Definition | Current aliases |
|---|---|---|
| **Dual Heartbeat** | The two-speed main loop: Fast (trading) + Slow (evolution) | "lifecycle", "bucle dual" |
| **Fast Loop** | The trading cycle that runs every iteration | "trading cycle" |
| **Slow Loop** | The evolutionary cycle that runs when resources allow | "evolution cycle" |
| **Resource Semaphore** | Green/Yellow/Red status based on CPU/RAM | "semáforo", "state" |
| **Bridge** | The JSONL file connecting trading outcomes to causal analysis | "puente", "evolutionary bridge" |
| **Health Event** | A significant system event (failure, recovery, degradation) | "alerta", "evento" |

---

## 7. Interface Contracts (Ports)

### 7.1 Core Port Definitions (Python Protocols)

```python
# domain/ports/data_port.py
from typing import Protocol, Optional
import pandas as pd

class MarketDataReader(Protocol):
    """Port for reading market data from any source."""
    def read_ohlcv(self, symbol: str, timeframe: str) -> pd.DataFrame: ...

class BridgeWriter(Protocol):
    """Port for writing trade outcomes to the evolutionary bridge."""
    def append_trade_outcome(self, outcome: "TradeOutcome") -> None: ...
    def read_trade_outcomes(self, limit: Optional[int] = None) -> list["TradeOutcome"]: ...


# domain/ports/prediction_port.py
class Predictor(Protocol):
    """Port for ML prediction filtering."""
    def predict(self, features: dict[str, float]) -> "Prediction": ...
    def is_available(self) -> bool: ...

class FeatureExtractor(Protocol):
    """Port for extracting features from candle data."""
    def extract(self, candle: "Candle") -> dict[str, float]: ...


# domain/ports/memory_port.py
class ActionLogger(Protocol):
    """Port for append-only action logging."""
    def log_action(self, action: "Action") -> None: ...
    def get_history(self, limit: Optional[int] = None) -> list["Action"]: ...

class StateStore(Protocol):
    """Port for mutable state persistence."""
    def get(self, key: str) -> Optional[dict]: ...
    def set(self, key: str, value: dict) -> None: ...


# domain/ports/llm_port.py
class LLMProvider(Protocol):
    """Port for LLM text generation."""
    def generate(self, prompt: str, temperature: float = 0.7) -> str: ...
    def is_available(self) -> bool: ...


# domain/ports/config_port.py
class ConfigReader(Protocol):
    """Port for reading typed configuration."""
    def get(self, key_path: str, default: Any = None) -> Any: ...
    def get_all(self) -> dict: ...

class ConfigWriter(Protocol):
    """Port for writing configuration with backup."""
    def set(self, key_path: str, value: Any) -> None: ...
    def rollback(self) -> bool: ...
```

---

## 8. Architecture Decision Records (ADRs)

### ADR-001: Unified Namespace Under `cgalpha`

**Status:** Proposed  
**Context:** The current codebase has fragmented namespaces: `core/`, `aiphalab/`, `trading_manager/`, `oracle/`, `data_processor/`, `data_postprocessor/`, `simulation/`, and `cgalpha/`. This creates confusion about package boundaries and makes `import` statements inconsistent.  
**Decision:** Consolidate all source code under a single top-level package `cgalpha/`.  
**Consequences:**  
- ✅ Single `import cgalpha.domain.models.signal` convention  
- ✅ Clearer package boundary for distribution  
- ✅ Eliminates `sys.path.insert(0, ...)` hacks in `life_cycle.py`  
- ⚠️ Requires updating all imports project-wide  
- ⚠️ Keep `aipha` as deprecated CLI alias for backward compat  

### ADR-002: Clean Architecture with Ports & Adapters

**Status:** Proposed  
**Context:** Cross-layer coupling prevents isolated testing. The trading engine directly instantiates detectors, the analyzer directly calls the LLM, the orchestrator directly accesses file paths.  
**Decision:** Apply Clean Architecture with explicit Port interfaces (Python `Protocol`) at every layer boundary.  
**Consequences:**  
- ✅ Each layer testable in complete isolation  
- ✅ Infrastructure swappable (Redis ↔ in-memory, OpenAI ↔ Ollama)  
- ✅ Domain logic has zero external dependencies  
- ⚠️ More files (ports directory)  
- ⚠️ Composition root required (`bootstrap.py`)  

### ADR-003: Decompose SimpleCausalAnalyzer into Pipeline

**Status:** Proposed  
**Context:** The 1460-LOC `SimpleCausalAnalyzer` violates SRP with 7 responsibilities.  
**Decision:** Decompose into focused components behind a `CausalAnalysisPipeline` facade:  
1. `TradeLogReader` — reads and parses JSONL logs  
2. `SnapshotExtractor` — extracts structured snapshots from raw records  
3. `PatternDetector` — detects patterns (Strategy pattern for 5 detectors)  
4. `HypothesisBuilder` — builds causal hypotheses from patterns  
5. `CausalInferenceEngine` — LLM-powered inference with heuristic fallback  
6. `AnalysisReporter` — generates and saves reports  
**Consequences:**  
- ✅ Each component independently testable  
- ✅ New pattern detectors can be added without touching existing code (Open/Closed)  
- ✅ LLM integration isolated and mockable  
- ⚠️ Requires careful data flow design between components  

### ADR-004: Dependency Injection via Composition Root

**Status:** Proposed  
**Context:** Current system uses 4+ global singletons (`get_health_monitor()`, `get_llm_assistant()`, etc.) which pollute tests and hide dependencies.  
**Decision:** Replace all singletons with explicit constructor injection. A single `bootstrap.py` file wires everything together.  
**Consequences:**  
- ✅ All dependencies visible in constructor signatures  
- ✅ Tests can inject mocks trivially  
- ✅ No global state  
- ⚠️ Constructor parameter lists may grow — mitigate with builder pattern  

### ADR-005: ProjectPaths Value Object

**Status:** Proposed  
**Context:** 10+ modules contain hardcoded relative paths to `memory/`, `aipha_memory/`, `aipha_config.json`, etc.  
**Decision:** Create a single `ProjectPaths` value object that calculates all paths relative to a configurable root.  
**Consequences:**  
- ✅ All paths centralized, portable, testable  
- ✅ Tests can point to temp directories trivially  
- ✅ Environment-specific path overrides possible  

---

## 9. Migration Strategy

### 9.1 Principles

1. **Always Working** — At every step, `pytest` passes and the CLI remains functional
2. **One Context at a Time** — Migrate one Bounded Context fully before starting the next
3. **Test-First Bridges** — Write acceptance tests that pass on both old and new implementations
4. **Git Atomicity** — Each migration step is one commit with clear message

### 9.2 Proposed Order

```
Phase 2.1: Foundation
  ├── Create cgalpha/domain/models/ (pure data models)
  ├── Create cgalpha/domain/ports/ (Protocol interfaces)
  ├── Create cgalpha/config/ (ProjectPaths, Settings)
  ├── Create cgalpha/bootstrap.py (composition root, initially thin)
  └── All existing tests still pass

Phase 2.2: Signal Detection Context
  ├── Move detectors into cgalpha/domain/services/
  ├── Move labelers into cgalpha/domain/services/
  ├── Create signal models (Signal, Candle VOs)
  ├── Create MarketDataReader port + DuckDB adapter
  └── Write unit tests for each detector in isolation

Phase 2.3: Prediction Context (Oracle)
  ├── Create Predictor port + sklearn adapter
  ├── Move feature engineering behind FeatureExtractor port
  ├── Create model loading infrastructure
  └── Write property-based tests for feature extraction

Phase 2.4: Causal Analysis Context (Ghost Architect) ⭐ Critical
  ├── Decompose SimpleCausalAnalyzer (ADR-003)
  ├── Create analysis pipeline with 6 focused classes
  ├── Create LLMProvider port + OpenAI adapter
  ├── Write acceptance tests for full analysis flow
  └── Verify readiness gates still work identically

Phase 2.5: Code Evolution Context (CodeCraft)
  ├── Already well-structured — mostly reorganize
  ├── Move TechnicalSpec to domain/models/
  ├── Create VCS port + Git adapter
  ├── Move test generation behind adapter
  └── Write integration tests for full pipeline

Phase 2.6: System Operations Context
  ├── Move HealthMonitor, QuarantineManager, etc.
  ├── Move ConfigManager behind port
  ├── Create ResourceMonitor adapter (psutil)
  └── Wire everything through bootstrap.py

Phase 2.7: Interface Layer (CLI)
  ├── Restructure CLI under cgalpha/interface/cli/
  ├── Update all CLI commands to use new orchestrator
  ├── Add backward-compatible aliases
  └── Final integration tests

Phase 3: Validation & Cleanup
  ├── Run full test suite
  ├── Verify CLI commands with integration tests
  ├── Remove old directories
  ├── Update all documentation
  └── Final commit: "v0.2.0 — Reconstructed Architecture"
```

### 9.3 Functional Parity Checklist

Before declaring Phase 3 complete, ALL of these must work identically:

- [ ] `cgalpha status` — shows system health
- [ ] `cgalpha cycle run` — executes improvement cycle
- [ ] `cgalpha oracle test-model` — validates Oracle
- [ ] `cgalpha auto-analyze` — runs Ghost Architect analysis
- [ ] `cgalpha codecraft execute` — runs auto-modification pipeline
- [ ] `python life_cycle.py` — runs dual heartbeat
- [ ] All existing JSONL files are readable
- [ ] All readiness gates produce same results
- [ ] Oracle predictions match (same model, same features, same thresholds)

---

## Next Steps

**Review this document and confirm:**

1. ✅ Does the Bounded Context decomposition feel right?
2. ✅ Does the proposed directory structure make sense?
3. ✅ Are the Ubiquitous Language terms correct?
4. ✅ Is the migration order acceptable?
5. ❓ Any additional pain points or priorities I missed?

Once confirmed, I'll begin **Phase 2.1: Foundation** — creating the domain models, port interfaces, and composition root.
