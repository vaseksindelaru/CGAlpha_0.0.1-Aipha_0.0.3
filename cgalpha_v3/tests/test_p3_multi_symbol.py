"""
CGAlpha v3 — P3.4 Multi-symbol Verification
===========================================
Valida la capacidad del sistema para ejecutar experimentos en múltiples 
activos (BTC, ETH, SOL) garantizando aislamiento de métricas y agregación coherente.
"""
from __future__ import annotations

import pytest
from cgalpha_v3.application.experiment_runner import ExperimentRunner, ExperimentResult
from cgalpha_v3.application.change_proposer import ChangeProposer
from cgalpha_v3.domain.models.signal import ApproachType


def _make_mock_data(symbol: str, n: int = 300) -> list[dict[str, Any]]:
    """Genera datos sintéticos específicos para un símbolo con retornos claros."""
    # Variamos un poco para diferenciar
    step = 5.0
    if symbol == "ETHUSDT": step = 8.0
    if symbol == "SOLUSDT": step = 15.0
    
    rows = []
    base = 1000.0 # Base baja para que % sea alto
    for i in range(n):
        rows.append({
            "open_time": 1700000000.0 + i * 300,
            "close_time": 1700000000.0 + (i + 1) * 300 - 1,
            "open": base + i * step,
            "high": base + i * step + 5,
            "low": base + i * step - 5,
            "close": base + (i + 1) * step,
            "volume": 1000.0,
            "symbol": symbol
        })
    return rows


def test_p3_4_multi_symbol_pipeline():
    proposer = ChangeProposer()
    runner = ExperimentRunner()
    
    # 1. Crear propuesta multi-symbol
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    prop = proposer.create_proposal(
        hypothesis="Trend following validation across assets",
        approach_types_targeted=[ApproachType.TOUCH],
        symbols=symbols
    )
    
    assert prop.symbols == symbols
    
    results: dict[str, ExperimentResult] = {}
    
    # 2. Ejecutar serie de experimentos aislados
    for sym in symbols:
        data = _make_mock_data(sym)
        res = runner.run_experiment(prop, data, symbol=sym)
        results[sym] = res
        
        # Validar que el resultado capturó el símbolo correcto
        assert res.symbol == sym
        assert res.metrics["net_return_pct"] != 0 # Debe haber operado
    
    # 3. Verificar aislamiento: Las métricas finales deben diferir ligeramente (por el factor mock)
    # En este mock simple, los retornos son similares porque la pendiente es 1.0, 
    # pero el precio absoluto cambia. El ROI pct (((curr - prev)/prev)) será diferente.
    # BTC: (50005-50000)/50000 = 0.01%
    # ETH: (25005-25000)/25000 = 0.02%
    # SOL: (5005-5000)/5000 = 0.1%
    
    returns = {s: r.metrics["net_return_pct"] for s, r in results.items()}
    assert returns["BTCUSDT"] < returns["ETHUSDT"] < returns["SOLUSDT"]
    
    # 4. Verificación de robustez (Promoción conjunta mock)
    # Si quisiéramos promover solo si todos son > 0
    all_positive = all(r.metrics["net_return_pct"] > 0 for r in results.values())
    assert all_positive is True


def test_p3_4_individual_symbol_execution_from_api_context():
    """Simula lo que haría el gui/server.py al recibir una petición multi-symbol."""
    runner = ExperimentRunner()
    proposer = ChangeProposer()
    
    prop = proposer.create_proposal(
        hypothesis="Multi-symbol API test",
        approach_types_targeted=[ApproachType.REJECTION],
        symbols=["BTCUSDT", "ETHUSDT"]
    )
    
    # El servidor típicamente ejecuta uno por uno basándose en la lista de la propuesta
    for sym in prop.symbols:
        data = _make_mock_data(sym, n=100)
        res = runner.run_experiment(prop, data, symbol=sym)
        assert res.symbol == sym
        assert res.proposal_id == prop.proposal_id
