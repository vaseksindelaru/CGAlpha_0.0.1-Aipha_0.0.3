"""
cgalpha.domain.ports — Interface contracts (Ports).

All ports are defined as Protocol classes (PEP 544), enabling structural
subtyping.  Adapters in the infrastructure layer implement these protocols
without needing to inherit from them explicitly.

Re-exports for convenience:
    from cgalpha_v2.domain.ports import MarketDataReader, Predictor, LLMProvider
"""

from __future__ import annotations

from cgalpha_v2.domain.ports.data_port import (
    MarketDataReader,
    BridgeWriter,
)
from cgalpha_v2.domain.ports.prediction_port import (
    Predictor,
    FeatureExtractor,
)
from cgalpha_v2.domain.ports.memory_port import (
    ActionLogger,
    StateStore,
)
from cgalpha_v2.domain.ports.llm_port import (
    LLMProvider,
)
from cgalpha_v2.domain.ports.config_port import (
    ConfigReader,
    ConfigWriter,
)

__all__ = [
    "MarketDataReader",
    "BridgeWriter",
    "Predictor",
    "FeatureExtractor",
    "ActionLogger",
    "StateStore",
    "LLMProvider",
    "ConfigReader",
    "ConfigWriter",
]
