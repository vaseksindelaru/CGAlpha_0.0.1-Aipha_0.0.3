# Signal Detector — Triple Coincidence System
**AIPHA System · Documentación Técnica**

---

## ¿Qué es el Sistema de Triple Coincidencia?

El Signal Detector es un framework de análisis técnico avanzado que identifica oportunidades de trading de alta probabilidad buscando la **convergencia simultánea de tres factores independientes** en el mismo punto del gráfico. La lógica es simple pero poderosa: una señal generada por un único factor es frágil; una señal confirmada por tres factores independientes es estadísticamente mucho más fiable.

```
Vela Clave  +  Zona de Acumulación  +  Mini-Tendencia  →  Triple Signal
```

---

## Los Tres Componentes

### 1. Vela Clave (`key_candles`)

Una vela que destaca morfológicamente respecto a su entorno, indicando un posible punto de inflexión.

| Criterio | Descripción |
|---|---|
| Volumen alto | Por encima del percentil configurado (VPT) en la ventana lookback |
| Cuerpo pequeño | Porcentaje del cuerpo sobre el rango total ≤ BPT |
| Contexto | Se evalúa contra las N velas anteriores (lookback) |

**Lógica de detección (`detect_candle.py`):**
```python
volume_percentile = np.percentile(data['volume'][idx-lookback:idx], VPT)
body_percentage   = 100 * abs(close - open) / (high - low)

is_key_candle = (volume >= volume_percentile) AND (body_percentage <= BPT)
```

**Puntuación de la vela:**
- Volumen (60%): normalizado al rango 0–1, referencia base = 150
- Morfología (40%): según tamaño de cuerpo

| Tamaño del cuerpo | Score morfológico |
|---|---|
| 15–40% (óptimo) | 1.0 |
| 40–60% (grande) | 0.8 |
| 5–15% (pequeño) | 0.6 |
| < 5% (muy pequeño) | 0.3 |

---

### 2. Zona de Acumulación (`detect_accumulation_zone_results`)

Área donde el precio consolida durante varios periodos con volumen significativo, indicando acumulación o distribución previa a un movimiento.

| Criterio | Descripción |
|---|---|
| Rango acotado | El precio permanece dentro de un rango estrecho (ATR × Multiplier) |
| Volumen elevado | Promedio de volumen ≥ `volume_threshold` |
| Cohesión | Factor de calidad interno del rango (`quality_score`) |

**Puntuación de la zona:**
```
zona_score = (quality_score - 0.45) / 0.4
```
Normalizado al rango de calidad efectivo: 0.45 → 0.85

---

### 3. Mini-Tendencia (`mini_trend_results`)

Segmento de precio con dirección definida, identificado mediante algoritmo ZigZag y regresión lineal.

| Criterio | Descripción |
|---|---|
| Pendiente | Clara dirección positiva (alcista) o negativa (bajista) |
| R² significativo | Indica qué tan bien ajusta la línea de tendencia al precio |
| Duración mínima | Evita segmentos cortos y aleatorios |

**Puntuación de la tendencia:**

| Categoría R² | Factor |
|---|---|
| R² ≥ 0.60 (Premium) | × 1.3 (premio) |
| R² ≥ 0.45 (Estándar) | × 1.0 (neutro) |
| R² < 0.45 (Básico) | × 0.9 (penalización leve) |

**Factor direccional:**

| Dirección | Factor |
|---|---|
| Alcista | × 1.15 (premio por mejor desempeño histórico) |
| Bajista | × 0.90 (neutro) |

---

## Sistema de Puntuación Final

La puntuación final combina los tres componentes en **dos niveles**:

### Nivel 1 — Componentes Básicos (70%)

```
basic_score = 0.35 × zona_score + 0.35 × trend_score + 0.30 × candle_score
```

### Nivel 2 — Factores Avanzados (30%)

| Factor | Peso | Descripción |
|---|---|---|
| Divergencia/Convergencia | 20% | Coherencia y alineación direccional entre los tres componentes |
| Fiabilidad | 15% | Bonus si R² > 0.75 |
| Potencial de Rentabilidad | 15% | Estimación del potencial de movimiento |

