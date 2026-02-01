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
│   └── risk_managers/    # Gestión de SL/TP dinámicos
├── strategies/           # Ensamblaje de bloques en flujos completos
│   └── proof_strategy.py # Estrategia de prueba inicial
├── docs/                 # Guías detalladas de construcción
└── README.md             # Este archivo
```

## 🧩 Componentes Implementados

### 1. Detectors (`SignalDetector`)
Localizado en `building_blocks/detectors/key_candle_detector.py`.
- **Lógica**: Utiliza percentiles de volumen y análisis del cuerpo de la vela para identificar momentos de alta actividad con baja convicción direccional (velas clave).
- **Output**: Columna booleana `is_key_candle` en el DataFrame.

### 2. Labelers (`PotentialCaptureEngine`)
Localizado en `building_blocks/labelers/potential_capture_engine.py`.
- **Lógica**: Implementa una versión simplificada del *Triple Barrier Method*.
- **Barreras**: Utiliza el ATR (Average True Range) para definir niveles de Take Profit y Stop Loss dinámicos adaptados a la volatilidad actual.
- **Output**: Etiquetas `1` (éxito), `-1` (fallo), `0` (límite de tiempo).

### 3. Strategies (`proof_strategy.py`)
El script principal que demuestra la integración:
1. Carga datos reales de `data_processor` (DuckDB).
2. Ejecuta la detección de señales.
3. Evalúa el potencial de cada señal.
4. Genera estadísticas de rendimiento (Win Rate, distribución de etiquetas).

## 🚀 Cómo empezar
Para ejecutar la estrategia de prueba y ver los resultados en consola:
```bash
python3 trading_manager/strategies/proof_strategy.py
```

## 📈 Verificación
El Trading Manager ha sido verificado con datos reales de BTCUSDT (1h) de Q1 2024, demostrando la capacidad del sistema para procesar miles de velas y generar métricas de rendimiento en segundos.
