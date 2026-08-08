"""
CGAlpha v3 — P3.2 Advanced Temporal Suite
=========================================
Tests avanzados de consistencia temporal, gaps, outliers y leakage complejo.
"""
from __future__ import annotations

import random
import pytest
from datetime import datetime, timedelta, timezone
from cgalpha_v3.application.experiment_runner import ExperimentRunner, WalkForwardWindow
from cgalpha_v3.data_quality.gates import TemporalLeakageError, check_oos_leakage


def _make_rows(n: int, start_ts: float = 1700000000.0, step: float = 300.0, gap_after: int | None = None, gap_size: float = 0.0) -> list[dict[str, Any]]:
    rows = []
    curr = start_ts
    for i in range(n):
        rows.append({
            "open_time": curr,
            "close_time": curr + step - 1,
            "open": 100.0 + i,
            "high": 105.0 + i,
            "low": 95.0 + i,
            "close": 100.0 + i + 1,
            "volume": 1000.0,
        })
        curr += step
        if gap_after is not None and i == gap_after:
            curr += gap_size
    return rows


# --- P3.2 Temporal Ordering & Gaps ---

def test_temporal_ordering_shuffled_input():
    """Verifica que build_walk_forward_windows ordena antes de procesar."""
    runner = ExperimentRunner()
    rows = _make_rows(300)
    shuffled = list(rows)
    random.shuffle(shuffled)
    
    # Si no ordenara, los ts de las ventanas estarían mezclados
    windows = runner.build_walk_forward_windows(shuffled, windows=3)
    
    assert windows[0].train_start_ts < windows[0].oos_end_ts
    assert windows[0].oos_end_ts <= windows[1].train_start_ts
    assert windows[1].oos_end_ts <= windows[2].train_start_ts
    
    # ts absolutos deben ser iguales a los del set original ordenado
    assert windows[0].train_start_ts == rows[0]["open_time"]
    assert windows[2].oos_end_ts == rows[-1]["close_time"]


def test_temporal_gaps_resilience():
    """
    Verifica que el sistema maneja gaps en el tiempo sin romper 
    la estructura de ventanas (basada en índices).
    """
    runner = ExperimentRunner()
    # Gap de 1 día (86400s) después del registro 100
    rows_with_gap = _make_rows(300, gap_after=100, gap_size=86400.0)
    
    windows = runner.build_walk_forward_windows(rows_with_gap, windows=3)
    
    assert len(windows) == 3
    # Ventana 1 incluye el gap al final o Ventana 2 al inicio?
    # 300 / 3 = 100 por ventana. 
    # W1: 0-99. W2: 100-199. 
    # El gap ocurre DESPUÉS del 100 (índice 100).
    # W2 empieza en índice 100.
    
    gap_start = rows_with_gap[100]["close_time"]
    gap_end = rows_with_gap[101]["open_time"]
    assert gap_end - gap_start > 86000.0 # Más de un día
    
    # W2 debe reflejar el gap en sus ts
    assert windows[1].train_start_ts == rows_with_gap[100]["open_time"]


# --- P3.2 Complex Leakage Detection ---

def test_oos_leakage_complex_window_boundary():
    """
    Simula leakage justo en la frontera del OOS. 
    Si una feature en el instante final de train/val usa el ts inicial de OOS.
    """
    runner = ExperimentRunner()
    rows = _make_rows(300)
    windows = runner.build_walk_forward_windows(rows, windows=3)
    w1 = windows[0]
    
    # oos_start_ts = 1700030000.0 (ejemplo)
    # Si una feature en 'val' tiene ese ts, es leakage.
    feature_ts_leaked = [w1.oos_start_ts] * w1.validation_rows
    
    with pytest.raises(TemporalLeakageError, match="TemporalLeakageError"):
        check_oos_leakage(
            train_end_ts=w1.validation_end_ts,
            oos_start_ts=w1.oos_start_ts,
            feature_timestamps=feature_ts_leaked,
        )


def test_no_leakage_on_clean_data():
    """Verifica que datos limpios pasan sin error."""
    runner = ExperimentRunner()
    rows = _make_rows(300)
    windows = runner.build_walk_forward_windows(rows, windows=3)
    w1 = windows[0]
    
    # Todas las features en val tienen ts de val (antes de OOS)
    clean_ts = [w1.validation_start_ts] * w1.validation_rows
    
    # No debe alzar excepción
    check_oos_leakage(
        train_end_ts=w1.validation_end_ts,
        oos_start_ts=w1.oos_start_ts,
        feature_timestamps=clean_ts
    )


def test_oos_leakage_train_contamination():
    """Detecta si el set de entrenamiento usa datos del OOS."""
    runner = ExperimentRunner()
    rows = _make_rows(300)
    windows = runner.build_walk_forward_windows(rows, windows=3)
    w = windows[0]
    
    # El ts final del entrenamiento es contaminado con el ts inicial del OOS
    leaked_ts = [w.train_start_ts] * (w.train_rows - 1) + [w.oos_start_ts]
    
    with pytest.raises(TemporalLeakageError, match="TemporalLeakageError"):
        check_oos_leakage(
            train_end_ts=w.train_end_ts,
            oos_start_ts=w.oos_start_ts,
            feature_timestamps=leaked_ts
        )


# --- P3.2 Outliers & Edge Cases ---

def test_insufficient_rows_error():
    """Verifica fallo con menos de 10 filas por ventana (P1.9/P3.2)."""
    runner = ExperimentRunner()
    rows = _make_rows(25) # 25 / 3 = 8.3 rows per window < 10
    
    with pytest.raises(ValueError, match="insufficient_rows_for_walk_forward"):
        runner.build_walk_forward_windows(rows, windows=3)
