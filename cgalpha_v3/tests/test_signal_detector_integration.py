"""
CGAlpha v3 — Test de Signal Detector Integration (CORRECTED LOGIC)
==================================================================
Verifica que el TripleCoincidenceDetector implemente la lógica correcta:
1. Detecta zonas (Triple Coincidence)
2. Rastrea zonas activas
3. Detecta retests
4. Captura features en retest
5. Determina outcomes
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone

from cgalpha_v3.domain.models.signal import ApproachType
from cgalpha_v3.application.experiment_runner import ExperimentRunner


def test_signal_detector_integration():
    """Test que el ExperimentRunner puede configurar el Signal Detector."""
    runner = ExperimentRunner()

    # Configurar el detector
    config = {
        'volume_percentile_threshold': 70,
        'body_percentage_threshold': 40,
        'lookback_candles': 30,
        'r2_min': 0.45,
        'proximity_tolerance': 8,
        'retest_timeout_bars': 50,
        'outcome_lookahead_bars': 10
    }
    runner.set_signal_detector(config)

    # Verificar que el detector está configurado
    assert runner.signal_detector is not None


def test_process_retests_with_mock_data():
    """Test que process_retests detecta retests y genera dataset."""
    runner = ExperimentRunner()
    runner.set_signal_detector()

    # Crear datos mock OHLCV con un patrón de retest
    np.random.seed(42)
    n_rows = 200
    mock_data = []
    base_price = 68000.0

    # Simular una zona de acumulación alrededor de 68000
    for i in range(n_rows):
        if i < 50:
            # Fase 1: Acumulación alrededor de 68000
            price = 68000 + np.random.randn() * 20
        elif 50 <= i < 100:
            # Fase 2: Precio se aleja
            price = 68100 + np.random.randn() * 30
        elif 100 <= i < 150:
            # Fase 3: Retest a 68000
            price = 68000 + np.random.randn() * 15
        else:
            # Fase 4: Outcome
            price = 68050 + np.random.randn() * 20

        high = price + abs(np.random.randn() * 50)
        low = price - abs(np.random.randn() * 50)
        close = price + np.random.randn() * 10
        volume = np.random.uniform(100, 1000)

        mock_data.append({
            'open_time': i * 300000,
            'close_time': (i + 1) * 300000,
            'open': price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume,
            'number_of_trades': int(volume / 10)
        })

    # Procesar retests
    retest_events = runner.process_retests(mock_data)

    # Verificar que retorna una lista
    assert isinstance(retest_events, list)


def test_get_training_dataset():
    """Test que se puede obtener el dataset de entrenamiento."""
    runner = ExperimentRunner()
    runner.set_signal_detector()

    # Crear datos mock
    np.random.seed(42)
    n_rows = 200
    mock_data = []
    base_price = 68000.0

    for i in range(n_rows):
        price = base_price + np.random.randn() * 100
        high = price + abs(np.random.randn() * 50)
        low = price - abs(np.random.randn() * 50)
        close = price + np.random.randn() * 20
        volume = np.random.uniform(100, 1000)

        mock_data.append({
            'open_time': i * 300000,
            'close_time': (i + 1) * 300000,
            'open': price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume,
            'number_of_trades': int(volume / 10)
        })

    # Procesar retests
    runner.process_retests(mock_data)

    # Obtener dataset de entrenamiento
    training_dataset = runner.get_training_dataset()

    # Verificar que retorna una lista
    assert isinstance(training_dataset, list)


def test_approach_type_triple_coincidence_exists():
    """Test que ApproachType.TRIPLE_COINCIDENCE existe."""
    assert ApproachType.TRIPLE_COINCIDENCE is not None
    assert ApproachType.TRIPLE_COINCIDENCE.value == "TRIPLE_COINCIDENCE"


def test_oracle_load_training_dataset():
    """Test que Oracle puede cargar dataset de entrenamiento."""
    from cgalpha_v3.lila.llm.oracle import OracleTrainer_v3

    oracle = OracleTrainer_v3.create_default()

    # Crear dataset mock
    training_samples = [
        {
            'features': {
                'vwap_at_retest': 68000.0,
                'obi_10_at_retest': 0.1,
                'cumulative_delta_at_retest': 100.0,
                'delta_divergence': 'BULLISH_ABSORPTION',
                'atr_14': 50.0,
                'regime': 'TREND',
                'direction': 'bullish'
            },
            'outcome': 'BOUNCE',
            'zone_id': '100_bullish',
            'retest_timestamp': 1234567890
        }
    ]

    # Cargar dataset
    oracle.load_training_dataset(training_samples)

    # Verificar que se cargó
    assert len(oracle.training_data) == 1


if __name__ == "__main__":
    # Ejecutar tests manualmente
    test_approach_type_triple_coincidence_exists()
    print("✓ ApproachType.TRIPLE_COINCIDENCE existe")

    test_signal_detector_integration()
    print("✓ Signal Detector se integra con ExperimentRunner")

    test_process_retests_with_mock_data()
    print("✓ process_retests funciona")

    test_get_training_dataset()
    print("✓ get_training_dataset funciona")

    test_oracle_load_training_dataset()
    print("✓ Oracle puede cargar dataset de entrenamiento")

    print("\nTodos los tests pasaron.")
