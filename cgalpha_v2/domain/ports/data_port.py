"""
cgalpha.domain.ports.data_port — Ports for market data and trade bridge I/O.

These ports abstract HOW market data is read and WHERE trade outcomes are
persisted.  The domain never knows whether data comes from DuckDB, CSV,
or an exchange API.

Implementations live in cgalpha.infrastructure.persistence.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Protocol, runtime_checkable

if TYPE_CHECKING:
    import pandas as pd
    from cgalpha_v2.domain.models.trade import TradeRecord


@runtime_checkable
class MarketDataReader(Protocol):
    """
    Port for reading OHLCV market data.

    Implementations may read from DuckDB, CSV files, exchange APIs,
    or in-memory fixtures for testing.
    """

    def read_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        limit: Optional[int] = None,
    ) -> "pd.DataFrame":
        """
        Read OHLCV candle data for a symbol and timeframe.

        Args:
            symbol:    Trading pair (e.g. 'BTCUSDT').
            timeframe: Candle period (e.g. '1h', '5m').
            limit:     Maximum number of candles to return (None = all).

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume.
            Sorted by timestamp ascending.

        Raises:
            DataLoadError: If the data source is unavailable or corrupt.
        """
        ...


@runtime_checkable
class BridgeWriter(Protocol):
    """
    Port for writing trade outcomes to the evolutionary bridge.

    The bridge is the JSONL append-only log that connects the Trading
    Engine's outputs to the Ghost Architect's inputs.

    Implementations may write to JSONL files, databases, or message queues.
    """

    def append_trade(self, trade: "TradeRecord") -> None:
        """
        Append a completed trade record to the bridge.

        Args:
            trade: The trade record to persist.

        Raises:
            MemoryError: If the bridge is inaccessible.
        """
        ...

    def read_trades(
        self,
        limit: Optional[int] = None,
    ) -> list["TradeRecord"]:
        """
        Read trade records from the bridge.

        Args:
            limit: Maximum number of records to return (None = all).
                   Returns most recent first when limited.

        Returns:
            List of TradeRecord instances, ordered by entry_time descending.

        Raises:
            DataLoadError: If the bridge file is corrupt.
        """
        ...

    def count(self) -> int:
        """Return the total number of trade records in the bridge."""
        ...