**Potencial de rentabilidad:**

| Condición | Valor |
|---|---|
| Alcista + volumen > 80 | 0.85 |
| Alcista + volumen > 50 | 0.75 |
| Bajista + cuerpo > 20% | 0.70 |
| Base (resto) | 0.60 |

### Interpretación del Score Final

| Rango | Calidad |
|---|---|
| < 0.5 | ⚪ Débil |
| 0.5 – 0.6 | 🟡 Moderada |
| 0.6 – 0.7 | 🟠 Fuerte |
| > 0.7 | 🟢 Muy fuerte |

---

## Parámetros de Configuración

### Detección de Vela Clave

| Parámetro | Valor actual | Descripción |
|---|---|---|
| `VPT` (Volume Percentile Threshold) | **70** | Percentil mínimo de volumen para considerar la vela |
| `BPT` (Body Percentage Threshold) | **40** | % máximo de cuerpo sobre el rango total |
| `lookback` | **30** | Ventana de velas hacia atrás para calcular el percentil |

### Detección de Zona de Acumulación

| Parámetro | Valor actual | Descripción |
|---|---|---|
| `ATR Period` | **14** | Periodos para calcular el ATR de referencia |
| `ATR Multiplier` | **1.0** | Factor sobre el ATR para definir el rango de la zona |
| `volume_threshold` | **1.1** | Ratio mínimo de volumen promedio vs. baseline |
| `quality_threshold` | **3.0** | Umbral interno de calidad para aceptar una zona |
| `recency_bonus` | **0.1** | Bonus por zonas más recientes |

### Detección de Mini-Tendencia

| Parámetro | Valor actual | Descripción |
|---|---|---|
| `ZigZag threshold` | Adaptativo (ATR) | Sensibilidad del algoritmo de segmentación |
| `R² mínimo` | **0.45** | R² mínimo para que un segmento sea considerado tendencia |

### Relación Espacial entre Componentes

| Parámetro | Valor actual | Descripción |
|---|---|---|
| `tolerancia de proximidad` | **8 velas** | Distancia máxima (en velas) entre los tres componentes para considerarlos coincidentes |

> **Nota de calibración:** La tolerancia fue ajustada progresivamente desde 3 → 5 → 8 velas para capturar relaciones más flexibles sin perder precisión.

### Umbrales de Calidad para Coincidencia

| Componente | Umbral mínimo |
|---|---|
| `quality_score` (zona) | ≥ 0.45 |
| R² (tendencia) | ≥ 0.45 |

---

## Flujo de Procesamiento

```
1. PREPROCESAMIENTO
   └── Carga OHLCV (CSV) → Normalización → Cálculo ATR, volumen relativo

2. DETECCIÓN INDIVIDUAL
   ├── save_detect_candles.py          → tabla: key_candles
   ├── save_detect_accumulation_zone.py → tabla: detect_accumulation_zone_results
   └── mini_trend.py                   → tabla: mini_trend_results

3. BÚSQUEDA DE COINCIDENCIAS
   └── JOIN SQL con tolerancia espacial (8 velas)
       + Filtro por umbrales mínimos de calidad

4. PUNTUACIÓN Y EVALUACIÓN
   └── Cálculo básico (70%) + Factores avanzados (30%)
       → score final normalizado 0–1

5. ALMACENAMIENTO
   └── Deduplicación → tabla: triple_signals (con JSON de detalles)
```

---

## Archivos del Sistema

| Script | Función |
|---|---|
| `run_combined_detection.py` | Orquestador principal del flujo completo |
| `save_detect_candles.py` | Detección y guardado de velas clave |
| `save_detect_accumulation_zone.py` | Detección y guardado de zonas de acumulación |
| `mini_trend.py` | Segmentación ZigZag + regresión + guardado |
| `save_triple_signals.py` | Cruce de componentes + puntuación + guardado |
| `view_triple_signals.py` | Visualización tabular de señales detectadas |
| `diagnostico_triple.py` | Herramienta de diagnóstico y propuesta de ajustes |

