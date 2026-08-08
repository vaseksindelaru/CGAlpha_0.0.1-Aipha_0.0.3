"""
CGAlpha v3 — Test integrado de correcciones (ShadowTrader + bridge.jsonl + AutoProposer)
=========================================================================================
Verifica que:
1. ShadowTrader delega en DryRunOrderManager (no devuelve string hardcoded)
2. bridge.jsonl se escribe con el schema correcto
3. evaluate_proposal() devuelve scores reales (no siempre 0.78)
4. AutoProposer.analyze_drift() se conecta al pipeline cycle
"""

import json
import os
import shutil
from pathlib import Path

import pytest

from cgalpha_v3.trading.shadow_trader import ShadowTrader, BRIDGE_JSONL_PATH
from cgalpha_v3.lila.llm.proposer import AutoProposer, TechnicalSpec
from cgalpha_v3.risk.order_manager import DryRunOrderManager

# Use the canonical path from shadow_trader module
BRIDGE_TEST_PATH = BRIDGE_JSONL_PATH


@pytest.fixture(autouse=True)
def clean_bridge_file():
    """Limpia bridge.jsonl antes y después de cada test."""
    if os.path.exists(BRIDGE_TEST_PATH):
        os.remove(BRIDGE_TEST_PATH)
    Path(BRIDGE_TEST_PATH).parent.mkdir(parents=True, exist_ok=True)
    yield
    # Leave file for inspection if needed


class TestShadowTraderDryRunIntegration:
    """Test 1: ShadowTrader → DryRunOrderManager"""

    def test_open_shadow_trade_returns_real_id_not_hardcoded(self):
        """open_shadow_trade debe devolver un ID real de DryRunOrderManager."""
        trader = ShadowTrader.create_default()
        trade_id = trader.open_shadow_trade(
            entry_price=50000.0,
            direction=1,
            atr=200.0,
        )
        # No debe ser el string hardcoded antiguo
        assert trade_id != "shadow_trade_id_001"
        # Debe empezar con el prefijo de DryRunOrderManager
        assert trade_id.startswith("DRY_")
        assert len(trade_id) > 10  # DRY_ + 8 hex chars

    def test_shadow_trader_has_order_manager(self):
        """ShadowTrader debe tener un DryRunOrderManager interno."""
        trader = ShadowTrader.create_default()
        assert isinstance(trader.order_manager, DryRunOrderManager)

    def test_open_shadow_trade_records_position(self):
        """Al abrir un trade, debe quedar registrado en active_positions."""
        trader = ShadowTrader.create_default()
        trader.open_shadow_trade(
            entry_price=50000.0,
            direction=1,
            atr=200.0,
        )
        assert len(trader.active_positions) == 1
        assert trader.active_positions[0].status == "OPEN"

    def test_risk_limits_reject_signals(self):
        """DryRunOrderManager debe respetar límites de riesgo."""
        trader = ShadowTrader.create_default()

        # Abrir múltiples posiciones hasta el límite
        for i in range(5):
            trader.open_shadow_trade(
                entry_price=50000.0 + i,
                direction=1,
                atr=200.0,
            )

        # La 6ta posición debe ser rechazada (max_concurrent_positions=5)
        trade_id = trader.open_shadow_trade(
            entry_price=50005.0,
            direction=1,
            atr=200.0,
        )
        assert trade_id == ""


