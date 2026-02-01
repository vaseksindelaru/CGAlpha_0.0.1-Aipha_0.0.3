import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class FeatureEngineer:
    """Extrae características (features) para el entrenamiento del Oráculo."""

    @staticmethod
    def extract_features(df: pd.DataFrame, t_events: pd.Index) -> pd.DataFrame:
        """
        Extrae un conjunto de características para cada evento detectado.
        
        Args:
            df: DataFrame OHLCV con las columnas calculadas por el detector.
            t_events: Índice de timestamps donde ocurrió una señal.
            
        Returns:
            DataFrame con las características para cada evento.
        """
        if t_events.empty:
            return pd.DataFrame()

        features_list = []
        
        for timestamp in t_events:
            if timestamp not in df.index:
                continue
            
            row = df.loc[timestamp]
            if isinstance(row, pd.DataFrame):
                row = row.iloc[0]
            
            # Características sugeridas
            features = {
                'body_percentage': row.get('body_percentage', 0),
                'volume_ratio': row['Volume'] / row['volume_threshold'] if 'volume_threshold' in row and row['volume_threshold'] > 0 else 1.0,
                'relative_range': (row['High'] - row['Low']) / row['Close'] if row['Close'] > 0 else 0,
                'hour_of_day': timestamp.hour
            }
            
            features_list.append(features)

        return pd.DataFrame(features_list, index=t_events)
