# CGAlpha v2 - Phase 2.2: Signal Detection

## Context

You are the ACTOR in an Actor-Critic workflow. Your role is to implement code based on specifications from the CRITIC.

**Current Status:** Phase 2.1 (Foundation) is COMPLETE. Phase 2.2 (Signal Detection) is PENDING.

## Task Overview

Migrate the Signal Detection bounded context from legacy code to `cgalpha_v2/`. This includes:
1. AccumulationZoneDetector
2. TrendDetector
3. KeyCandleDetector
4. SignalCombiner
5. ATRLabeler (MFE/MAE trajectories)

## Source Files (Legacy - DO NOT MODIFY)

```
trading_manager/building_blocks/
├── detectors/
│   ├── accumulation_zone_detector.py
│   ├── trend_detector.py
│   └── key_candle_detector.py
├── labelers/
│   └── potential_capture_engine.py
└── signal_combiner.py
```

## Target Files (Create in cgalpha_v2/)

```
cgalpha_v2/
├── domain/
│   └── services/
│       ├── __init__.py
│       ├── accumulation_zone_detector.py
│       ├── trend_detector.py
│       ├── key_candle_detector.py
│       ├── signal_combiner.py
│       └── atr_labeler.py
└── infrastructure/
    └── data/
        ├── __init__.py
        └── duckdb_reader.py (adapter for MarketDataReader port)
```

## Implementation Rules

1. **Pure Domain Logic**: Services in `domain/services/` must have ZERO external dependencies
2. **Use Ports**: Data access must go through ports defined in `domain/ports/`
3. **Immutable Models**: Use the models from `domain/models/` (Signal, Candle, Trend)
4. **Type Hints**: All functions must have complete type hints
5. **Tests First**: Write tests in `tests_v2/unit/domain/` before implementing

## Step-by-Step Instructions

### Step 1: Create domain/services/__init__.py

```python
"""Signal Detection domain services."""
from .accumulation_zone_detector import AccumulationZoneDetector
from .trend_detector import TrendDetector
from .key_candle_detector import KeyCandleDetector
from .signal_combiner import SignalCombiner
from .atr_labeler import ATRLabeler

__all__ = [
    "AccumulationZoneDetector",
    "TrendDetector",
    "KeyCandleDetector",
    "SignalCombiner",
    "ATRLabeler",
]
```

### Step 2: Implement AccumulationZoneDetector

Read `trading_manager/building_blocks/detectors/accumulation_zone_detector.py` and:
1. Extract the core detection logic
2. Create a pure function that takes Candle list and returns zones
3. Remove any pandas/external dependencies (use list comprehensions)
4. Return domain model objects (AccumulationZone if exists, or dict)

### Step 3: Implement TrendDetector

Read `trading_manager/building_blocks/detectors/trend_detector.py` and:
1. Extract R² calculation logic
2. Create pure function for trend quality measurement
3. Return Trend domain model

### Step 4: Implement KeyCandleDetector

Read `trading_manager/building_blocks/detectors/key_candle_detector.py` and:
1. Extract institutional absorption detection
2. Create pure function
3. Return list of detected key candles

### Step 5: Implement SignalCombiner

Read `trading_manager/building_blocks/signal_combiner.py` and:
1. Extract triple coincidence logic
2. Create pure function that combines detector outputs
3. Return Signal domain model

### Step 6: Implement ATRLabeler

Read `trading_manager/building_blocks/labelers/potential_capture_engine.py` and:
1. Extract MFE/MAE trajectory calculation
2. Create pure function for ordinal labeling
3. Return TradeRecord with trajectory data

## Verification

After each implementation:
```bash
# Run mypy strict
mypy cgalpha_v2/domain/services/ --strict

# Run tests
pytest tests_v2/unit/domain/test_<service>.py -v
```

## Report Format

After completing each file, report:

```
## Implementation Complete

**File:** cgalpha_v2/domain/services/<name>.py
**Lines:** X
**Tests:** tests_v2/unit/domain/test_<name>.py (Y tests)
**Dependencies:** None (domain layer)
**Mypy:** ✅ Pass
**Tests:** ✅ Pass

### Summary
<Brief description of what was implemented>

### Key Changes from Legacy
- <Change 1>
- <Change 2>

### Next Step
<What to implement next>
```

## Questions?

If you encounter ambiguity:
1. Check `.context/decisions.jsonl` for architectural decisions
2. Check `.context/migration_status.json` for current status
3. Ask the CRITIC for clarification before proceeding

---

**Begin with Step 1: Create the __init__.py file**
