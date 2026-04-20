"""
CGAlpha v3 — Triple Coincidence Signal Detector (CORRECTED LOGIC)
=================================================================
Lógica correcta de la estrategia:
1. Detectar Triple Coincidence (vela clave + zona)
2. Rastrear zona activa
3. Detectar retest del precio a la zona
4. Capturar features en el momento del retest (VWAP, OBI, cumulative delta)
5. Observar outcome (rebote vs ruptura)
6. Generar dataset para entrenamiento del Oracle
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field


# ──────────────────────────────────────────────────────────────
# DATACLASSES PARA LÓGICA CORRECTA
# ──────────────────────────────────────────────────────────────

@dataclass
class ActiveZone:
    """Zona activa detectada por Triple Coincidence."""
    candle_index: int
    zone_top: float
    zone_bottom: float
    vwap_at_detection: float
    detection_timestamp: int
    direction: str  # 'bullish' or 'bearish'
    key_candle: Dict
    accumulation_zone: Dict
    mini_trend: Dict
    retest_detected: bool = False
    retest_index: Optional[int] = None
    outcome: Optional[str] = None  # 'BOUNCE' | 'BREAKOUT' | 'PENDING'


@dataclass
class RetestEvent:
    """Evento de retest del precio a una zona activa."""
    zone: ActiveZone
    retest_index: int
    retest_price: float
    retest_timestamp: int
    # Features capturadas en el momento del retest
    vwap_at_retest: float
    obi_10_at_retest: float
    cumulative_delta_at_retest: float
    delta_divergence: str
    atr_14: float
    regime: str
    # Outcome observado después del retest
    outcome: Optional[str] = None  # 'BOUNCE' | 'BREAKOUT'
    outcome_confidence: Optional[float] = None


@dataclass
class TrainingSample:
    """Sample de entrenamiento para el Oracle."""
    features: Dict[str, Any]  # VWAP, OBI, delta, etc. en retest
    outcome: str  # 'BOUNCE' | 'BREAKOUT'
    zone_id: str
    retest_timestamp: int


# ──────────────────────────────────────────────────────────────
# COMPONENTE 1 — Detector de Velas Clave
# ──────────────────────────────────────────────────────────────

class KeyCandleDetector:
    """
    Detector de velas clave para la estrategia Triple Coincidence.
    Identifica velas con alto volumen relativo y cuerpo pequeño.
    """

    def __init__(self, config: Dict = None):
        self.config = config or {
            'volume_percentile_threshold': 70,
            'body_percentage_threshold': 40,
            'lookback_candles': 30
        }
        self.data = None

    def load_data(self, data: pd.DataFrame):
        """Carga datos OHLCV."""
        self.data = data.copy()

    def detect(self, index: int) -> Optional[Dict]:
        """
        Evalúa si la vela en `index` es una vela clave.

        Returns:
            dict | None: Información de la vela clave o None
        """
        if self.data is None or index < self.config['lookback_candles']:
            return None

        vpt = self.config['volume_percentile_threshold']
        bpt = self.config['body_percentage_threshold']
        lookback = self.config['lookback_candles']

        volume_percentile = np.percentile(
            self.data['volume'].iloc[index - lookback:index], vpt
        )
        current = self.data.iloc[index]
        body_size = abs(current['close'] - current['open'])
        candle_range = current['high'] - current['low']

        if candle_range == 0:
            return None

        body_pct = 100 * body_size / candle_range
        is_high_vol = current['volume'] >= volume_percentile
        is_small_body = body_pct <= bpt

        if is_high_vol and is_small_body:
            return {
                'index': index,
                'open': float(current['open']),
                'high': float(current['high']),
                'low': float(current['low']),
                'close': float(current['close']),
                'volume': float(current['volume']),
                'volume_percentile': float(volume_percentile),
                'body_percentage': body_pct,
                'timestamp': self.data.index[index] if hasattr(self.data.index[index], '__int__') else index
            }
        return None

    def detect_all(self) -> List[Dict]:
        """Detecta todas las velas clave en el dataset."""
        if self.data is None:
            return []

        key_candles = []
        for idx in range(self.config['lookback_candles'], len(self.data)):
            candle = self.detect(idx)
            if candle:
                key_candles.append(candle)
        return key_candles


# ──────────────────────────────────────────────────────────────
# COMPONENTE 2 — Detector de Zona de Acumulación
# ──────────────────────────────────────────────────────────────

class AccumulationZoneDetector:
    """
    Detecta zonas de acumulación (price consolidation + volume)
    anteriores a las velas clave.
    """

    def __init__(self, config: Dict = None):
        self.config = config or {
            'atr_period': 14,
            'atr_multiplier': 1.5,
            'volume_threshold': 1.2,
            'min_zone_bars': 5,
            'quality_threshold': 0.7
        }
        self.data = None

    def load_data(self, data: pd.DataFrame):
        """Carga datos OHLCV."""
        self.data = data.copy()
        # Asegurar columnas numéricas
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in self.data.columns:
                self.data[col] = pd.to_numeric(self.data[col], errors='coerce')

    def _calculate_atr(self, index: int) -> float:
        """Calcula ATR en el índice dado (optimizado con numpy)."""
        period = self.config['atr_period']
        if index < period:
            return self.data['close'].iloc[index] * 0.01

        high = self.data['high'].values[index - period:index]
        low = self.data['low'].values[index - period:index]
        close = self.data['close'].values[index - period:index]
        close_prev = np.roll(close, 1)
        close_prev[0] = close[0]
        tr = np.maximum(
            high - low,
            np.maximum(np.abs(high - close_prev), np.abs(low - close_prev))
        )
        return float(np.mean(tr))

    def _quality_score(self, start: int, end: int, range_width: float,
                       avg_vol: float, vwap: float, mfi: float) -> float:
        """
        Calcula el quality_score de la zona (0-1).
        """
        try:
            atr = self._calculate_atr(end)
            if atr == 0:
                atr = self.data['close'].iloc[end] * 0.01

            vol_pct = np.percentile(
                self.data['volume'].values[max(0, start - 150):end], 65
            )

            # Criterio 1: rango estrecho
            range_score = 1 - min(range_width / (self.config['atr_multiplier'] * atr * 1.5), 1)

            # Criterio 2: volumen
            vol_score = max(0.3, min(avg_vol / (vol_pct * 0.8), 1)) if vol_pct > 0 else 0.3

            # Criterio 3: precio ≈ VWAP
            vwap_score = 1.0 if abs(self.data['close'].iloc[end] - vwap) / vwap <= 0.03 else 0.6

            # Criterio 4: MFI en rango neutro
            mfi_score = 1.0 if 30 <= mfi <= 70 else 0.6

            quality = (0.35 * range_score + 0.35 * vol_score +
                       0.15 * vwap_score + 0.10 * mfi_score)

            # Bonus por duración
            n_bars = end - start
            quality += min(0.15, 0.05 * max(0, n_bars - 2))

            return min(quality, 1.0)
        except Exception:
            return 0.5

    def _vwap(self, start: int, end: int) -> float:
        """Calcula VWAP del segmento."""
        tp = (self.data['high'].values[start:end] +
              self.data['low'].values[start:end] +
              self.data['close'].values[start:end]) / 3
        vol = self.data['volume'].values[start:end]
        total_vol = vol.sum()
        return float((tp * vol).sum() / total_vol) if total_vol > 0 else float(self.data['close'].iloc[start])

    def detect(self, candle_index: int) -> Optional[Dict]:
        """
        Busca la mejor zona de acumulación anterior a la vela.
        """
        if self.data is None or candle_index < self.config['min_zone_bars']:
            return None

        lookback = min(candle_index, 30)  # Reducido de 50 para performance
        start_idx = max(0, candle_index - lookback)

        best_zone = None
        best_quality = 0
        min_window = max(self.config['min_zone_bars'], 2)

        # Pre-compute candle data una sola vez
        c_high = self.data['high'].iloc[candle_index]
        c_low = self.data['low'].iloc[candle_index]
        c_close = self.data['close'].iloc[candle_index]
        price_2pct = c_close * 0.02
        global_avg = self.data['volume'].values[max(0, start_idx - 50):candle_index].mean()

        for win in range(min_window, min(lookback, 12) + 1):
            for ws in range(start_idx, candle_index - win + 1):
                we = ws + win
                high_max = self.data['high'].values[ws:we].max()
                low_min = self.data['low'].values[ws:we].min()
                rng = high_max - low_min

                atr = self._calculate_atr(we)
                if atr == 0:
                    atr = c_close * 0.01

                # Filtro 1: rango estrecho
                if rng > self.config['atr_multiplier'] * atr * 1.5:
                    continue

                # Filtro 2: volumen suficiente
                avg_vol = self.data['volume'].values[ws:we].mean()
                if avg_vol < max(0.5, self.config['volume_threshold']) * global_avg * 0.7:
                    continue

                # Filtro 3: zona toca la vela clave
                touches = (
                    (low_min <= c_high + price_2pct and high_max >= c_low - price_2pct) or
                    (abs(high_max - c_low) <= price_2pct) or
                    (abs(low_min - c_high) <= price_2pct)
                )
                if not touches:
                    continue

                # Calcular métricas
                vwap = self._vwap(ws, we)
                mfi = 50  # Simplificado
                quality = self._quality_score(ws, we, rng, avg_vol, vwap, mfi)

                # Bonus de recencia
                quality += 0.2 * (1 - (candle_index - we) / lookback) if lookback > 0 else 0

                if quality > best_quality and quality >= self.config['quality_threshold'] * 0.8:
                    best_quality = quality
                    best_zone = {
                        'start_idx': ws,
                        'end_idx': we,
                        'high': float(high_max),
                        'low': float(low_min),
                        'volume_avg': float(avg_vol),
                        'vwap': float(vwap),
                        'mfi': mfi,
                        'quality_score': quality
                    }

        return best_zone

    def detect_all(self, key_candle_indices: List[int]) -> List[Dict]:
        """Detecta zonas para todas las velas clave."""
        zones = []
        for idx in key_candle_indices:
            zone = self.detect(idx)
            if zone:
                zones.append(zone)
        return zones


# ──────────────────────────────────────────────────────────────
# COMPONENTE 3 — Detector de Mini-Tendencia
# ──────────────────────────────────────────────────────────────

class MiniTrendDetector:
    """
    Detecta mini-tendencias usando segmentación ZigZag y regresión lineal.
    """

    def __init__(self, config: Dict = None):
        self.config = config or {
            'r2_min': 0.45,
            'min_trend_length': 5
        }
        self.data = None

    def load_data(self, data: pd.DataFrame):
        """Carga datos OHLCV."""
        self.data = data.copy()

    def _zigzag_segment(self, threshold_pct: float = 0.02) -> List[Dict]:
        """
        Segmentación ZigZag simplificada.
        """
        if self.data is None or len(self.data) < 10:
            return []

        pivots = []
        last_pivot = self.data['close'].iloc[0]
        last_idx = 0
        direction = None

        for i in range(1, len(self.data)):
            price = self.data['close'].iloc[i]
            change_pct = abs(price - last_pivot) / last_pivot

            if change_pct >= threshold_pct:
                direction = 'up' if price > last_pivot else 'down'
                pivots.append({'index': i, 'price': price, 'direction': direction})
                last_pivot = price
                last_idx = i

        # Crear segmentos
        segments = []
        for i in range(len(pivots) - 1):
            start = pivots[i]
            end = pivots[i + 1]
            segments.append({
                'start_idx': start['index'],
                'end_idx': end['index'],
                'direction': start['direction'],
                'start_price': start['price'],
                'end_price': end['price']
            })

        return segments

    def _linear_regression(self, start_idx: int, end_idx: int) -> Dict:
        """
        Calcula regresión lineal y R² para un segmento.
        """
        segment = self.data.iloc[start_idx:end_idx + 1]
        x = np.arange(len(segment))
        y = segment['close'].values

        # Regresión lineal
        coeffs = np.polyfit(x, y, 1)
        slope = coeffs[0]
        intercept = coeffs[1]

        # Calcular R²
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        # Normalizar slope (0-1)
        slope_norm = min(abs(slope) / (segment['close'].mean() * 0.01), 1.0)

        return {
            'slope': float(slope),
            'slope_normalized': slope_norm,
            'r2': float(r2),
            'direction': 'bullish' if slope > 0 else 'bearish'
        }

    def detect_all(self) -> List[Dict]:
        """Detecta todas las mini-tendencias."""
        if self.data is None:
            return []

        segments = self._zigzag_segment()
        trends = []

        for seg in segments:
            if seg['end_idx'] - seg['start_idx'] >= self.config['min_trend_length']:
                regression = self._linear_regression(seg['start_idx'], seg['end_idx'])

                if regression['r2'] >= self.config['r2_min']:
                    trends.append({
                        **seg,
                        **regression
                    })

        return trends


# ──────────────────────────────────────────────────────────────
# COMPONENTE 4 — Scoring de Triple Coincidencia
# ──────────────────────────────────────────────────────────────

def score_triple_signal(quality_score: float, r2: float, slope: float,
                       direction: str, candle_volume: float,
                       body_pct: float) -> Dict[str, Any]:
    """
    Calcula el score final de una señal de triple coincidencia (0.0 – 1.0).
    """
    # Nivel 1: componentes básicos (70%)
    zona_score = max(0.0, min((quality_score - 0.45) / 0.4, 1.0))

    r2_factor = 1.3 if r2 >= 0.6 else (1.0 if r2 >= 0.45 else 0.9)
    dir_factor = 1.15 if direction == 'bullish' else 0.90
    slope_f = max(0.3, min(slope, 1.0))
    trend_score = min(r2 * r2_factor * dir_factor * slope_f, 1.0)

    vol_score = min(candle_volume / 150, 1.0)
    if 15 <= body_pct <= 40:
        morph = 1.0
    elif 40 < body_pct <= 60:
        morph = 0.8
    elif 5 <= body_pct < 15:
        morph = 0.6
    else:
        morph = 0.3
    candle_score = 0.6 * vol_score + 0.4 * morph

    basic_score = 0.35 * zona_score + 0.35 * trend_score + 0.30 * candle_score

    # Nivel 2: factores avanzados (30%)
    scores = [zona_score, trend_score, candle_score]
    convergence = 1 - (max(scores) - min(scores))

    reliability = 1.0 if r2 >= 0.75 else (0.7 + r2 * 0.4)

    if direction == 'bullish' and candle_volume > 80:
        potential = 0.85
    elif direction == 'bullish' and candle_volume > 50:
        potential = 0.75
    elif direction == 'bearish' and body_pct > 20:
        potential = 0.70
    else:
        potential = 0.60

    advanced = 0.20 * convergence + 0.15 * reliability + 0.15 * potential
    final = min(0.70 * basic_score + 0.30 * advanced, 1.0)

    if final >= 0.7:
        label = '🟢 Muy fuerte'
    elif final >= 0.6:
        label = '🟠 Fuerte'
    elif final >= 0.5:
        label = '🟡 Moderada'
    else:
        label = '⚪ Débil'

    return {
        'zona_score': round(zona_score, 3),
        'trend_score': round(trend_score, 3),
        'candle_score': round(candle_score, 3),
        'basic_score': round(basic_score, 3),
        'convergence': round(convergence, 3),
        'reliability': round(reliability, 3),
        'potential': round(potential, 3),
        'final_score': round(final, 3),
        'label': label
    }


# ──────────────────────────────────────────────────────────────
# COMPONENTE 5 — Detector Principal (Triple Coincidence)
# ──────────────────────────────────────────────────────────────

@dataclass
class TripleSignal:
    """Resultado de una detección de triple coincidencia."""
    index: int
    price: float
    direction: str
    quality_score: float
    label: str
    key_candle: Dict
    accumulation_zone: Dict
    mini_trend: Dict
    scoring_details: Dict


class TripleCoincidenceDetector:
    """
    Detector principal con lógica correcta de la estrategia:
    1. Detecta Triple Coincidence (vela clave + zona)
    2. Rastrea zonas activas
    3. Detecta retests del precio
    4. Captura features en el momento del retest
    5. Determina outcome (rebote vs ruptura)
    """

    def __init__(self, config: Dict = None):
        self.config = config or {
            'volume_percentile_threshold': 70,
            'body_percentage_threshold': 40,
            'lookback_candles': 30,
            'atr_period': 14,
            'atr_multiplier': 1.5,
            'volume_threshold': 1.2,
            'min_zone_bars': 5,
            'quality_threshold': 0.45,
            'r2_min': 0.45,
            'min_trend_length': 5,
            'proximity_tolerance': 8,
            'retest_timeout_bars': 50,  # Máximo velas para esperar retest
            'outcome_lookahead_bars': 10,  # Velas para determinar outcome
        }
        self.key_candle_detector = KeyCandleDetector(self.config)
        self.zone_detector = AccumulationZoneDetector(self.config)
        self.trend_detector = MiniTrendDetector(self.config)

        # Estado: zonas activas pendientes de retest
        self.active_zones: List[ActiveZone] = []
        # Dataset de entrenamiento para Oracle
        self.training_samples: List[TrainingSample] = []

    def detect(self, df: pd.DataFrame) -> List[TripleSignal]:
        """
        Detecta señales de Triple Coincidence (método legacy para compatibilidad).
        """
        # Cargar datos en sub-detectores
        self.key_candle_detector.load_data(df)
        self.zone_detector.load_data(df)
        self.trend_detector.load_data(df)

        key_candles = self.key_candle_detector.detect_all()
        zones = self.zone_detector.detect_all([kc['index'] for kc in key_candles])
        trends = self.trend_detector.detect_all()

        coincidences = self._find_coincidences(key_candles, zones, trends, df)
        signals = self._score_signals(coincidences)

        return signals

    def _find_coincidences(self, key_candles: List[Dict],
                          zones: List[Dict], trends: List[Dict],
                          data: pd.DataFrame) -> List[Dict]:
        """
        Busca coincidencias espaciales entre los tres componentes.
        """
        coincidences = []
        tolerance = self.config['proximity_tolerance']

        # Para cada vela clave, buscar zona y tendencia cercanas
        for candle in key_candles:
            candle_idx = candle['index']

            # Buscar zona cercana
            matching_zone = None
            for zone in zones:
                zone_center = (zone['start_idx'] + zone['end_idx']) // 2
                if abs(candle_idx - zone_center) <= tolerance:
                    matching_zone = zone
                    break

            if not matching_zone:
                continue

            # Buscar tendencia cercana
            matching_trend = None
            for trend in trends:
                trend_center = (trend['start_idx'] + trend['end_idx']) // 2
                if abs(candle_idx - trend_center) <= tolerance:
                    matching_trend = trend
                    break

            if not matching_trend:
                continue

            # Verificar umbrales mínimos
            if matching_zone.get('quality_score', 0) < self.config['quality_threshold']:
                continue
            if matching_trend.get('r2', 0) < self.config['r2_min']:
                continue

            coincidences.append({
                'key_candle': candle,
                'accumulation_zone': matching_zone,
                'mini_trend': matching_trend
            })

        return coincidences

    def _score_signals(self, coincidences: List[Dict]) -> List[TripleSignal]:
        """
        Calcula score final para cada coincidencia.
        """
        signals = []

        for coinc in coincidences:
            candle = coinc['key_candle']
            zone = coinc['accumulation_zone']
            trend = coinc['mini_trend']

            scoring = score_triple_signal(
                quality_score=zone.get('quality_score', 0.5),
                r2=trend.get('r2', 0),
                slope=trend.get('slope_normalized', 0),
                direction=trend.get('direction', 'bullish'),
                candle_volume=candle.get('volume_percentile', 0),
                body_pct=candle.get('body_percentage', 30)
            )

            signals.append(TripleSignal(
                index=candle['index'],
                price=candle['close'],
                direction=trend['direction'],
                quality_score=scoring['final_score'],
                label=scoring['label'],
                key_candle=candle,
                accumulation_zone=zone,
                mini_trend=trend,
                scoring_details=scoring
            ))

        return signals

    def process_live_tick(self, new_kline: Dict, micro_data: Dict) -> List[RetestEvent]:
        """
        Procesa una vela cerrada en tiempo real.
        Mantiene el historial interno (buffer) para los cálculos de indicadores.
        """
        # 1. Mantener buffer interno de velas (necesario para indicadores como ATR/regresión)
        if not hasattr(self, '_kline_buffer'):
            self._kline_buffer = []
        
        self._kline_buffer.append(new_kline)
        if len(self._kline_buffer) > 200:
            self._kline_buffer.pop(0)

        if len(self._kline_buffer) < self.config['lookback_candles']:
            return []

        # Convertir buffer a DataFrame para compatibilidad con lógica interna
        df = pd.DataFrame(self._kline_buffer)
        current_idx = len(df) - 1

        # 2. Cargar datos en sub-detectores
        self.key_candle_detector.load_data(df)
        self.zone_detector.load_data(df)
        self.trend_detector.load_data(df)

        retest_events = []

        # 3. Detectar nuevas zonas en esta vela
        new_zones = self._detect_new_zones(df, current_idx)
        self.active_zones.extend(new_zones)

        # 4. Monitorear retests de zonas activas
        for zone in self.active_zones:
            if not zone.retest_detected:
                # Mock de micro-features para la comparación
                # En live, micro_data viene del WS
                mf = pd.DataFrame([micro_data]) 
                # Ajustamos el índice para que coincida con lo esperado por _check_retest
                retest = self._check_retest(df, current_idx, zone, mf.rename(index={0: current_idx}))
                if retest:
                    retest_events.append(retest)
                    zone.retest_detected = True
                    zone.retest_index = current_idx

        # 5. Limpieza de zonas expiradas
        self._cleanup_expired_zones(current_idx)

        return retest_events

    def process_stream(self, df: pd.DataFrame, micro_features: Optional[pd.DataFrame] = None) -> List[RetestEvent]:
        """
        Procesa stream de datos con lógica correcta:
        1. Detecta nuevas zonas (Triple Coincidence)
        2. Monitorea retests de zonas activas
        3. Captura features en retest
        4. Determina outcomes

        Args:
            df: DataFrame OHLCV
            micro_features: DataFrame opcional con VWAP, OBI, cumulative delta

        Returns:
            Lista de RetestEvent detectados
        """
        # Pre-cargar datos en sub-detectores
        self.key_candle_detector.load_data(df)
        self.zone_detector.load_data(df)
        self.trend_detector.load_data(df)

        # Pre-calcular tendencias (no cambian por iteración)
        all_trends = self.trend_detector.detect_all()

        retest_events = []

        for idx in range(len(df)):
            # 1. Detectar nuevas zonas
            new_zones = self._detect_new_zones(df, idx, all_trends)
            self.active_zones.extend(new_zones)

            # 2. Monitorear retests de zonas activas
            for zone in self.active_zones:
                if not zone.retest_detected:
                    retest = self._check_retest(df, idx, zone, micro_features)
                    if retest:
                        retest_events.append(retest)
                        zone.retest_detected = True
                        zone.retest_index = retest.retest_index

                        # 3. Determinar outcome (si hay suficientes datos futuros)
                        if idx + self.config['outcome_lookahead_bars'] < len(df):
                            outcome = self._determine_outcome(df, retest.retest_index, retest.zone)
                            retest.outcome = outcome
                            zone.outcome = outcome

                            # 4. Guardar sample de entrenamiento
                            training_sample = TrainingSample(
                                features={
                                    'vwap_at_retest': retest.vwap_at_retest,
                                    'obi_10_at_retest': retest.obi_10_at_retest,
                                    'cumulative_delta_at_retest': retest.cumulative_delta_at_retest,
                                    'delta_divergence': retest.delta_divergence,
                                    'atr_14': retest.atr_14,
                                    'regime': retest.regime,
                                    'direction': zone.direction,
                                },
                                outcome=outcome,
                                zone_id=f"{zone.candle_index}_{zone.direction}",
                                retest_timestamp=retest.retest_timestamp
                            )
                            self.training_samples.append(training_sample)

            # 3. Limpiar zonas expiradas (timeout)
            self._cleanup_expired_zones(idx)

        return retest_events

    def _detect_new_zones(self, df: pd.DataFrame, current_idx: int,
                          precomputed_trends: List[Dict] = None) -> List[ActiveZone]:
        """Detecta nuevas zonas de Triple Coincidence en el índice actual."""
        if current_idx < self.config['lookback_candles']:
            return []

        # Detectar vela clave en índice actual
        key_candle = self.key_candle_detector.detect(current_idx)
        if key_candle is None:
            return []

        # Buscar zona de acumulación asociada
        zone = self.zone_detector.detect(current_idx)
        if zone is None:
            return []

        # Usar tendencias pre-calculadas o calcular
        trends = precomputed_trends if precomputed_trends is not None else self.trend_detector.detect_all()

        # Buscar coincidencias
        coincidences = self._find_coincidences([key_candle], [zone], trends, df)

        new_zones = []
        for coinc in coincidences:
            candle = coinc['key_candle']
            zone_data = coinc['accumulation_zone']
            trend = coinc['mini_trend']

            active_zone = ActiveZone(
                candle_index=candle['index'],
                zone_top=zone_data.get('high', zone_data.get('zone_top', candle['high'])),
                zone_bottom=zone_data.get('low', zone_data.get('zone_bottom', candle['low'])),
                vwap_at_detection=zone_data.get('vwap', candle['close']),
                detection_timestamp=int(df.iloc[current_idx].get('close_time', candle['index'] * 300000)),
                direction=trend['direction'],
                key_candle=candle,
                accumulation_zone=zone_data,
                mini_trend=trend,
            )
            new_zones.append(active_zone)

        return new_zones

    def _check_retest(self, df: pd.DataFrame, idx: int, zone: ActiveZone,
                     micro_features: Optional[pd.DataFrame] = None) -> Optional[RetestEvent]:
        """Verifica si el precio retestea la zona activa."""
        current_price = df.iloc[idx]['close']

        # Verificar si el precio está en la zona
        if zone.zone_bottom <= current_price <= zone.zone_top:
            # Capturar features del retest
            vwap = micro_features.iloc[idx]['vwap'] if micro_features is not None else zone.vwap_at_detection
            obi_10 = micro_features.iloc[idx]['obi_10'] if micro_features is not None else 0.0
            cumulative_delta = micro_features.iloc[idx]['cumulative_delta'] if micro_features is not None else 0.0

            # Calcular delta divergence
            if zone.direction == 'bullish':
                delta_divergence = "BULLISH_ABSORPTION"
            else:
                delta_divergence = "BEARISH_EXHAUSTION"

            # Calcular ATR
            atr = self._calculate_atr(df, idx)

            # Determinar régimen
            regime = self._determine_regime(df, idx)

            return RetestEvent(
                zone=zone,
                retest_index=idx,
                retest_price=current_price,
                retest_timestamp=int(df.iloc[idx].get('close_time', idx * 300000)),
                vwap_at_retest=vwap,
                obi_10_at_retest=obi_10,
                cumulative_delta_at_retest=cumulative_delta,
                delta_divergence=delta_divergence,
                atr_14=atr,
                regime=regime,
            )

        return None

    def _determine_outcome(self, df: pd.DataFrame, retest_idx: int, zone=None) -> str:
        """Determina outcome (BOUNCE vs BREAKOUT) usando los límites de la zona."""
        if zone is None:
            return 'BOUNCE' # Fallback legacy
        
        lookahead = self.config['outcome_lookahead_bars']
        if retest_idx + lookahead >= len(df):
            return 'PENDING'

        zone_top = zone.zone_top
        zone_bottom = zone.zone_bottom

        for i in range(1, lookahead + 1):
            future_idx = retest_idx + i
            future_close = df.iloc[future_idx]['close']
            
            if zone.direction == 'bullish':
                if future_close < zone_bottom:
                    return 'BREAKOUT'  # rompió hacia abajo
                if future_close > zone_top:
                    return 'BOUNCE'    # rebotó hacia arriba
            else:
                if future_close > zone_top:
                    return 'BREAKOUT'  # rompió hacia arriba
                if future_close < zone_bottom:
                    return 'BOUNCE'    # rebotó hacia abajo
        
        return 'BOUNCE'  # se mantuvo en zona
    def _calculate_atr(self, df: pd.DataFrame, idx: int) -> float:
        """Calcula ATR."""
        period = self.config['atr_period']
        if idx < period:
            return 0.0

        high_range = df.iloc[idx - period:idx + 1]['high'].max()
        low_range = df.iloc[idx - period:idx + 1]['low'].min()
        return high_range - low_range

    def _determine_regime(self, df: pd.DataFrame, idx: int) -> str:
        """Determina régimen de mercado."""
        if idx < 20:
            return 'LATERAL'

        # Calcular R² de regresión lineal
        prices = df.iloc[idx - 20:idx + 1]['close'].values
        x = np.arange(len(prices))
        slope, intercept = np.polyfit(x, prices, 1)
        y_pred = slope * x + intercept
        ss_res = np.sum((prices - y_pred) ** 2)
        ss_tot = np.sum((prices - np.mean(prices)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        if r2 >= 0.6:
            return 'TREND'
        else:
            return 'LATERAL'

    def _cleanup_expired_zones(self, current_idx: int):
        """Elimina zonas que han expirado (timeout)."""
        timeout = self.config['retest_timeout_bars']
        self.active_zones = [
            z for z in self.active_zones
            if current_idx - z.candle_index < timeout and not z.retest_detected
        ]

    def get_training_dataset(self) -> List[TrainingSample]:
        """Retorna dataset de entrenamiento para Oracle."""
        return self.training_samples


# ──────────────────────────────────────────────────────────────
# ADAPTADOR PARA ORACLE INTEGRATION (LEGACY - DEPRECATED)
# ──────────────────────────────────────────────────────────────

def triple_signal_to_microstructure(signal: TripleSignal, data: pd.DataFrame,
                                    symbol: str = "BTCUSDT") -> Dict:
    """
    Convierte TripleSignal a formato compatible con Oracle.

    Nota: Esta es una implementación simplificada que usa placeholders
    para features de microestructura que requieren datos de order book.
    En producción, estos valores deben calcularse desde datos reales.
    """
    candle = signal.key_candle
    zone = signal.accumulation_zone
    trend = signal.mini_trend

    # Calcular VWAP aproximado desde la zona
    vwap = zone.get('vwap', signal.price)

    # Calcular ATR aproximado desde datos
    atr = data['high'].iloc[max(0, signal.index - 14):signal.index + 1].max() - \
          data['low'].iloc[max(0, signal.index - 14):signal.index + 1].min()

    # Placeholder para OBI (requiere order book)
    obi_10 = 0.0

    # Placeholder para cumulative delta (requiere trade-by-trade)
    cumulative_delta = 0.0

    # Determinar delta divergence basado en dirección
    if signal.direction == 'bullish':
        delta_divergence = "BULLISH_ABSORPTION"
    else:
        delta_divergence = "BEARISH_EXHAUSTION"

    # Determinar régimen basado en tendencia
    if trend['r2'] >= 0.6:
        regime = "TREND"
    elif atr > signal.price * 0.01:
        regime = "HIGH_VOL"
    else:
        regime = "LATERAL"

    # Crear dict compatible con MicrostructureRecord
    microstructure = {
        'timestamp': int(signal.index),
        'symbol': symbol,
        'open': candle['open'],
        'high': candle['high'],
        'low': candle['low'],
        'close': candle['close'],
        'volume': candle['volume'],
        'vwap': vwap,
        'vwap_std_1': atr * 0.5,  # Placeholder
        'vwap_std_2': atr * 0.3,  # Placeholder
        'obi_10': obi_10,
        'cumulative_delta': cumulative_delta,
        'delta_divergence': delta_divergence,
        'atr_14': atr,
        'regime': regime
    }

    return microstructure
