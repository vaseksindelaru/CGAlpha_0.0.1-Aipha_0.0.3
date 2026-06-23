"""
Tests para L2RingBuffer — P3 Puerta de Cobertura Base
=====================================================
Componente prerrequisito de Oracle Fase B. La lógica de synthesize_at_retest()
es la pieza que implementa D-014 (acoplamiento temporal causal), por lo que
requiere cobertura ≥ 80%.

CRB: cgalpha_v4/CRB_BinanceWebSocketManager_P3.md §6 Fase A punto 1.
"""

import pytest

from cgalpha_v3.infrastructure.l2_ring_buffer import L2RingBuffer


def _push_snapshot(buf, ts_ms, obi_10=0.5, cum_delta=100.0, epoch=0, **kwargs):
    """Helper: empuja un snapshot con valores por defecto razonables."""
    buf.mark_reconnection(epoch) if epoch else None
    buf.push(
        binance_ts_ms=ts_ms,
        local_offset_ms=kwargs.get("local_offset_ms", 5.0),
        obi_1=kwargs.get("obi_1", 0.3),
        obi_5=kwargs.get("obi_5", 0.4),
        obi_10=obi_10,
        obi_20=kwargs.get("obi_20", 0.6),
        cum_delta=cum_delta,
        best_bid_size=kwargs.get("best_bid_size", 1.0),
        best_ask_size=kwargs.get("best_ask_size", 1.0),
        bid_depth_10=kwargs.get("bid_depth_10", 10.0),
        ask_depth_10=kwargs.get("ask_depth_10", 10.0),
        spread_bps=kwargs.get("spread_bps", 1.5),
        trade_count=kwargs.get("trade_count", 5),
        aggressive_buy_vol=kwargs.get("aggressive_buy_vol", 0.5),
        aggressive_sell_vol=kwargs.get("aggressive_sell_vol", 0.3),
    )


class TestL2RingBufferInit:
    """Tests del constructor y configuración del buffer."""

    def test_max_slots_300_with_defaults(self):
        """Con defaults (30s, 100ms) el buffer debe tener 300 slots."""
        buf = L2RingBuffer()
        assert buf.max_slots == 300

    def test_custom_max_seconds_and_sample_rate(self):
        """Parámetros custom se respetan."""
        buf = L2RingBuffer(max_seconds=10.0, sample_rate_ms=200)
        assert buf.max_slots == 50  # 10 * 1000 / 200 = 50

    def test_buffer_starts_empty(self):
        buf = L2RingBuffer()
        assert len(buf.get_raw_buffer()) == 0
        assert buf._current_epoch == 0


class TestL2RingBufferPush:
    """Tests del método push()."""

    def test_push_populates_buffer(self):
        """push() añade un snapshot al buffer."""
        buf = L2RingBuffer()
        _push_snapshot(buf, ts_ms=1000)
        raw = buf.get_raw_buffer()
        assert len(raw) == 1
        assert raw[0]["obi_10"] == 0.5
        assert raw[0]["ts"] == 1.0  # 1000ms / 1000 = 1.0 segundos

    def test_push_respects_max_slots(self):
        """El buffer no excede max_slots (deque maxlen)."""
        buf = L2RingBuffer(max_seconds=1.0, sample_rate_ms=100)  # 10 slots
        for i in range(20):
            _push_snapshot(buf, ts_ms=i * 100)
        assert len(buf.get_raw_buffer()) == 10

    def test_push_stores_all_15_fields(self):
        """push() debe almacenar los 15 campos del snapshot."""
        buf = L2RingBuffer()
        _push_snapshot(buf, ts_ms=1000)
        snap = buf.get_raw_buffer()[0]
        expected_keys = {
            "ts",
            "local_offset_ms",
            "epoch",
            "obi_1",
            "obi_5",
            "obi_10",
            "obi_20",
            "cum_delta",
            "best_bid_size",
            "best_ask_size",
            "bid_depth_10",
            "ask_depth_10",
            "spread_bps",
            "trade_count",
            "agg_buy_vol",
            "agg_sell_vol",
        }
        assert set(snap.keys()) == expected_keys

    def test_push_converts_types(self):
        """push() convierte a float/int según el campo."""
        buf = L2RingBuffer()
        buf.push(
            binance_ts_ms=1000,
            local_offset_ms=5.0,
            obi_1="0.3",
            obi_5="0.4",
            obi_10="0.5",
            obi_20="0.6",
            cum_delta="100",
            best_bid_size="1",
            best_ask_size="1",
            bid_depth_10="10",
            ask_depth_10="10",
            spread_bps="1.5",
            trade_count="5",
            aggressive_buy_vol="0.5",
            aggressive_sell_vol="0.3",
        )
        snap = buf.get_raw_buffer()[0]
        assert isinstance(snap["obi_10"], float)
        assert isinstance(snap["trade_count"], int)
        assert snap["obi_10"] == 0.5


