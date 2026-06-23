"""
Tests para BinanceWebSocketManager — P3 Puerta de Cobertura Base
================================================================
Componente prerrequisito de Oracle Fase B. Maneja la conexión a Binance
y la inyección de snapshots al L2RingBuffer.

Umbral CRB P3: >= 50% (async/red, difícil de mockear).
No se testea el loop de websockets (depende de red); se testean los
métodos síncronos: get_current_obi, get_rolling_delta, create_default,
y la normalización de mensajes spot/futures en _handle_message.

CRB: cgalpha_v4/CRB_BinanceWebSocketManager_P3.md §6 Fase A punto 2.
"""

import asyncio

import pytest

from cgalpha_v3.domain.base_component import ComponentManifest
from cgalpha_v3.infrastructure.binance_websocket_manager import BinanceWebSocketManager


def _make_manifest():
    return ComponentManifest(
        name="BinanceWebSocketManager",
        category="infrastructure",
        function="Ingesta de datos en tiempo real via Binance WebSocket",
        inputs=["symbol_list"],
        outputs=["LiveStreamEvents", "TickData"],
        causal_score=0.95,
    )


class TestBinanceWebSocketManagerInit:
    """Tests del constructor."""

    def test_init_default_symbols(self):
        ws = BinanceWebSocketManager(_make_manifest())
        assert ws.symbols == ["btcusdt"]
        assert ws.is_running is False
        assert ws.market == "futures"

    def test_init_custom_symbols(self):
        ws = BinanceWebSocketManager(_make_manifest(), symbols=["ETHUSDT", "SOLUSDT"])
        assert ws.symbols == ["ethusdt", "solusdt"]

    def test_init_creates_l2_buffer_per_symbol(self):
        """Cada símbolo tiene su propio L2RingBuffer."""
        from cgalpha_v3.infrastructure.l2_ring_buffer import L2RingBuffer

        ws = BinanceWebSocketManager(_make_manifest(), symbols=["btcusdt", "ethusdt"])
        assert set(ws.l2_buffers.keys()) == {"btcusdt", "ethusdt"}
        assert all(isinstance(buf, L2RingBuffer) for buf in ws.l2_buffers.values())

    def test_init_connection_epoch_starts_zero(self):
        ws = BinanceWebSocketManager(_make_manifest())
        assert ws._connection_epoch == 0


class TestGetCurrentOBI:
    """Tests de get_current_obi() — cálculo multi-nivel del imbalance."""

    def test_obi_no_state_returns_zero(self):
        """Sin estado del libro, OBI = 0.0."""
        ws = BinanceWebSocketManager(_make_manifest())
        assert ws.get_current_obi("BTCUSDT", levels=10) == 0.0

    def test_obi_balanced_book_returns_zero(self):
        """Libro balanceado (bid_qty == ask_qty) → OBI = 0.0."""
        ws = BinanceWebSocketManager(_make_manifest())
        ws.order_book_state["BTCUSDT"] = {
            "bids": [["100", "5"], ["99", "5"]],
            "asks": [["101", "5"], ["102", "5"]],
            "timestamp": 1000,
        }
        assert ws.get_current_obi("BTCUSDT", levels=10) == 0.0

    def test_obi_bid_heavy_returns_positive(self):
        """Libro con más bids → OBI positivo."""
        ws = BinanceWebSocketManager(_make_manifest())
        ws.order_book_state["BTCUSDT"] = {
            "bids": [["100", "10"], ["99", "10"]],
            "asks": [["101", "2"], ["102", "2"]],
            "timestamp": 1000,
        }
        # (20 - 4) / 24 = 0.666...
        obi = ws.get_current_obi("BTCUSDT", levels=10)
        assert obi > 0.5
        assert obi < 0.7

    def test_obi_ask_heavy_returns_negative(self):
        """Libro con más asks → OBI negativo."""
        ws = BinanceWebSocketManager(_make_manifest())
        ws.order_book_state["BTCUSDT"] = {
            "bids": [["100", "2"], ["99", "2"]],
            "asks": [["101", "10"], ["102", "10"]],
            "timestamp": 1000,
        }
        obi = ws.get_current_obi("BTCUSDT", levels=10)
        assert obi < -0.5

    def test_obi_levels_truncation(self):
        """levels=N solo considera los primeros N niveles del libro."""
        ws = BinanceWebSocketManager(_make_manifest())
        ws.order_book_state["BTCUSDT"] = {
            "bids": [["100", "1"], ["99", "1"], ["98", "100"]],
            "asks": [["101", "1"], ["102", "1"], ["103", "100"]],
            "timestamp": 1000,
        }
        # Con levels=2: bids=[1,1]=2, asks=[1,1]=2 → OBI=0
        obi_2 = ws.get_current_obi("BTCUSDT", levels=2)
        assert obi_2 == 0.0
        # Con levels=3: bids=[1,1,100]=102, asks=[1,1,100]=102 → OBI=0
        obi_3 = ws.get_current_obi("BTCUSDT", levels=3)
        assert obi_3 == 0.0

    def test_obi_symbol_case_insensitive(self):
        """get_current_obi usa symbol.upper() para lookup."""
        ws = BinanceWebSocketManager(_make_manifest())
        ws.order_book_state["BTCUSDT"] = {
            "bids": [["100", "10"]],
            "asks": [["101", "5"]],
            "timestamp": 1000,
        }
        # Minúsculas deben funcionar (se convierte a upper internamente)
        assert ws.get_current_obi("btcusdt", levels=10) > 0.0

    def test_obi_total_zero_returns_zero(self):
        """Si bid_qty + ask_qty == 0, retorna 0.0 (evita división por cero)."""
        ws = BinanceWebSocketManager(_make_manifest())
        ws.order_book_state["BTCUSDT"] = {
            "bids": [["100", "0"]],
            "asks": [["101", "0"]],
            "timestamp": 1000,
        }
        assert ws.get_current_obi("BTCUSDT", levels=10) == 0.0


