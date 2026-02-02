import numpy as np
import pandas as pd

class KeyCandleDetector:
    @staticmethod
    def detect(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        df_res = df.copy()
        # Parámetros CORREGIDOS según configuración original
        vl = kwargs.get('volume_lookback', 50)  # CORRECCIÓN: 50 en lugar de 20
        vpt = kwargs.get('volume_percentile_threshold', 80)  # CORRECCIÓN: 80 en lugar de 90
        bpt = kwargs.get('body_percentile_threshold', 30)
        ema_period = kwargs.get('ema_period', 200)  # NUEVO: parámetro faltante
        
        # Calcular volumen threshold
        df_res["volume_threshold"] = df_res["volume"].rolling(window=vl, min_periods=vl).quantile(vpt/100).shift(1)
        
        # Calcular tamaño del cuerpo
        df_res["body_size"] = abs(df_res["close"] - df_res["open"])
        cr = df_res["high"] - df_res["low"]
        df_res["body_percentage"] = np.where(cr > 0, (df_res["body_size"] / cr) * 100, 100)
        
        # Calcular EMA para filtro de tendencia
        df_res["ema"] = df_res["close"].ewm(span=ema_period, adjust=False).mean()
        df_res["is_uptrend"] = df_res["close"] > df_res["ema"]
        
        # Condiciones para vela clave
        high_volume = df_res["volume"] >= df_res["volume_threshold"]
        small_body = df_res["body_percentage"] <= bpt
        
        df_res["is_key_candle"] = ((high_volume & small_body).fillna(False).astype(bool))
        
        return df_res


import pandas as pd
import pandas_ta as ta

class AccumulationZoneDetector:
    def __init__(self, **kwargs):
        self.config = {
            'atr_period': kwargs.get('atr_period', 14),
            'atr_multiplier': kwargs.get('atr_multiplier', 1.5),
            'min_zone_bars': kwargs.get('min_zone_bars', 5),
            'volume_ma_period': kwargs.get('volume_ma_period', 20),
            'volume_threshold': kwargs.get('volume_threshold', 1.1)
        }
    
    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        df_res = df.copy()
        df_res['atr'] = ta.atr(df_res['high'], df_res['low'], df_res['close'], length=self.config['atr_period'])
        df_res['volume_ma'] = df_res['volume'].rolling(window=self.config['volume_ma_period']).mean()
        df_res['in_accumulation_zone'] = False
        df_res['zone_id'] = pd.NA
        
        in_zone = False
        zone_start_idx, zone_id_counter = -1, 0
        zone_high, zone_low = 0.0, 0.0
        
        for i in range(len(df_res)):
            candle = df_res.iloc[i]
            if pd.isna(candle['atr']) or pd.isna(candle['volume_ma']):
                continue
            
            vol_ok = candle['volume'] >= candle['volume_ma'] * self.config['volume_threshold']
            
            if in_zone:
                current_high = max(zone_high, candle['high'])
                current_low = min(zone_low, candle['low'])
                zone_height = current_high - current_low
                max_h = df_res.loc[zone_start_idx, 'atr'] * self.config['atr_multiplier'] if pd.notna(df_res.loc[zone_start_idx, 'atr']) else float('inf')
                
                if zone_height > max_h:
                    if (i - 1 - zone_start_idx + 1) >= self.config['min_zone_bars']:
                        df_res.loc[zone_start_idx:i-1, 'in_accumulation_zone'] = True
                        df_res.loc[zone_start_idx:i-1, 'zone_id'] = zone_id_counter
                        zone_id_counter += 1
                    in_zone = False
            
            if not in_zone and vol_ok:
                in_zone, zone_start_idx, zone_high, zone_low = True, i, candle['high'], candle['low']
        
        if in_zone and (len(df_res) - zone_start_idx) >= self.config['min_zone_bars']:
            df_res.loc[zone_start_idx:len(df_res)-1, 'in_accumulation_zone'] = True
            df_res.loc[zone_start_idx:len(df_res)-1, 'zone_id'] = zone_id_counter
        
        df_res.drop(columns=['atr', 'volume_ma'], inplace=True, errors='ignore')
        df_res['zone_id'] = df_res['zone_id'].astype("Int64")
        return df_res


from typing import Any, List
from scipy.stats import linregress

class TrendDetector:
    def __init__(self, **kwargs: Any):
        self.config = {
            "lookback_period": kwargs.get("lookback_period", 20),  # NUEVO: parámetro faltante
            "zigzag_threshold": kwargs.get("zigzag_threshold", 0.005)  # CORRECCIÓN: 0.005 en lugar de 0.5
        }
    
    def _detect_zigzag_pivots(self, series: pd.Series) -> List[int]:
        pivots = [series.index[0]]
        trend = None
        last_pivot_val = series.iloc[0]
        last_pivot_idx = series.index[0]
        
        for idx, val in series.items():
            if trend is None:
                if abs(val / last_pivot_val - 1) * 100 >= self.config["zigzag_threshold"]:
                    trend = 'up' if val > last_pivot_val else 'down'
            elif trend == 'up':
                if val < last_pivot_val:
                    trend = 'down'
                    pivots.append(last_pivot_idx)
                if val >= last_pivot_val:
                    last_pivot_val = val
                    last_pivot_idx = idx
            elif trend == 'down':
                if val > last_pivot_val:
                    trend = 'up'
                    pivots.append(last_pivot_idx)
                if val <= last_pivot_val:
                    last_pivot_val = val
                    last_pivot_idx = idx
        
        if series.index[-1] not in pivots:
            pivots.append(series.index[-1])
        
        return sorted(list(set(pivots)))
    
    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        df_res = df.copy()
        
        if len(df_res) < 2:
            return df_res
        
        pivot_indices = self._detect_zigzag_pivots(df_res["close"])
        
        for col in ["trend_id", "trend_direction", "trend_slope", "trend_r_squared"]:
            df_res[col] = pd.NA if col != "trend_direction" else ""
        
        for i in range(len(pivot_indices) - 1):
            start, end = pivot_indices[i], pivot_indices[i+1]
            if start >= end:
                continue
            
            segment = df_res.loc[start:end]
            x = np.arange(len(segment))
            y = segment["close"].values
            
            if len(segment) < 2:
                continue
            
            slope, _, r_val, _, _ = linregress(x, y)
            df_res.loc[start:end, ["trend_id", "trend_direction", "trend_slope", "trend_r_squared"]] = \
                i, "alcista" if slope > 0 else "bajista", slope, r_val**2
        
        df_res["trend_id"] = df_res["trend_id"].astype("Int64")
        return df_res