class TestL2RingBufferMarkReconnection:
    """Tests del epoch tracking para detección de PARTIAL."""

    def test_mark_reconnection_changes_epoch(self):
        """mark_reconnection() actualiza el epoch actual."""
        buf = L2RingBuffer()
        assert buf._current_epoch == 0
        buf.mark_reconnection(1)
        assert buf._current_epoch == 1
        buf.mark_reconnection(5)
        assert buf._current_epoch == 5

    def test_push_uses_current_epoch(self):
        """push() almacena el epoch actual en el snapshot."""
        buf = L2RingBuffer()
        buf.mark_reconnection(3)
        _push_snapshot(buf, ts_ms=1000)
        assert buf.get_raw_buffer()[0]["epoch"] == 3


class TestL2RingBufferSynthesize:
    """Tests de synthesize_at_retest() — la pieza crítica de D-014."""

    def test_synthesize_empty_buffer_returns_empty_profile(self):
        """Buffer vacío retorna _empty_profile()."""
        buf = L2RingBuffer()
        profile = buf.synthesize_at_retest()
        assert profile["l2_data_quality"] == "EMPTY"
        assert profile["n_snapshots"] == 0

    def test_synthesize_below_10_snapshots_returns_empty(self):
        """< 10 snapshots retorna _empty_profile() (threshold del código L42)."""
        buf = L2RingBuffer()
        for i in range(9):
            _push_snapshot(buf, ts_ms=i * 100)
        profile = buf.synthesize_at_retest()
        assert profile["l2_data_quality"] == "EMPTY"
        assert profile["n_snapshots"] == 0

    def test_synthesize_full_quality_single_epoch(self):
        """10+ snapshots con un solo epoch → l2_data_quality = FULL."""
        buf = L2RingBuffer()
        buf.mark_reconnection(1)
        for i in range(15):
            _push_snapshot(buf, ts_ms=i * 100, epoch=1)
        profile = buf.synthesize_at_retest()
        assert profile["l2_data_quality"] == "FULL"
        assert profile["n_snapshots"] == 15

    def test_synthesize_partial_quality_multi_epoch(self):
        """Snapshots con múltiples epochs → l2_data_quality = PARTIAL."""
        buf = L2RingBuffer()
        # Primera tanda con epoch 1
        buf.mark_reconnection(1)
        for i in range(10):
            _push_snapshot(buf, ts_ms=i * 100, epoch=1)
        # Reconexión: epoch 2
        buf.mark_reconnection(2)
        for i in range(10):
            _push_snapshot(buf, ts_ms=(10 + i) * 100, epoch=2)
        profile = buf.synthesize_at_retest()
        assert profile["l2_data_quality"] == "PARTIAL"

    def test_synthesize_returns_23_fields(self):
        """synthesize_at_retest() devuelve exactamente 23 campos."""
        buf = L2RingBuffer()
        buf.mark_reconnection(1)
        for i in range(15):
            _push_snapshot(buf, ts_ms=i * 100, epoch=1)
        profile = buf.synthesize_at_retest()
        assert len(profile) == 23

    def test_synthesize_window_segmentation(self):
        """Las ventanas 5s/15s/30s segmentan correctamente."""
        buf = L2RingBuffer()
        buf.mark_reconnection(1)
        # 30 snapshots a 100ms = 3 segundos de datos
        for i in range(30):
            _push_snapshot(buf, ts_ms=i * 100, epoch=1)
        profile = buf.synthesize_at_retest()
        # Con 3s de datos, w5 y w15 deben tener todos los snapshots
        # w30 también (porque 3s < 30s)
        assert profile["n_snapshots"] == 30

    def test_synthesize_obi_gradient_rising(self):
        """OBI creciente produce gradiente positivo."""
        buf = L2RingBuffer()
        buf.mark_reconnection(1)
        for i in range(15):
            _push_snapshot(buf, ts_ms=i * 100, obi_10=0.1 + i * 0.05, epoch=1)
        profile = buf.synthesize_at_retest()
        # Gradiente debe ser positivo (OBI sube)
        assert profile["obi_10_gradient_30s"] > 0

    def test_synthesize_obi_gradient_falling(self):
        """OBI decreciente produce gradiente negativo."""
        buf = L2RingBuffer()
        buf.mark_reconnection(1)
        for i in range(15):
            _push_snapshot(buf, ts_ms=i * 100, obi_10=0.9 - i * 0.05, epoch=1)
        profile = buf.synthesize_at_retest()
        assert profile["obi_10_gradient_30s"] < 0

    def test_synthesize_delta_rate_positive(self):
        """CumDelta creciente produce delta_rate positivo."""
        buf = L2RingBuffer()
        buf.mark_reconnection(1)
        for i in range(15):
            _push_snapshot(buf, ts_ms=i * 100, cum_delta=100.0 + i * 10, epoch=1)
        profile = buf.synthesize_at_retest()
        assert profile["delta_rate_30s"] > 0

    def test_synthesize_delta_rate_negative(self):
        """CumDelta decreciente produce delta_rate negativo."""
        buf = L2RingBuffer()
        buf.mark_reconnection(1)
        for i in range(15):
            _push_snapshot(buf, ts_ms=i * 100, cum_delta=1000.0 - i * 10, epoch=1)
        profile = buf.synthesize_at_retest()
        assert profile["delta_rate_30s"] < 0

    def test_synthesize_trade_intensity(self):
        """trade_intensity suma los trade_count de la ventana."""
        buf = L2RingBuffer()
        buf.mark_reconnection(1)
        for i in range(15):
            _push_snapshot(buf, ts_ms=i * 100, trade_count=10, epoch=1)
        profile = buf.synthesize_at_retest()
        # 15 snapshots * 10 trades = 150 en w30
        # w5 cubre los últimos 5s = ~50 snapshots, pero solo tenemos 15
        assert profile["trade_intensity_5s"] == 150  # todos caen en w5

    def test_synthesize_aggressive_buy_pct(self):
        """aggressive_buy_pct calcula el ratio de compra agresiva."""
        buf = L2RingBuffer()
        buf.mark_reconnection(1)
        for i in range(15):
            _push_snapshot(
                buf,
                ts_ms=i * 100,
                aggressive_buy_vol=0.7,
                aggressive_sell_vol=0.3,
                epoch=1,
            )
        profile = buf.synthesize_at_retest()
        # 0.7 / (0.7 + 0.3) = 0.7
        assert abs(profile["aggressive_buy_pct_5s"] - 0.7) < 0.01

    def test_synthesize_aggressive_buy_pct_no_volume(self):
        """Sin volumen agresivo, aggressive_buy_pct = 0.5 (default)."""
        buf = L2RingBuffer()
        buf.mark_reconnection(1)
        for i in range(15):
            _push_snapshot(
                buf,
                ts_ms=i * 100,
                aggressive_buy_vol=0.0,
                aggressive_sell_vol=0.0,
                epoch=1,
            )
        profile = buf.synthesize_at_retest()
        assert profile["aggressive_buy_pct_5s"] == 0.5

    def test_synthesize_depth_ratio(self):
        """depth_ratio_1_10 = obi_1 / obi_10 del último snapshot."""
        buf = L2RingBuffer()
        buf.mark_reconnection(1)
        for i in range(15):
            _push_snapshot(buf, ts_ms=i * 100, obi_1=0.3, obi_10=0.6, epoch=1)
        profile = buf.synthesize_at_retest()
        # 0.3 / 0.6 = 0.5
        assert abs(profile["depth_ratio_1_10"] - 0.5) < 0.01

    def test_synthesize_depth_ratio_obi_10_zero(self):
        """obi_10 = 0 → depth_ratio = 1.0 (fallback seguro)."""
        buf = L2RingBuffer()
        buf.mark_reconnection(1)
        for i in range(15):
            _push_snapshot(buf, ts_ms=i * 100, obi_1=0.3, obi_10=0.0, epoch=1)
        profile = buf.synthesize_at_retest()
        assert profile["depth_ratio_1_10"] == 1.0


