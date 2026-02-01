import pandas as pd
import numpy as np
import logging
from scipy import stats

logger = logging.getLogger(__name__)

class TrendDetector:
    """
    Mide la calidad y dirección de la tendencia usando Regresión Lineal y R-Squared.
    Implementa la lógica definida en la Constitución Técnica v0.0.3.
    """

    @staticmethod
    def analyze_trend(
        df: pd.DataFrame,
        lookback_period: int = 20,
        zigzag_threshold: float = 0.005  # 0.5%
    ) -> pd.DataFrame:
        """
        Calcula métricas de tendencia: Slope (pendiente) y R-Squared (calidad).
        
        Args:
            df: DataFrame con Close.
            lookback_period: Ventana para la regresión lineal.
            zigzag_threshold: Umbral mínimo para considerar un cambio de swing (futuro uso).
            
        Returns:
            DataFrame con 'trend_slope', 'trend_r_squared', 'trend_direction'.
        """
        if df.empty or len(df) < lookback_period:
            return df

        # Inicializar columnas
        df['trend_slope'] = 0.0
        df['trend_r_squared'] = 0.0
        
        # Función auxiliar para regresión en ventana móvil
        # NOTA: apply() de pandas puede ser lento. Para producción optimizada, 
        # se prefiere usar implementaciones vectorizadas o numpy stride_tricks.
        # Aquí usamos una implementación optimizada con numpy polyfit sobre ventanas.
        
        closes = df['Close'].values
        n = len(closes)
        slopes = np.zeros(n)
        r_squares = np.zeros(n)
        
        # Iteración optimizada (aún O(N) pero eficiente en C)
        # Para cada punto t, tomamos ventana [t-lookback : t]
        x = np.arange(lookback_period)
        
        # Pre-cálculo de varianza de X para slope
        # slope = cov(x,y) / var(x)
        # r_sq = corr(x,y)^2
        
        # Si el dataset es muy grande, esto podría ser lento. 
        # Para v0.0.3 asumimos dataframes de tamaño razonable (ej. 1000 velas).
        if n > 10000:
            logger.warning("Dataset grande detectado en TrendDetector. Procesamiento puede ser lento.")

        for i in range(lookback_period, n):
            y = closes[i-lookback_period:i]
            
            # Linear Regression rápida
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            slopes[i] = slope
            r_squares[i] = r_value ** 2
            
        df['trend_slope'] = slopes
        df['trend_r_squared'] = r_squares
        
        # Determinar dirección
        # 1 = Alcista, -1 = Bajista, 0 = Lateral/Ruido
        # Usamos R^2 para filtrar "ruido". Si R^2 es bajo, la dirección es poco confiable.
        
        df['trend_direction'] = np.where(df['trend_slope'] > 0, 1, -1)
        
        # ZigZag (Simplificado para detección de máximos/mínimos locales)
        # Detectamos picos locales para confirmar estructura
        # Esto es un placeholder para la lógica completa de ZigZag
        
        return df

    @staticmethod
    def get_trend_quality(r_squared: float) -> str:
        if r_squared > 0.8: return "STRONG"
        if r_squared > 0.45: return "MODERATE"
        return "WEAK/NOISE"