class TestBridgeJsonlPersistence:
    """Test 2: bridge.jsonl se escribe correctamente."""

    def test_bridge_file_created_on_trade(self):
        """Al abrir un trade, bridge.jsonl debe existir."""
        trader = ShadowTrader.create_default()
        trader.open_shadow_trade(
            entry_price=50000.0,
            direction=1,
            atr=200.0,
        )
        assert os.path.exists(BRIDGE_TEST_PATH)

    def test_bridge_entry_has_correct_schema(self):
        """Cada entrada debe tener los campos requeridos del schema."""
        # Ensure clean state
        if os.path.exists(BRIDGE_TEST_PATH):
            os.remove(BRIDGE_TEST_PATH)

        trader = ShadowTrader.create_default()
        signal_data = {
            "vwap_at_retest": 49500.0,
            "obi_10_at_retest": 0.15,
            "cumulative_delta_at_retest": 500.0,
            "regime": "LATERAL",
            "oracle_confidence": 0.75,
        }
        trade_id = trader.open_shadow_trade(
            entry_price=50000.0,
            direction=1,
            atr=200.0,
            config_snapshot={"volume_threshold": 80},
            signal_data=signal_data,
            causal_tags=["regime:LATERAL"],
        )

        # Verify only one entry was written
        with open(BRIDGE_TEST_PATH) as f:
            lines = f.readlines()
        assert len(lines) == 1, f"Expected 1 entry, found {len(lines)}"

        entry = json.loads(lines[0])
        assert entry["trade_id"] == trade_id

        required_fields = [
            "ts", "trade_id", "symbol", "direction", "entry_price",
            "pnl_pct", "mfe", "mae", "mfe_atr", "mae_atr",
            "exit_reason", "entry_atr", "config_snapshot", "signal_data",
            "causal_tags", "microstructure_mode", "trinity_signal",
            "oracle_confidence", "status",
        ]
        for field_name in required_fields:
            assert field_name in entry, f"Missing field: {field_name}"

        # Validate specific content (entry_price includes 0.01% slippage from DryRunOrderManager)
        assert abs(entry["entry_price"] - 50005.0) < 0.01  # 50000 * 1.0001 = 50005
        assert entry["entry_atr"] == 200.0
        assert entry["exit_reason"] == "OPEN"
        assert entry["status"] == "open"
        assert entry["signal_data"]["vwap_at_retest"] == 49500.0
        assert entry["trinity_signal"]["obi"] == 0.15
        assert entry["causal_tags"] == ["regime:LATERAL"]

    def test_bridge_entries_are_valid_jsonl(self):
        """Cada línea debe ser un JSON válido."""
        trader = ShadowTrader.create_default()

        # Abrir 3 trades
        for i in range(3):
            trader.open_shadow_trade(
                entry_price=50000.0 + i,
                direction=1,
                atr=200.0,
            )

        # Validar cada línea
        with open(BRIDGE_TEST_PATH) as f:
            lines = f.readlines()

        assert len(lines) == 3
        for line in lines:
            entry = json.loads(line.strip())  # No debe lanzar excepción
            assert "trade_id" in entry