class TestGetRollingDelta:
    """Tests de get_rolling_delta() — CumDelta rolling window."""

    def test_rolling_delta_empty_trades_returns_zero(self):
        """Sin trades, delta = 0.0."""
        ws = BinanceWebSocketManager(_make_manifest())
        ws.last_known_binance_ts_ms = 1000000
        assert ws.get_rolling_delta("BTCUSDT", window_seconds=300) == 0.0

    def test_rolling_delta_buy_heavy_positive(self):
        """Más compras agresivas (is_buyer_maker=False) → delta positivo."""
        ws = BinanceWebSocketManager(_make_manifest())
        ws.last_known_binance_ts_ms = 1000000
        ws.last_trades = [
            {"price": 100, "qty": 5.0, "is_buyer_maker": False, "timestamp": 900000},
            {"price": 101, "qty": 3.0, "is_buyer_maker": False, "timestamp": 950000},
        ]
        delta = ws.get_rolling_delta("BTCUSDT", window_seconds=300)
        assert delta == 8.0  # 5 + 3

    def test_rolling_delta_sell_heavy_negative(self):
        """Más ventas agresivas (is_buyer_maker=True) → delta negativo."""
        ws = BinanceWebSocketManager(_make_manifest())
        ws.last_known_binance_ts_ms = 1000000
        ws.last_trades = [
            {"price": 100, "qty": 5.0, "is_buyer_maker": True, "timestamp": 900000},
            {"price": 101, "qty": 3.0, "is_buyer_maker": True, "timestamp": 950000},
        ]
        delta = ws.get_rolling_delta("BTCUSDT", window_seconds=300)
        assert delta == -8.0  # -(5 + 3)

    def test_rolling_delta_mixed_trades(self):
        """Trades mixtos: delta = buy_qty - sell_qty."""
        ws = BinanceWebSocketManager(_make_manifest())
        ws.last_known_binance_ts_ms = 1000000
        ws.last_trades = [
            {"price": 100, "qty": 5.0, "is_buyer_maker": False, "timestamp": 900000},
            {"price": 101, "qty": 3.0, "is_buyer_maker": True, "timestamp": 950000},
        ]
        delta = ws.get_rolling_delta("BTCUSDT", window_seconds=300)
        assert delta == 2.0  # 5 - 3

    def test_rolling_delta_excludes_old_trades(self):
        """Trades fuera de la ventana son excluidos."""
        ws = BinanceWebSocketManager(_make_manifest())
        ws.last_known_binance_ts_ms = 1000000
        # Trade a 400s atrás (fuera de ventana de 300s)
        ws.last_trades = [
            {"price": 100, "qty": 5.0, "is_buyer_maker": False, "timestamp": 600000},
            # Trade dentro de la ventana
            {"price": 101, "qty": 3.0, "is_buyer_maker": False, "timestamp": 900000},
        ]
        delta = ws.get_rolling_delta("BTCUSDT", window_seconds=300)
        assert delta == 3.0  # solo el trade a 900000

    def test_rolling_delta_fallback_to_time_time(self):
        """Si last_known_binance_ts_ms == 0, usa time.time() como fallback."""
        import time as _time

        ws = BinanceWebSocketManager(_make_manifest())
        ws.last_known_binance_ts_ms = 0.0
        now_ms = _time.time() * 1000
        # Trade reciente (dentro de ventana)
        ws.last_trades = [
            {
                "price": 100,
                "qty": 2.0,
                "is_buyer_maker": False,
                "timestamp": now_ms - 1000,
            },
        ]
        delta = ws.get_rolling_delta("BTCUSDT", window_seconds=300)
        assert delta == 2.0


