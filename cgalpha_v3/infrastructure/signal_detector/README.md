# CGAlpha v3 — Signal Detector Module

## Descripción

Módulo de detección de señales basado en el sistema de **Triple Coincidence** con lógica correcta de entrenamiento del Oracle.

## Lógica Correcta de la Estrategia

```
1. Datos Binance (OHLCV + Order Book + Trades)
   │
   ▼
2. SignalDetector.detect() → Triple Coincidence (vela clave + zona)
   │
   ▼
3. Rastrear zona activa
   │
   ▼
4. Detectar retest del precio a la zona
   │
   ▼
5. En el MOMENTO DEL RETEST, capturar features:
   - VWAP en ese nivel
   - OBI (order book imbalance)
   - Cumulative delta
   │
   ▼
6. Observar outcome posterior:
   - ¿Rebotó? (BOUNCE)
   - ¿Rompieron? (BREAKOUT)
   │
   ▼
7. Entrenar Oracle: [features del retest] → outcome
```

## Estructura del Módulo

```
cgalpha_v3/infrastructure/signal_detector/
├── __init__.py                    # Exporta TripleCoincidenceDetector
└── triple_coincidence.py          # Implementación con lógica correcta
```

## Componentes Principales

### Dataclasses

- **ActiveZone**: Zona activa detectada por Triple Coincidence
- **RetestEvent**: Evento de retest con features capturadas
- **TrainingSample**: Sample de entrenamiento para Oracle

### Clases

- **KeyCandleDetector**: Detecta velas clave (alto volumen + cuerpo pequeño)
- **AccumulationZoneDetector**: Detecta zonas de acumulación
- **MiniTrendDetector**: Detecta mini-tendencias
- **TripleCoincidenceDetector**: Wrapper principal con lógica correcta

## Uso Básico

### 1. Configurar el Detector

```python
from cgalpha_v3.infrastructure.signal_detector import TripleCoincidenceDetector

config = {
    'volume_percentile_threshold': 70,
    'body_percentage_threshold': 40,
    'lookback_candles': 30,
    'atr_period': 14,
    'atr_multiplier': 1.5,
    'volume_threshold': 1.2,
    'min_zone_bars': 5,
    'quality_threshold': 0.45,
    'r2_min': 0.45,
    'proximity_tolerance': 8,
    'retest_timeout_bars': 50,      # Máximo velas para esperar retest
    'outcome_lookahead_bars': 10    # Velas para determinar outcome
}

detector = TripleCoincidenceDetector(config)
```

### 2. Procesar Stream con Lógica Correcta

```python
import pandas as pd

# Cargar datos OHLCV
df = pd.read_csv('BTCUSDT-1h.csv')

# Cargar features de microestructura (opcional)
micro_df = pd.read_csv('BTCUSDT-1h-micro.csv')  # VWAP, OBI, delta

# Procesar stream con lógica correcta
retest_events = detector.process_stream(df, micro_features=micro_df)

for event in retest_events:
    print(f"Retest en índice: {event.retest_index}")
    print(f"Precio: {event.retest_price}")
    print(f"VWAP: {event.vwap_at_retest}")
    print(f"OBI: {event.obi_10_at_retest}")
    print(f"Delta: {event.cumulative_delta_at_retest}")
    print(f"Outcome: {event.outcome}")
```

### 3. Obtener Dataset de Entrenamiento

```python
# El detector genera automáticamente TrainingSamples
training_samples = detector.get_training_dataset()

for sample in training_samples:
    print(f"Features: {sample.features}")
    print(f"Outcome: {sample.outcome}")
```

### 4. Entrenar Oracle con el Dataset

```python
from cgalpha_v3.lila.llm.oracle import OracleTrainer_v3

oracle = OracleTrainer_v3.create_default()

# Cargar dataset
training_data = [sample.features for sample in training_samples]
oracle.load_training_dataset(training_data)

# Entrenar modelo
oracle.train_model()
```

### 5. Integración con ExperimentRunner

```python
from cgalpha_v3.application.experiment_runner import ExperimentRunner

runner = ExperimentRunner()

# Configurar el detector
runner.set_signal_detector(config)

# Procesar retests
retest_events = runner.process_retests(rows, micro_features)

# Obtener dataset de entrenamiento
training_dataset = runner.get_training_dataset()
```

## API Endpoints

### GET /api/signal-detector/config
Lee la configuración actual del Signal Detector.

```bash
curl -H "Authorization: Bearer cgalpha-v3-local-dev" \
     http://localhost:8080/api/signal-detector/config
```

### POST /api/signal-detector/config
Actualiza la configuración del Signal Detector.

```bash
curl -X POST \
     -H "Authorization: Bearer cgalpha-v3-local-dev" \
     -H "Content-Type: application/json" \
     -d '{"enabled": true, "volume_percentile_threshold": 75}' \
     http://localhost:8080/api/signal-detector/config
```