class TestL2RingBufferEmptyProfile:
    """Tests de _empty_profile() — issue #5 del CRB P3 (schema inconsistente)."""

    def test_empty_profile_has_n_snapshots_zero(self):
        """_empty_profile() incluye n_snapshots = 0."""
        buf = L2RingBuffer()
        profile = buf.synthesize_at_retest()
        assert profile["n_snapshots"] == 0

    def test_empty_profile_has_quality_empty(self):
        """_empty_profile() incluye l2_data_quality = EMPTY."""
        buf = L2RingBuffer()
        profile = buf.synthesize_at_retest()
        assert profile["l2_data_quality"] == "EMPTY"

    def test_empty_profile_schema_matches_synthesize_keys(self):
        """
        Issue #5 del CRB P3: _empty_profile() debe tener las mismas
        keys que synthesize_at_retest() para que el schema sea consistente.
        """
        buf = L2RingBuffer()
        # Profile vacío
        empty_profile = buf.synthesize_at_retest()
        # Profile lleno
        buf.mark_reconnection(1)
        for i in range(15):
            _push_snapshot(buf, ts_ms=i * 100, epoch=1)
        full_profile = buf.synthesize_at_retest()
        # Las keys deben coincidir
        assert set(empty_profile.keys()) == set(full_profile.keys())


