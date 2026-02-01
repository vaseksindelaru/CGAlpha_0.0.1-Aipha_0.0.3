import pandas as pd
import numpy as np
import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

def get_atr_labels(
    prices: pd.DataFrame,
    t_events: pd.Index,
    sides: Optional[pd.Series] = None,
    atr_period: int = 14,
    tp_factor: float = 2.0,
    sl_factor: float = 1.0,
    time_limit: int = 24,
    profit_factors: Optional[List[float]] = None,
    drawdown_threshold: float = 0.8,
    return_trajectories: bool = True
) -> pd.Series:
    """
    🚨 **VERSION 0.0.3 - SENSOR ORDINAL** 🚨
    
    Triple Barrier Method MODIFICADO para CGAlpha:
    - NO hace 'break' al tocar TP (registra trayectoria completa)
    - Soporta múltiples niveles de TP (profit_factors)
    - Calcula MFE (Max Favorable Excursion) y MAE (Max Adverse Excursion)
    - Retorna resultado ORDINAL (0, 1, 2, 3+) en lugar de binario
    
    CAMBIOS vs v0.0.2:
    1. ❌ ELIMINADO: 'break' en líneas 94-96, 101-103
    2. ✅ AGREGADO: Tracking completo de trayectoria
    3. ✅ AGREGADO: Múltiples niveles de TP (escalones)
    4. ✅ AGREGADO: Drawdown tolerance para SL inteligente
    
    Args:
        prices: DataFrame con columnas High, Low, Close.
        t_events: Índice de timestamps donde ocurrió una señal.
        sides: Serie con el lado de la señal (1 o -1) para cada timestamp en t_events.
        atr_period: Periodo para el cálculo del ATR.
        tp_factor: Multiplicador del ATR para el Take Profit (si profit_factors=None).
        sl_factor: Multiplicador del ATR para el Stop Loss.
        time_limit: Número máximo de velas para mantener la posición.
        profit_factors: Lista de factores para TPs escalonados [1.0, 2.0, 3.0]
        drawdown_threshold: Tolerancia al drawdown (0.8 = acepta 80% de dd antes de SL)
        return_trajectories: Si True, retorna dict con MFE/MAE/Ordinal
        
    Returns:
        Si return_trajectories=False: Serie con etiquetas ordinales (0, 1, 2, 3+)
        Si return_trajectories=True: Dict con {labels, mfe_atr, mae_atr, highest_tp_hit}
    """
    if t_events.empty:
        if return_trajectories:
            return {
                'labels': pd.Series(dtype='int64'),
                'mfe_atr': pd.Series(dtype='float64'),
                'mae_atr': pd.Series(dtype='float64'),
                'highest_tp_hit': pd.Series(dtype='int64')
            }
        return pd.Series(dtype='int64')

    # 1. Calcular ATR (Average True Range)
    high_low = prices['High'] - prices['Low']
    high_close = abs(prices['High'] - prices['Close'].shift())
    low_close = abs(prices['Low'] - prices['Close'].shift())
    
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(window=atr_period).mean()

    # 2. Configurar profit factors (niveles de TP)
    if profit_factors is None:
        profit_factors = [tp_factor]
    else:
        profit_factors = sorted(profit_factors)  # Asegurar orden ascendente

    labels = []
    mfe_list = []  # Max Favorable Excursion
    mae_list = []  # Max Adverse Excursion
    tp_hits = []   # Nivel de TP alcanzado
    
    for start_time in t_events:
        if start_time not in prices.index:
            labels.append(0)
            mfe_list.append(0.0)
            mae_list.append(0.0)
            tp_hits.append(0)
            continue
            
        # Determinar el lado (por defecto Long si no se provee)
        side = sides.loc[start_time] if sides is not None else 1
        if isinstance(side, pd.Series):
            side = side.iloc[0]
            
        # Obtener datos desde el evento
        idx = prices.index.get_loc(start_time)
        if isinstance(idx, slice):
            idx = idx.start
        elif isinstance(idx, np.ndarray):
            idx = np.where(idx)[0][0]
            
        future_prices = prices.iloc[idx : idx + time_limit + 1]
        
        if len(future_prices) < 2:
            labels.append(0)
            mfe_list.append(0.0)
            mae_list.append(0.0)
            tp_hits.append(0)
            continue
            
        entry_price = future_prices.iloc[0]['Close']
        current_atr = atr.loc[start_time]
        if isinstance(current_atr, pd.Series):
            current_atr = current_atr.iloc[0]
        
        if pd.isna(current_atr) or current_atr == 0:
            labels.append(0)
            mfe_list.append(0.0)
            mae_list.append(0.0)
            tp_hits.append(0)
            continue

        # 3. Definir barreras según el lado
        if side == 1:  # Long
            tp_barriers = {i+1: entry_price + (current_atr * pf) 
                          for i, pf in enumerate(profit_factors)}
            sl_barrier = entry_price - (current_atr * sl_factor)
        else:  # Short
            tp_barriers = {i+1: entry_price - (current_atr * pf) 
                          for i, pf in enumerate(profit_factors)}
            sl_barrier = entry_price + (current_atr * sl_factor)
        
        # 4. 🚨 TRACKING COMPLETO (Sin break) 🚨
        label = 0  # Default: Time limit reached
        max_favorable = entry_price
        max_adverse = entry_price
        highest_tp_level = 0
        sl_triggered = False
        
        # Recorrer el futuro COMPLETO (no breaking early)
        for i in range(1, len(future_prices)):
            high = future_prices.iloc[i]['High']
            low = future_prices.iloc[i]['Low']
            
            if side == 1:  # Lógica Long
                # Actualizar MFE
                if high > max_favorable:
                    max_favorable = high
                    
                # Actualizar MAE
                if low < max_adverse:
                    max_adverse = low
                
                # 🔍 Verificar niveles de TP (del más alto al más bajo)
                for level, tp_price in sorted(tp_barriers.items(), reverse=True):
                    if high >= tp_price and level > highest_tp_level:
                        highest_tp_level = level
                
                # 🛑 Verificar SL (con tolerancia a drawdown)
                if not sl_triggered and low <= sl_barrier:
                    # Análisis de drawdown antes de SL
                    if max_favorable > entry_price:
                        # Estuvimos en ganancias
                        gain = max_favorable - entry_price
                        drawdown = (max_favorable - low) / gain if gain > 0 else 0
                        
                        if drawdown < drawdown_threshold:
                            # DD aceptable, seguimos en posición
                            pass
                        else:
                            # DD excesivo, marcar SL
                            sl_triggered = True
                            label = -1
                    else:
                        # Nunca estuvimos en ganancias, SL directo
                        sl_triggered = True
                        label = -1
                        
            else:  # Lógica Short
                # Actualizar MFE (en short, favorable es hacia abajo)
                if low < max_favorable:
                    max_favorable = low
                    
                # Actualizar MAE (en short, adverso es hacia arriba)
                if high > max_adverse:
                    max_adverse = high
                
                # Verificar niveles de TP
                for level, tp_price in sorted(tp_barriers.items(), reverse=True):
                    if low <= tp_price and level > highest_tp_level:
                        highest_tp_level = level
                
                # Verificar SL
                if not sl_triggered and high >= sl_barrier:
                    if max_favorable < entry_price:
                        gain = entry_price - max_favorable
                        drawdown = (high - max_favorable) / gain if gain > 0 else 0
                        
                        if drawdown < drawdown_threshold:
                            pass
                        else:
                            sl_triggered = True
                            label = -1
                    else:
                        sl_triggered = True
                        label = -1
        
        # 5. Determinar label final (si no hubo SL, usar el nivel de TP alcanzado)
        if not sl_triggered:
            label = highest_tp_level  # 0 si no tocó ningún TP, 1+ según nivel
        
        # 6. Calcular MFE/MAE en unidades de ATR
        if side == 1:
            mfe_atr = (max_favorable - entry_price) / current_atr
            mae_atr = (max_adverse - entry_price) / current_atr
        else:
            mfe_atr = (entry_price - max_favorable) / current_atr
            mae_atr = (entry_price - max_adverse) / current_atr
        
        labels.append(label)
        mfe_list.append(mfe_atr)
        mae_list.append(mae_atr)
        tp_hits.append(highest_tp_level)

    # 7. Retornar según configuración
    if return_trajectories:
        return {
            'labels': pd.Series(labels, index=t_events),
            'mfe_atr': pd.Series(mfe_list, index=t_events),
            'mae_atr': pd.Series(mae_list, index=t_events),
            'highest_tp_hit': pd.Series(tp_hits, index=t_events)
        }
    else:
        return pd.Series(labels, index=t_events)
