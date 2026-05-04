"""
Tests de Robustez para los scripts de Fix 6.
"""
import pytest
import json
import pandas as pd
import io
import zipfile
from pathlib import Path
from unittest.mock import patch, MagicMock

def create_mock_zip(csv_content: str):
    """Auxiliar para crear un buffer de ZIP válido para los tests."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("test.csv", csv_content)
    return buf.getvalue()

# --- Test 1: Threshold guard ---

def test_threshold_guard_fails_on_wrong_value(tmp_path, monkeypatch):
    """Si zigzag_threshold no es 0.0025, el script debe abortar."""
    import scripts.fix6_process_historical as fix6
    config = {
        'expected_threshold': '0.0030',
        'expected_threshold_label': '0.30%'
    }
    with pytest.raises(SystemExit) as exc:
        fix6.verify_threshold_guard(config)
    assert exc.value.code != 0

def test_threshold_guard_passes_on_correct_value():
    """Con threshold correcto, la guardia no aborta."""
    import scripts.fix6_process_historical as fix6
    config = {
        'expected_threshold': '0.0018',
        'expected_threshold_label': '0.18%'
    }
    fix6.verify_threshold_guard(config)

# --- Test 2: Modo degradado ---

def test_degraded_mode_continues_with_partial_data(monkeypatch):
    """Si algunos días fallan (403), el script continúa con los exitosos."""
    import scripts.fix6_historical_training as fix6
    
    valid_zip = create_mock_zip("1704067200000,70000.0,70100.0,69900.0,70050.0,100.0,1704067500000,0,0,0,0,0\n")
    
    call_count = 0
    def mock_download_day(url, timeout, max_retries, retry_delay):
        nonlocal call_count
        call_count += 1
        if call_count % 4 == 0:
            return None # Fallo
        return valid_zip

    monkeypatch.setenv("FIX6_DAYS", "10")
    monkeypatch.setenv("FIX6_MIN_SUCCESS_DAYS", "5")
    
    with patch("scripts.fix6_historical_training._download_single_day", side_effect=mock_download_day):
        with patch("pandas.DataFrame.to_csv"):
            result = fix6.download_historical()
    
    assert result is not None
    assert len(result) > 0

def test_degraded_mode_aborts_below_minimum(monkeypatch):
    """Si los días exitosos son menos que MIN_SUCCESS_DAYS, debe abortar."""
    import scripts.fix6_historical_training as fix6
    with patch("scripts.fix6_historical_training._download_single_day", return_value=None):
        monkeypatch.setenv("FIX6_DAYS", "5")
        monkeypatch.setenv("FIX6_MIN_SUCCESS_DAYS", "3")
        with pytest.raises(RuntimeError, match="Fracaso crítico"):
            fix6.download_historical()

# --- Test 3: Formato CSV ---

def test_malformed_csv_raises_error():
    """CSV con columnas incorrectas debe ser detectado."""
    import scripts.fix6_historical_training as fix6
    # ZIP con CSV de pocas columnas
    bad_zip = create_mock_zip("col1,col2\n1,2\n")
    with pytest.raises(ValueError, match="Formato CSV inválido"):
        fix6.process_csv_zip(bad_zip)

def test_valid_csv_processing():
    """ZIP con CSV de Binance se procesa correctamente."""
    import scripts.fix6_historical_training as fix6
    valid_zip = create_mock_zip("1704067200000,42000.0,42100.0,41900.0,42050.0,100.0,0,0,0,0,0,0\n")
    df = fix6.process_csv_zip(valid_zip)
    assert len(df) == 1
    assert df['close'].iloc[0] == 42050.0

# --- Test 4: Variables de Entorno ---

def test_env_variables_override_defaults(monkeypatch):
    """Las variables FIX6_* deben gobernar la configuración."""
    import scripts.fix6_historical_training as fix6
    monkeypatch.setenv("FIX6_SYMBOL", "ETHUSDT")
    monkeypatch.setenv("FIX6_DAYS", "45")
    config = fix6.get_config()
    assert config['symbol'] == "ETHUSDT"
    assert config['days'] == 45
