import pytest
import pandas as pd
import numpy as np
from cgalpha_v3.infrastructure.signal_detector.triple_coincidence import TripleCoincidenceDetector, ActiveZone

def test_clearance_instrumentation_robust():
    """
    Test robusto para la instrumentación:
    1. Inyecta una zona activa manualmente.
    2. Simula movimiento de precio.
    3. Verifica que los extremos se actualicen.
    4. Verifica el cálculo final en el TrainingSample.
    """
    detector = TripleCoincidenceDetector({})
    
    # Simular zona detectada en index 10
    zone = ActiveZone(
        candle_index=10,
        zone_top=10010.0,
        zone_bottom=9990.0,
        vwap_at_detection=10000.0,
        detection_timestamp=1000,
        direction='bullish',
        key_candle={'index': 10, 'close': 10005},
        accumulation_zone={},
        mini_trend={},
        atr_at_detection=20.0, # ATR de referencia
        max_price_since_detection=10005.0,
        min_price_since_detection=10005.0
    )
    detector.active_zones = [zone]
    
    # Datos para simular alejamiento (index 11)
    data = []
    # Llenar hasta index 10 (Por encima de la zona, sin inflar el max_price)
    for i in range(11):
        data.append({'high': 10015, 'low': 10012, 'close': 10015, 'volume': 100})
    
    # Velas de alejamiento (index 11, 12)
    data.append({'high': 10050.0, 'low': 10015.0, 'close': 10030.0, 'volume': 100})
    data.append({'high': 10100.0, 'low': 10040.0, 'close': 10070.0, 'volume': 100})
    
    # Vela de retest (index 13)
    data.append({'high': 10005.0, 'low': 10002.0, 'close': 10002.0, 'volume': 100})
    
    # Necesitamos outcome_lookahead_bars (10 por defecto) para cerrar el sample
    for i in range(15):
        data.append({'high': 10200, 'low': 10150, 'close': 10150, 'volume': 100})
        
    df = pd.DataFrame(data)
    
    # Procesar velas
    _ = detector.process_stream(df)
    
    # 1. Verificar seguimiento de extremos
    assert zone.max_price_since_detection == 10100.0
    
    # 2. Verificar TrainingSample
    samples = detector.get_training_dataset()
    assert len(samples) > 0
    
    # (10100 (max) - 10010 (top)) / 20 (atr) = 90 / 20 = 4.5
    expected_clearance = 4.5
    
    feature = samples[0].features
    assert feature['max_clearance_atr'] == expected_clearance


if __name__ == "__main__":
    test_clearance_instrumentation_robust()
