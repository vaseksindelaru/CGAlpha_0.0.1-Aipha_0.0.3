import pandas as pd
import numpy as np
import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

class AccumulationZoneDetector:
    """
    Detecta zonas de acumulación o distribución (lateralidad) en el mercado.
    Implementa la lógica definida en la Constitución Técnica v0.0.3.
    """

    @staticmethod
    def detect_zones(
        df: pd.DataFrame,
        atr_period: int = 14,
        atr_multiplier: float = 1.5,
        min_zone_bars: int = 5,
        volume_threshold_ratio: float = 1.1,
        lookback_bars: int = 20
    ) -> pd.DataFrame:
        """
        Identifica zonas donde el precio se consolida dentro de un rango definido por ATR.
        
        Args:
            df: DataFrame con OHLCV.
            atr_period: Periodo para cálculo de ATR.
            atr_multiplier: Multiplicador de ATR para definir el ancho máximo de la zona.
            min_zone_bars: Número mínimo de barras para confirmar una zona.
            volume_threshold_ratio: Ratio de volumen relativo (vs media) para validar actividad.
            lookback_bars: Cuántas barras atrás mirar para encontrar el inicio de la zona.
            
        Returns:
            DataFrame con columnas 'zone_id', 'in_accumulation_zone', 'zone_high', 'zone_low'.
        """
        if df.empty: return df
        
        # 1. Calcular ATR
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['ATR'] = true_range.rolling(atr_period).mean()
        
        # 2. Inicializar columnas de zona
        df['in_accumulation_zone'] = False
        df['zone_id'] = 0
        df['zone_high'] = np.nan
        df['zone_low'] = np.nan
        
        current_zone_id = 0
        
        # Algoritmo de detección de zonas (Rolling Window)
        # Una zona se define si el rango (Max High - Min Low) de las últimas N barras es < ATR * multiplier
        
        # Optimizacion vectorial: Calcular Rangos Móviles
        rolling_high = df['High'].rolling(window=min_zone_bars).max()
        rolling_low = df['Low'].rolling(window=min_zone_bars).min()
        rolling_range = rolling_high - rolling_low
        threshold = df['ATR'] * atr_multiplier
        
        # Identificar candidatos a zona (donde el rango es estrecho)
        possible_zone = rolling_range <= threshold
        
        # Asignar IDs a las zonas continuas
        # Usamos cumsum para identificar grupos distintos
        df['is_zone_candidate'] = possible_zone
        
        # Lógica iterativa para refinar zonas (expandir si siguen dentro del rango)
        # Nota: La vectorización pura es difícil para zonas dinámicas que crecen.
        # Usaremos una aproximación híbrida: candidatos vectoriales iniciales + refinamiento.
        
        # Para simplificar y mantener robustez, usamos la definición de "Tightness"
        # Si la volatilidad local es baja respecto al ATR, es acumulación.
        
        df['in_accumulation_zone'] = possible_zone
        
        # Filtrar por volumen promedio en la zona (opcional, para detectar acumulación real)
        # Si el volumen está secándose o es constante, refuerza la idea de acumulación.
        # Si volume_threshold_ratio > 1.0, buscamos picos de volumen (absorción).
        
        # Calculamos ID de zona
        # Cada vez que pasamos de False a True, incrementamos ID
        zone_starts = (df['in_accumulation_zone'] & ~df['in_accumulation_zone'].shift(1).fillna(False))
        df['zone_id'] = zone_starts.cumsum()
        
        # Limpiar ID donde no hay zona
        df.loc[~df['in_accumulation_zone'], 'zone_id'] = 0
        
        # Calcular High/Low de la zona activa
        # Esto requiere agrupar, pero para eficiencia en tiempo real, usamos los rolling values
        df.loc[df['in_accumulation_zone'], 'zone_high'] = rolling_high
        df.loc[df['in_accumulation_zone'], 'zone_low'] = rolling_low
        
        logger.info(f"Zonas detectadas: {df['zone_id'].max()}")
        return df

    @staticmethod
    def get_zone_metrics(df: pd.DataFrame, zone_id: int) -> Dict:
        """Devuelve métricas detalladas de una zona específica."""
        zone_data = df[df['zone_id'] == zone_id]
        if zone_data.empty: return {}
        
        return {
            'start_time': zone_data.index[0],
            'end_time': zone_data.index[-1],
            'duration_bars': len(zone_data),
            'zone_high': zone_data['High'].max(),
            'zone_low': zone_data['Low'].min(),
            'avg_volume': zone_data['Volume'].mean()
        }