class TestL2RingBufferD014CausalFilter:
    """Tests del filtrado causal D-014 en synthesize_at_retest().

    D-014: t_feature <= t_candle_close - epsilon (epsilon=200ms).
    Los snapshots con ts > (t_candle_close_ms - epsilon_ms) / 1000
    deben ser excluidos del perfil sintetizado.
    """

    def test_d014_no_filter_when_t_candle_close_none(self):
        """Si t_candle_close_ms es None, no se filtra (compatibilidad)."""
        buf = L2RingBuffer()
        buf.mark_reconnection(1)
        for i in range(15):
            _push_snapshot(buf, ts_ms=i * 100, epoch=1)
        # Sin t_candle_close_ms → comportamiento pre-D-014
        profile = buf.synthesize_at_retest(t_candle_close_ms=None)
        assert profile["l2_data_quality"] == "FULL"
        assert profile["n_snapshots"] == 15

    def test_d014_filters_snapshots_after_candle_close(self):
        """Snapshots posteriores a t_candle_close - epsilon se excluyen."""
        buf = L2RingBuffer()
        buf.mark_reconnection(1)
        # 20 snapshots: ts de 0 a 1900ms (cada 100ms)
        for i in range(20):
            _push_snapshot(buf, ts_ms=i * 100, epoch=1)
        # t_candle_close = 1500ms, epsilon = 200ms
        # cutoff = (1500 - 200) / 1000 = 1.3s = 1300ms
        # Snapshots con ts <= 1.3s: ts=0,100,...,1300 → 14 snapshots
        profile = buf.synthesize_at_retest(t_candle_close_ms=1500, epsilon_ms=200)
        assert profile["l2_data_quality"] == "FULL"
        assert profile["n_snapshots"] == 14  # 0-1300ms

    def test_d014_causal_rejected_when_too_few_snapshots_after_filter(self):
        """Si el filtrado deja <10 snapshots, retorna CAUSAL_REJECTED."""
        buf = L2RingBuffer()
        buf.mark_reconnection(1)
        # 15 snapshots: ts de 0 a 1400ms
        for i in range(15):
            _push_snapshot(buf, ts_ms=i * 100, epoch=1)
        # t_candle_close = 800ms, epsilon = 200ms
        # cutoff = (800 - 200) / 1000 = 0.6s = 600ms
        # Snapshots con ts <= 0.6s: ts=0,100,200,300,400,500,600 → 7 snapshots
        # 7 < 10 → CAUSAL_REJECTED
        profile = buf.synthesize_at_retest(t_candle_close_ms=800, epsilon_ms=200)
        assert profile["l2_data_quality"] == "CAUSAL_REJECTED"
        assert profile["n_snapshots"] == 0

    def test_d014_custom_epsilon(self):
        """epsilon_ms personalizable."""
        buf = L2RingBuffer()
        buf.mark_reconnection(1)
        for i in range(20):
            _push_snapshot(buf, ts_ms=i * 100, epoch=1)
        # t_candle_close = 1500ms, epsilon = 500ms
        # cutoff = (1500 - 500) / 1000 = 1.0s = 1000ms
        # Snapshots con ts <= 1.0s: ts=0,100,...,1000 → 11 snapshots
        profile = buf.synthesize_at_retest(t_candle_close_ms=1500, epsilon_ms=500)
        assert profile["l2_data_quality"] == "FULL"
        assert profile["n_snapshots"] == 11

    def test_d014_causal_rejected_profile_has_same_schema(self):
        """CAUSAL_REJECTED profile tiene las mismas keys que FULL profile."""
        buf = L2RingBuffer()
        buf.mark_reconnection(1)
        for i in range(15):
            _push_snapshot(buf, ts_ms=i * 100, epoch=1)
        # Forzar CAUSAL_REJECTED
        rejected = buf.synthesize_at_retest(t_candle_close_ms=100, epsilon_ms=200)
        # Profile FULL
        full = buf.synthesize_at_retest()
        assert set(rejected.keys()) == set(full.keys())
        assert rejected["l2_data_quality"] == "CAUSAL_REJECTED"

    def test_d014_all_snapshots_within_window_passes(self):
        """Si todos los snapshots están antes del cutoff, no se filtra nada."""
        buf = L2RingBuffer()
        buf.mark_reconnection(1)
        # 15 snapshots: ts de 0 a 1400ms
        for i in range(15):
            _push_snapshot(buf, ts_ms=i * 100, epoch=1)
        # t_candle_close = 10000ms (muy futuro), epsilon = 200ms
        # cutoff = (10000 - 200) / 1000 = 9.8s
        # Todos los snapshots (ts <= 1.4s) pasan
        profile = buf.synthesize_at_retest(t_candle_close_ms=10000, epsilon_ms=200)
        assert profile["l2_data_quality"] == "FULL"
        assert profile["n_snapshots"] == 15

    def test_d014_epsilon_zero_filters_exactly_at_candle_close(self):
        """Con epsilon=0, filtra snapshots con ts > t_candle_close."""
        buf = L2RingBuffer()
        buf.mark_reconnection(1)
        for i in range(20):
            _push_snapshot(buf, ts_ms=i * 100, epoch=1)
        # t_candle_close = 1000ms, epsilon = 0
        # cutoff = 1000 / 1000 = 1.0s
        # Snapshots con ts <= 1.0s: ts=0,100,...,1000 → 11 snapshots
        profile = buf.synthesize_at_retest(t_candle_close_ms=1000, epsilon_ms=0)
        assert profile["l2_data_quality"] == "FULL"
        assert profile["n_snapshots"] == 11