---

## Estructura de la Base de Datos

```
MySQL
├── key_candles                      ← Velas clave detectadas
├── detect_accumulation_zone_results ← Zonas de acumulación
├── mini_trend_results               ← Mini-tendencias (ZigZag + R²)
└── triple_signals                   ← Señales finales (JSON de detalles)
```

---

## Guía de Ajuste de Parámetros

| Objetivo | Ajuste recomendado |
|---|---|
| Más señales detectadas | Bajar `VPT`, subir `BPT`, ampliar `tolerancia`, bajar umbrales R² y quality |
| Señales más precisas | Subir `VPT`, bajar `BPT`, reducir `tolerancia`, subir umbrales R² y quality |
| Mayor sensibilidad a volumen | Bajar `VPT` (más velas clasifican como alta actividad) |
| Zonas más estrictas | Subir `quality_threshold` y `volume_threshold` |
| Tendencias más limpias | Subir R² mínimo (≥ 0.6 para solo tomar tendencias Premium) |

---

## Componentes Reutilizables del Código

Esta sección contiene los bloques de código extraídos directamente del sistema, listos para reutilizar o extender.

---

### Componente 1 — Detector de Velas Clave (`detect_candle.py`)

Clase autocontenida. Solo requiere `pandas` y `numpy`. Entrada: CSV en formato Binance OHLCV.

```python
import pandas as pd
import numpy as np
import os

class Detector:
    """
    Detector de velas clave para la estrategia Shakeout.
    Identifica velas con alto volumen relativo y cuerpo pequeño.
    """

    def __init__(self, csv_path=None):
        self.detection_params = {}
        self.data = None
        if csv_path:
            self.load_csv(csv_path)

    def load_csv(self, csv_path):
        """Carga datos OHLCV desde un CSV en formato Binance."""
        binance_columns = [
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ]
        self.data = pd.read_csv(csv_path, names=binance_columns, header=None)
        # Eliminar columna de índice si viene incluida
        if self.data.columns[0] in ['timestamp', 'open_time']:
            self.data = self.data.iloc[:, 1:]

    def set_detection_params(self,
                             volume_percentile_threshold=70,
                             body_percentage_threshold=40,
                             lookback_candles=30):
        """
        Configura los parámetros de detección.

        Args:
            volume_percentile_threshold (int): Percentil mínimo de volumen (VPT).
                70 = la vela debe estar en el top 30% de volumen.
            body_percentage_threshold (int): % máximo del cuerpo sobre el rango total (BPT).
                40 = cuerpo ≤ 40% del rango high-low.
            lookback_candles (int): Ventana de velas hacia atrás para calcular el percentil.
        """
        self.detection_params = {
            'volume_percentile_threshold': volume_percentile_threshold,
            'body_percentage_threshold': body_percentage_threshold,
            'lookback_candles': lookback_candles
        }

    def detect_key_candle(self, index):
        """
        Evalúa si la vela en `index` es una vela clave.

        Returns:
            bool: True si cumple criterios de volumen alto y cuerpo pequeño.
        """
        vpt      = self.detection_params.get('volume_percentile_threshold', 80)
        bpt      = self.detection_params.get('body_percentage_threshold', 30)
        lookback = self.detection_params.get('lookback_candles', 50)

        if self.data is None or index < lookback:
            return False

        volume_percentile = np.percentile(
            self.data['volume'].iloc[index - lookback:index], vpt
        )
        current       = self.data.iloc[index]
        body_size     = abs(current['close'] - current['open'])
        candle_range  = current['high'] - current['low']

        if candle_range == 0:
            return False

        body_pct     = 100 * body_size / candle_range
        is_high_vol  = current['volume'] >= volume_percentile
        is_small_body = body_pct <= bpt

        return is_high_vol and is_small_body

    def process_csv(self):
        """
        Recorre todo el DataFrame y retorna la lista de velas clave detectadas.

        Returns:
            list[dict]: Cada dict contiene index, OHLCV, volume_percentile,
                        body_percentage, is_key_candle, timestamp.
        """
        if self.data is None:
            return []

        vpt      = self.detection_params.get('volume_percentile_threshold', 80)
        bpt      = self.detection_params.get('body_percentage_threshold', 30)
        lookback = self.detection_params.get('lookback_candles', 50)
        key_candles = []

        for idx in range(lookback, len(self.data)):
            vol_pct    = float(np.percentile(self.data['volume'].iloc[idx - lookback:idx], vpt))
            current    = self.data.iloc[idx]
            body_size  = abs(float(current['close']) - float(current['open']))
            rng        = float(current['high']) - float(current['low'])

            if rng == 0:
                continue

            body_pct      = 100 * body_size / rng
            is_key_candle = (float(current['volume']) >= vol_pct) and (body_pct <= bpt)

            if is_key_candle:
                timestamp = (
                    self.data.iloc[idx].get('timestamp') or
                    self.data.iloc[idx].get('open_time')
                )
                key_candles.append({
                    'index':            idx,
                    'open':             float(current['open']),
                    'high':             float(current['high']),
                    'low':              float(current['low']),
                    'close':            float(current['close']),
                    'volume':           float(current['volume']),
                    'volume_percentile': vol_pct,
                    'body_percentage':  body_pct,
                    'is_key_candle':    True,
                    'timestamp':        timestamp
                })

        return key_candles


# ── Uso rápido ────────────────────────────────────────────────────────────────
# detector = Detector('BTCUSDT-1h.csv')
# detector.set_detection_params(
#     volume_percentile_threshold=70,   # top 30% volumen
#     body_percentage_threshold=40,     # cuerpo ≤ 40% del rango
#     lookback_candles=30
# )
# resultados = detector.process_csv()
# print(f"{len(resultados)} velas clave encontradas")
```

