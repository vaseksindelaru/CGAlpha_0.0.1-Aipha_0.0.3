from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from io import BytesIO
import logging
from pathlib import Path
from typing import List
from zipfile import ZipFile

import numpy as np
import pandas as pd
import requests

from cgalpha_v3.domain.base_component import BaseComponentV3, ComponentManifest


log = logging.getLogger(__name__)


@dataclass
class MicrostructureRecord:
    timestamp: int
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: float
    vwap_std_1: float
    vwap_std_2: float
    obi_10: float
    cumulative_delta: float
    delta_divergence: str
    atr_14: float
    regime: str


class BinanceVisionFetcher_v3(BaseComponentV3):
    """
    Descarga OHLCV diario desde Binance Vision y enriquece microestructura.
    """

    def __init__(self, manifest: ComponentManifest):
        super().__init__(manifest)
        project_root = Path(__file__).resolve().parent.parent.parent
        self.cache_dir = project_root / "cgalpha_v3" / "data" / "binance_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.base_url = "https://data.binance.vision/data/futures/um/daily/klines"
        self.interval = "1h"
        self.timeout_s = 20

    def evaluate(self, symbol: str, start_time: datetime, end_time: datetime) -> List[MicrostructureRecord]:
        """
        Cosecha OHLCV diario desde Binance Vision.

        Nota: en Fase 1 el entrenamiento principal se mantiene en datos sintéticos;
        este fetcher queda habilitado para ingestión real bajo demanda.
        """
        if end_time < start_time:
            raise ValueError("end_time must be >= start_time")

        start = self._ensure_utc(start_time).date()
        end = self._ensure_utc(end_time).date()
        all_rows: list[pd.DataFrame] = []

        day = start
        while day <= end:
            daily = self._fetch_daily_klines(symbol=symbol, day=day)
            if daily is not None and not daily.empty:
                all_rows.append(daily)
            day += timedelta(days=1)

        if not all_rows:
            log.warning("[BinanceVisionFetcher_v3] No data available for %s in requested range.", symbol)
            return []

        df = pd.concat(all_rows, ignore_index=True)
        df = df.sort_values("open_time").drop_duplicates(subset=["open_time"]).reset_index(drop=True)

        start_ms = int(self._ensure_utc(start_time).timestamp() * 1000)
        end_ms = int(self._ensure_utc(end_time).timestamp() * 1000)
        df = df[(df["open_time"] >= start_ms) & (df["open_time"] <= end_ms)].copy()
        if df.empty:
            return []

        enriched = self._enrich_microstructure(df)
        return self._to_records(enriched, symbol)

    @staticmethod
    def _ensure_utc(ts: datetime) -> datetime:
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)

    def _fetch_daily_klines(self, symbol: str, day: date) -> pd.DataFrame | None:
        filename = f"{symbol}-{self.interval}-{day.isoformat()}.zip"
        cache_path = self.cache_dir / symbol / self.interval / filename
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        if not cache_path.exists():
            url = f"{self.base_url}/{symbol}/{self.interval}/{filename}"
            try:
                response = requests.get(url, timeout=self.timeout_s)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                cache_path.write_bytes(response.content)
            except requests.RequestException:
                return None

        try:
            with ZipFile(cache_path, "r") as zf:
                members = zf.namelist()
                if not members:
                    return None
                with zf.open(members[0]) as csv_file:
                    return self._parse_klines_csv(csv_file.read())
        except Exception:
            return None

    @staticmethod
    def _parse_klines_csv(raw_bytes: bytes) -> pd.DataFrame:
        columns = [
            "open_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_asset_volume",
            "number_of_trades",
            "taker_buy_base_asset_volume",
            "taker_buy_quote_asset_volume",
            "ignore",
        ]
        df = pd.read_csv(BytesIO(raw_bytes), header=None, names=columns)
        numeric_cols = ["open", "high", "low", "close", "volume", "open_time", "close_time"]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.dropna(subset=["open_time", "close_time", "open", "high", "low", "close", "volume"])
        return df

    @staticmethod
    def _enrich_microstructure(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        typical_price = (out["high"] + out["low"] + out["close"]) / 3.0
        cum_vol = out["volume"].cumsum().replace(0, np.nan)
        out["vwap"] = (typical_price * out["volume"]).cumsum() / cum_vol
        out["vwap"] = out["vwap"].fillna(out["close"])

        returns = out["close"].pct_change().fillna(0.0)
        out["obi_10"] = np.clip(returns.rolling(10, min_periods=1).mean() * 120.0, -1.0, 1.0)
        out["cumulative_delta"] = (returns * out["volume"]).cumsum()

        high_low = out["high"] - out["low"]
        high_close_prev = (out["high"] - out["close"].shift(1)).abs()
        low_close_prev = (out["low"] - out["close"].shift(1)).abs()
        tr = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
        out["atr_14"] = tr.rolling(14, min_periods=1).mean()

        vwap_spread_std = (out["close"] - out["vwap"]).rolling(20, min_periods=1).std().fillna(0.0)
        out["vwap_std_1"] = vwap_spread_std
        out["vwap_std_2"] = vwap_spread_std * 2.0

        out["delta_divergence"] = np.where(
            (returns > 0.001) & (out["obi_10"] > 0.10),
            "BULLISH_ABSORPTION",
            np.where(
                (returns < -0.001) & (out["obi_10"] < -0.10),
                "BEARISH_EXHAUSTION",
                "NEUTRAL",
            ),
        )

        vol_score = returns.abs().rolling(20, min_periods=1).std().fillna(0.0)
        trend_score = out["close"].pct_change(20).abs().fillna(0.0)
        vol_threshold = float(vol_score.quantile(0.75)) if len(vol_score) > 4 else float(vol_score.max())
        trend_threshold = float(trend_score.quantile(0.65)) if len(trend_score) > 4 else float(trend_score.max())
        out["regime"] = np.where(
            vol_score >= vol_threshold,
            "HIGH_VOL",
            np.where(trend_score >= trend_threshold, "TREND", "LATERAL"),
        )
        return out

    @staticmethod
    def _to_records(df: pd.DataFrame, symbol: str) -> List[MicrostructureRecord]:
        records: list[MicrostructureRecord] = []
        for row in df.itertuples(index=False):
            records.append(
                MicrostructureRecord(
                    timestamp=int(row.open_time),
                    symbol=symbol,
                    open=float(row.open),
                    high=float(row.high),
                    low=float(row.low),
                    close=float(row.close),
                    volume=float(row.volume),
                    vwap=float(row.vwap),
                    vwap_std_1=float(row.vwap_std_1),
                    vwap_std_2=float(row.vwap_std_2),
                    obi_10=float(row.obi_10),
                    cumulative_delta=float(row.cumulative_delta),
                    delta_divergence=str(row.delta_divergence),
                    atr_14=float(row.atr_14),
                    regime=str(row.regime),
                )
            )
        return records

    @classmethod
    def create_default(cls):
        manifest = ComponentManifest(
            name="BinanceVisionFetcher_v3",
            category="infrastructure",
            function="Ingestión y enriquecimiento de datos OHLCV + Trinity Microstructure",
            inputs=["symbol", "start_time", "end_time"],
            outputs=["List[MicrostructureRecord]"],
            heritage_source="legacy_vault/infrastructure/data_processor/data_system/fetcher.py",
            heritage_contribution="Robust ZIP downloading and extraction logic.",
            v3_adaptations="Type-safe MicrostructureRecord output and Trinity integration.",
            causal_score=0.85,
        )
        return cls(manifest)
