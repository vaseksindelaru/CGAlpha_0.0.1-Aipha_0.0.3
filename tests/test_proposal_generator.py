"""
Tests para el ProposalGenerator de Code Craft Sage - Fase 6.

Este archivo contiene tests unitarios para verificar que el ProposalGenerator
funciona correctamente y genera propuestas basadas en reglas heurísticas.
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime

from cgalpha.codecraft.proposal_generator import ProposalGenerator, THRESHOLDS


class TestProposalGenerator:
    """Tests para la clase ProposalGenerator."""
    
    def test_initialization(self):
        """Verifica que el ProposalGenerator se inicializa correctamente."""
        generator = ProposalGenerator()
        
        assert generator.data_dir == Path("aipha_memory")
        assert generator.min_confidence == 0.70
    
    def test_generate_proposal_id(self):
        """Verifica que se genera un ID único."""
        generator = ProposalGenerator()
        
        proposal_id = generator.generate_proposal_id()
        
        assert proposal_id.startswith("AUTO_PROP_")
        assert len(proposal_id) == 30  # AUTO_PROP_YYYYMMDD_HHMMSS_XXXX
    
    def test_analyze_performance_with_dummy_data(self):
        """Verifica que se generan propuestas con datos dummy."""
        generator = ProposalGenerator()
        
        proposals = generator.analyze_performance()
        
        # Con datos dummy, debería generar al menos una propuesta
        assert isinstance(proposals, list)
    
    def test_proposal_structure(self):
        """Verifica la estructura de una propuesta."""
        generator = ProposalGenerator()
        
        proposals = generator.analyze_performance()
        
        if proposals:
            prop = proposals[0]
            
            # Verificar campos requeridos
            assert "proposal_id" in prop
            assert "proposal_text" in prop
            assert "reason" in prop
            assert "confidence" in prop
            assert "source" in prop
            assert "severity" in prop
    
    def test_proposal_id_format(self):
        """Verifica el formato del ID de propuesta."""
        generator = ProposalGenerator()
        
        proposal_id = generator.generate_proposal_id()
        
        # Formato: AUTO_PROP_YYYYMMDD_HHMMSS_XXXX
        parts = proposal_id.split("_")
        assert len(parts) == 5
        assert parts[0] == "AUTO"
        assert parts[1] == "PROP"
        # parts[2] es YYYYMMDD
        # parts[3] es HHMMSS
        # parts[4] es suffix de 4 chars
    
    def test_confidence_threshold(self):
        """Verifica que las propuestas tienen confianza >= min_confidence."""
        generator = ProposalGenerator(min_confidence=0.70)
        
        proposals = generator.analyze_performance()
        
        for prop in proposals:
            assert prop["confidence"] >= generator.min_confidence
    
    def test_empty_proposals_when_metrics_good(self):
        """Verifica que no se generan propuestas si las métricas están bien."""
        # Crear generator con datos de métricas buenas
        generator = ProposalGenerator.__new__(ProposalGenerator)
        generator.data_dir = Path(tempfile.mkdtemp())
        generator.min_confidence = 0.70
        
        # Crear archivo de estado con métricas perfectas
        state = {
            "win_rate": 0.60,  # Por encima del target
            "max_drawdown": 0.05,  # Por debajo del máximo
            "total_trades": 100,
            "test_coverage": 0.90  # Por encima del mínimo
        }
        
        # Guardar archivo
        generator.current_state_path = generator.data_dir / "operational" / "current_state.json"
        generator.current_state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(generator.current_state_path, 'w') as f:
            json.dump(state, f)
        
        # No crear bridge.jsonl para que use lista vacía
        generator.bridge_path = generator.data_dir / "evolutionary" / "bridge.jsonl"
        
        # Analizar
        proposals = generator._analyze_current_state(state)
        
        # No debería generar propuestas con métricas perfectas
        assert len(proposals) == 0


class TestProposalGeneratorHeuristics:
    """Tests para las reglas heurísticas del ProposalGenerator."""
    
    def test_low_win_rate_proposal(self):
        """Verifica propuesta cuando Win Rate está bajo."""
        generator = ProposalGenerator.__new__(ProposalGenerator)
        generator.data_dir = Path(tempfile.mkdtemp())
        generator.min_confidence = 0.70
        
        state = {
            "win_rate": 0.35,  # Por debajo del crítico
            "max_drawdown": 0.10,
            "total_trades": 100,
            "test_coverage": 0.85
        }
        
        proposals = generator._analyze_current_state(state)
        
        # Debe generar propuesta de Win Rate
        win_rate_props = [p for p in proposals if "confidence_threshold" in p["proposal_text"]]
        assert len(win_rate_props) >= 1
        
        prop = win_rate_props[0]
        assert prop["severity"] in ["high", "critical"]
        assert prop["confidence"] > 0.80
    
    def test_high_drawdown_proposal(self):
        """Verifica propuesta cuando Drawdown está alto."""
        generator = ProposalGenerator.__new__(ProposalGenerator)
        generator.data_dir = Path(tempfile.mkdtemp())
        generator.min_confidence = 0.70
        
        state = {
            "win_rate": 0.55,
            "max_drawdown": 0.22,  # Por encima del crítico
            "total_trades": 100,
            "test_coverage": 0.85
        }
        
        proposals = generator._analyze_current_state(state)
        
        # Debe generar propuesta de Drawdown
        drawdown_props = [p for p in proposals if "exposure" in p["proposal_text"].lower() or "position" in p["proposal_text"].lower()]
        assert len(drawdown_props) >= 1
    
    def test_low_test_coverage_proposal(self):
        """Verifica propuesta cuando Cobertura de tests está baja."""
        generator = ProposalGenerator.__new__(ProposalGenerator)
        generator.data_dir = Path(tempfile.mkdtemp())
        generator.min_confidence = 0.70
        
        state = {
            "win_rate": 0.55,
            "max_drawdown": 0.10,
            "total_trades": 100,
            "test_coverage": 0.70  # Por debajo del 80%
        }
        
        proposals = generator._analyze_current_state(state)
        
        # Debe generar propuesta de Coverage
        coverage_props = [p for p in proposals if "test" in p["proposal_text"].lower() or "coverage" in p["reason"].lower()]
        assert len(coverage_props) >= 1


class TestProposalGeneratorTradeHistory:
    """Tests para análisis de historial de trades."""
    
    def test_loss_streak_detection(self):
        """Verifica detección de racha de pérdidas."""
        generator = ProposalGenerator.__new__(ProposalGenerator)
        generator.data_dir = Path(tempfile.mkdtemp())
        generator.min_confidence = 0.70
        
        # Crear trades con racha de pérdidas
        trades = []
        for i in range(10):
            if i < 6:  # Primeros 6 trades son pérdidas
                trades.append({"profit": -100, "trade_id": f"TRADE_{i}"})
            else:
                trades.append({"profit": 100, "trade_id": f"TRADE_{i}"})
        
        proposals = generator._analyze_trade_history(trades)
        
        # Debe detectar la racha de pérdidas
        streak_props = [p for p in proposals if "streak" in p["reason"].lower() or "position" in p["proposal_text"].lower()]
        assert len(streak_props) >= 1
    
    def test_low_win_rate_from_history(self):
        """Verifica propuesta cuando Win Rate del historial está bajo."""
        generator = ProposalGenerator.__new__(ProposalGenerator)
        generator.data_dir = Path(tempfile.mkdtemp())
        generator.min_confidence = 0.70
        
        # Crear historial con Win Rate bajo (~35%)
        trades = []
        for i in range(50):
            if i % 3 == 0:  # ~33% win rate (wins on 0, 3, 6...)
                trades.append({"profit": 100, "trade_id": f"TRADE_{i}"})
            else:
                trades.append({"profit": -80, "trade_id": f"TRADE_{i}"})
        
        proposals = generator._analyze_trade_history(trades)
        
        # Debe generar propuesta de Win Rate
        win_rate_props = [p for p in proposals if "win rate" in p["reason"].lower() or "confidence" in p["proposal_text"].lower()]
        assert len(win_rate_props) >= 1


class TestThresholds:
    """Tests para los umbrales de configuración."""
    
    def test_win_rate_thresholds(self):
        """Verifica umbrales de Win Rate."""
        assert THRESHOLDS["win_rate"]["target"] == 0.50
        assert THRESHOLDS["win_rate"]["critical"] == 0.40
    
    def test_drawdown_thresholds(self):
        """Verifica umbrales de Drawdown."""
        assert THRESHOLDS["drawdown"]["max_acceptable"] == 0.15
        assert THRESHOLDS["drawdown"]["critical"] == 0.20
    
    def test_loss_streak_thresholds(self):
        """Verifica umbrales de racha de pérdidas."""
        assert THRESHOLDS["loss_streak"]["max_streak"] == 5
    
    def test_coverage_thresholds(self):
        """Verifica umbrales de cobertura."""
        assert THRESHOLDS["test_coverage"]["minimum"] == 0.80


class TestCLIIntegration:
    """Tests para integración con CLI."""
    
    def test_analyze_and_report_function(self):
        """Verifica la función de conveniencia analyze_and_report."""
        from cgalpha.codecraft.proposal_generator import analyze_and_report
        
        proposals = analyze_and_report()
        
        assert isinstance(proposals, list)


class TestDummyData:
    """Tests para datos dummy."""
    
    def test_dummy_state(self):
        """Verifica que se generan datos dummy de estado."""
        generator = ProposalGenerator.__new__(ProposalGenerator)
        generator.data_dir = Path(tempfile.mkdtemp())
        
        dummy_state = generator._get_dummy_state()
        
        assert isinstance(dummy_state, dict)
        assert "win_rate" in dummy_state
        assert "max_drawdown" in dummy_state
        assert "total_trades" in dummy_state
    
    def test_dummy_trades(self):
        """Verifica que se generan datos dummy de trades."""
        generator = ProposalGenerator.__new__(ProposalGenerator)
        generator.data_dir = Path(tempfile.mkdtemp())
        
        dummy_trades = generator._get_dummy_trades()
        
        assert isinstance(dummy_trades, list)
        assert len(dummy_trades) > 0
        
        # Verificar estructura de trade
        trade = dummy_trades[0]
        assert "trade_id" in trade
        assert "profit" in trade