---

### Componente 2 — Detector de Zona de Acumulación (`detect_accumulation_zone.py`)

Clase que busca la mejor zona de acumulación previa a cada vela clave. Requiere `pandas`, `numpy` y `pandas_ta`.

```python
import pandas as pd
import numpy as np
import pandas_ta as ta
import os, logging

class AccumulationZoneDetector:
    """
    Detecta zonas de acumulación (price consolidation + volume) anteriores
    a las velas clave. Utiliza Volume Profile, VWAP, MFI y ATR dinámico.
    """

    def __init__(self, csv_path=None):
        self.data   = None
        self.params = {
            'atr_period':          14,   # Periodos para ATR
            'atr_multiplier':      1.5,  # Amplitud máxima del rango (× ATR)
            'volume_threshold':    1.2,  # Ratio volumen zona vs. global
            'min_zone_bars':       5,    # Mínimo de barras en la zona
            'volume_profile_bins': 50,   # Resolución del Volume Profile
            'mfi_period':          14,   # Periodos para MFI
            'sma_period':          200,  # Periodos para SMA (contexto)
            'quality_threshold':   0.7   # Score mínimo de calidad (0-1)
        }
        if csv_path:
            self.load_csv(csv_path)

    def load_csv(self, csv_path):
        """Carga CSV Binance OHLCV y añade columna datetime."""
        binance_columns = [
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ]
        self.data = pd.read_csv(csv_path, names=binance_columns, header=None)
        self.data = self.data.iloc[1:].reset_index(drop=True)
        for col in ['open', 'high', 'low', 'close', 'volume']:
            self.data[col] = pd.to_numeric(self.data[col])
        self.data['datetime'] = pd.to_datetime(self.data['timestamp'], unit='us')

    def set_params(self, **kwargs):
        """Actualiza parámetros. Acepta cualquier clave del dict self.params."""
        self.params.update(kwargs)

    # ── Helpers internos ──────────────────────────────────────────────────────

    def _dynamic_lookback(self, index):
        """Lookback adaptativo basado en ATR relativo al precio."""
        atr = self.data.ta.atr(length=self.params['atr_period']).iloc[index]
        lb  = max(self.params['min_zone_bars'],
                  int(atr / self.data['close'].iloc[index] * 1000))
        return min(lb, 50)

    def _volume_profile_poc(self, start, end):
        """Calcula el POC (Price at max volume) y el volumen total del segmento."""
        seg       = self.data.iloc[start:end]
        p_min     = seg['low'].min()
        p_max     = seg['high'].max()
        p_range   = max(p_max - p_min, 0.001)
        n_bins    = self.params['volume_profile_bins']
        bin_size  = p_range / n_bins
        profile   = np.zeros(n_bins)

        for _, c in seg.iterrows():
            lo_b = max(0, min(int((c['low']  - p_min) / bin_size), n_bins - 1))
            hi_b = max(0, min(int((c['high'] - p_min) / bin_size), n_bins - 1))
            if lo_b == hi_b:
                profile[lo_b] += c['volume']
            else:
                c_range = max(c['high'] - c['low'], 0.001)
                for b in range(lo_b, hi_b + 1):
                    overlap = max(0, min(p_min + (b+1)*bin_size, c['high'])
                                     - max(p_min + b*bin_size,   c['low']))
                    profile[b] += c['volume'] * (overlap / c_range)

        poc = p_min + (np.argmax(profile) + 0.5) * bin_size
        return poc, seg['volume'].sum()

    def _vwap(self, start, end):
        """VWAP del segmento [start, end)."""
        tp  = (self.data['high'].iloc[start:end] +
               self.data['low'].iloc[start:end]  +
               self.data['close'].iloc[start:end]) / 3
        vol = self.data['volume'].iloc[start:end]
        return (tp * vol).cumsum().iloc[-1] / vol.cumsum().iloc[-1]

    def _quality_score(self, start, end, range_width, avg_vol, vwap, poc, mfi):
        """
        Calcula el quality_score (0-1) de la zona.

        Criterios ponderados:
          35% rango estrecho  |  35% volumen elevado
          15% precio ≈ VWAP   |  10% MFI en zona neutra (30-70)
           5% contexto SMA    +  bonus por duración (hasta +15%)
        """
        try:
            atr = self.data.ta.atr(length=self.params['atr_period']).iloc[start:end].mean()
            if pd.isna(atr) or atr == 0:
                atr = self.data['close'].iloc[end] * 0.01

            vol_pct = np.percentile(
                self.data['volume'].iloc[max(0, start-150):end], 65
            )

            # Criterio 1: rango estrecho
            range_score  = 1 - min(range_width / (self.params['atr_multiplier'] * atr * 1.5), 1)

            # Criterio 2: volumen
            vol_score    = max(0.3, min(avg_vol / (vol_pct * 0.8), 1) if vol_pct > 0 else 0.3)

            # Criterio 3: precio ≈ VWAP (tolerancia 3%)
            vwap_score   = 1.0 if abs(self.data['close'].iloc[end] - vwap) / vwap <= 0.03 else 0.6

            # Criterio 4: MFI en rango neutro
            mfi_score    = 1.0 if 30 <= mfi <= 70 else 0.6

            # Criterio 5: contexto SMA
            try:
                sma = self.data.ta.sma(length=self.params['sma_period']).iloc[end]
                context_score = 1.0 if (not pd.isna(sma) and
                                        abs(self.data['close'].iloc[end] - sma) / sma <= 0.02
                                       ) else 0.8
            except Exception:
                context_score = 0.8

            quality = (0.35 * range_score + 0.35 * vol_score +
                       0.15 * vwap_score  + 0.10 * mfi_score +
                       0.05 * context_score)

            # Bonus por duración
            n_bars  = end - start
            quality += min(0.15, 0.05 * max(0, n_bars - 2))

            return min(quality, 1.0)
        except Exception:
            return 0.5  # valor neutro ante error

    # ── API pública ───────────────────────────────────────────────────────────

    def detect_accumulation_zone(self, candle_index):
        """
        Busca la mejor zona de acumulación anterior a la vela en `candle_index`.

        Returns:
            dict | None: Zona con start/end, high, low, volume_avg, vwap, poc,
                         mfi, quality_score, datetime_start, datetime_end.
                         None si no se encuentra zona válida.
        """
        if self.data is None or candle_index < self.params['min_zone_bars'] + self.params['atr_period']:
            return None

        lookback   = min(self._dynamic_lookback(candle_index) * 2, 50)
        start_idx  = max(0, candle_index - lookback)

        try:
            atr_series = self.data.ta.atr(length=self.params['atr_period'])
            atr        = atr_series.iloc[start_idx:candle_index].mean()
            if pd.isna(atr) or atr == 0:
                atr = self.data['close'].iloc[candle_index] * 0.01
        except Exception:
            atr = self.data['close'].iloc[candle_index] * 0.01

        best_zone    = None
        best_quality = 0
        min_window   = max(self.params['min_zone_bars'], 2)
        price_2pct   = self.data['close'].iloc[candle_index] * 0.02

        for win in range(min_window, min(lookback, 15) + 1):
            for ws in range(start_idx, candle_index - win + 1):
                we        = ws + win
                high_max  = self.data['high'].iloc[ws:we].max()
                low_min   = self.data['low'].iloc[ws:we].min()
                rng       = high_max - low_min

                # Filtro 1: rango estrecho
                if rng > self.params['atr_multiplier'] * atr * 1.5:
                    continue

                # Filtro 2: volumen suficiente
                avg_vol    = self.data['volume'].iloc[ws:we].mean()
                global_avg = self.data['volume'].iloc[max(0, start_idx-50):candle_index].mean()
                if avg_vol < max(0.5, self.params['volume_threshold']) * global_avg * 0.7:
                    continue

                # Filtro 3: zona toca la vela clave (±2% precio)
                c_high = self.data['high'].iloc[candle_index]
                c_low  = self.data['low'].iloc[candle_index]
                touches = (
                    (low_min  <= c_high + price_2pct and high_max >= c_low - price_2pct) or
                    (abs(high_max - c_low) <= price_2pct) or
                    (abs(low_min  - c_high) <= price_2pct)
                )
                if not touches:
                    continue

                # Calcular métricas
                poc, vol_total = self._volume_profile_poc(ws, we)
                vwap           = self._vwap(ws, we)
                try:
                    mfi_s = self.data.ta.mfi(
                        high=self.data['high'], low=self.data['low'],
                        close=self.data['close'], volume=self.data['volume'],
                        length=self.params['mfi_period']
                    )
                    mfi = mfi_s.iloc[candle_index] if not pd.isna(mfi_s.iloc[candle_index]) else 50
                except Exception:
                    mfi = 50

                quality = self._quality_score(ws, we, rng, avg_vol, vwap, poc, mfi)

                # Bonus de recencia
                quality += 0.2 * (1 - (candle_index - we) / lookback)

                if quality > best_quality and quality >= self.params['quality_threshold'] * 0.8:
                    best_quality = quality
                    best_zone = {
                        'start_idx':      ws,
                        'end_idx':        we,
                        'high':           high_max,
                        'low':            low_min,
                        'volume_avg':     avg_vol,
                        'vol_total':      vol_total,
                        'vwap':           vwap,
                        'poc':            poc,
                        'mfi':            mfi,
                        'quality_score':  quality,
                        'datetime_start': self.data['datetime'].iloc[ws],
                        'datetime_end':   self.data['datetime'].iloc[we],
                    }

        return best_zone

    def process_candles(self, key_candle_indices):
        """
        Procesa una lista de índices de velas clave.

        Args:
            key_candle_indices (list[int]): Índices de las velas clave.

        Returns:
            list[dict]: Zonas de acumulación detectadas.
        """
        zones = []
        for idx in key_candle_indices:
            zone = self.detect_accumulation_zone(idx)
            if zone:
                zones.append(zone)
        print(f"Zonas detectadas: {len(zones)} / {len(key_candle_indices)} velas clave")
        return zones


# ── Uso rápido ────────────────────────────────────────────────────────────────
# detector = AccumulationZoneDetector('BTCUSDT-1h.csv')
# detector.set_params(
#     atr_period=14,
#     atr_multiplier=1.5,
#     volume_threshold=1.2,
#     min_zone_bars=5,
#     quality_threshold=0.7
# )
# key_indices = [120, 250, 380]   # índices de velas clave previas
# zones = detector.process_candles(key_indices)
```

