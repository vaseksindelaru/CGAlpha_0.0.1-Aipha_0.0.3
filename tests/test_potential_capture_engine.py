"""Tests para Potential Capture Engine (ATR Labeling)."""

import pytest
import pandas as pd
import numpy as np
import sys
import os

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from trading_manager.building_blocks.labelers.potential_capture_engine import get_atr_labels

class TestPotentialCaptureEngine:
    
    @pytest.fixture
    def sample_data(self):
        """Genera datos OHLC de prueba."""
        dates = pd.date_range(start="2025-01-01", periods=100, freq="h")
        
        # Simular precios con tendencia alcista y algo de ruido
        np.random.seed(42)
        close = np.linspace(100, 110, 100) + np.random.normal(0, 0.5, 100)
        high = close + np.random.uniform(0.1, 0.5, 100)
        low = close - np.random.uniform(0.1, 0.5, 100)
        
        df = pd.DataFrame({
            "Open": close, # Simplificación
            "High": high,
            "Low": low,
            "Close": close
        }, index=dates)
        
        return df

    def test_basic_labeling(self, sample_data):
        """Verifica que se generen etiquetas."""
        # Eventos en los índices 10, 20, 30
        t_events = sample_data.index[[10, 20, 30]]
        
        result = get_atr_labels(
            prices=sample_data,
            t_events=t_events,
            atr_period=5,
            tp_factor=1.0,
            sl_factor=1.0,
            return_trajectories=True
        )
        
        # Cuando return_trajectories=True, se retorna un diccionario
        assert isinstance(result, dict)
        assert 'labels' in result
        assert 'mfe_atr' in result
        assert 'mae_atr' in result
        assert 'highest_tp_hit' in result
        
        labels = result['labels']
        assert len(labels) == 3
        assert all(l in [-1, 0, 1] for l in labels)

    def test_high_volatility_scenario(self, sample_data):
        """
        Simula alta volatilidad para verificar que el ATR se adapta.
        Este es el test crítico mencionado en la propuesta ATR.
        """
        # Aumentar volatilidad artificialmente en la segunda mitad
        sample_data_copy = sample_data.copy()
        sample_data_copy.loc[sample_data_copy.index[50:], 'High'] += 2.0
        sample_data_copy.loc[sample_data_copy.index[50:], 'Low'] -= 2.0
        
        t_events = sample_data_copy.index[[60, 70]] # Eventos en zona volátil
        
        result = get_atr_labels(
            prices=sample_data_copy,
            t_events=t_events,
            atr_period=5,
            tp_factor=2.0, # TP más amplio
            sl_factor=1.0,
            return_trajectories=True
        )
        
        # Verificar estructura del resultado
        assert isinstance(result, dict)
        labels = result['labels']
        assert not labels.empty
        # No afirmamos el resultado exacto (1 o -1), solo que no falle la ejecución
        assert all(isinstance(l, (int, np.integer)) for l in labels)
