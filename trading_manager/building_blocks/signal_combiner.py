import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class SignalScorer:
    """Evaluador de calidad de señales."""
    
    @staticmethod
    def score_signal(
        row: pd.Series, 
        zone_weight: float = 0.5, 
        trend_weight: float = 0.5
    ) -> float:
        """
        Calcula un puntaje de calidad (0.0 - 1.0).
        - Calidad de Zona: Basada en cuántas veces se respetó (no implementado en V1, asumimos 1.0 si existe)
        - Calidad de Tendencia: Basada en R-Squared
        """
        # Score de Tendencia (R^2 directo)
        trend_score = row.get('trend_r_squared', 0.0)
        
        # Score de Zona (Simple: existe o no)
        zone_score = 1.0 if row.get('in_accumulation_zone', False) else 0.0
        
        # Combinación ponderada
        final_score = (zone_score * zone_weight) + (trend_score * trend_weight)
        return round(final_score, 2)


class SignalCombiner:
    """
    Fusiona señales de múltiples detectores para validar la 'Triple Coincidencia'.
    Lógica: Vela Clave + Zona de Acumulación + Tendencia Favorable.
    """

    @staticmethod
    def combine_signals(
        df: pd.DataFrame,
        tolerance_bars: int = 8,
        min_r_squared: float = 0.45
    ) -> pd.DataFrame:
        """
        Detecta la Triple Coincidencia.
        
        Condiciones:
        1. Vela Clave detectada en barra actual.
        2. Zona de Acumulación activa (o reciente dentro de 'tolerance').
        3. Tendencia:
           - Si Reversión: Dirección opuesta a vela clave (ya manejado en key_candle).
           - Calidad (R^2) > min_r_squared (para asegurar que no es ruido puro).
           
        Args:
            df: DataFrame con resultados de detectores previos.
            tolerance_bars: Ventana de tolerancia para la coincidencia de zona.
            min_r_squared: Calidad mínima de tendencia requerida.
            
        Returns:
            DataFrame con 'is_triple_coincidence', 'final_score'.
        """
        required_cols = [
            'is_key_candle', 'in_accumulation_zone', 
            'trend_r_squared', 'trend_direction'
        ]
        
        # Validación de columnas
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            logger.warning(f"Faltan columnas para SignalCombiner: {missing}")
            return df
            
        # 1. Expandir la influencia de la Zona (Tolerancia)
        # Si hubo zona hace poco, todavía cuenta.
        df['zone_active_window'] = df['in_accumulation_zone'].rolling(
            window=tolerance_bars, min_periods=1
        ).max().astype(bool)
        
        # 2. Verificar condiciones
        # Condición A: Tenemos una vela clave
        cond_candle = df['is_key_candle']
        
        # Condición B: Estamos en (o cerca de) una zona de acumulación
        cond_zone = df['zone_active_window']
        
        # Condición C: La tendencia tiene estructura mínima (R^2 suficiente)
        # Esto filtra "Key Candles" en medio del ruido absoluto
        cond_trend_structure = df['trend_r_squared'] >= min_r_squared
        
        # Lógica de Triple Coincidencia
        df['is_triple_coincidence'] = cond_candle & cond_zone & cond_trend_structure
        
        # 3. Calcular Score
        # Solo para las coincidencias (o para todas si se desea análisis)
        df['final_score'] = df.apply(SignalScorer.score_signal, axis=1)
        
        # Forzar score 0 si no es coincidencia (opcional, pero limpio)
        # df.loc[~df['is_triple_coincidence'], 'final_score'] = 0.0
        
        matches = df['is_triple_coincidence'].sum()
        logger.info(f"Triple Coincidencia detectadas: {matches}")
        
        return df