---

### Componente 3 — Cálculo del Quality Score de Zona (función standalone)

Versión desacoplada de `_quality_score`, útil para pruebas o integración en otros sistemas.

```python
def calculate_zone_quality(range_width, avg_vol, vwap, close_price,
                            mfi, atr, vol_percentile_65,
                            sma=None, n_bars=0,
                            atr_multiplier=1.5):
    """
    Calcula el quality_score de una zona de acumulación (0.0 – 1.0).

    Args:
        range_width         : high_max - low_min de la zona
        avg_vol             : volumen promedio de la zona
        vwap                : VWAP de la zona
        close_price         : precio de cierre al final de la zona
        mfi                 : Money Flow Index al cierre de la zona
        atr                 : ATR promedio de la zona
        vol_percentile_65   : percentil 65 de volumen del contexto
        sma                 : SMA(200) al cierre (None = sin contexto)
        n_bars              : número de barras de la zona
        atr_multiplier      : multiplicador para rango estrecho

    Returns:
        float: score entre 0.0 y 1.0
    """
    range_score  = 1 - min(range_width / (atr_multiplier * atr * 1.5), 1)
    vol_score    = max(0.3, min(avg_vol / (vol_percentile_65 * 0.8), 1))
    vwap_score   = 1.0 if abs(close_price - vwap) / vwap <= 0.03 else 0.6
    mfi_score    = 1.0 if 30 <= mfi <= 70 else 0.6
    ctx_score    = (1.0 if sma and abs(close_price - sma) / sma <= 0.02 else 0.8)

    quality = (0.35 * range_score + 0.35 * vol_score +
               0.15 * vwap_score  + 0.10 * mfi_score +
               0.05 * ctx_score)
    quality += min(0.15, 0.05 * max(0, n_bars - 2))   # bonus duración

    return min(quality, 1.0)
```