class TestHandleMessageNormalization:
    """Tests de _handle_message() — normalización spot/futures y timestamp.

    _handle_message es async, pero no requiere un event loop real porque
    no hay awaits internos (los callbacks están vacíos en estos tests).
    Usamos asyncio.run() para ejecutar la coroutine en un test síncrono,
    evitando la dependencia de pytest-asyncio.
    """

    def test_spot_format_normalization(self):
        """Spot depth20 usa 'bids'/'asks' (no 'b'/'a') y se normaliza."""
        ws = BinanceWebSocketManager(_make_manifest())
        spot_msg = {
            "stream": "btcusdt@depth20@100ms",
            "data": {
                "bids": [["100", "5"], ["99", "3"]],
                "asks": [["101", "2"], ["102", "1"]],
                "E": 1234567890,
            },
        }
        asyncio.run(ws._handle_message(spot_msg))
        # El estado debe tener el formato normalizado con 'b' y 'a'
        state = ws.order_book_state.get("BTCUSDT")
        assert state is not None
        assert state["bids"] == [["100", "5"], ["99", "3"]]
        assert state["asks"] == [["101", "2"], ["102", "1"]]
        assert state["timestamp"] == 1234567890

    def test_futures_format_no_normalization(self):
        """Futures depth20 usa 'b'/'a' directamente, sin normalización."""
        ws = BinanceWebSocketManager(_make_manifest())
        futures_msg = {
            "stream": "btcusdt@depth20@100ms",
            "data": {
                "b": [["100", "5"], ["99", "3"]],
                "a": [["101", "2"], ["102", "1"]],
                "E": 1234567890,
                "s": "BTCUSDT",
            },
        }
        asyncio.run(ws._handle_message(futures_msg))
        state = ws.order_book_state.get("BTCUSDT")
        assert state is not None
        assert state["bids"] == [["100", "5"], ["99", "3"]]

    def test_binance_ts_ms_extraction_from_E_field(self):
        """El timestamp se extrae del campo 'E' (event time)."""
        ws = BinanceWebSocketManager(_make_manifest())
        msg = {
            "stream": "btcusdt@depth20@100ms",
            "data": {
                "b": [["100", "5"]],
                "a": [["101", "2"]],
                "E": 9999999,
                "s": "BTCUSDT",
            },
        }
        asyncio.run(ws._handle_message(msg))
        assert ws.last_known_binance_ts_ms == 9999999

    def test_binance_ts_ms_extraction_from_T_field(self):
        """Si no hay 'E', el timestamp se extrae de 'T' (trade time)."""
        ws = BinanceWebSocketManager(_make_manifest())
        msg = {
            "stream": "btcusdt@depth20@100ms",
            "data": {
                "b": [["100", "5"]],
                "a": [["101", "2"]],
                "T": 8888888,
                "s": "BTCUSDT",
            },
        }
        asyncio.run(ws._handle_message(msg))
        assert ws.last_known_binance_ts_ms == 8888888

    def test_trade_event_populates_last_trades(self):
        """Evento trade añade a last_trades con price, qty, is_buyer_maker."""
        ws = BinanceWebSocketManager(_make_manifest())
        msg = {
            "stream": "btcusdt@trade",
            "data": {
                "e": "trade",
                "p": "50000.5",
                "q": "0.123",
                "m": False,
                "T": 1234567890,
                "s": "BTCUSDT",
            },
        }
        asyncio.run(ws._handle_message(msg))
        assert len(ws.last_trades) == 1
        trade = ws.last_trades[0]
        assert trade["price"] == 50000.5
        assert trade["qty"] == 0.123
        assert trade["is_buyer_maker"] is False
        assert trade["timestamp"] == 1234567890

    def test_depth_update_pushes_to_l2_buffer(self):
        """Depth update empuja un snapshot al L2RingBuffer del símbolo."""
        ws = BinanceWebSocketManager(_make_manifest())
        msg = {
            "stream": "btcusdt@depth20@100ms",
            "data": {
                "b": [
                    ["100", "5"],
                    ["99", "3"],
                    ["98", "2"],
                    ["97", "1"],
                    ["96", "1"],
                    ["95", "1"],
                    ["94", "1"],
                    ["93", "1"],
                    ["92", "1"],
                    ["91", "1"],
                ],
                "a": [
                    ["101", "2"],
                    ["102", "1"],
                    ["103", "1"],
                    ["104", "1"],
                    ["105", "1"],
                    ["106", "1"],
                    ["107", "1"],
                    ["108", "1"],
                    ["109", "1"],
                    ["110", "1"],
                ],
                "E": 1000000,
                "s": "BTCUSDT",
            },
        }
        asyncio.run(ws._handle_message(msg))
        buf = ws.l2_buffers["btcusdt"]
        assert len(buf.get_raw_buffer()) == 1
        snap = buf.get_raw_buffer()[0]
        assert snap["obi_1"] != 0.0  # Se calculó OBI
        assert snap["ts"] == 1000.0  # 1000000ms / 1000 = 1000.0s


class TestCreateDefault:
    """Tests de create_default() — factory method."""

    def test_create_default_btcusdt(self):
        ws = BinanceWebSocketManager.create_default("BTCUSDT")
        assert ws.symbols == ["btcusdt"]
        assert ws.market == "futures"
        assert "btcusdt" in ws.l2_buffers

    def test_create_default_manifest_fields(self):
        ws = BinanceWebSocketManager.create_default("ETHUSDT")
        assert ws.manifest.name == "BinanceWebSocketManager"
        assert ws.manifest.category == "infrastructure"
        assert ws.manifest.causal_score == 0.95
