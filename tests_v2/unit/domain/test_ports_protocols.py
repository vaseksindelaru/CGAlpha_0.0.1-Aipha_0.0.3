"""Unit tests for cgalpha_v2.domain.ports protocols."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from cgalpha_v2.domain.models import Prediction, TradeRecord
from cgalpha_v2.domain.ports import (
    ActionLogger,
    BridgeWriter,
    ConfigReader,
    ConfigWriter,
    FeatureExtractor,
    LLMProvider,
    MarketDataReader,
    Predictor,
    StateStore,
)


class DummyConfigReader:
    def get(self, key_path: str, default: Any = None) -> Any:
        _ = key_path
        return default

    def get_all(self) -> dict[str, Any]:
        return {"Trading": {"tp_factor": 2.0}}


class DummyConfigWriter:
    def set(self, key_path: str, value: Any) -> None:
        _ = key_path, value

    def rollback(self) -> bool:
        return True


class DummyMarketDataReader:
    def read_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        _ = symbol, timeframe, limit
        return []


class DummyBridgeWriter:
    def __init__(self) -> None:
        self._trades: list[TradeRecord] = []

    def append_trade(self, trade: TradeRecord) -> None:
        self._trades.append(trade)

    def read_trades(self, limit: int | None = None) -> list[TradeRecord]:
        if limit is None:
            return list(self._trades)
        return list(self._trades[-limit:])

    def count(self) -> int:
        return len(self._trades)


class DummyFeatureExtractor:
    def extract(self, candle: Any) -> dict[str, float]:
        _ = candle
        return {"body_ratio": 0.5}


class DummyPredictor:
    def predict(self, features: dict[str, float], signal_id: str) -> Prediction:
        _ = features
        return Prediction(
            signal_id=signal_id,
            passed=True,
            probability=0.8,
            threshold=0.7,
            model_id="dummy",
            features_used=1,
            created_at=datetime.now(timezone.utc),
        )

    def is_available(self) -> bool:
        return True


class IncompletePredictor:
    def predict(self, features: dict[str, float], signal_id: str) -> Prediction:
        _ = features
        return Prediction(
            signal_id=signal_id,
            passed=True,
            probability=0.8,
            threshold=0.7,
            model_id="dummy",
            features_used=1,
            created_at=datetime.now(timezone.utc),
        )


class DummyActionLogger:
    def __init__(self) -> None:
        self._history: list[dict[str, Any]] = []

    def log_action(
        self,
        agent: str,
        action_type: str,
        *,
        details: dict[str, Any] | None = None,
        proposal_id: str | None = None,
    ) -> None:
        self._history.append(
            {
                "agent": agent,
                "action_type": action_type,
                "details": details,
                "proposal_id": proposal_id,
            }
        )

    def get_history(
        self,
        limit: int | None = None,
        action_type: str | None = None,
    ) -> list[dict[str, Any]]:
        data = self._history
        if action_type is not None:
            data = [entry for entry in data if entry["action_type"] == action_type]
        if limit is None:
            return list(data)
        return list(data[-limit:])


class DummyStateStore:
    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    def get(self, key: str) -> dict[str, Any] | None:
        return self._store.get(key)

    def set(self, key: str, value: dict[str, Any]) -> None:
        self._store[key] = value

    def delete(self, key: str) -> bool:
        existed = key in self._store
        if existed:
            del self._store[key]
        return existed


class DummyLLMProvider:
    @property
    def name(self) -> str:
        return "dummy"

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        _ = prompt, system_prompt, temperature, max_tokens
        return "ok"

    def is_available(self) -> bool:
        return True


def test_protocol_runtime_checks_positive(sample_trade_record: TradeRecord) -> None:
    reader = DummyConfigReader()
    writer = DummyConfigWriter()
    market = DummyMarketDataReader()
    bridge = DummyBridgeWriter()
    extractor = DummyFeatureExtractor()
    predictor = DummyPredictor()
    logger = DummyActionLogger()
    store = DummyStateStore()
    llm = DummyLLMProvider()

    bridge.append_trade(sample_trade_record)
    logger.log_action("orchestrator", "CYCLE_COMPLETED", details={"ok": True})
    store.set("state", {"cycle": 1})

    assert isinstance(reader, ConfigReader)
    assert isinstance(writer, ConfigWriter)
    assert isinstance(market, MarketDataReader)
    assert isinstance(bridge, BridgeWriter)
    assert isinstance(extractor, FeatureExtractor)
    assert isinstance(predictor, Predictor)
    assert isinstance(logger, ActionLogger)
    assert isinstance(store, StateStore)
    assert isinstance(llm, LLMProvider)

    assert bridge.count() == 1
    assert store.get("state") == {"cycle": 1}
    assert llm.generate("hello") == "ok"


def test_protocol_runtime_checks_negative() -> None:
    assert not isinstance(IncompletePredictor(), Predictor)