---

### Componente 4 — Puntuación Final de Triple Señal (función standalone)

Implementa la fórmula completa del sistema de scoring de dos niveles.

```python
def score_triple_signal(quality_score, r2, slope, direction,
                        candle_volume, body_pct):
    """
    Calcula el score final de una señal de triple coincidencia (0.0 – 1.0).

    Args:
        quality_score  : score de la zona de acumulación (0-1)
        r2             : coeficiente R² de la mini-tendencia (0-1)
        slope          : pendiente normalizada (0-1)
        direction      : 'bullish' | 'bearish'
        candle_volume  : volumen relativo de la vela clave (ref. 150 = máx.)
        body_pct       : tamaño del cuerpo como % del rango total

    Returns:
        dict: {
            'zona_score', 'trend_score', 'candle_score',
            'basic_score', 'convergence', 'reliability',
            'potential', 'final_score', 'label'
        }
    """

    # ── Nivel 1: componentes básicos (70%) ───────────────────────────────────

    # Zona (35%)
    zona_score = max(0.0, min((quality_score - 0.45) / 0.4, 1.0))

    # Mini-tendencia (35%)
    r2_factor  = 1.3 if r2 >= 0.6 else (1.0 if r2 >= 0.45 else 0.9)
    dir_factor = 1.15 if direction == 'bullish' else 0.90
    slope_f    = max(0.3, min(slope, 1.0))
    trend_score = min(r2 * r2_factor * dir_factor * slope_f, 1.0)

    # Vela clave (30%)
    vol_score     = min(candle_volume / 150, 1.0)
    if   15 <= body_pct <= 40:  morph = 1.0
    elif 40 <  body_pct <= 60:  morph = 0.8
    elif  5 <= body_pct <  15:  morph = 0.6
    else:                        morph = 0.3
    candle_score = 0.6 * vol_score + 0.4 * morph

    basic_score = 0.35 * zona_score + 0.35 * trend_score + 0.30 * candle_score

    # ── Nivel 2: factores avanzados (30%) ────────────────────────────────────

    # Convergencia/divergencia (20%)
    scores      = [zona_score, trend_score, candle_score]
    convergence = 1 - (max(scores) - min(scores))   # 1 = perfectamente alineados

    # Fiabilidad (15%)
    reliability = 1.0 if r2 >= 0.75 else (0.7 + r2 * 0.4)

    # Potencial de rentabilidad (15%)
    if   direction == 'bullish' and candle_volume > 80: potential = 0.85
    elif direction == 'bullish' and candle_volume > 50: potential = 0.75
    elif direction == 'bearish' and body_pct > 20:      potential = 0.70
    else:                                                potential = 0.60

    advanced = 0.20 * convergence + 0.15 * reliability + 0.15 * potential
    final    = min(0.70 * basic_score + 0.30 * advanced, 1.0)

    # Etiqueta
    if   final >= 0.7: label = '🟢 Muy fuerte'
    elif final >= 0.6: label = '🟠 Fuerte'
    elif final >= 0.5: label = '🟡 Moderada'
    else:              label = '⚪ Débil'

    return {
        'zona_score':    round(zona_score,   3),
        'trend_score':   round(trend_score,  3),
        'candle_score':  round(candle_score, 3),
        'basic_score':   round(basic_score,  3),
        'convergence':   round(convergence,  3),
        'reliability':   round(reliability,  3),
        'potential':     round(potential,    3),
        'final_score':   round(final,        3),
        'label':         label
    }


# ── Ejemplo de uso ────────────────────────────────────────────────────────────
# result = score_triple_signal(
#     quality_score  = 0.72,    # zona de buena calidad
#     r2             = 0.65,    # tendencia Premium
#     slope          = 0.8,     # pendiente pronunciada
#     direction      = 'bullish',
#     candle_volume  = 90,      # volumen alto (ref 150)
#     body_pct       = 25       # cuerpo óptimo
# )
# print(result)
# → {'final_score': 0.741, 'label': '🟢 Muy fuerte', ...}
```

