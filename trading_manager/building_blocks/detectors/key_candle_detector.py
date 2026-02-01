import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class SignalDetector:
    """Detecta señales basadas en características específicas de las velas."""

    @staticmethod
    def detect_key_candles(
        df: pd.DataFrame,
        volume_lookback: int = 50,
        volume_percentile_threshold: int = 80,
        body_percentile_threshold: int = 30,
        ema_period: int = 200,
        reversal_mode: bool = True
    ) -> pd.DataFrame:
        """
        Detecta 'velas clave' basadas en volumen inusual, cuerpo pequeño y tendencia.
        
        Args:
            df: DataFrame con columnas Open, High, Low, Close, Volume.
            volume_lookback: Periodo para calcular el percentil de volumen.
            volume_percentile_threshold: Percentil de volumen para considerar 'alto volumen'.
            body_percentile_threshold: Porcentaje máximo del cuerpo respecto al rango total.
            ema_period: Periodo para la Media Móvil Exponencial (filtro de tendencia).
            reversal_mode: Si es True, busca reversiones (señal contra tendencia).
                           Si es False, busca continuación (señal a favor de tendencia).
            
        Returns:
            DataFrame con la columna 'is_key_candle'.
        """
        if df.empty:
            logger.warning("DataFrame vacío recibido en detect_key_candles.")
            return df

        # Asegurar que las columnas necesarias existen
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_cols:
            if col not in df.columns:
                logger.error(f"Columna faltante: {col}")
                return df

        # 1. Calcular el umbral de volumen (percentil móvil)
        df['volume_threshold'] = df['Volume'].rolling(window=volume_lookback).apply(
            lambda x: np.percentile(x, volume_percentile_threshold)
        )

        # 2. Cálculos de tamaño de vela
        df['body_size'] = abs(df['Close'] - df['Open'])
        df['candle_range'] = df['High'] - df['Low']
        
        # Evitar división por cero
        df['body_percentage'] = np.where(
            df['candle_range'] > 0,
            (df['body_size'] / df['candle_range']) * 100,
            100
        )

        # 3. Filtro de Tendencia (EMA)
        df['ema'] = df['Close'].ewm(span=ema_period, adjust=False).mean()
        df['is_uptrend'] = df['Close'] > df['ema']

        # 4. Detección de la vela clave con alineación de tendencia (o reversión)
        is_bullish = df['Close'] >= df['Open']
        
        if reversal_mode:
            # Lógica de Reversión: Bullish en Downtrend, Bearish en Uptrend
            trend_alignment = (is_bullish != df['is_uptrend'])
        else:
            # Lógica de Continuación: Bullish en Uptrend, Bearish en Downtrend
            trend_alignment = (is_bullish == df['is_uptrend'])

        df['is_key_candle'] = (
            (df['Volume'] >= df['volume_threshold']) & 
            (df['body_percentage'] <= body_percentile_threshold) &
            trend_alignment
        )

        # 5. Determinar el lado de la señal (1 = Long, -1 = Short)
        df['signal_side'] = np.where(is_bullish, 1, -1)

        mode_str = "REVERSIÓN" if reversal_mode else "CONTINUACIÓN"
        logger.info(f"Detección completada ({mode_str}). Velas clave encontradas: {df['is_key_candle'].sum()}")
        return df
