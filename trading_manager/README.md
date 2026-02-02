# Aipha Trading Manager

Este nivel del sistema Aipha se encarga de transformar los datos crudos (Data Processor) en señales accionables y estrategias de trading completas.

## 🎯 Propósito
El **Trading Manager** es el motor de ejecución lógica de Aipha. Su función es descomponer la lógica de trading en componentes reutilizables (*Building Blocks*) y ensamblarlos en estrategias coherentes que pueden ser evaluadas y optimizadas.

## 🏗️ Estructura de Directorios

```text
trading_manager/
├── building_blocks/      # Componentes atómicos reutilizables
│   ├── detectors/        # Identificación de eventos (ej: key_candle_detector.py)
│   ├── labelers/         # Motores de etiquetado y potencial (ej: potential_capture_engine.py)
│   ├── posicion_sizers/  # Gestión del tamaño de posición
│   ├── risk_managers/    # Gestión de SL/TP dinámicos
│   └── signal_combiner.py # Combinador de señales para Triple Coincidencia
├── strategies/           # Ensamblaje de bloques en flujos completos
│   └── proof_strategy.py # Estrategia de prueba con Triple Coincidencia en 5m
├── docs/                 # Guías detalladas de construcción
└── README.md             # Este archivo
```

## 🧩 Componentes Implementados

### 1. Triple Coincidencia en 5 Minutos (NEW ✨)
**`SignalCombiner`** + **`proof_strategy.py`** - Implementación completa de la Triple Coincidencia:

**Flujo:**
1. **AccumulationZoneDetector** → Detecta zonas de acumulación en 5m
2. **TrendDetector** → Mide calidad de tendencia (R²) en 5m
3. **KeyCandleDetector** → Encuentra velas clave de absorción en 5m
4. **SignalCombiner** → Fusiona las 3 señales para obtener `is_triple_coincidence`
5. **PotentialCaptureEngine** → Aplica barreras dinámicas de SL/TP

**Características:**
- ✅ Detecta en **temporalidad de 5 minutos** (como especifica la Constitución)
- ✅ Utiliza ATR dinámico para adaptar barreras a volatilidad actual
- ✅ Registra trayectorias completas (MFE/MAE) para análisis causal
- ✅ Genera métricas de Win Rate y rendimiento

### 2. Detectors (`SignalDetector`)
Localizado en `building_blocks/detectors/key_candle_detector.py`.
- **Lógica**: Utiliza percentiles de volumen y análisis del cuerpo de la vela para identificar momentos de alta actividad con baja convicción direccional (velas clave).
- **Output**: Columna booleana `is_key_candle` en el DataFrame.

### 3. AccumulationZoneDetector
Localizado en `building_blocks/detectors/accumulation_zone_detector.py`.
- **Lógica**: Identifica rangos laterales donde el mercado "respira" sin dirección clara.
- **Variables**: ATR-based zone detection con multiplicador configurableOutput**: `in_accumulation_zone`, `zone_id`.

### 4. TrendDetector
Localizado en `building_blocks/detectors/trend_detector.py`.
- **Lógica**: Calcula tendencia mediante regresión lineal (slope) y R² para medir calidad.
- **Output**: `trend_direction`, `trend_slope`, `trend_r_squared`.

### 5. Labelers (`PotentialCaptureEngine`)
Localizado en `building_blocks/labelers/potential_capture_engine.py`.
- **Lógica**: Implementa Triple Barrier Method con ATR dinámico.
- **Barreras**: Utiliza ATR para definir niveles de Take Profit y Stop Loss adaptados a la volatilidad.
- **Output**: Etiquetas `1` (TP hit), `-1` (SL hit), `0` (timeout) + trayectorias (MFE/MAE).

## 🚀 Cómo Empezar

### Paso 1: Descargar Datos de 5 Minutos
```bash
# Descargar solo datos de 5 minutos
python3 data_processor/acquire_data.py --interval 5m

# O descargar ambos (1h y 5m)
python3 data_processor/acquire_data.py --interval all
```

**Salida esperada:**
```
✅ Éxito: ~8900 velas obtenidas (5M).
✅ Datos guardados en la tabla 'btc_5m_data'.
```

### Paso 2: Ejecutar la Estrategia con Triple Coincidencia
```bash
python3 trading_manager/strategies/proof_strategy.py
```

**Salida esperada:**
```
============================================================
INICIANDO PROOF STRATEGY - TRIPLE COINCIDENCIA EN 5 MINUTOS
============================================================
✅ Datos cargados: 8900 velas de 5m de 2024-01-01 a 2024-01-31

--- EJECUTANDO DETECTORES DE TRIPLE COINCIDENCIA ---
1️⃣  Detectando zonas de acumulación...
   ✅ 350 barras en zona de acumulación
2️⃣  Detectando tendencia (R² y Slope)...
   ✅ R² promedio: 0.520
3️⃣  Detectando velas clave (volumen + cuerpo pequeño)...
   ✅ 45 velas clave detectadas

--- COMBINANDO SEÑALES (TRIPLE COINCIDENCIA) ---
✅ 12 TRIPLE COINCIDENCIAS detectadas en 5m

--- ETIQUETANDO 12 SEÑALES CON TRIPLE BARRIER METHOD ---
============================================================
RESULTADOS FINALES - ESTRATEGIA DE 5 MINUTOS
============================================================
  Total Señales Etiquetadas: 12
  Take Profit (TP hit): 8
  Stop Loss (SL hit): 3
  Neutral (Time Limit): 1

  🎯 Win Rate (TP vs Total): 66.67%
✅ Métrica registrada en memoria del sistema.
============================================================
✅ PROOF STRATEGY COMPLETADA
============================================================
```

## 📈 Verificación
El Trading Manager ha sido verificado con datos reales de BTCUSDT en las siguientes temporalidades:
- ✅ **1h (1 hora):** Q1 2024 - Contexto macro
- ✅ **5m (5 minutos):** Enero 2024 - Triple Coincidencia (NEW)

Ambas implementaciones demuestran la capacidad del sistema para procesar miles de velas y generar métricas de rendimiento en segundos.

## 📊 Configuración Avanzada

Los parámetros de la estrategia se definen en el `ConfigManager` (core/config_manager.py):

```python
# Detectores
Trading.volume_lookback = 20
Trading.volume_percentile_threshold = 90
Trading.body_percentile_threshold = 30
Trading.ema_period = 200

# Tendencia
Trading.trend_lookback = 20
Trading.min_r_squared = 0.45

# Zonas
Trading.tolerance_bars = 8

# Barreras Dinámicas (ATR)
Trading.atr_period = 14
Trading.tp_factor = 2.0
Trading.sl_factor = 1.0
Trading.time_limit = 20
```

Modifica estos valores para ajustar la sensibilidad de los detectores.

## 🔄 Próximos Pasos

- [ ] Integrar con Oracle (predicciones probabilísticas)
- [ ] Backtesting con múltiples pares de criptomonedas
- [ ] Optimización de hiperparámetros usando CGAlpha Labs
- [ ] Modo "Paper Trading" para validación en vivo
