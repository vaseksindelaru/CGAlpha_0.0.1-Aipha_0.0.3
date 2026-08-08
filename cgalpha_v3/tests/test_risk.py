"""
Tests — Risk Management Layer (cgalpha_v3)

Cubre:
  - KillSwitch: 2 pasos de confirmación
  - CircuitBreaker: activación por drawdown
  - RiskManager: validación de señales
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from datetime import datetime, timezone

from cgalpha_v3.domain.models.signal import Signal, ApproachType
from cgalpha_v3.risk.risk_manager import (
    RiskManager, RiskParams, KillSwitchState, CircuitBreaker,
)


# ── FIXTURES ──────────────────────────────────────

@pytest.fixture
def params() -> RiskParams:
    return RiskParams(
        max_drawdown_session_pct=5.0,
        min_signal_quality_score=0.65,
        max_signals_per_hour=5,
    )


@pytest.fixture
def risk_manager(params: RiskParams) -> RiskManager:
    return RiskManager(params=params)


def make_signal(quality: float = 0.8, approach: ApproachType = ApproachType.TOUCH) -> Signal:
    return Signal.new(
        symbol="BTCUSDT",
        interval="5m",
        direction="LONG",
        approach_type=approach,
        quality_score=quality,
        price=60000.0,
    )


# ── KILL-SWITCH ───────────────────────────────────

class TestKillSwitch:
    def test_initial_state_is_armed(self):
        ks = KillSwitchState()
        assert ks.state == "armed"
        assert not ks.is_triggered

    def test_two_step_activation(self):
        ks = KillSwitchState()
        ks.arm_request()
        assert ks.state == "arming"
        assert not ks.is_triggered
        ks.confirm()
        assert ks.state == "triggered"
        assert ks.is_triggered

    def test_confirm_without_request_raises(self):
        ks = KillSwitchState()
        with pytest.raises(ValueError, match="No hay solicitud"):
            ks.confirm()

    def test_reset(self):
        ks = KillSwitchState()
        ks.arm_request()
        ks.confirm()
        ks.reset()
        assert ks.state == "armed"
        assert not ks.is_triggered


# ── CIRCUIT BREAKER ───────────────────────────────

class TestCircuitBreaker:
    def test_not_active_initially(self, params: RiskParams):
        cb = CircuitBreaker(params)
        assert not cb.is_active

    def test_activates_on_drawdown_breach(self, params: RiskParams):
        cb = CircuitBreaker(params)
        triggered = cb.check_drawdown(params.max_drawdown_session_pct + 0.1)
        assert triggered
        assert cb.is_active

    def test_no_activation_under_limit(self, params: RiskParams):
        cb = CircuitBreaker(params)
        triggered = cb.check_drawdown(params.max_drawdown_session_pct - 0.1)
        assert not triggered
        assert not cb.is_active

    def test_consecutive_rejections(self, params: RiskParams):
        cb = CircuitBreaker(params)
        cb.record_signal_rejection()
        cb.record_signal_rejection()
        assert not cb.is_active
        triggered = cb.record_signal_rejection()  # 3rd → activate
        assert triggered
        assert cb.is_active

    def test_reset_clears_state(self, params: RiskParams):
        cb = CircuitBreaker(params)
        cb.check_drawdown(params.max_drawdown_session_pct + 1.0)
        cb.reset()
        assert not cb.is_active
        assert cb.reason is None


# ── RISK MANAGER ──────────────────────────────────

class TestRiskManager:
    def test_valid_signal_passes(self, risk_manager: RiskManager):
        sig = make_signal(quality=0.8)
        ok, reason = risk_manager.validate_signal(sig, data_quality_ok=True)
        assert ok, reason

    def test_low_quality_signal_rejected(self, risk_manager: RiskManager):
        sig = make_signal(quality=0.4)
        ok, reason = risk_manager.validate_signal(sig, data_quality_ok=True)
        assert not ok
        assert "Calidad" in reason

    def test_kill_switch_blocks_signal(self, risk_manager: RiskManager):
        risk_manager.kill_switch.arm_request()
        risk_manager.kill_switch.confirm()
        sig = make_signal(quality=0.9)
        ok, reason = risk_manager.validate_signal(sig, data_quality_ok=True)
        assert not ok
        assert "Kill-switch" in reason

    def test_bad_data_quality_blocks_signal(self, risk_manager: RiskManager):
        sig = make_signal(quality=0.9)
        ok, reason = risk_manager.validate_signal(sig, data_quality_ok=False)
        assert not ok
        assert "Data Quality" in reason

    def test_rate_limit(self, risk_manager: RiskManager):
        """No más de max_signals_per_hour señales."""
        max_sph = risk_manager.params.max_signals_per_hour
        for _ in range(max_sph):
            sig = make_signal(quality=0.9)
            ok, _ = risk_manager.validate_signal(sig, data_quality_ok=True)
            assert ok

        # La siguiente debe ser rechazada
        sig = make_signal(quality=0.9)
        ok, reason = risk_manager.validate_signal(sig, data_quality_ok=True)
        assert not ok
        assert "Límite" in reason

    def test_drawdown_triggers_circuit_breaker(self, risk_manager: RiskManager):
        risk_manager.update_drawdown(10.0)  # >5% → CB activo
        sig = make_signal(quality=0.9)
        ok, reason = risk_manager.validate_signal(sig, data_quality_ok=True)
        assert not ok
        assert "Circuit breaker" in reason

    def test_status_snapshot_keys(self, risk_manager: RiskManager):
        snap = risk_manager.status_snapshot()
        required = {
            "kill_switch_status", "circuit_breaker_active",
            "drawdown_session_pct", "max_drawdown_session_pct",
        }
        assert required.issubset(snap.keys())