## Parámetros de Configuración

| Parámetro | Default | Descripción |
|-----------|---------|-------------|
| `volume_percentile_threshold` | `70` | Percentil mínimo de volumen (VPT) |
| `body_percentage_threshold` | `40` | % máximo del cuerpo sobre rango (BPT) |
| `lookback_candles` | `30` | Ventana de lookback |
| `atr_period` | `14` | Periodos para ATR |
| `atr_multiplier` | `1.5` | Multiplicador ATR para zonas |
| `volume_threshold` | `1.2` | Ratio volumen zona vs global |
| `min_zone_bars` | `5` | Mínimo de barras en zona |
| `quality_threshold` | `0.45` | Score mínimo de calidad de zona |
| `r2_min` | `0.45` | R² mínimo para tendencia |
| `proximity_tolerance` | `8` | Tolerancia espacial (velas) |
| `min_signal_quality` | `0.65` | Score mínimo para aceptar señal |
| `retest_timeout_bars` | `50` | Máximo velas para esperar retest |
| `outcome_lookahead_bars` | `10` | Velas para determinar outcome |

## Scoring de Señales

El score final combina componentes básicos (70%) y factores avanzados (30%):

### Componentes Básicos (70%)
- **Zona (35%)**: `(quality_score - 0.45) / 0.4`
- **Tendencia (35%)**: `R² × factor_R² × factor_dirección × slope_normalizado`
- **Vela Clave (30%)**: `0.6 × volumen_normalizado + 0.4 × morfología`

### Factores Avanzados (30%)
- **Convergencia (20%)**: Alineación entre los tres componentes
- **Fiabilidad (15%)**: Bonus si R² > 0.75
- **Potencial (15%)**: Estimación de movimiento

### Interpretación del Score

| Rango | Calidad |
|-------|---------|
| < 0.5 | ⚪ Débil |
| 0.5 – 0.6 | 🟡 Moderada |
| 0.6 – 0.7 | 🟠 Fuerte |
| > 0.7 | 🟢 Muy fuerte |

## Integración con Oracle (Meta-Labeling)

El Signal Detector genera automáticamente el dataset de entrenamiento para el Oracle.

### Flujo de Integración

```
SignalDetector.process_stream()
    │
    ▼
Detecta zonas activas
    │
    ▼
Detecta retests
    │
    ▼
Captura features en retest (VWAP, OBI, delta)
    │
    ▼
Determina outcome (BOUNCE vs BREAKOUT)
    │
    ▼
Genera TrainingSample
    │
    ▼
Oracle.load_training_dataset()
    │
    ▼
Oracle.train_model()
    │
    ▼
Oracle.predict() → Predice outcome de nuevos retests
```

### Features Capturadas en Retest

- **vwap_at_retest**: VWAP en el momento del retest
- **obi_10_at_retest**: Order Book Imbalance (10 niveles)
- **cumulative_delta_at_retest**: Delta acumulado
- **delta_divergence**: "BULLISH_ABSORPTION" | "BEARISH_EXHAUSTION"
- **atr_14**: ATR de contexto
- **regime**: "TREND" | "LATERAL" | "HIGH_VOL"
- **direction**: "bullish" | "bearish"

### Outcome

- **BOUNCE**: El precio rebotó de la zona
- **BREAKOUT**: El precio rompió la zona

## Integración con Library

El Signal Detector está registrado como fuente primary en la Library:

```python
LibrarySource(
    source_id="signal-detector-triple-coincidence",
    title="Signal Detector — Triple Coincidence System",
    source_type="primary",
    venue="cgalpha_internal",
    tags=["signal_detection", "triple_coincidence", "technical_analysis"]
)
```

## Tests

Ejecutar tests de integración:

```bash
PYTHONPATH=/home/vaclav/CGAlpha_0.0.1-Aipha_0.0.3 python cgalpha_v3/tests/test_signal_detector_integration.py
```

Tests incluidos:
- `test_signal_detector_integration()` — Configuración del detector
- `test_process_retests_with_mock_data()` — Procesamiento de retests
- `test_get_training_dataset()` — Generación de dataset
- `test_oracle_load_training_dataset()` — Integración con Oracle

## Referencias

- Documentación original: `signal_detector_doc.md`
- Domain models: `cgalpha_v3/domain/models/signal.py`
- Experiment Runner: `cgalpha_v3/application/experiment_runner.py`
- Oracle (Meta-Labeling): `cgalpha_v3/lila/llm/oracle.py`
- Oracle Construction Guide: `legacy_vault/documentation/docs/archive/module_guides/oracle_construction_guide.md`
- Legacy indicators: `cgalpha_v3/indicators/legacy_signals.py` (VWAP, OBI, Delta)
- Zone monitor: `cgalpha_v3/indicators/zone_monitors.py` (detección de retests)