---

### Componente 5 — Esquema SQL de Tablas

DDL completo para recrear las tablas de almacenamiento en MySQL.

```sql
-- Velas clave detectadas
CREATE TABLE IF NOT EXISTS key_candles (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    candle_index   INT,
    symbol         VARCHAR(20),
    timeframe      VARCHAR(10),
    open           FLOAT, high FLOAT, low FLOAT, close FLOAT,
    volume         FLOAT,
    volume_percentile FLOAT,
    body_percentage   FLOAT,
    timestamp      BIGINT,
    csv_file       VARCHAR(255),
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Zonas de acumulación
CREATE TABLE IF NOT EXISTS detect_accumulation_zone_results (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    start_idx      INT,
    end_idx        INT,
    high           FLOAT, low FLOAT,
    volume_avg     FLOAT, vol_total FLOAT,
    vwap           FLOAT, poc FLOAT, mfi FLOAT,
    quality_score  FLOAT,
    datetime_start DATETIME,
    datetime_end   DATETIME,
    detection_params JSON,
    symbol         VARCHAR(20),
    timeframe      VARCHAR(10),
    csv_file       VARCHAR(255),
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Mini-tendencias (ZigZag + regresión lineal)
CREATE TABLE IF NOT EXISTS mini_trend_results (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    start_idx      INT,
    end_idx        INT,
    direction      VARCHAR(10),   -- 'bullish' | 'bearish'
    slope          FLOAT,
    r2             FLOAT,
    symbol         VARCHAR(20),
    timeframe      VARCHAR(10),
    csv_file       VARCHAR(255),
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Señales de triple coincidencia
CREATE TABLE IF NOT EXISTS triple_signals (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    candle_id      INT,
    zone_id        INT,
    trend_id       INT,
    symbol         VARCHAR(20),
    timeframe      VARCHAR(10),
    final_score    FLOAT,
    zona_score     FLOAT,
    trend_score    FLOAT,
    candle_score   FLOAT,
    direction      VARCHAR(10),
    details        JSON,          -- desglose completo del scoring
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_symbol_tf (symbol, timeframe),
    INDEX idx_score     (final_score)
) ENGINE=InnoDB;
```