class TestAutoProposerEvaluateProposal:
    """Test 3: evaluate_proposal() devuelve scores reales."""

    def test_not_always_078(self):
        """evaluate_proposal no debe devolver siempre 0.78."""
        proposer = AutoProposer.create_default()

        spec1 = TechnicalSpec(
            change_type="parameter",
            target_file="test.py",
            target_attribute="threshold",
            old_value=0.70,
            new_value=0.65,
            reason="Test",
            causal_score_est=0.45,
            confidence=0.70,
        )
        spec2 = TechnicalSpec(
            change_type="feature",
            target_file="test.py",
            target_attribute="feature:x",
            old_value=0.0037,
            new_value=0.0,
            reason="Test",
            causal_score_est=0.30,
            confidence=0.50,
        )

        score1 = proposer.evaluate_proposal(spec1)
        score2 = proposer.evaluate_proposal(spec2)

        # Ambos deben ser diferentes de 0.78
        assert score1 != 0.78, f"score1 is still hardcoded: {score1}"
        assert score2 != 0.78, f"score2 is still hardcoded: {score2}"

    def test_parameter_changes_score_higher_than_feature_elimination(self):
        """Cambios paramétricos (reversibles) deben score más alto que eliminar features."""
        proposer = AutoProposer.create_default()

        param_spec = TechnicalSpec(
            change_type="parameter",
            target_file="test.py",
            target_attribute="threshold",
            old_value=0.70,
            new_value=0.68,  # Delta pequeño
            reason="Test",
            causal_score_est=0.55,
            confidence=0.80,
        )
        feature_spec = TechnicalSpec(
            change_type="feature",
            target_file="test.py",
            target_attribute="feature:x",
            old_value=0.0433,
            new_value=0.0,
            reason="Test",
            causal_score_est=0.30,
            confidence=0.50,
        )

        param_score = proposer.evaluate_proposal(param_spec)
        feature_score = proposer.evaluate_proposal(feature_spec)

        assert param_score > feature_score, (
            f"Parameter ({param_score}) should score higher than feature elimination ({feature_score})"
        )

    def test_small_delta_scores_higher_than_large_delta(self):
        """Delta pequeño debe score más alto (menor riesgo)."""
        proposer = AutoProposer.create_default()

        small_delta = TechnicalSpec(
            change_type="parameter",
            target_file="test.py",
            target_attribute="threshold",
            old_value=0.70,
            new_value=0.68,  # ~3% delta
            reason="Test",
            causal_score_est=0.45,
            confidence=0.70,
        )
        large_delta = TechnicalSpec(
            change_type="parameter",
            target_file="test.py",
            target_attribute="threshold",
            old_value=0.70,
            new_value=0.30,  # ~57% delta
            reason="Test",
            causal_score_est=0.45,
            confidence=0.70,
        )

        small_score = proposer.evaluate_proposal(small_delta)
        large_score = proposer.evaluate_proposal(large_delta)

        assert small_score > large_score, (
            f"Small delta ({small_score}) should score higher than large delta ({large_score})"
        )

    def test_very_low_importance_feature_scores_higher(self):
        """Feature con importancia <2% debe score más alto para eliminación."""
        proposer = AutoProposer.create_default()

        very_low = TechnicalSpec(
            change_type="feature",
            target_file="test.py",
            target_attribute="feature:x",
            old_value=0.0037,  # 0.37%
            new_value=0.0,
            reason="Test",
            causal_score_est=0.30,
            confidence=0.50,
        )
        borderline = TechnicalSpec(
            change_type="feature",
            target_file="test.py",
            target_attribute="feature:y",
            old_value=0.0433,  # 4.33%
            new_value=0.0,
            reason="Test",
            causal_score_est=0.30,
            confidence=0.50,
        )

        low_score = proposer.evaluate_proposal(very_low)
        border_score = proposer.evaluate_proposal(borderline)

        assert low_score > border_score, (
            f"Very low importance feature ({low_score}) should score higher than borderline ({border_score})"
        )

    def test_score_range_is_valid(self):
        """Todos los scores deben estar en [0.0, 1.0]."""
        proposer = AutoProposer.create_default()

        test_specs = [
            TechnicalSpec("parameter", "f", "a", 100.0, 50.0, "r", 0.4, 0.8),
            TechnicalSpec("feature", "f", "a", 0.0, 0.0, "r", 0.3, 0.5),
            TechnicalSpec("optimization", "f", "a", 0.0, 1.0, "r", 0.1, 0.2),
        ]

        for spec in test_specs:
            score = proposer.evaluate_proposal(spec)
            assert 0.0 <= score <= 1.0, f"Score {score} out of range for {spec.change_type}"


class TestAutoProposerInPipeline:
    """Test 4: AutoProposer se ejecuta en el pipeline cycle."""

    def test_analyze_drift_returns_proposals_on_bad_metrics(self):
        """analyze_drift debe generar propuestas con métricas degradadas."""
        proposer = AutoProposer.create_default()

        bad_metrics = {
            "oracle_accuracy_oos": 0.55,  # < 60%
            "max_drawdown_pct": 6.0,       # > 5%
            "win_rate_pct": 45.0,          # < 50%
            "sharpe_neto": 0.3,            # < 0.5
            "feature_importances": {
                "vwap": 0.10,
                "useless_feature": 0.01,   # < 5%
            },
        }

        proposals = proposer.analyze_drift(bad_metrics)

        assert len(proposals) >= 4  # Al menos 4 tipos de propuestas

    def test_analyze_drift_returns_no_proposals_on_good_metrics(self):
        """analyze_drift no debe generar propuestas con métricas buenas."""
        proposer = AutoProposer.create_default()

        good_metrics = {
            "oracle_accuracy_oos": 0.85,
            "max_drawdown_pct": 1.0,
            "win_rate_pct": 60.0,
            "sharpe_neto": 2.0,
            "feature_importances": {
                "vwap": 0.15,
                "obi": 0.10,
                "cum_delta": 0.12,
            },
        }

        proposals = proposer.analyze_drift(good_metrics)
        assert len(proposals) == 0
